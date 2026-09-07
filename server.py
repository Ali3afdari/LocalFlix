import os, json, subprocess, threading
from flask import Flask, jsonify, request, send_file, send_from_directory, abort
from waitress import serve

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
os.makedirs(MEDIA_DIR, exist_ok=True)

VIDEO_EXT = {'.mp4','.webm','.ogg','.mkv','.avi','.mov','.m4v'}
TML = '.tml'
PCTS = [0.10, 0.25, 0.50, 0.70, 0.90]

galleries_state = {}
state_lock = threading.Lock()

def get_state(gallery):
    with state_lock:
        if gallery not in galleries_state:
            galleries_state[gallery] = {'ready': set(), 'processing': set(), 'queue': [], 'worker_running': False, 'lock': threading.Lock()}
        return galleries_state[gallery]

def get_video_info(path):
    try:
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height','-of','json', path],
            capture_output=True, text=True, check=True, timeout=10)
        d = json.loads(r.stdout)
        dur = float(d['format']['duration'])
        w = h = 0
        for s in d.get('streams', []):
            if 'width' in s: w, h = int(s['width']), int(s['height']); break
        return dur, w, h
    except: return 0.0, 0, 0

def gen_thumb(video_path, thumb_path, seek_time):
    cmd = [
        'ffmpeg', '-y', '-hwaccel', 'auto',
        '-ss', str(seek_time), '-i', video_path,
        '-frames:v', '1', '-q:v', '2', thumb_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=20)
        return True
    except: return False

def background_worker(gallery):
    state = get_state(gallery)
    g_path = os.path.join(MEDIA_DIR, gallery)
    tml_path = os.path.join(g_path, TML)
    os.makedirs(tml_path, exist_ok=True)

    while True:
        with state['lock']:
            if not state['queue']:
                state['worker_running'] = False
                break
            item = state['queue'].pop(0)
            state['processing'].add(item['base'])

        base, filename = item['base'], item['name']
        video_path = os.path.join(g_path, filename)
        dur, w, h = get_video_info(video_path)

        if dur > 0:
            for i, pct in enumerate(PCTS):
                gen_thumb(video_path, os.path.join(tml_path, f"{base}_{i+1}.jpg"), dur * pct)

            meta = {"duration": dur, "width": w, "height": h, "size": os.path.getsize(video_path),
                    "lastModified": os.path.getmtime(video_path), "video_name": filename}
            with open(os.path.join(tml_path, f"{base}.json"), 'w') as f:
                json.dump(meta, f)

        with state['lock']:
            state['processing'].discard(base)
            state['ready'].add(base)

def extract_base_from_tml_filename(filename):
    if filename == 'faces_db.json': return None
    if filename.endswith('.json'): return os.path.splitext(filename)[0]
    if filename.endswith('.jpg'):
        no_ext = os.path.splitext(filename)[0]
        parts = no_ext.rsplit('_', 1)
        if len(parts) == 2 and parts[1].isdigit(): return parts[0]
        return no_ext
    return None

# --- NEW: Validates JSON structure to detect corruption ---
def is_meta_valid(meta_file):
    if not os.path.exists(meta_file): return False
    try:
        with open(meta_file, 'r') as f:
            data = json.load(f)
        # Ensure essential keys exist and are valid
        return 'duration' in data and 'video_name' in data and data['duration'] > 0
    except:
        return False

def sync_gallery(gallery):
    state = get_state(gallery)
    g_path = os.path.join(MEDIA_DIR, gallery)
    tml_path = os.path.join(g_path, TML)

    actual_videos = {}
    if os.path.exists(g_path):
        for f in os.listdir(g_path):
            if os.path.splitext(f)[1].lower() in VIDEO_EXT:
                actual_videos[os.path.splitext(f)[0]] = f

    if os.path.exists(tml_path):
        for f in os.listdir(tml_path):
            if not (f.endswith('.json') or f.endswith('.jpg')): continue
            base = extract_base_from_tml_filename(f)
            if base is None: continue
            if base not in actual_videos:
                try: os.remove(os.path.join(tml_path, f))
                except: pass

    with state['lock']:
        state['ready'].clear()
        for base, filename in actual_videos.items():
            meta_file = os.path.join(tml_path, f"{base}.json")
            thumb_1 = os.path.join(tml_path, f"{base}_1.jpg")

            # Check if thumb exists AND metadata is valid
            if os.path.exists(thumb_1) and is_meta_valid(meta_file):
                state['ready'].add(base)
            else:
                # If metadata is corrupted/missing, delete it and queue for regeneration
                if os.path.exists(meta_file):
                    try: os.remove(meta_file)
                    except: pass

                if base not in state['processing'] and not any(q['base'] == base for q in state['queue']):
                    state['queue'].append({'base': base, 'name': filename})

        if not state['worker_running'] and state['queue']:
            state['worker_running'] = True
            threading.Thread(target=background_worker, args=(gallery,), daemon=True).start()

        return {
            'videos': [{'name': f, 'baseName': b, 'size': os.path.getsize(os.path.join(g_path, f)), 'lastModified': os.path.getmtime(os.path.join(g_path, f))} for b, f in actual_videos.items()],
            'ready': list(state['ready']),
            'processing': list(state['processing'])
        }

# --- API ROUTES ---
@app.route('/')
def index(): return send_from_directory(BASE_DIR, 'gallery.html')

@app.route('/api/galleries')
def api_galleries():
    return jsonify([d for d in os.listdir(MEDIA_DIR) if os.path.isdir(os.path.join(MEDIA_DIR, d)) and not d.startswith('.')])

@app.route('/api/galleries/<gallery>/sync', methods=['POST'])
def api_sync(gallery): return jsonify(sync_gallery(gallery))

@app.route('/api/galleries/<gallery>/status')
def api_status(gallery):
    state = get_state(gallery)
    with state['lock']: return jsonify({'ready': list(state['ready']), 'processing': list(state['processing'])})

@app.route('/api/galleries/<gallery>/thumbs/batch', methods=['POST'])
def api_thumbs_batch(gallery):
    data = request.json or {}
    videos = data.get('videos', [])
    state = get_state(gallery)
    tml_path = os.path.join(MEDIA_DIR, gallery, TML)
    results = []
    priority_queue = []

    with state['lock']:
        for v in videos:
            base = v['baseName']
            if base in state['ready']:
                try:
                    with open(os.path.join(tml_path, f"{base}.json")) as f: results.append({"name": v['name'], "success": True, "metadata": json.load(f)})
                except: pass
            elif base in state['processing']: results.append({"name": v['name'], "status": "processing"})
            else: priority_queue.append({'base': base, 'name': v['name']})
        state['queue'] = priority_queue + state['queue']
        if not state['worker_running'] and state['queue']:
            state['worker_running'] = True
            threading.Thread(target=background_worker, args=(gallery,), daemon=True).start()
    return jsonify({"results": results})

@app.route('/api/galleries/<gallery>/tml-names')
def api_tml_names(gallery):
    tp = os.path.join(MEDIA_DIR, gallery, TML)
    if not os.path.exists(tp): return jsonify([])
    return jsonify([f.lower() for f in os.listdir(tp) if os.path.isfile(os.path.join(tp, f))])

@app.route('/api/galleries/<gallery>/tml/<path:filename>')
def api_tml(gallery, filename):
    return send_from_directory(os.path.join(MEDIA_DIR, gallery, TML), filename, max_age=86400)

@app.route('/api/galleries/<gallery>/video/<filename>')
def api_video(gallery, filename):
    vp = os.path.join(MEDIA_DIR, gallery, filename)
    if not os.path.exists(vp): abort(404)
    return send_file(vp, conditional=True)

if __name__ == '__main__':
    print(f"✅ Server starting in Stable CPU Mode...")
    serve(app, host='0.0.0.0', port=5000, threads=8, connection_limit=200)
