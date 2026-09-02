@echo off
title Testing Tools - TCP Server (Crestron TCP Client test)
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    pause
    exit /b 1
)

echo.
echo TCP mock SERVER - for TCP Client (Dynamic IP)
echo Listen: 0.0.0.0:23
echo Point Address$ at THIS PC LAN IP (not 127.0.0.1). Port = 23.
echo Hold Connect high. Type here to send. [RX] is data from the processor.
echo Ctrl+C to stop.
echo.
echo Windows Firewall blocks inbound TCP 23 until you allow it.
echo Right-click allow-firewall.bat and Run as administrator (once).
echo Address$ must be this PC LAN IP, not 127.0.0.1.
echo.

python -u mock.py tcp-server --port 23

if errorlevel 1 (
    echo.
    echo Server exited with an error.
    pause
)
