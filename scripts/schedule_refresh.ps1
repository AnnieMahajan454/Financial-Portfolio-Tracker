# Registers a Windows scheduled task that runs `python -m tracker refresh` every
# 15 minutes. The command is called with --market-hours-only, so it exits right
# away outside NYSE hours and the task doesn't need to know the local time zone.
#
#   powershell -ExecutionPolicy Bypass -File scripts\schedule_refresh.ps1
#   Unregister-ScheduledTask -TaskName PortfolioTrackerRefresh   # to remove

param(
    [int]$EveryMinutes = 15,
    [string]$TaskName = "PortfolioTrackerRefresh"
)

$repo   = Split-Path -Parent $PSScriptRoot
$python = (Get-Command python -ErrorAction Stop).Source

$action  = New-ScheduledTaskAction -Execute $python `
             -Argument "-m tracker refresh --market-hours-only" `
             -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date `
             -RepetitionInterval (New-TimeSpan -Minutes $EveryMinutes) `
             -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
             -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Pull quotes and re-export Power BI data" -Force | Out-Null

Write-Host "Registered $TaskName (every $EveryMinutes min) running from $repo"
