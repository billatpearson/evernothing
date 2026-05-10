@echo off
echo ============================================
echo  SMS Service + ngrok Tunnel
echo ============================================
echo.

set SMS_DIR=C:\source\ai\evernothing\sms_service
set PYTHON=C:\Users\bills\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\python.exe

:: Start the Flask SMS service in background
echo [1/2] Starting SMS service on port 5050...
start /B "" "%PYTHON%" "%SMS_DIR%\app.py"
timeout /t 2 /nobreak >nul

:: Start ngrok tunnel
echo [2/2] Starting ngrok tunnel...
echo.
echo Your public URL will appear below.
echo Set this URL as your Twilio webhook:
echo   Twilio Console -> Phone Numbers -> Your Number -> Messaging -> Webhook
echo   URL: https://YOUR-NGROK-URL/sms/inbound
echo   Method: POST
echo.
"%SMS_DIR%\ngrok.exe" http 5050
