@echo off
title YouTube Autopilot AI Installer
cd /d "%~dp0"
py -3 --version
if errorlevel 1 (echo Install Python 3.10+ from https://www.python.org/downloads/ and select Add Python to PATH & pause & exit /b 1)
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
if errorlevel 1 (echo Package installation failed. Check internet/Python. & pause & exit /b 1)
where ffmpeg >nul 2>nul
if errorlevel 1 echo FFmpeg missing. Install from https://ffmpeg.org/download.html and add its bin folder to PATH.
echo Setup finished. Run START.bat.
pause
