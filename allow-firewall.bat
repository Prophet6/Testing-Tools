@echo off
title Testing-Tools - allow inbound bench ports
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
netsh advfirewall firewall delete rule name="Testing-Tools UDP 50001" >nul 2>&1
netsh advfirewall firewall delete rule name="Testing-Tools HTTP 8080" >nul 2>&1
netsh advfirewall firewall delete rule name="Testing-Tools HTTPS 8443" >nul 2>&1
netsh advfirewall firewall delete rule name="Testing-Tools FTP 2121" >nul 2>&1
netsh advfirewall firewall delete rule name="Testing-Tools FTP passive" >nul 2>&1

netsh advfirewall firewall add rule name="Testing-Tools TCP 23" dir=in action=allow protocol=TCP localport=23
netsh advfirewall firewall add rule name="Testing-Tools SSH 2222" dir=in action=allow protocol=TCP localport=2222
netsh advfirewall firewall add rule name="Testing-Tools TCP 5000" dir=in action=allow protocol=TCP localport=5000
netsh advfirewall firewall add rule name="Testing-Tools UDP 50001" dir=in action=allow protocol=UDP localport=50001
netsh advfirewall firewall add rule name="Testing-Tools HTTP 8080" dir=in action=allow protocol=TCP localport=8080
netsh advfirewall firewall add rule name="Testing-Tools HTTPS 8443" dir=in action=allow protocol=TCP localport=8443
netsh advfirewall firewall add rule name="Testing-Tools FTP 2121" dir=in action=allow protocol=TCP localport=2121
netsh advfirewall firewall add rule name="Testing-Tools FTP passive" dir=in action=allow protocol=TCP localport=2122-2130

echo.
echo Done. Re-run this if you add a new listen port.
echo TCP: leave start-tcp-server.bat running, then toggle Connect on the RMC4.
echo UDP: leave start-udp.bat running, then Enable the processor UDP symbol.
pause
