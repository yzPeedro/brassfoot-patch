#requires -Version 5.1
<#
Configura, uma única vez, o ciclo diário do Brasfoot Patch no próprio Windows.
Usa o usuário atual e suas credenciais gh locais. Não envia chaves ao repositório.
Não utiliza GitHub Actions. O agendador executa tarefas perdidas quando possível.
#>
[CmdletBinding()]
param(
    [string]$Horario = '07:00',
    [string]$Nome = 'Brassfoot Patch 2026 - Ciclo Automatico'
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($Horario -notmatch '^([01]\d|2[0-3]):[0-5]\d$') { throw 'Horario deve estar em HH:mm' }
$script = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'ciclo-automatico.ps1')).Path
if (-not (Get-Command Register-ScheduledTask -ErrorAction SilentlyContinue)) {
    throw 'Agendador de Tarefas do Windows não disponível'
}
$parts=$Horario.Split(':')
$time=(Get-Date).Date.AddHours([int]$parts[0]).AddMinutes([int]$parts[1])
$exe = Join-Path $PSHOME 'powershell.exe'
$argument='-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$script+'"'
$action=New-ScheduledTaskAction -Execute $exe -Argument $argument -WorkingDirectory (Split-Path $PSScriptRoot -Parent)
$trigger=New-ScheduledTaskTrigger -Daily -At $time
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 4)
$identity=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal=New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $Nome -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "Ciclo diário configurado para $Horario no usuário $identity." -ForegroundColor Green
Write-Host 'O computador deve estar ligado e o usuário autenticado; nenhuma aprovação de release é solicitada.'
