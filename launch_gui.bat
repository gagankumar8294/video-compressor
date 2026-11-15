@echo off
setlocal

set "HANDBRAKE_EXE=C:\Program Files\HandBrake\HandBrake.exe"

if exist "%HANDBRAKE_EXE%" (
    echo Starting HandBrake GUI...
    start "" "%HANDBRAKE_EXE%"
) else (
    echo [ERROR] HandBrake GUI executable not found at: %HANDBRAKE_EXE%
    pause
)
