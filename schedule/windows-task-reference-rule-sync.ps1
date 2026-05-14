# Windows Task Scheduler template for Reference Rule Sync.
# Run this script from the copied schedule/ directory, or edit $ProjectRoot.

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$TaskName = "Reference Rule Sync"
$Script = Join-Path $ProjectRoot "reference_rule_sync.py"

if ($env:REFERENCE_RULE_PYTHON) {
  $Python = $env:REFERENCE_RULE_PYTHON
} else {
  $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $Python) {
  throw "Python executable not found. Set REFERENCE_RULE_PYTHON to the full python.exe path before registering the task."
}

$Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`" sync --root `"$ProjectRoot`""
$Trigger = New-ScheduledTaskTrigger -Daily -At 3:20am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Sync Reference_sources and upstream wrappers." -Force

Write-Host "Registered scheduled task: $TaskName"
