@echo off
:: Register the EverNothing scheduled task. No admin needed.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_task.ps1"
pause
