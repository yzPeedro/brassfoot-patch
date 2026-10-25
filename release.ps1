#requires -Version 5.1
[CmdletBinding()]
param(
  [string]$PackagePath = '.\payload',
  [string]$GamePath = '',
  [switch]$Publish
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = $PSScriptRoot
Set-Location $root

function Run([string]$File, [string[]]$Arguments) {
  & $File @Arguments
  if ($LASTEXITCODE -ne 0) { throw "Comando falhou (exit=$LASTEXITCODE): $File $($Arguments -join ' ')" }
}

Write-Host 'Brasfoot Patch 2026 — build seguro do instalador' -ForegroundColor Green
$package = (Resolve-Path -LiteralPath $PackagePath -ErrorAction Stop).Path
$manifest = Join-Path $package 'manifest.json'
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) { throw 'Falta payload/manifest.json validado.' }
$m = Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
if ($m.schemaVersion -ne 2 -or $m.kind -ne 'BRASFOOT_VERIFIED_PATCH' -or
    $m.publicationAllowed -ne $true -or $m.compatibilityTestedInGame -ne $true) {
  throw 'Pacote não é uma release verificada dentro do Brasfoot. Build e publicação bloqueados.'
}
if (-not $GamePath) { throw 'Informe -GamePath com a instalação real utilizada na validação.' }
$game = (Resolve-Path -LiteralPath $GamePath -ErrorAction Stop).Path
if (-not (Test-Path -LiteralPath (Join-Path $game 'options.bcf'))) { throw 'Pasta do Brasfoot incompatível.' }

Run 'py' @('-3', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py', '-q')
Run 'py' @('-3', '-m', 'PyInstaller', '--version')
# A verificação detalhada do patch também é realizada pelo executável antes de qualquer gravação.
$dist = Join-Path $root 'dist'
New-Item -ItemType Directory -Force -Path $dist | Out-Null
Run 'py' @('-3', '-m', 'PyInstaller', '--clean', '--noconfirm', '--onefile', '--windowed',
  '--name', 'Brasfoot-Patch-2026-Setup', '--distpath', $dist,
  '--add-data', "$package;payload", '--paths', $root, (Join-Path $root 'installer-entry.py'))
$exe = Join-Path $dist 'Brasfoot-Patch-2026-Setup.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or (Get-Item $exe).Length -lt 100000) {
  throw 'Nenhum executável Windows válido foi produzido.'
}
$hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "Build criado: $exe`nSHA-256: $hash" -ForegroundColor Green
if ($Publish) {
  # Falhar de maneira segura: compilar não é prova de que o jogo realmente abrirá os .ban.
  throw 'Publicação automática indisponível sem validação funcional independente do .exe no Windows e dos arquivos .ban dentro do Brasfoot. Não anuncie release não testada.'
}
