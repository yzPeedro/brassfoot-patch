[CmdletBinding()]
param(
    [switch]$Refresh,
    [switch]$DryRun,
    [switch]$Offline,
    [switch]$NoFallback,
    [ValidateRange(0,100)][int]$MaxRequests=25
)
$ErrorActionPreference = 'Stop'
$injected = $false
if (-not $Offline -and [string]::IsNullOrWhiteSpace($env:API_FOOTBALL_KEY)) {
    $secretDir = Join-Path $env:LOCALAPPDATA 'BrassfootPatch'
    $secretPath = Join-Path $secretDir 'api-football.key'
    if (-not (Test-Path -LiteralPath $secretPath -PathType Leaf)) {
        New-Item -Path $secretDir -ItemType Directory -Force | Out-Null
        Write-Host 'Cole a chave API-Football. Ela sera armazenada via DPAPI, apenas para seu usuario.'
        $secure = Read-Host 'API-Football Key' -AsSecureString
        $encrypted = ConvertFrom-SecureString -SecureString $secure
        Set-Content -LiteralPath $secretPath -Encoding ASCII -Value $encrypted
    } else {
        $encrypted = (Get-Content -LiteralPath $secretPath -Raw).Trim()
        $secure = ConvertTo-SecureString -String $encrypted
    }
    $key = (New-Object System.Net.NetworkCredential('', $secure)).Password
    if ([string]::IsNullOrWhiteSpace($key)) { throw 'A chave da API esta vazia.' }
    $env:API_FOOTBALL_KEY = $key
    $injected = $true
    Remove-Variable key, secure, encrypted -ErrorAction SilentlyContinue
}
Push-Location $PSScriptRoot
try {
    $cliArgs = @('api_football_sync.py','--max-requests', "$MaxRequests")
    if ($Refresh) { $cliArgs += '--refresh' }
    if ($DryRun) { $cliArgs += '--dry-run' }
    if ($Offline) { $cliArgs += '--offline' }
    if ($NoFallback) { $cliArgs += '--no-fallback' }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 @cliArgs
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python @cliArgs
    } else {
        throw 'Python 3.10+ nao encontrado.'
    }
    if ($LASTEXITCODE -ne 0) { throw "Coleta falhou (exit code $LASTEXITCODE). Consulte data/api-football/2026/YYYY-MM-DD/mapping-report.json." }
}
finally {
    if ($injected) { Remove-Item Env:\API_FOOTBALL_KEY -ErrorAction SilentlyContinue }
    Pop-Location
}
