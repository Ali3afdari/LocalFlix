@echo off
setlocal

:: --- Configuration ---
set VENV_DIR=venv
set PYTHON_CMD=python

echo 🎬 Starting LocalFlix Setup...

:: 1. Check and create Virtual Environment
if not exist "%VENV_DIR%\" (
    echo 📦 Virtual environment not found. Creating '%VENV_DIR%'...
    %PYTHON_CMD% -m venv %VENV_DIR%
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment. Make sure Python is installed and in PATH.
        pause
        exit /b 1
    )
) else (
    echo ✅ Virtual environment found.
)

:: 2. Activate Virtual Environment
echo 🔌 Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat

:: 3. Install/Update Dependencies
echo 📥 Installing Python dependencies (Flask, Waitress)...
pip install --upgrade pip >nul 2>&1
pip install flask waitress >nul 2>&1
echo ✅ Dependencies installed.

:: 4. Check for FFmpeg (Strict Requirement)
echo 🔍 Checking for FFmpeg...
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo ❌ ERROR: FFmpeg is not installed or not in your PATH!
    echo    This application requires FFmpeg to generate thumbnails.
    echo    Please download FFmpeg from https://www.gyan.dev/ffmpeg/builds/
    echo    and add the 'bin' folder to your Windows Environment Variables PATH.
    pause
    exit /b 1
)
echo ✅ FFmpeg found.

:: 5. Create media folder if it doesn't exist
if not exist "media\" (
    echo 📁 Creating 'media' directory...
    mkdir media
)

:: 6. Launch Server
echo 🚀 Launching server at http://localhost:5000 ...
echo ---------------------------------------------------
python server.py

:: If the server stops, pause so the user can read any error messages
pause