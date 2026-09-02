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
echo If the processor cannot connect, allow inbound TCP 23 in Windows Firewall:
echo   New-NetFirewallRule -DisplayName "TCP mock (23)" -Direction Inbound -Protocol TCP -LocalPort 23 -Action Allow
echo.

python -u mock.py tcp-server --port 23

if errorlevel 1 (
    echo.
    echo Server exited with an error.
    pause
)
