[CmdletBinding()]
param(
    [string]$GamePath = 'C:\Brasfoot22-23',
    [string]$OutputDirectory = "$env:USERPROFILE\Downloads"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$game = (Resolve-Path -LiteralPath $GamePath -ErrorAction Stop).ProviderPath
$teams = Join-Path $game 'teams'
if (-not (Test-Path -LiteralPath $teams -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $game 'options.bcf') -PathType Leaf)) {
    throw 'Pasta invalida: selecione a instalacao do Brasfoot que contem teams e options.bcf.'
}

New-Item -Path $OutputDirectory -ItemType Directory -Force | Out-Null
$outDir = (Resolve-Path -LiteralPath $OutputDirectory).ProviderPath
$gamePrefix = $game.TrimEnd('\') + '\'
if ($outDir.Equals($game, [StringComparison]::OrdinalIgnoreCase) -or
    $outDir.StartsWith($gamePrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Por seguranca, o ZIP deve ficar fora da pasta do jogo.'
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$destination = Join-Path $outDir "Brasfoot-2026-estrutura-privada-$stamp.zip"
$banFiles = @(Get-ChildItem -LiteralPath $teams -File -Filter '*.ban')
$competitionFiles = @(Get-ChildItem -LiteralPath $game -File -Filter '*.ces')
if ($banFiles.Count -lt 10) { throw 'Poucos arquivos .ban encontrados; confirme o caminho da instalacao.' }

function Assert-RegularInput([IO.FileInfo] $file) {
    if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Link simbolico recusado: $($file.Name)"
    }
    if ($file.Length -lt 4 -or $file.Length -gt 16777216) {
        throw "Arquivo fora dos limites permitidos: $($file.Name) ($($file.Length) bytes)"
    }
}

$archive = [IO.Compression.ZipFile]::Open($destination, [IO.Compression.ZipArchiveMode]::Create)
try {
    $teamsInfo = @()
    foreach ($file in $banFiles) {
        Assert-RegularInput $file
        $entry = 'teams/' + $file.Name
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $file.FullName, $entry, [IO.Compression.CompressionLevel]::Optimal) | Out-Null
        $teamsInfo += [pscustomobject]@{
            path = $entry
            bytes = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }

    $competitionsInfo = @()
    foreach ($file in $competitionFiles) {
        Assert-RegularInput $file
        $entry = 'competitions/' + $file.Name
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $file.FullName, $entry, [IO.Compression.CompressionLevel]::Optimal) | Out-Null
        $competitionsInfo += [pscustomobject]@{
            path = $entry
            bytes = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }

    $assetDirs = @('teams\escudos', 'teams\escudosMini', 'teams\camisas',
                   'teams\camisas2', 'teams\camisas3')
    $assets = @()
    foreach ($relative in $assetDirs) {
        $dir = Join-Path $game $relative
        if (-not (Test-Path -LiteralPath $dir -PathType Container)) { continue }
        foreach ($file in @(Get-ChildItem -LiteralPath $dir -File)) {
            if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
            if ($file.Length -le 0 -or $file.Length -gt 20971520) { continue }
            $assets += [pscustomobject]@{
                path = ($relative.Replace('\','/') + '/' + $file.Name)
                bytes = $file.Length
                extension = $file.Extension.ToLowerInvariant()
                sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        }
    }

    $metadata = [pscustomobject]@{
        schemaVersion = 1
        purpose = 'private-offline-Brasfoot-structure-audit'
        capturedAtUtc = (Get-Date).ToUniversalTime().ToString('o')
        teamCount = $teamsInfo.Count
        competitionCount = $competitionsInfo.Count
        assetCount = $assets.Count
        teams = $teamsInfo
        competitions = $competitionsInfo
        imageInventory = $assets
        exclusions = @('saved games', '*.s22', '*.sbck', 'options.bcf', '*.exe', 'API keys', 'full graphic assets')
        warning = 'Contains licensed original game team and competition data. Keep private; NEVER publish the ZIP.'
    }
    $json = $metadata | ConvertTo-Json -Depth 8
    $record = $archive.CreateEntry('metadata.json', [IO.Compression.CompressionLevel]::Optimal)
    $stream = $record.Open()
    $writer = [IO.StreamWriter]::new($stream, [Text.UTF8Encoding]::new($false))
    try { $writer.Write($json) } finally { $writer.Dispose() }
} finally {
    $archive.Dispose()
}

Write-Host "Coleta concluida: $destination" -ForegroundColor Green
Write-Host "Equipes: $($banFiles.Count) | Competições: $($competitionFiles.Count) | Arquivos graficos inventariados: $($assets.Count)" -ForegroundColor Cyan
Write-Host 'Nenhum save, configuração pessoal ou executável do jogo foi copiado.'
Write-Host 'ATENCAO: ZIP PRIVADO. Nao publique no GitHub.' -ForegroundColor Yellow
