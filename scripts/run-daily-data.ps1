#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $root
$logDir = Join-Path $root 'data/private/daily'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ('maintenance-' + (Get-Date -Format 'yyyyMMdd') + '.log')
& python -m tools.daily_maintenance *>> $log
exit $LASTEXITCODE
