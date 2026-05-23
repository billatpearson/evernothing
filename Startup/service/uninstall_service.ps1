# uninstall_service.ps1 - Stop and remove the EverNothing service.
# Leaves DB, logs, AWS creds, and source code untouched.

$ErrorActionPreference = 'Stop'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin  = (New-Object Security.Principal.WindowsPrincipal $identity).IsInRole(
              [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Elevating to administrator..." -ForegroundColor Yellow
    Start-Process -FilePath 'powershell' `
        -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File","`"$PSCommandPath`"" `
        -Verb RunAs
    exit 0
}

$ServiceName = 'EverNothing'
$Nssm        = Join-Path $PSScriptRoot 'nssm.exe'

$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $svc) {
    Write-Host "Service '$ServiceName' is not registered. Nothing to do." -ForegroundColor Yellow
    Read-Host "Press Enter to close" | Out-Null
    exit 0
}

Write-Host "Stopping $ServiceName..." -ForegroundColor Cyan
if (Test-Path $Nssm) {
    & $Nssm stop $ServiceName 2>&1 | Out-Null
} else {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

Write-Host "Removing $ServiceName..." -ForegroundColor Cyan
if (Test-Path $Nssm) {
    & $Nssm remove $ServiceName confirm 2>&1 | Out-Null
} else {
    sc.exe delete $ServiceName | Out-Null
}

Start-Sleep -Seconds 2
$still = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($still) {
    Write-Host "WARNING: service still registered. You may need to reboot." -ForegroundColor Red
} else {
    Write-Host "Service removed cleanly." -ForegroundColor Green
}
Write-Host ""
Write-Host "Note: DB, log files, and AWS credentials were NOT touched." -ForegroundColor Cyan
Write-Host "Press Enter to close."
Read-Host | Out-Null
