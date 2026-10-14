@echo off
title Install Testing-Tools Dependencies
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    echo Install Python from https://www.python.org/downloads/
    echo Check "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)

echo Installing paramiko, pyftpdlib, and cryptography...
python -m pip install --user -r requirements.txt

if errorlevel 1 (
    echo.
    echo Install failed.
    pause
    exit /b 1
)

echo.
echo Done. Use start-ssh-server.bat, start-tcp-server.bat, start-tcp-client.bat, or start-remote-file-sync.bat
pause
