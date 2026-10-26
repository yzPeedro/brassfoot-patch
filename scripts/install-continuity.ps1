#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Name = 'Brasfoot Mega Patch - Continuity',
    [string]$Config = 'config/continuity.local.json',
    [int]$IntervalMinutes = 15
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$configPath = (Resolve-Path (Join-Path $root $Config)).Path
$runner = Join-Path $PSScriptRoot 'run-continuity.ps1'
$arguments = '-NoProfile -NonInteractive -WindowStyle Hidden -File "' + $runner + '" -Config "' + $configPath + '"'
$action = New-ScheduledTaskAction -Execute (Join-Path $PSHOME 'powershell.exe') -Argument $arguments -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$login = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $Name -Action $action -Trigger @($trigger,$login) -Settings $settings -Principal $principal -Force | Out-Null
Get-ScheduledTask -TaskName $Name | Select-Object TaskName,State
