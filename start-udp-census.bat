@echo off
title Testing Tools - UDP Census peer
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    pause
    exit /b 1
)

set /p PORT="Port [50001]: "
if "%PORT%"=="" set PORT=50001

echo.
echo This PC answers ?POLL and can send one.
echo On the RMC4 use UDP Census v1.0. Leave the v2 beacon off.
echo Do not run start-udp.bat at the same time. Both want this port.
echo Commands in the next window: poll, peers N, window S, help, quit.
echo Ctrl+C to stop.
echo.
echo Windows Firewall blocks inbound UDP until you allow it.
echo Right-click allow-firewall.bat and Run as administrator (once).
echo.

python -u udp-census\census_peer.py --port %PORT%

if errorlevel 1 (
    echo.
    echo UDP Census peer exited with an error.
    pause
)
