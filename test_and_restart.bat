@echo off
setlocal

set PYTHON=C:\Users\bills\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\python.exe
set APP_DIR=C:\source\ai\evernothing\evernothing
set PID_FILE=%APP_DIR%\server.pid
set VBS=%TEMP%\start_evernothing.vbs

echo ============================================
echo  EverNothing - Test and Restart
echo ============================================

:: --- Stop server using saved PID ---
echo [1/3] Stopping server...
if exist "%PID_FILE%" (
    for /f %%p in (%PID_FILE%) do (
        taskkill /F /PID %%p >nul 2>&1
        echo       Stopped PID %%p.
    )
    del "%PID_FILE%"
) else (
    echo       No PID file found, skipping.
)
timeout /t 1 /nobreak >nul

:: --- Run tests ---
echo [2/3] Running unit tests...
cd /d "%APP_DIR%"
"%PYTHON%" tests\test_evernothing.py -v
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAILED] Tests failed. Server NOT restarted.
    exit /b 1
)

echo.
echo [PASSED] All tests passed.

:: --- Start server via PowerShell detached process ---
echo [3/3] Starting server...
if not exist "%APP_DIR%\log" mkdir "%APP_DIR%\log"

powershell -Command "Start-Process -FilePath '%PYTHON%' -ArgumentList '%APP_DIR%\evernothing.py' -WorkingDirectory '%APP_DIR%' -WindowStyle Hidden -RedirectStandardOutput '%APP_DIR%\log\server.log' -RedirectStandardError '%APP_DIR%\log\server_err.log'"

timeout /t 2 /nobreak >nul

:: Save PID
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    echo %%p> "%PID_FILE%"
    echo       Server running on http://127.0.0.1:5000 ^(PID %%p^)
    goto :done
)
echo [WARNING] Server did not start on port 5000. Check log\server_err.log

:done
echo ============================================
endlocal
