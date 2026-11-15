@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo        Starting Video Compressor Web UI...
echo ==========================================================
echo.

start "" "http://localhost:5000"
python app.py

pause
