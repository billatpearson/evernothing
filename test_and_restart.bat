@echo off
setlocal

set PYTHON=C:\Users\bills\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\python.exe
set APP_DIR=C:\source\ai\evernothing\evernothing
set ANDROID_DIR=C:\source\ai\evernothing\evernothing_android
set PID_FILE=%APP_DIR%\server.pid

echo ============================================
echo  EverNothing - Test and Restart
echo ============================================

:: --- Stop server using saved PID ---
echo [1/4] Stopping server...
if exist "%PID_FILE%" (
    for /f %%p in (%PID_FILE%) do (
        taskkill /F /PID %%p >nul 2>&1
        echo       Stopped PID %%p.
    )
    del "%PID_FILE%"
) else (
    echo       No PID file found, skipping.
)

:: --- Kill any orphaned evernothing.py processes on port 5000 ---
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    echo       Killed orphaned process on port 5000 ^(PID %%p^).
)
timeout /t 1 /nobreak >nul

:: --- Run all tests ---
echo [2/4] Running unit tests...
echo.
cd /d "%APP_DIR%"

echo --- Main app tests ---
"%PYTHON%" -m pytest test_evernothing.py test_all.py test_note_operations.py test_dashboard.py tests/test_evernothing.py tests/test_s3_sync.py tests/test_s3_integration.py -v --tb=short 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAILED] Main app tests failed. Server NOT restarted.
    exit /b 1
)

echo.
echo --- Android tests ---
cd /d "%ANDROID_DIR%"
"%PYTHON%" -m pytest test_android.py -v --tb=short 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAILED] Android tests failed. Server NOT restarted.
    exit /b 1
)

echo.
echo [PASSED] All tests passed.

:: --- Start server via PowerShell detached process ---
echo [3/4] Starting server...
cd /d "%APP_DIR%"
if not exist "%APP_DIR%\log" mkdir "%APP_DIR%\log"

powershell -Command "Start-Process -FilePath '%PYTHON%' -ArgumentList '%APP_DIR%\evernothing.py' -WorkingDirectory '%APP_DIR%' -WindowStyle Hidden -RedirectStandardOutput '%APP_DIR%\log\server.log' -RedirectStandardError '%APP_DIR%\log\server_err.log'"

timeout /t 4 /nobreak >nul

:: --- Save PID ---
echo [4/4] Verifying server...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    echo %%p> "%PID_FILE%"
    echo       Server running on http://127.0.0.1:5000 ^(PID %%p^)
    goto :done
)
echo [WARNING] Server did not start on port 5000. Check log\server_err.log

:done
echo ============================================
endlocal
