@echo off
setlocal

::
:: test_and_restart.bat - Development cycle script.
::
:: Architecture: the scheduled task 'EverNothing' is the single source of
:: truth for the running server (auto-starts at logon, restarts on crash).
:: This script does NOT spawn the python process directly. It only:
::
::   1. Stops the scheduled task (graceful)
::   2. Kills any orphan python or cmd shells from prior dev cycles
::   3. Runs the unit tests in parallel (pytest -n auto)
::   4. Starts the scheduled task again
::
:: No detach gymnastics, no inherited handles, no zombie shells. The task
:: handles all process supervision.
::
:: Prerequisite: install the task once with Startup\task\install_task.bat.
::

set PYTHON=C:\Users\bills\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\python.exe
set APP_DIR=C:\source\ai\evernothing\evernothing
set ANDROID_DIR=C:\source\ai\evernothing\evernothing_android
set TASK_NAME=EverNothing

echo ============================================
echo  EverNothing - Test and Restart
echo ============================================

::
:: [1/4] Stop the scheduled task (graceful, waits for the python to exit)
::
echo [1/4] Stopping scheduled task...
schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if errorlevel 1 (
    echo       Task '%TASK_NAME%' not registered.
    echo       Run Startup\task\install_task.bat to set it up.
    exit /b 1
)
schtasks /End /TN "%TASK_NAME%" >nul 2>&1
:: schtasks /End sends the stop signal but doesn't wait. Poll until the
:: task is really not running, max 10s.
set /a tries=0
:wait_stopped
schtasks /Query /TN "%TASK_NAME%" /FO LIST 2>nul | findstr /B /C:"Status:" | findstr /I "Running" >nul
if errorlevel 1 goto stopped
set /a tries+=1
if %tries% GEQ 10 (
    echo       WARNING: task did not stop within 10s; continuing anyway.
    goto stopped
)
timeout /t 1 /nobreak >nul
goto wait_stopped
:stopped
echo       Task stopped.

::
:: [2/4] Clean up orphan processes from prior dev cycles
::
:: Anything still listening on 5000/5443 is something we don't recognize -
:: kill it. Then nuke any python3.9 that's been alive less than an hour and
:: isn't a child of the scheduled task (the task should be stopped right
:: now anyway, so no false positives).
::
echo [2/4] Cleaning orphan processes...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    echo       Killed orphan on port 5000 ^(PID %%p^).
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5443 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    echo       Killed orphan on port 5443 ^(PID %%p^).
)
:: Kill orphan cmd.exe shells whose command line references this app dir
:: AND that are older than 5 minutes. Those are typically leftovers from
:: prior interrupted bat runs.
powershell -NoProfile -Command "$cutoff = (Get-Date).AddMinutes(-5); Get-CimInstance Win32_Process -Filter \"Name='cmd.exe'\" -ErrorAction SilentlyContinue | Where-Object { $_.CreationDate -lt $cutoff -and $_.CommandLine -match [regex]::Escape('%APP_DIR%') } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop; Write-Host ('       Killed orphan cmd PID ' + $_.ProcessId) } catch {} }"

::
:: [3/4] Run tests (parallel, -n auto)
::
echo [3/4] Running unit tests...
echo.
cd /d "%APP_DIR%"

echo --- Main app tests ---
"%PYTHON%" -m pytest Test/test_evernothing.py Test/test_all.py Test/test_note_operations.py Test/test_dashboard.py Test/test_themes.py Test/test_security.py Test/test_feature_matrix.py tests/test_evernothing.py tests/test_s3_sync.py tests/test_s3_integration.py -n auto --dist loadfile --tb=short 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAILED] Main app tests failed. Task NOT restarted.
    exit /b 1
)

echo.
echo --- Android tests ---
cd /d "%ANDROID_DIR%"
"%PYTHON%" -m pytest test_android.py -n auto --tb=short 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAILED] Android tests failed. Task NOT restarted.
    exit /b 1
)

echo.
echo [PASSED] All tests passed.

::
:: [4/4] Start the scheduled task again
::
echo [4/4] Starting scheduled task...
cd /d "%APP_DIR%"
schtasks /Run /TN "%TASK_NAME%" >nul 2>&1
if errorlevel 1 (
    echo       FAILED to start task '%TASK_NAME%'.
    exit /b 1
)

:: Poll for the listener (task may take a few seconds to boot python).
set /a tries=0
:wait_listening
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5443 " ^| findstr "LISTENING"') do (
    echo       Server running on https://127.0.0.1:5443 ^(PID %%p^)
    goto done
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    echo       Server running on http://127.0.0.1:5000 ^(PID %%p^)
    goto done
)
set /a tries+=1
if %tries% GEQ 20 (
    echo       WARNING: task started but no listener on 5443/5000 after 20s.
    echo       Check log\task.log and log\task_err.log
    goto done
)
timeout /t 1 /nobreak >nul
goto wait_listening

:done
echo ============================================
endlocal
