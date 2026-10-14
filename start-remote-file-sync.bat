@echo off
title Testing Tools - Remote File Sync (HTTP / HTTPS / FTP)
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    pause
    exit /b 1
)

echo.
echo Remote File Sync bench - this PC listens, the processor connects out.
echo HTTP 8080, HTTPS 8443, FTP 2121.
echo Point Remote_URL at the LAN IP this window prints, not 127.0.0.1.
echo.
echo Windows Firewall blocks these ports until you allow them.
echo Right-click allow-firewall.bat and Run as administrator (once).
echo.

python -u remote-file-sync\server.py

if errorlevel 1 (
    echo.
    echo Server exited with an error.
    pause
)
