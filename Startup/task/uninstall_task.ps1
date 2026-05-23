# uninstall_task.ps1 -- Remove the EverNothing scheduled task.
$ErrorActionPreference = 'Stop'
$TaskName   = 'EverNothing'
$TaskFolder = '\'

$existing = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskFolder -ErrorAction SilentlyContinue
if (-not $existing) {
    Write-Host "Task '$TaskName' is not registered. Nothing to do." -ForegroundColor Yellow
    return
}

Write-Host "Stopping task if running..." -ForegroundColor Cyan
Stop-ScheduledTask -TaskName $TaskName -TaskPath $TaskFolder -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "Unregistering task..." -ForegroundColor Cyan
Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskFolder -Confirm:$false

Write-Host "Done. The Python process (if any) keeps running until logoff." -ForegroundColor Green
Write-Host "To kill it now: Get-Process python3.9 | Stop-Process -Force"
