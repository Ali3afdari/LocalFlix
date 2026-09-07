#!/bin/bash

# --- Configuration ---
VENV_DIR="venv"
PYTHON_CMD="python3"

# Fallback to 'python' if 'python3' is not found
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "🎬 Starting LocalFlix Setup..."

# 1. Check and create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Virtual environment not found. Creating '$VENV_DIR'..."
    $PYTHON_CMD -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment. Make sure python3-venv is installed."
        echo "   (Ubuntu/Debian: sudo apt install python3-venv)"
        exit 1
    fi
else
    echo "✅ Virtual environment found."
fi

# 2. Activate Virtual Environment
echo "🔌 Activating virtual environment..."
source $VENV_DIR/bin/activate

# 3. Install/Update Dependencies
echo "📥 Installing Python dependencies (Flask, Waitress)..."
pip install --upgrade pip > /dev/null
pip install flask waitress > /dev/null
echo "✅ Dependencies installed."

# 4. Check for FFmpeg (Strict Requirement)
echo "🔍 Checking for FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ERROR: FFmpeg is not installed or not in your PATH!"
    echo "   This application requires FFmpeg to generate thumbnails."
    echo "   - Ubuntu/Debian: sudo apt install ffmpeg"
    echo "   - macOS: brew install ffmpeg"
    echo "   - Windows: Download from gyan.dev and add to PATH"
    deactivate 2>/dev/null
    exit 1
fi
echo "✅ FFmpeg found: $(ffmpeg -version | head -n 1)"

# 5. Create media folder if it doesn't exist
if [ ! -d "media" ]; then
    echo "📁 Creating 'media' directory..."
    mkdir media
fi

# 6. Launch Server
echo "🚀 Launching server at http://localhost:5000 ..."
echo "---------------------------------------------------"
python server.py