# 🎬 LocalFlix - Self-Hosted Video Gallery

A blazing-fast, self-hosted video gallery web application built with Python and Flask. It automatically scans your local directories, generates full-resolution thumbnails in the background, and presents them in a beautiful, Netflix-style UI with smooth crossfade animations and exact-frame seek previews.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Waitress-black?logo=flask)
![FFmpeg](https://img.shields.io/badge/Powered%20by-FFmpeg-green?logo=ffmpeg)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🖼️ Smart Thumbnail Engine
* **5-Image Crossfade:** Generates 5 full-resolution thumbnails per video. Cards smoothly crossfade between them every 5 seconds.
* **Background Processing:** Thumbnails are generated in background threads. The UI is never blocked.
* **"Wait!" Overlay:** If you scroll to a video that is still generating, a pulsing overlay appears and disappears the moment it's ready.
* **Auto-Cleanup:** Intelligently detects and deletes orphaned thumbnails if you remove or rename videos in your folder.

### 🎯 Cinematic Playback & UI
* **Exact-Frame Seek Preview:** Hover over the seekbar to see the exact frame rendered in real-time via HTML5 Canvas.
* **Hover Previews:** Hovering over a card starts a muted video preview exactly at the timestamp of the currently displayed thumbnail.
* **Immersive Fullscreen:** Controls and the mouse cursor automatically hide after 5 seconds of inactivity during playback.
* **Memory Safe:** Aggressively offloads off-screen images and video decoders to prevent browser crashes, even with thousands of videos.
* **Keyboard Navigation:** Full shortcut support for a seamless experience.

### 🧠 Performance & Architecture
* **O(1) Existence Checks:** Fetches directory names once into a `Set` for instantaneous thumbnail loading without 404 network spam.
* **Production-Ready Server:** Uses `Waitress` for robust, multi-threaded HTTP handling.
* **Stable CPU Fallback:** Uses FFmpeg's `auto` hardware acceleration, ensuring it runs perfectly on any machine without crashing from missing GPU drivers.

---

## 🛠️ Prerequisites

You only need **two things** installed on your system before running the launcher:

### 1. Python 3.8+
* **Windows:** Download from [python.org](https://www.python.org/downloads/) (check "Add to PATH" during install)
* **Linux:** `sudo apt install python3 python3-venv`
* **macOS:** `brew install python3`

### 2. FFmpeg
* **Windows:** Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), extract, and add the `bin` folder to your system `PATH`
* **Linux:** `sudo apt install ffmpeg`
* **macOS:** `brew install ffmpeg`

> ⚠️ The launcher script will automatically check for FFmpeg and warn you if it's missing.

---

## 🚀 Installation & Usage (One-Click Launch)

### 1. Clone / Download the repository

git clone https://github.com/yourusername/localflix.git
cd localflix

2. Add your videos
Place your video folders inside the media directory (it will be auto-created on first run if missing):

localflix/
├── server.py
├── gallery.html
├── start.sh          <-- Linux / macOS launcher
├── start.bat         <-- Windows launcher
└── media/            <-- Put your videos here
    ├── Vacation 2026/
    │   ├── clip1.mp4
    │   └── clip2.mp4
    └── Tutorials/
        └── python.mp4

3. Run the launcher
🐧 Linux / macOS
chmod +x start.sh
./start.sh

Double-click start.bat or run it from Command Prompt:
start.bat

What the launcher does automatically:
	
Checks if a Python virtual environment (venv) exists; creates one if not
Activates the virtual environment
Installs/updates flask and waitress silently
Verifies FFmpeg is installed and accessible in your PATH
Creates the media folder if it doesn't exist
🚀 Launches the server

⌨️ Keyboard Shortcuts
When the video player is open:
Space Play / Pause
F Toggle Fullscreen
Mb Mute / Unmute
← (Left) Previous Video
→ (Right) Next Video
Esc Close Player / Exit Fullscreen

 How It Works (Under the Hood)
  Directory Sync: When you open a gallery, the server compares the actual video files against the .tml (Thumbnail/Metadata) cache folder.
  Orphan Deletion: Any .jpg or .json file in .tml that doesn't match a current video's base name is instantly deleted.
  Queueing: Missing thumbnails are added to a background queue. The server uses a thread pool to process them using FFmpeg.
  Caching: Metadata (duration, resolution, size) and thumbnail paths are saved in .tml/<video_name>.json.
  Frontend Rendering: The frontend requests the list of existing .tml files, stores them in a JavaScript Set, and uses IntersectionObserver to only load images for cards currently visible on screen.

Customization

   Change Port: Edit the last line of server.py:
   serve(app, host='0.0.0.0', port=8080, threads=8, connection_limit=200)

Change Thumbnail Timestamps: Edit the PCTS array in server.py to change the exact percentages of the video where thumbnails are captured:

  PCTS = [0.10, 0.25, 0.50, 0.70, 0.90] # 10%, 25%, 50%, 70%, 90%

Force GPU (Vulkan/CUDA):

If you have a properly configured GPU environment, 
you can change the FFmpeg command in gen_thumb() inside server.py from -hwaccel auto to -hwaccel vulkan or -hwaccel cuda.
