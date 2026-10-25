# Requires JDK 17+ (java + javac on PATH). Never writes to the game installation.
[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [ValidateSet('audit','export','inspect','clone','rename-player','replace-roster')]
    [string]$Command = 'audit',

    [string]$GameRoot = 'C:\Brasfoot22-23',
    [string]$InputFile,
    [string]$OutputPath,
    [string]$OldName,
    [string]$NewName,
    [string]$RosterJson
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$classes = Join-Path $root 'build\classes'
$javaFiles = @(
    Get-ChildItem -LiteralPath (Join-Path $root 'src') -Recurse -Filter '*.java' -File |
        ForEach-Object { $_.FullName }
)

foreach ($program in @('java','javac')) {
    if (-not (Get-Command $program -ErrorAction SilentlyContinue)) {
        throw "Nao foi encontrado '$program'. Instale um JDK 17+ e coloque bin no PATH."
    }
}

if ($javaFiles.Count -eq 0) { throw 'Nenhum fonte Java encontrado.' }
New-Item -ItemType Directory -Path $classes -Force | Out-Null
& javac -encoding UTF-8 -d $classes @javaFiles
if ($LASTEXITCODE -ne 0) { throw "Compilacao Java falhou ($LASTEXITCODE)." }

$teams = Join-Path $GameRoot 'teams'
$arguments = switch ($Command) {
    'audit' {
        if (-not (Test-Path -LiteralPath $teams -PathType Container)) {
            throw "Diretorio nao encontrado: $teams"
        }
        @('audit-directory', $teams)
    }
    'export' {
        if (-not $OutputPath) { throw 'Informe -OutputPath para a exportacao.' }
        @('export-directory', $teams, $OutputPath)
    }
    'inspect' {
        if (-not $InputFile) { throw 'Informe -InputFile.' }
        @('inspect', $InputFile)
    }
    'clone' {
        if (-not $InputFile -or -not $OutputPath) { throw 'Informe -InputFile e -OutputPath.' }
        @('clone', $InputFile, $OutputPath)
    }
    'replace-roster' {
        if (-not $InputFile -or -not $OutputPath -or -not $RosterJson) {
            throw 'Informe -InputFile, -OutputPath e -RosterJson.'
        }
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) { throw 'Python 3 nao encontrado no PATH.' }
        $tsv = Join-Path ([System.IO.Path]::GetTempPath()) ('brassfoot-roster-' + [guid]::NewGuid().ToString('N') + '.tsv')
        try {
            & python (Join-Path $root 'roster_to_tsv.py') --json $RosterJson --out $tsv
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao validar o elenco JSON.' }
            & java -cp $classes app.Main replace-roster $InputFile $tsv $OutputPath
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao serializar o .ban.' }
            return
        } finally {
            Remove-Item -LiteralPath $tsv -Force -ErrorAction SilentlyContinue
        }
    }
    'rename-player' {
        if (-not $InputFile -or -not $OutputPath -or -not $OldName -or -not $NewName) {
            throw 'Informe -InputFile, -OutputPath, -OldName e -NewName.'
        }
        @('rename-player', $InputFile, $OldName, $NewName, $OutputPath)
    }
}

& java -cp $classes app.Main @arguments
if ($LASTEXITCODE -ne 0) { throw "Comando falhou ($LASTEXITCODE)." }
