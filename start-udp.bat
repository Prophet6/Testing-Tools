@echo off
title Testing Tools - UDP (Crestron UDP broadcast test)
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    pause
    exit /b 1
)

set /p PORT="Port [50001]: "
if "%PORT%"=="" set PORT=50001

set /p HOST="Send to [255.255.255.255] (broadcast, or processor IP): "
if "%HOST%"=="" set HOST=255.255.255.255

echo.
echo UDP listen 0.0.0.0:%PORT%  send -^> %HOST%:%PORT%
echo Enable the processor UDP symbol first (Enable high).
echo Type in this window to send. [RX] is datagrams from the LAN.
echo Ctrl+C to stop.
echo.
echo Windows Firewall blocks inbound UDP until you allow it.
echo Right-click allow-firewall.bat and Run as administrator (once).
echo.

python -u mock.py udp --host %HOST% --port %PORT%

if errorlevel 1 (
    echo.
    echo UDP tool exited with an error.
    pause
)
