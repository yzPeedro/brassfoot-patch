[CmdletBinding()]
param(
    [string]$GamePath = 'C:\Brasfoot22-23',
    [string]$OutputDirectory = "$env:USERPROFILE\Downloads"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$root = (Resolve-Path -LiteralPath $GamePath -ErrorAction Stop).ProviderPath.TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $root 'teams') -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $root 'options.bcf') -PathType Leaf)) {
    throw 'Instalacao nao reconhecida: teams e options.bcf nao encontrados.'
}
$national = Join-Path $root 'conf_ligas_nacionais'
$states = Join-Path $root 'conf_estadual'
if (-not (Test-Path -LiteralPath (Join-Path $national 'BRA.cfg') -PathType Leaf) -or
    -not (Test-Path -LiteralPath $states -PathType Container)) {
    throw 'Nao encontrei a configuracao BRA.cfg e a pasta conf_estadual.'
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$outDir = (Resolve-Path -LiteralPath $OutputDirectory).ProviderPath
if ($outDir.Equals($root,[StringComparison]::OrdinalIgnoreCase) -or
    $outDir.StartsWith(($root + '\'),[StringComparison]::OrdinalIgnoreCase)) {
    throw 'A saida deve ficar fora da pasta do Brasfoot.'
}
$files = @()
foreach ($country in @('BRA.cfg','ESP.cfg')) {
    $file = Join-Path $national $country
    if (Test-Path -LiteralPath $file -PathType Leaf) {
        $files += [pscustomobject]@{Name=('conf_ligas_nacionais/'+$country);Path=$file}
    }
}
$stateFiles = @(Get-ChildItem -LiteralPath $states -File -Filter '*.ces' |
    Where-Object { $_.Name -match '^[A-Z]{2}\.ces$' } | Sort-Object Name)
foreach ($file in $stateFiles) {
    $files += [pscustomobject]@{Name=('conf_estadual/'+$file.Name);Path=$file.FullName}
}
if ($stateFiles.Count -lt 20 -or $files.Count -gt 30) {
    throw 'Quantidade inesperada de arquivos. Abortando coleta.'
}
$infos = @()
foreach ($item in $files) {
    $f = Get-Item -LiteralPath $item.Path -ErrorAction Stop
    if (($f.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $f.Length -lt 1 -or $f.Length -gt 1048576) {
        throw ('Arquivo de configuracao inseguro ou invalido: '+$item.Name)
    }
    $infos += [pscustomobject]@{
        path=$item.Name
        bytes=[long]$f.Length
        sha256=(Get-FileHash -LiteralPath $item.Path -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$meta=[pscustomobject]@{
    schemaVersion=1
    kind='private-brasfoot-competition-configs'
    capturedAtUtc=(Get-Date).ToUniversalTime().ToString('o')
    fileCount=$infos.Count
    files=$infos
    exclusions=@('saves','options.bcf','teams/*.ban','images','executables')
    warning='ZIP privado; nao publicar no GitHub.'
}
$destination=Join-Path $outDir ('Brasfoot-2026-configuracoes-privadas-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.zip')
$zip=[IO.Compression.ZipFile]::Open($destination,[IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($item in $files) {
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,$item.Path,$item.Name,[IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
    $entry=$zip.CreateEntry('metadata.json',[IO.Compression.CompressionLevel]::Optimal)
    $writer=[IO.StreamWriter]::new($entry.Open(),[Text.UTF8Encoding]::new($false))
    try { $writer.Write(($meta | ConvertTo-Json -Depth 8)) }
    finally { $writer.Dispose() }
}
finally { $zip.Dispose() }
$check=[IO.Compression.ZipFile]::OpenRead($destination)
try {
    foreach ($info in $infos) {
        $entry=$check.GetEntry($info.path)
        if ($null -eq $entry -or $entry.Length -ne $info.bytes) {
            throw ('Arquivo ausente ou tamanho incorreto: '+$info.path)
        }
        $stream=$entry.Open()
        $sha256=[Security.Cryptography.SHA256]::Create()
        try { $actual=[BitConverter]::ToString($sha256.ComputeHash($stream)).Replace('-','').ToLowerInvariant() }
        finally { $stream.Dispose();$sha256.Dispose() }
        if ($actual -ne $info.sha256) { throw ('SHA-256 invalido: '+$info.path) }
    }
}
finally { $check.Dispose() }
Write-Host ('ZIP privado criado: '+$destination) -ForegroundColor Green
Write-Host ('Configuracoes nacionais: '+($files.Count-$stateFiles.Count)+'; estaduais: '+$stateFiles.Count) -ForegroundColor Cyan
Write-Host 'Nenhum save, arquivo .ban, imagem ou executavel foi copiado ou modificado.'
Write-Host 'Envie o ZIP nesta conversa; nao o publique.' -ForegroundColor Yellow
