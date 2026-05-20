# install_task.ps1
# Register a Windows Task Scheduler task that launches EverNothing at user
# logon. Runs as the current user with their normal privileges, no UAC,
# no admin token required.

$ErrorActionPreference = 'Stop'

$TaskName    = 'EverNothing'
$TaskFolder  = '\'
$AppDir      = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Wrapper     = Join-Path $PSScriptRoot 'run_evernothing.bat'
$Description = 'Launches EverNothing notes web service at logon. Listens on https://127.0.0.1:5443'

Write-Host "================================================" -ForegroundColor Cyan
Write-Host " Registering scheduled task: $TaskName"           -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AppDir  : $AppDir"
Write-Host "  Wrapper : $Wrapper"
Write-Host ""

if (-not (Test-Path $Wrapper)) { throw "Wrapper not found at $Wrapper" }

# Remove any existing task with this name (idempotent re-install)
$existing = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskFolder -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Existing task found, unregistering..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskFolder -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute $Wrapper -WorkingDirectory $AppDir
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
# Slight delay so the network and AWS profile resolution are ready when the
# python process boots.
$trigger.Delay = 'PT30S'

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName `
    -TaskPath $TaskFolder `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description $Description | Out-Null

Write-Host "Task registered." -ForegroundColor Green
$task = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskFolder
Write-Host ""
Write-Host "Name        : $($task.TaskName)"
Write-Host "State       : $($task.State)"
Write-Host "Triggers    : at logon (30s delay) for $env:USERDOMAIN\$env:USERNAME"
Write-Host "Restarts    : up to 3 times, 5 min apart, on failure"
Write-Host "Stdout log  : $AppDir\log\task.log"
Write-Host "Stderr log  : $AppDir\log\task_err.log"
Write-Host ""

# Offer to start it now so we don't have to wait for next logon
$answer = Read-Host "Start the task right now? [Y/n]"
if ([string]::IsNullOrWhiteSpace($answer) -or $answer.Trim().ToLower() -eq 'y') {
    Write-Host "Starting..." -ForegroundColor Cyan
    Start-ScheduledTask -TaskName $TaskName -TaskPath $TaskFolder
    Start-Sleep -Seconds 6
    $task = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskFolder
    $info = Get-ScheduledTaskInfo -TaskName $TaskName -TaskPath $TaskFolder
    Write-Host ""
    Write-Host "State            : $($task.State)"
    Write-Host "Last run         : $($info.LastRunTime)"
    Write-Host "Last result code : $($info.LastTaskResult)  (267009 = currently running)"
    $listening = (Get-NetTCPConnection -LocalPort 5443 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($listening) {
        Write-Host "Port 5443        : LISTENING on PID $($listening.OwningProcess)" -ForegroundColor Green
    } else {
        Write-Host "Port 5443        : not listening yet (server still starting, or check task_err.log)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Useful commands:"
Write-Host "  Status    : Get-ScheduledTask -TaskName EverNothing | Format-List"
Write-Host "  Run now   : Start-ScheduledTask -TaskName EverNothing"
Write-Host "  Stop      : Stop-ScheduledTask -TaskName EverNothing"
Write-Host "  Uninstall : Startup\task\uninstall_task.bat"
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
