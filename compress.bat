@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo        High-Quality Video Compressor (Lossless Clarity)
echo ========================================================
echo.

if "%~1"=="" (
    echo [INFO] No file dropped. Checking current folder...
    python compress.py
) else (
    echo [INFO] Processing dropped file/folder: %~1
    python compress.py -i "%~1"
)

echo.
echo Press any key to exit...
pause >nul
