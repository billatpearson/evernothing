@echo off
:: Convenience launcher — calls the PowerShell installer with the right flags.
:: The PowerShell script self-elevates; double-clicking this works fine.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_service.ps1"
