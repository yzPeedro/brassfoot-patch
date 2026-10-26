#requires -Version 5.1
<#
Ciclo sem aprovação manual, executado em um único Windows autenticado no gh.
Não usa minutos de GitHub Actions. A ausência de candidato validado encerra o ciclo.
Ordem: fonte web -> testes -> build -> release -> SHA -> site -> GitHub Pages.
#>
[CmdletBinding()]
param([switch]$DryRun)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = 'yzPeedro/brassfoot-patch'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$logDir = Join-Path $root 'data\private\auto-release-logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logFile = Join-Path $logDir ('cycle-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')
$lock = $null

function Record([string]$message) {
    $entry = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' | ' + $message
    Write-Host $entry
    Add-Content -LiteralPath $logFile -Value $entry -Encoding UTF8
}
function Run([string]$binary, [string[]]$arguments) {
    & $binary @arguments
    if ($LASTEXITCODE -ne 0) { throw "Comando falhou: $binary $($arguments -join ' ')" }
}
function Newer([string]$candidate, [string]$current) {
    if ($candidate -notmatch '^2026\.\d+\.\d+$' -or $current -notmatch '^2026\.\d+\.\d+$') {
        throw 'Versao fora do padrao 2026.n.n'
    }
    $a = @($candidate.Split('.') | ForEach-Object { [int]$_ })
    $b = @($current.Split('.') | ForEach-Object { [int]$_ })
    return ($a[1] -gt $b[1] -or ($a[1] -eq $b[1] -and $a[2] -gt $b[2]))
}
function PublicRelease([string]$tag) {
    try {
        $headers = @{ 'User-Agent'='BrassfootPatch-2026'; 'Accept'='application/vnd.github+json' }
        return Invoke-RestMethod -Method Get -Headers $headers -Uri ("https://api.github.com/repos/"+$repo+"/releases/tags/"+$tag) -TimeoutSec 35
    } catch {
        if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404) { return $null }
        throw
    }
}
function ConfirmAsset([string]$tag, [string]$filename, [string]$digest, [long]$size) {
    for ($i=0;$i -lt 6;$i++) {
        $release = PublicRelease $tag
        if ($null -ne $release -and -not $release.draft) {
            $assets = @($release.assets | Where-Object { $_.name -eq $filename -and $_.state -eq 'uploaded' })
            if ($assets.Count -eq 1 -and [long]$assets[0].size -eq $size -and $assets[0].digest -eq ('sha256:'+$digest)) {
                return $release
            }
        }
        Start-Sleep -Seconds 5
    }
    throw "Release $tag sem asset público verificável. O site anterior foi preservado."
}
try {
    $lock = [IO.File]::Open((Join-Path $logDir 'cycle.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    Set-Location -LiteralPath $root
    Record 'Ciclo iniciado com lock exclusivo.'
    foreach ($program in @('git','gh','go','node','py')) {
        if (-not (Get-Command $program -ErrorAction SilentlyContinue)) { throw "Dependência ausente: $program" }
    }
    Run 'gh' @('auth','status','--hostname','github.com')
    $branchName = (& git branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $branchName -ne 'main') { throw 'Publicação somente a partir de main' }
    $dirty = @(& git status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) { throw 'Árvore Git com alterações locais; publicação abortada' }
    Run 'git' @('fetch','origin','main','gh-pages')
    Run 'git' @('merge','--ff-only','origin/main')

    # Fontes web e cache primeiro. Esta etapa não consome API-Football.
    Run 'py' @('-3','tools/prepare_bc_2026_source_snapshot.py')
    $manifest = Get-Content -LiteralPath 'windows-installer/bundled_release/manifest.json' -Raw -Encoding UTF8 | ConvertFrom-Json
    $current = Get-Content -LiteralPath 'site/data/release.json' -Raw -Encoding UTF8 | ConvertFrom-Json
    $version = [string]$manifest.version
    if (-not (Newer $version ([string]$current.publishedVersion))) {
        Record "Nenhuma versão nova ($version / $($current.publishedVersion)); release e site inalterados."
        return
    }
    if ($manifest.schemaVersion -ne 4 -or $manifest.kind -ne 'BRASFOOT_VERIFIED_PATCH' -or
        $manifest.publicationAllowed -ne $true -or $manifest.compatibilityTestedInGame -ne $true) {
        Record 'Manifesto de candidato ainda não homologado para release in-place.'
        return
    }
    if (@($manifest.files | Where-Object { $_.path -eq 'bf22-23.exe' -and $_.operation -eq 'replace' }).Count -ne 1) {
        throw 'Executável original sem receita diferencial reconhecida'
    }
    if ($manifest.inPlace -ne $true -or $manifest.bcRostersVerified -ne 40 -or $manifest.serieDUnmodified -ne $true) {
        throw 'Faltam comprovantes automáticos: in-place, B/C completos ou Série D intacta'
    }
    if (-not (Test-Path -LiteralPath 'data/private/bc-release-ready.json')) {
        throw 'Relatório de validação final B/C ausente; não gerar release'
    }
    $ready = Get-Content -LiteralPath 'data/private/bc-release-ready.json' -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($ready.readyForDistribution -ne $true -or $ready.clubCount -ne 60 -or $ready.bcClubCount -ne 40 -or
        $ready.gameplayValidated -ne $true -or $ready.serieDModified -ne $false -or $ready.savesModified -ne $false) {
        throw '40 elencos B/C não verificados; versão anterior preservada'
    }
    Record "Candidato v$version verificado; criando snapshot público a partir de 60 plantéis homologados."
    Run 'py' @('-3','tools/build_public_rosters_2026.py')
    Record 'Iniciando testes e build automático.'
    Run 'py' @('-3','-m','unittest','discover','-s','tests','-q')
    Run 'node' @('site/tests/site.test.js')
    Run 'node' @('site/tests/seo-pix.test.js')
    Run 'node' @('site/tests/explorer-interaction.test.js')
    Push-Location 'windows-installer'
    try {
        Run 'go' @('test','./...')
        Run 'go' @('vet','./...')
        $filename = 'Brassfoot-Patch-2026-Setup.exe'
        $exe = Join-Path $logDir $filename
        Run 'go' @('build','-trimpath','-ldflags=-H windowsgui','-o',$exe,'.')
    } finally { Pop-Location }
    $length = (Get-Item -LiteralPath $exe).Length
    $hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($length -lt 100000 -or $hash -notmatch '^[a-f0-9]{64}$') { throw 'Integridade do instalador inválida' }
    $notes = 'data/private/release-ready-notes.md'
    if (-not (Test-Path -LiteralPath $notes)) { throw 'Changelog completo ausente' }
    if ((Get-Content -LiteralPath $notes -Raw -Encoding UTF8).Length -lt 30) { throw 'Changelog curto ou inválido' }
    if ($DryRun) { Record "DRY RUN aprovado para v$version ($hash); sem publicar."; return }

    $tag = 'v' + $version
    if ($null -eq (PublicRelease $tag)) {
        Record "Criando $tag no GitHub Releases, sem confirmação humana."
        Run 'gh' @('release','create',$tag,$exe,'--repo',$repo,'--target','main','--latest',
                    '--title',("Brasfoot Patch "+$version+" - Atualizacao 2026"),
                    '--notes-file',$notes)
    } else { Record "$tag já existe; conferindo artefato publicado." }
    $verified = ConfirmAsset $tag $filename $hash $length
    Record "Download da release verificado com hash $hash e $length bytes."
    $day = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
    Run 'py' @('-3','tools/publish_site_release.py','--version',$version,'--filename',$filename,
                '--file-size',([string]$length),'--sha256',$hash,'--published-at',$day,'--notes-file',$notes)
    Run 'node' @('site/tests/site.test.js')
    Run 'node' @('site/tests/seo-pix.test.js')
    Run 'node' @('site/tests/explorer-interaction.test.js')
    Run 'git' @('add','site')
    Run 'git' @('commit','-m',("site: divulgar release verificada "+$version))
    Run 'git' @('push','origin','main')

    # O Pages atual usa gh-pages na raiz. Não depende de workflows personalizados.
    $temporary = Join-Path $logDir ('pages-' + [guid]::NewGuid().ToString('N'))
    Run 'git' @('worktree','add','--detach',$temporary,'origin/gh-pages')
    try {
        Push-Location $temporary
        try {
            $tracked = @(& git ls-files)
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao inventariar Pages' }
            foreach ($relative in $tracked) {
                $file = Join-Path $temporary $relative
                if (Test-Path -LiteralPath $file -PathType Leaf) { Remove-Item -LiteralPath $file -Force }
            }
            Copy-Item -Path (Join-Path $root 'site/*') -Destination $temporary -Recurse -Force
            Run 'git' @('add','-A')
            if (@(& git status --porcelain).Count -gt 0) {
                Run 'git' @('commit','-m',("site: publicar "+$version))
                Run 'git' @('push','origin','HEAD:gh-pages')
            }
        } finally { Pop-Location }
    } finally { Run 'git' @('worktree','remove','--force',$temporary) }

    $publicUrl = 'https://yzpeedro.github.io/brassfoot-patch/data/release.json'
    $online = $false
    for ($attempt=0;$attempt -lt 12;$attempt++) {
        try {
            $public = Invoke-RestMethod -Uri ($publicUrl+'?v='+$version+'&attempt='+$attempt) -TimeoutSec 25
            if ($public.publishedVersion -eq $version -and $public.sha256 -eq $hash) { $online=$true; break }
        } catch { Record 'Aguardando propagação do GitHub Pages.' }
        Start-Sleep -Seconds 10
    }
    if (-not $online) { throw 'Release criada, mas a publicação pública do Pages não foi confirmada' }
    Record "SUCESSO: release $tag e GitHub Pages com checksum conferidos."
} catch {
    Record ('ERRO: '+$_.Exception.Message)
    throw
} finally {
    if ($null -ne $lock) { $lock.Dispose() }
}
