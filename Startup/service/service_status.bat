@echo off
:: Quick read-only status check. No elevation needed.
echo ============================================
echo  EverNothing service status
echo ============================================
sc query EverNothing 2>nul
if errorlevel 1 (
    echo.
    echo Service is not registered. Run install_service.bat to install it.
    goto :eof
)
echo.
echo --- Listening ports ---
netstat -ano | findstr ":5443 " | findstr "LISTENING"
netstat -ano | findstr ":5000 " | findstr "LISTENING"
echo.
echo --- Recent stdout (last 20 lines) ---
powershell -NoProfile -Command "Get-Content '%~dp0..\..\log\service.log' -Tail 20 -ErrorAction SilentlyContinue"
echo.
echo --- Recent stderr (last 20 lines) ---
powershell -NoProfile -Command "Get-Content '%~dp0..\..\log\service_err.log' -Tail 20 -ErrorAction SilentlyContinue"
