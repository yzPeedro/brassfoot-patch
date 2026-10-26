# Continuidade Windows

Tarefa: `Brasfoot Mega Patch - Continuity`, a cada 15 minutos e no login, usuário atual sem elevação. Requer computador ligado e usuário autenticado; `StartWhenAvailable` recupera disparos perdidos. Não depende de conversa aberta.

Entrada: `scripts/run-continuity.ps1` → `tools/continuity_service.py` → Alethe → Codex não interativo, modelo econômico `gpt-6-luna`, esforço high. Cada worker tem prazo de 120 segundos; duas chamadas/dia e limite de 20.000 tokens reportados/dia. Reservas conservadoras impedem novas chamadas quando uso não foi reportado. Limites não aumentam automaticamente.

Configuração local: `config/continuity.local.json` (não versionada), baseada em `config/continuity.example.json`. Backlog versionado: `config/backlog.json`. Estado, reservas, tentativas, planos e logs: `data/private/continuity/`. Falhas preservam alterações para recuperação; não há reset/clean destrutivo.

Cota real: RPC `account/rateLimits/read` do app-server, sem iniciar turno de modelo, conforme [documentação oficial](https://learn.chatgpt.com/docs/app-server). Somente autenticação ChatGPT já existente; API key/provedores pagos recusados. Leitura indisponível adia execução; uso ≥70% espera reset e nova consulta. Nenhum crédito/reset é comprado ou consumido.

Integração automática restrita aos caminhos do contrato, após checks; commit e push sem force. Falha de push permanece recuperável. Nenhum binário novo é publicado por este serviço. A coleta mundial e a promoção de releases permanecem pendentes no backlog; não confundir o agendador com essas funcionalidades.

Diagnóstico: `python tools/continuity.py --config config/continuity.local.json status`. Recuperação: corrigir causa registrada no journal, preservar diff, e reprogramar apenas a tarefa afetada no estado local. Parada: desabilitar a tarefa no Windows Task Scheduler. Instalação reproduzível: `powershell -NoProfile -File scripts/install-continuity.ps1`.

Teste inicial real: tarefa separada `Continuity Smoke` executou em 26/10/2026 às 19:35:11 (PID 71536), terminou com código 0; nova execução automática às 19:35:39 (PID 24496) reutilizou o checkpoint e não repetiu a operação diária. Evidência em `data/private/continuity-smoke/`. Esse teste prova scheduler/processos/estado; a recuperação de onda Codex precisa ser comprovada separadamente.

Incidente de or?amento: Alethe reportou 163.273 tokens (mais 5.928.192 de cache) numa chamada configurada para 20.000. O limite reportado n?o ? teto r?gido durante a chamada. Consumo real lan?ado no ledger: nenhuma nova onda hoje. Pr?ximas chamadas limitadas a 120 segundos; monitorar consumo antes de ampliar. Custo monet?rio n?o reportado.
