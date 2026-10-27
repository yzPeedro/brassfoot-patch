#requires -Version 5.1
[CmdletBinding()]
param(
  [string]$PackagePath = '.\windows-installer\bundled_release',
  [string]$OutputDirectory = '',
  [switch]$Publish,
  [switch]$PublishExisting
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Set-Location -LiteralPath $PSScriptRoot
function Invoke-ReleaseCommand([string]$File, [string[]]$Arguments) {
  & $File @Arguments
  if ($LASTEXITCODE -ne 0) { throw "Falha no comando de distribuição: $File (exit=$LASTEXITCODE)" }
}
$edition = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'config/edition.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $PSScriptRoot ('dist/' + $edition.version) }
$notes = Join-Path $PSScriptRoot ('docs/releases/v' + $edition.version + '.md')
if (-not (Test-Path -LiteralPath $notes -PathType Leaf)) { throw 'Escreva as notas da edição antes de construir/publicar.' }
if (-not $PublishExisting) {
  Invoke-ReleaseCommand 'python' @('-m', 'tools.daily_update')
  Invoke-ReleaseCommand 'python' @('tools/build_distribution.py', '--bundle', $PackagePath, '--output', $OutputDirectory, '--snapshot', 'data/private/daily/snapshot.json')
}
Write-Host 'Distribuição experimental. Nenhuma suíte de testes foi executada.'
if ($Publish -or $PublishExisting) {
  Invoke-ReleaseCommand 'python' @('tools/publish_distribution.py', '--directory', $OutputDirectory, '--notes', $notes)
  Invoke-ReleaseCommand 'git' @('add', '--', 'site/data/distribution.json', 'site/data/world-status.json')
  & git diff --cached --quiet
  if ($LASTEXITCODE -eq 1) { Invoke-ReleaseCommand 'git' @('commit', '-m', ('release: publish Mega Patch ' + $edition.version + ' metadata [skip ci]')) }
  elseif ($LASTEXITCODE -ne 0) { throw 'Não foi possível ler o estado do índice Git.' }
  Invoke-ReleaseCommand 'git' @('push', 'origin', 'main')
  Invoke-ReleaseCommand 'python' @('tools/publish_pages.py')
}
