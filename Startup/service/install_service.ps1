# install_service.ps1 - Register EverNothing as a Windows service.
#
# Uses NSSM (Non-Sucking Service Manager) to wrap the python process.
# Service runs as the current user so AWS credentials in
# ~/.aws/credentials and SECRET_KEY in .env keep working.
# Start type is SERVICE_DELAYED_AUTO_START so the box can boot fully
# before the notes service spins up.
#
# Idempotent - re-running this updates settings on an existing service
# rather than failing.

$ErrorActionPreference = 'Stop'

# --- Self-elevate if not admin ------------------------------------------------
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

# --- Configuration ------------------------------------------------------------
$ServiceName  = 'EverNothing'
$DisplayName  = 'EverNothing Notes Service'
$Description  = 'EverNothing encrypted notes web service. Listens on https://127.0.0.1:5443'
$AppDir       = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Python       = 'C:\Users\bills\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\python.exe'
$AppScript    = Join-Path $AppDir 'evernothing.py'
$LogDir       = Join-Path $AppDir 'log'
$ServiceDir   = $PSScriptRoot
$Nssm         = Join-Path $ServiceDir 'nssm.exe'
$NssmZipUrl   = 'https://nssm.cc/release/nssm-2.24.zip'

Write-Host "================================================" -ForegroundColor Cyan
Write-Host " Installing $ServiceName as a Windows service"     -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AppDir : $AppDir"
Write-Host "  Python : $Python"
Write-Host "  Script : $AppScript"
Write-Host ""

# --- Sanity checks ------------------------------------------------------------
if (-not (Test-Path $Python))     { throw "Python not found at $Python" }
if (-not (Test-Path $AppScript))  { throw "App script not found at $AppScript" }
if (-not (Test-Path $LogDir))     { New-Item -ItemType Directory -Path $LogDir | Out-Null }

# --- Fetch NSSM if missing ----------------------------------------------------
if (-not (Test-Path $Nssm)) {
    Write-Host "NSSM not found locally - downloading..." -ForegroundColor Yellow
    $tmpZip = Join-Path $env:TEMP 'nssm.zip'
    $tmpDir = Join-Path $env:TEMP 'nssm-extract'
    if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
    Invoke-WebRequest -Uri $NssmZipUrl -OutFile $tmpZip -UseBasicParsing
    Expand-Archive -Path $tmpZip -DestinationPath $tmpDir -Force
    $nssmSrc = Get-ChildItem -Path $tmpDir -Filter 'nssm.exe' -Recurse |
               Where-Object { $_.FullName -match 'win64' } |
               Select-Object -First 1
    if (-not $nssmSrc) {
        $nssmSrc = Get-ChildItem -Path $tmpDir -Filter 'nssm.exe' -Recurse |
                   Select-Object -First 1
    }
    if (-not $nssmSrc) { throw "Could not find nssm.exe inside $tmpZip" }
    Copy-Item -Path $nssmSrc.FullName -Destination $Nssm -Force
    Remove-Item $tmpZip, $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "NSSM installed at $Nssm" -ForegroundColor Green
}

# --- Stop existing service if present so we can reconfigure -------------------
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Service already exists; stopping it for reconfigure..." -ForegroundColor Yellow
    & $Nssm stop $ServiceName 2>&1 | Out-Null
    Start-Sleep -Seconds 2
} else {
    Write-Host "Registering new service..." -ForegroundColor Cyan
    & $Nssm install $ServiceName $Python $AppScript
    if ($LASTEXITCODE -ne 0) { throw "nssm install failed: $LASTEXITCODE" }
}

# --- Configure ----------------------------------------------------------------
& $Nssm set $ServiceName Application       $Python                                | Out-Null
& $Nssm set $ServiceName AppParameters     $AppScript                             | Out-Null
& $Nssm set $ServiceName AppDirectory      $AppDir                                | Out-Null
& $Nssm set $ServiceName DisplayName       $DisplayName                           | Out-Null
& $Nssm set $ServiceName Description       $Description                           | Out-Null
& $Nssm set $ServiceName AppStdout         (Join-Path $LogDir 'service.log')      | Out-Null
& $Nssm set $ServiceName AppStderr         (Join-Path $LogDir 'service_err.log')  | Out-Null
& $Nssm set $ServiceName AppRotateFiles    1                                      | Out-Null
& $Nssm set $ServiceName AppRotateOnline   1                                      | Out-Null
& $Nssm set $ServiceName AppRotateBytes    10485760                               | Out-Null   # 10 MB
& $Nssm set $ServiceName AppExit           Default Restart                        | Out-Null
& $Nssm set $ServiceName AppRestartDelay   5000                                   | Out-Null
& $Nssm set $ServiceName Start             SERVICE_DELAYED_AUTO_START             | Out-Null

# --- Service account ----------------------------------------------------------
# Run as LocalSystem (built-in account, no password). Trade-off: the service
# cannot read user-profile files like %USERPROFILE%\.aws\credentials or
# the user's HOME-relative .env. To make S3 sync work under LocalSystem,
# either:
#   - put AWS keys in the project's own .env (already supported), or
#   - copy %USERPROFILE%\.aws\credentials to a machine-readable location
#     and point AWS_SHARED_CREDENTIALS_FILE at it.
# We do NOT prompt for a password here. PIN / Windows Hello are not
# accepted by the Service Control Manager, so requesting a password
# from a typical Hello-only user fails reliably.
$null = & sc.exe config $ServiceName obj= 'LocalSystem'
if ($LASTEXITCODE -ne 0) {
    throw "sc.exe config failed with exit code $LASTEXITCODE - service account NOT updated"
}
Write-Host ""
Write-Host "Service account: LocalSystem (no password)" -ForegroundColor Cyan

# --- Start --------------------------------------------------------------------
Write-Host ""
Write-Host "Starting service..." -ForegroundColor Cyan
& $Nssm start $ServiceName 2>&1 | Out-Null
Start-Sleep -Seconds 6

# --- Status -------------------------------------------------------------------
$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $svc) {
    Write-Host "ERROR: service did not register" -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "Status        : $($svc.Status)"          -ForegroundColor Green
Write-Host "Start type    : Delayed auto-start (boots ~2 min after Windows)"
Write-Host "Stdout log    : $LogDir\service.log"
Write-Host "Stderr log    : $LogDir\service_err.log"
Write-Host ""
Write-Host "URL after start : https://127.0.0.1:5443"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  Stop      : sc stop $ServiceName"
Write-Host "  Start     : sc start $ServiceName"
Write-Host "  Status    : sc query $ServiceName"
Write-Host "  Uninstall : Startup\service\uninstall_service.bat"
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " Done. Press Enter to close this window."
Read-Host | Out-Null
