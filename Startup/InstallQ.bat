@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo    Amazon Q Developer CLI Installer
echo ==========================================

:: 1. Define a safe temporary path to avoid character errors
set "TEMP_SCRIPT=%TEMP%\q_install.ps1"

echo [1/3] Downloading installer script...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ua = 'Mozilla/5.0'; Invoke-WebRequest -Uri 'https://desktop-release.q.us-east-1.amazonaws.com/shell/install.ps1' -UserAgent $ua -OutFile '%TEMP_SCRIPT%'"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to download the installer. Check your internet connection.
    pause
    exit /b
)

echo [2/3] Running installation...
powershell -ExecutionPolicy Bypass -File "%TEMP_SCRIPT%"

echo [3/3] Cleaning up...
del "%TEMP_SCRIPT%"

echo.
echo ==========================================
echo INSTALLATION COMPLETE
echo Please RESTART your Terminal or VS Code.
echo Then type 'q --version' to verify.
echo ==========================================
pause