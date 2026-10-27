#requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$Config)
$env:NINEROUTER_API_KEY = [Environment]::GetEnvironmentVariable("NINEROUTER_API_KEY", "User")

# Public daily collection needs no provider credential. A configured worker
# reports its own authentication failure without disabling daily maintenance.

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $root
# Keep javac and java on the same JDK without changing the user's global PATH.
$javac = Get-Command javac -ErrorAction SilentlyContinue
if ($javac) { $env:PATH = (Split-Path $javac.Source) + ';' + $env:PATH }
$configObject = Get-Content -Raw -Encoding UTF8 -LiteralPath $Config | ConvertFrom-Json
$logDir = $configObject.stateDir
if (-not [IO.Path]::IsPathRooted($logDir)) { $logDir = Join-Path $root $logDir }
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir ('scheduler-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + $PID + '.log')
& python (Join-Path $root 'tools/continuity_service.py') --config $Config *>> $log
exit $LASTEXITCODE



