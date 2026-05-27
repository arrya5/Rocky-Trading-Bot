# setup_scheduler.ps1
# Creates 4 Windows Task Scheduler tasks to run the trading bot routines
# automatically every weekday (Mon-Fri) in IST.
#
# Run ONCE from an Administrator PowerShell:
#   powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1
#
# To remove all tasks later:
#   schtasks /delete /tn "TradingBot-PreMarket"  /f
#   schtasks /delete /tn "TradingBot-MarketOpen" /f
#   schtasks /delete /tn "TradingBot-Midday"     /f
#   schtasks /delete /tn "TradingBot-EOD"        /f

$ProjectDir = "C:\documents\Ultimate Trading Bot"
$PythonExe  = (Get-Command python -ErrorAction SilentlyContinue).Source

if (-not $PythonExe) {
    Write-Error "Python not found in PATH. Install Python and re-run."
    exit 1
}

$RunScript = Join-Path $ProjectDir "run.py"
if (-not (Test-Path $RunScript)) {
    Write-Error "run.py not found at $RunScript"
    exit 1
}

Write-Host "Using Python : $PythonExe"
Write-Host "Project root : $ProjectDir"
Write-Host ""

# Task definitions: Name | IST time | routine argument
$Tasks = @(
    [PSCustomObject]@{ Name = "TradingBot-PreMarket";   Time = "08:30"; Routine = "pre_market"  },
    [PSCustomObject]@{ Name = "TradingBot-MarketOpen";  Time = "09:20"; Routine = "market_open" },
    [PSCustomObject]@{ Name = "TradingBot-Midday";      Time = "12:30"; Routine = "midday"      },
    [PSCustomObject]@{ Name = "TradingBot-EOD";         Time = "15:45"; Routine = "eod"         }
)

foreach ($T in $Tasks) {
    # Build the action: python run.py <routine>
    $Action = New-ScheduledTaskAction `
        -Execute    $PythonExe `
        -Argument   "`"$RunScript`" $($T.Routine)" `
        -WorkingDirectory $ProjectDir

    # Trigger: weekly, Mon-Fri, at the specified IST time
    $Trigger = New-ScheduledTaskTrigger `
        -Weekly `
        -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday `
        -At $T.Time

    # Settings: run even if missed, 1-hour execution cap
    $Settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable

    # Register (overwrites if already exists)
    Register-ScheduledTask `
        -TaskName $T.Name `
        -Action   $Action `
        -Trigger  $Trigger `
        -Settings $Settings `
        -RunLevel Highest `
        -Force | Out-Null

    Write-Host "CREATED  $($T.Name)  →  weekdays at $($T.Time) IST  (python run.py $($T.Routine))"
}

Write-Host ""
Write-Host "All 4 tasks registered. Verify in Task Scheduler (taskschd.msc)."
Write-Host ""
Write-Host "To test immediately:"
Write-Host "  Start-ScheduledTask -TaskName 'TradingBot-PreMarket'"
Write-Host ""
Write-Host "Logs appear in the console/Telegram. No Claude Code subscription needed."
