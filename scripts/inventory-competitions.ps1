[CmdletBinding()]
param(
    [string]$GamePath = 'C:\Brasfoot22-23',
    [string]$OutputDirectory = "$env:USERPROFILE\Downloads"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path -LiteralPath $GamePath -ErrorAction Stop).ProviderPath.TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $root 'teams') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $root 'options.bcf') -PathType Leaf)) {
    throw 'Pasta invalida: selecione o Brasfoot com teams e options.bcf.'
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$dest = (Resolve-Path -LiteralPath $OutputDirectory).ProviderPath
if ($dest.Equals($root, [StringComparison]::OrdinalIgnoreCase) -or
    $dest.StartsWith(($root + '\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Por seguranca, grave fora da pasta do Brasfoot.'
}

$extensions = @{}
$directories = New-Object 'System.Collections.Generic.List[string]'
$candidates = New-Object 'System.Collections.Generic.List[object]'
$prefix = $root + '\'
$excluded = '(?i)(^|/)(saves?|backups?|logs?|screenshots?|users?|profiles?|crashdumps?|temp)(/|$)'
$competitionTerms = '(?i)compet|camp(eonato)?|league|liga|division|divis[aã]o|serie|copa|cup|torneio|brasil|national|tabela|regra|ranking'
$dataExtensions = @('.ces','.dat','.db','.db3','.sqlite','.sqlite3','.idx','.bin','.bcf','.bfc','.bf','.pak','.cfg','.ini','.xml','.json','.csv','.properties')
$ignoredExtensions = @('.s22','.sbck','.bak','.png','.jpg','.jpeg','.gif','.bmp','.webp','.mp4','.mp3','.wav','.dll','.exe','.jar','.class','.zip','.rar','.7z')

foreach ($dir in @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)) {
    if (($dir.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
    if (-not $dir.FullName.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { continue }
    $relative = $dir.FullName.Substring($prefix.Length).Replace('\','/')
    if ($relative -match $excluded) { continue }
    if ($directories.Count -lt 3000) { $directories.Add($relative) }
}
foreach ($file in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)) {
    if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
    if (-not $file.FullName.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { continue }
    $relative = $file.FullName.Substring($prefix.Length).Replace('\','/')
    if ($relative -match $excluded) { continue }
    $ext = $file.Extension.ToLowerInvariant()
    if ($ignoredExtensions -contains $ext) { continue }
    if (-not $extensions.ContainsKey($ext)) { $extensions[$ext] = 0 }
    $extensions[$ext] += 1
    if ($ext -in $dataExtensions -or $relative -match $competitionTerms) {
        if ($relative -eq 'options.bcf') { continue }
        if ($candidates.Count -lt 8000) {
            $candidates.Add([PSCustomObject]@{ relativePath = $relative; extension = $ext; bytes = $file.Length })
        }
    }
}
$result = [PSCustomObject]@{
    schemaVersion = 1
    purpose = 'read-only-competition-structure-discovery'
    capturedAtUtc = (Get-Date).ToUniversalTime().ToString('o')
    rootDirectoryIncluded = $false
    contentCopied = $false
    ignoredUserData = @('saves','profiles','options.bcf','executables','archives','images','audio','backups')
    fileCountsByExtension = $extensions
    directoryNames = $directories.ToArray()
    candidateDataFiles = $candidates.ToArray()
}
$out = Join-Path $dest ('Brasfoot-2026-competicoes-inventario-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.json')
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Inventario salvo em: $out" -ForegroundColor Green
Write-Host "Diretorios: $($directories.Count) | Arquivos de dados candidatos: $($candidates.Count)" -ForegroundColor Cyan
Write-Host 'Nenhum arquivo do jogo foi copiado ou modificado. O relatorio contem apenas nomes relativos, tipos e tamanhos.'
