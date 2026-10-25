# Inventário seguro/read-only de arquivos adicionais da instalação do Brasfoot.
[CmdletBinding()]
param(
    [string]$GameRoot = 'C:\Brasfoot22-23',
    [string]$OutputPath = "$PSScriptRoot\installation-diagnostics.json"
)
$ErrorActionPreference='Stop'
if (-not (Test-Path -LiteralPath $GameRoot -PathType Container)) {
    throw "Instalacao nao encontrada: $GameRoot"
}
$files=@(Get-ChildItem -LiteralPath $GameRoot -Recurse -File)
$interesting=@($files | Where-Object { $_.Extension -in @('.ces','.bcf','.cfg','.info') })
$metadata=@(foreach ($file in $interesting) {
    $buf=New-Object byte[] 32
    $stream=[System.IO.File]::OpenRead($file.FullName)
    try { $count=$stream.Read($buf,0,32) }
    finally { $stream.Dispose() }
    [ordered]@{
        file=$file.FullName.Substring($GameRoot.Length).TrimStart('\')
        size=$file.Length
        prefix=([BitConverter]::ToString($buf,0,$count)).Replace('-','')
    }
})
$stems=@('flamengo','palmeiras','fluminense','gremio','vasco','santos','bahia','vitoria','mirassol','remo')
$evidence=@(foreach ($stem in $stems) {
    [ordered]@{
        club=$stem
        paths=@($files | Where-Object {
            $_.BaseName -match ('(?i)' + [regex]::Escape($stem))
        } | ForEach-Object {
            $_.FullName.Substring($GameRoot.Length).TrimStart('\')
        })
    }
})
$diagnostics=[ordered]@{
    source=$GameRoot
    totalFiles=$files.Count
    teamBanCount=@($files | Where-Object {$_.Extension -eq '.ban'}).Count
    assetPngCount=@($files | Where-Object {$_.Extension -eq '.png'}).Count
    extraFormats=$metadata
    missingClubNameEvidence=$evidence
    warning='Nomes encontrados em arquivos nao comprovam equipes jogaveis; nao inclui binarios nem dados do executavel.'
}
$diagnostics | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host "Relatorio gerado em $OutputPath"
