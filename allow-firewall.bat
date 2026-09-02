@echo off
title Testing-Tools - allow inbound TCP 23 / 2222 / 5000
cd /d "%~dp0"

net session >nul 2>&1
if errorlevel 1 (
    echo This must run as Administrator to add firewall rules.
    echo Right-click allow-firewall.bat and choose Run as administrator.
    pause
    exit /b 1
)

echo Adding inbound allow rules for Testing-Tools...
netsh advfirewall firewall delete rule name="Testing-Tools TCP 23" >nul 2>&1
netsh advfirewall firewall delete rule name="Testing-Tools SSH 2222" >nul 2>&1
netsh advfirewall firewall delete rule name="Testing-Tools TCP 5000" >nul 2>&1

netsh advfirewall firewall add rule name="Testing-Tools TCP 23" dir=in action=allow protocol=TCP localport=23
netsh advfirewall firewall add rule name="Testing-Tools SSH 2222" dir=in action=allow protocol=TCP localport=2222
netsh advfirewall firewall add rule name="Testing-Tools TCP 5000" dir=in action=allow protocol=TCP localport=5000

echo.
echo Done. Leave start-tcp-server.bat running, then toggle Connect on the RMC4.
pause
