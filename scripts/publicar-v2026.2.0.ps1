#requires -version 5.1
<#
 Publishes only the exact V4 ZIP approved by the maintainer.
 The release workflow validates SHA-256 again before enabling the website.
#>
param([string] $ZipPath = (Join-Path $env:USERPROFILE 'Downloads\Brasfoot-2026-ABC20-Compatibilidade-v4.zip'))
$ErrorActionPreference = 'Stop'
$repo = 'yzPeedro/brassfoot-patch'
$tag = 'v2026.2.0'
$assetName = 'Brasfoot-2026-ABC20-Compatibilidade-v4.zip'
$exeName = 'Brasfoot-2026-ABC20-Compatibilidade-v4.exe'
$expectedZipSHA = '25264615120dba5681c5238b331d5012c40b3ffea1c933f1d23bdfe755b2cbd3'
$expectedExeSHA = 'a894362f73a09f23cdb187a4b1574df820a8d696478803ebe7d488221f708654'
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw 'GitHub CLI (gh) nao encontrado. Instale e autentique antes de publicar.'
}
$ZipPath = (Resolve-Path -LiteralPath $ZipPath).Path
$file = Get-Item -LiteralPath $ZipPath
if ($file.Name -ne $assetName -or $file.Length -ne 967095) {
    throw 'Nome ou tamanho do ZIP invalido. Nada publicado.'
}
$actualZip = (Get-FileHash -Algorithm SHA256 -LiteralPath $ZipPath).Hash.ToLowerInvariant()
if ($actualZip -ne $expectedZipSHA) {
    throw "SHA-256 ZIP invalido: $actualZip. Nada publicado."
}
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
try {
    $entry = $archive.GetEntry($exeName)
    if ($null -eq $entry -or $entry.Length -ne 2199040) {
        throw 'EXE V4 ausente ou tamanho inesperado.'
    }
    $stream = $entry.Open()
    try {
        $hasher = [System.Security.Cryptography.SHA256]::Create()
        try {
            $actualExe = ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
        } finally {
            $hasher.Dispose()
        }
        if ($actualExe -ne $expectedExeSHA) {
            throw "SHA-256 EXE invalido: $actualExe. Nada publicado."
        }
    } finally { $stream.Dispose() }
} finally { $archive.Dispose() }

& gh auth status --hostname github.com
if ($LASTEXITCODE -ne 0) { throw 'gh nao autenticado. Nao publicado.' }
# Nao chame 'gh release view' aqui: quando a release ainda nao existe,
# o gh escreve 'release not found' em stderr e o Windows PowerShell 5.1
# converte essa mensagem em erro terminante com ErrorActionPreference=Stop.
# 'gh release create' ja recusa o tag que possua release publicada, sem sobrescrever.
Write-Host "Criando $tag. Se a release ja existir, gh release create ira recusar a operacao."
$notes = @'
## Brasfoot Patch 2026.2.0 — primeira versão de ano e divisões corrigidas
- Seletor de carreira somente 2026.
- Series A/B/C com 20 clubes cada, incluido Maranhao experimental.
- Reconhece hashes originais e da antiga v2026.0.2.
- Cria copia isolada sem modificar jogo original nem copiar saves.

LIMITACOES: nao instala novos elencos B/C; mantem plantéis históricos. Maranhao
usa atributos experimentais. Serie D mantém configuracao original de 64
clubes/8 grupos, mas participacao pode ser afetada pela reclassificacao.
Temporadas inteiras e transicao para 2027 nao foram homologadas.

Como instalar: extraia o ZIP, abra o utilitario V4, indique Brasfoot 22-23
original e execute bf22-23.exe na nova pasta criada.
'@
$notesFile = Join-Path $env:TEMP 'brasfoot-v2026.2.0-notes.md'
[System.IO.File]::WriteAllText($notesFile, $notes, (New-Object System.Text.UTF8Encoding($false)))
Write-Host 'SHA-256 ZIP e EXE validados. Publicando release...' -ForegroundColor Cyan
& gh release create $tag $ZipPath -R $repo --target main --latest --title 'Brasfoot Patch 2026.2.0 - Ano e series A/B/C' --notes-file $notesFile
if ($LASTEXITCODE -ne 0) { throw 'Falha ao publicar a release.' }
Write-Host 'Release criada. O workflow confirmara o ZIP e atualizara o site automaticamente.' -ForegroundColor Green
Write-Host "https://github.com/$repo/releases/tag/$tag"
