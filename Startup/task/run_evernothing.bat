@echo off
:: Wrapper invoked by Task Scheduler at logon.
:: Sets the working dir, runs python, redirects output to log files.
setlocal
set APP_DIR=C:\source\ai\evernothing\evernothing
set PYTHON=C:\Users\bills\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\python.exe

cd /d "%APP_DIR%"
if not exist "%APP_DIR%\log" mkdir "%APP_DIR%\log"

"%PYTHON%" evernothing.py >> "%APP_DIR%\log\task.log" 2>> "%APP_DIR%\log\task_err.log"
endlocal
