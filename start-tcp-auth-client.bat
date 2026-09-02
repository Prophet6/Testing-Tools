@echo off
title Testing Tools - TCP Auth Client (Crestron TCP Server with Authentication)
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found in PATH.
    pause
    exit /b 1
)

set /p HOST="RMC4 / processor IP: "
if "%HOST%"=="" (
    echo No IP entered.
    pause
    exit /b 1
)

set /p PORT="Port [50001]: "
if "%PORT%"=="" set PORT=50001

set /p TLS="TLS? y/N: "
set TLSFLAG=
if /I "%TLS%"=="y" set TLSFLAG=--tls

set /p USER="AUTH username (blank = no AUTH): "
set PASS=
if not "%USER%"=="" set /p PASS="AUTH password: "

echo.
echo Connecting to %HOST%:%PORT%
echo.

if "%USER%"=="" (
    python -u tcp-auth-client\tcp_auth_client.py --host %HOST% --port %PORT% %TLSFLAG%
) else (
    python -u tcp-auth-client\tcp_auth_client.py --host %HOST% --port %PORT% %TLSFLAG% --user %USER% --password %PASS%
)

if errorlevel 1 (
    echo.
    echo Client exited with an error.
    pause
)
