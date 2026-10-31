# Continuidade e pendências — Brasfoot Mega Patch

Arquivo carregado automaticamente pelo `CLAUDE.md` da raiz. Registra, por frente ativa, o último estado **verificado** e a próxima ação. Checkpoints antigos não são o estado atual: confira a data de cada frente e revalide no Git e no disco antes de agir.

**Última revisão:** 31/10/2026 ~19h (Brasília), pelo Claude Code, durante a integração da base de conhecimento.

## Protocolo de retomada (toda sessão)

1. `git status --short --branch`, `git fetch origin` e `git log --oneline -5 origin/main`. A rotina das 18h publica a partir de um **worktree separado**, então este checkout pode ficar atrás do remoto.
2. Se houver alterações locais e o checkout estiver atrás:
   - salve `git diff` e um `tar` dos arquivos alterados e não rastreados em `data/private/working-tree-backup-<data>/`;
   - compare cada arquivo com `origin/main` ignorando CRLF;
   - descarte só o que for idêntico ou superado no remoto;
   - avance com `git merge --ff-only`.
   - Nunca usar `reset --hard`, `clean` ou `stash pop` às cegas.
3. `gh release view --json tagName,isDraft,isPrerelease,publishedAt` mostra a última release pública.
4. Leia o checkpoint mais recente em `data/private/scheduled-maintenance/<data>/checkpoint.md`.
5. Identifique a frente abaixo, leia os documentos indicados nela e continue a partir da **próxima ação**. Não refaça etapas listadas como concluídas sem motivo técnico.

## Modelo de checkpoint (atualizar a frente ao encerrar)

```text
Frente / data-hora (Brasília) / agente:
Objetivo final:
Última alteração concluída (commit ou arquivo + mtime):
Arquivos envolvidos:
Estado atual (solicitada/planejada/parcial/implementada/compilada/testada/homologada/publicada):
Problemas identificados:
Correções tentadas e resultado observado:
Evidências (hashes, caminhos, logs, linhas do transcript):
Validações pendentes:
Próxima ação recomendada:
Dependências ou bloqueadores:
```

---

## F1 — Campo animado da partida (prévia PRIVADA) · prioridade P0

- **Objetivo final:** desenhar um campo 2D dentro da tela original de partida, abaixo do placar e acima da tabela de outros jogos, com jogadores, bola e eventos sincronizados com a engine, **sem alterar o resultado simulado**. Entrega somente como instalador local para o proprietário testar. **Proibido publicar** (release, tag, asset ou site) sem nova instrução explícita.
- **Contexto completo:**
  - Manual §6: [manual operacional](BRASFOOT-MEGA-PATCH-MANUAL-OPERACIONAL.md) (linhas 537–697).
  - Transcript do Work: Apêndice A do [contexto mestre](BRASFOOT-MEGA-PATCH-CONTEXTO-MESTRE.md), linhas 891–3085.
  - Os números de linha "L" abaixo referem-se ao contexto mestre.
- **Arquivos (todos locais e não commitados, preservados):**
  - `tools/live-match-view-src/LiveMatchPanel.java`: painel, estado, física e eventos.
  - `tools/live-match-view-src/LiveMatchTransformer.java`: ASM; injeta `mega/LiveMatchPanel.install(JPanel)` no construtor `a.dV.<init>(Ljavax/swing/JFrame;I)V`.
  - `tools/patch_live_match_view.py`: exige base SHA `8193758a…a119`, o EXE publicado desde a 4.5/4.6, em `data/private/continental-cups-2026.4.5-final/`.
  - `tools/build_live_match_preview_bundle.py`.
  - `config/edition-live-match-preview.json`: `version=2026.4.27`, `channel=local-preview`.
  - Ajustes locais em `tools/build_distribution.py` (canal lido da edição) e `tools/build_release_bundle.py` (ignora a variante cuja origem é o próprio alvo).
  - Artefatos: `data/private/live-match-preview-20261031-*` e `dist/live-match-preview-2026.4.*`. Ambos ficam **fora do Git**; existe só a cópia local.
- **Arquitetura confirmada no código:**
  - A tela real da partida é `a.dV`. Até a 4.13 a injeção ia para `a.hk`, que é a tela errada.
  - Classes compiladas para Java 7 (`-source 7 -target 7`, major 51); o transformer roda no JDK 17.
  - O painel fica no `JLayeredPane.PALETTE_LAYER` em y=165. Um timer próprio a 30–144 Hz aproxima a taxa do monitor; não é VSync.
  - O timer para quando a tela sai.
  - Eventos oficiais vêm de `best.A` via `hE()`, tipos 1–8. As estatísticas vêm dos vetores `hz…hD` de `best.I`.
  - Passes, conduções, laterais, posicionamento e local do chute são **reconstrução sintética**.
  - Durante paralisações visuais, o relógio da engine (`GO`, um `javax.swing.Timer`) é parado.
- **Última alteração concluída:** prévia **2026.4.27**, gerada às 18:39–18:40 de 31/10. Verificado em disco:
  - instalador `dist/live-match-preview-2026.4.27/Brasfoot-Mega-Patch-2026.4.27-windows-x64.exe`, 7.476.224 bytes, SHA-256 `29ae6bca272197521a8912f7c486d78fa145fcc1465bef3050f6fb1725d80eb7`, igual ao `SHA256SUMS.txt`;
  - EXE de destino `9544506c841a0e40b76c8fc1ae702dbf0534bf23cb05b0b2967e96e30dd29fe0`;
  - manifest `BRASFOOT_HOMOLOGATION_PATCH` com `publicationAllowed=false`, 398 arquivos;
  - aceita 23 origens: prévias anteriores, originais e publicadas.
  - O `LiveMatchPanel.java` (mtime 18:39:24) **não foi editado depois** desse build.
  - O comando completo de geração está no transcript, L3071.
- **Estado:**
  - A 4.27 está **compilada**, sem teste e sem homologação.
  - A sessão do Work terminou por limite de uso (L3075–3082) **antes de entregar** a 4.26 e a 4.27 ao proprietário.
  - O jogo instalado em `C:\Brasfoot22-23` está com o EXE da **prévia 4.25**, SHA `4c8c46c6…` (`stat-synced-stoppages`); a 4.26 e a 4.27 não foram instaladas.
- **Problemas relatados pelo proprietário na última rodada (L3007–3034):**
  - gols de muito longe;
  - bola fora de sincronia, com jogador marcando sem tocar na bola;
  - impossível pausar ou substituir durante a recomposição;
  - saída de bola após gol pelo jogador errado;
  - loop de passes entre adversários;
  - tooltip indevido;
  - gol durante a recomposição.
- **Correções tentadas e presentes no código da 4.27** (respostas a esses pedidos; nenhuma observada em jogo):
  - identidade pelo nome completo (`findPlayer`);
  - posse só por contato (`handleBallArrival`);
  - chute só com o autor a ≤ 0,025 da bola;
  - zonas de chute plausíveis (`isPlausibleShot`, `choosePlannedSpot`);
  - relógio bloqueado a cada quadro durante paralisação;
  - click-through (`contains()` retorna `false`);
  - tooltip removido;
  - saída do time que sofreu o gol com dois jogadores no centro;
  - reinício do 2º tempo detectado por `dB`.
- **Riscos e dúvidas identificados na leitura do código (não verificados em execução):**
  1. `resumeGameClock()` chama `GO.restart()` sem verificar a pausa manual do Brasfoot. O campo `GU:Z` foi estudado (L3015) mas não é usado; o relógio pode voltar a correr com o jogo pausado.
  2. O caminho de fallback textual `applyEvent` ainda sorteia o alvo do passe (`random.nextInt`). Só roda quando não há objeto de lance.
  3. O "loop de passes entre adversários" foi tratado só pela separação passador/receptor. Não há evidência de que foi resolvido.
  4. O desfecho do pênalti perdido (defesa, trave ou fora) é sorteado, porque a engine não informa.
  5. Os nomes de instalador da 4.8 e da 4.24 não refletem o conteúdo: os bundles saíram com versão anterior porque o build do bundle falhou e a distribuição rodou mesmo assim (comandos encadeados com `;`). **Encadear com verificação de código de saída.**
  6. O código e os scripts da prévia contêm comentários e docstrings em prosa, o que contraria a preferência do proprietário. Remover ao retomar a edição.
- **Validações pendentes:**
  - instalação da 4.27 pelo proprietário sobre a 4.25 instalada;
  - checklist comportamental do manual §6.8;
  - ausência de deadlock na pausa manual e na substituição;
  - pós-jogo sem travar.
- **Próxima ação recomendada:**
  1. Entregar ao proprietário o caminho e o SHA da 4.27 já gerada (sem novo build), com as ressalvas acima.
  2. Coletar o resultado do teste dele.
  3. Antes de uma 4.28, corrigir o risco 1 (respeitar a pausa manual) e remover os comentários.
  4. Gerar com `patch_live_match_view.py` → `build_live_match_preview_bundle` → `build_distribution --target windows/amd64 --edition config/edition-live-match-preview.json`, abortando em erro.
  5. Atualizar a versão em `config/edition-live-match-preview.json` e o padrão `--version` do bundle.
- **Dependências e bloqueadores:**
  - Base pública atual: a 4.7 manteve o EXE da 4.5, então a trava SHA `8193758a…` continua válida. Se uma release futura trocar o EXE, o patcher precisa ser adaptado.
  - Decisão do proprietário sobre versionar no Git o código da prévia. Hoje só existe neste disco; o repositório é público.

## F2 — Manutenção diária pública (elencos, release, site) · operacional

- **Objetivo:** ciclo das 18h conforme [scheduled-maintenance.md](../scheduled-maintenance.md).
- **Última execução concluída:** 31/10/2026, release **v2026.4.7** final/latest.
  - Fonte `2d61dc5`, manifestos `0b1c00b`, confirmação `61511cc`.
  - Windows com 5.470.720 bytes, SHA `6c0ebbaf…09f7`.
  - Pages `fd0ca2c6`, `built`.
  - Checkpoint em `data/private/scheduled-maintenance/2026-10-31/checkpoint.md`.
- **Execução:** rotina `atualizar-brasfoot-e-site` no app Codex. As tarefas do Task Scheduler do Windows (`Continuity` e `Daily Data`) estavam **Disabled** em 31/10 ~19h.
- **Próxima ação:** a próxima execução das 18h de 01/11 segue o playbook. Sem mudança material, não há release.

## F3 — Cobertura de elencos · P1

- **Estado em 31/10:** 704 clubes; 288 fontes completas, 54 parciais preservadas e 362 sem fonte completa. Compilados: 300 substituídos, 54 parciais e 350 preservados.
- **Próxima ação:** ampliar `config/live-roster-team-map.json` e as fontes confiáveis para os 362 clubes sem fonte, sem inventar atributos (manual §5.2).

## F4 — Documentação e metadados defasados · P2

- `config/specification-coverage.json` ainda em `edition=2026.4.0` (9 `implemented` e 33 `partial`, de 42 seções).
- `README.md` cita a 2026.4.1 como atual.
- `release.ps1` exige `docs/releases/v<versão>.md`, que só existe até v2026.4.2; as notas 4.3–4.7 estão em `docs/release-2026.4.N.md`.
- `docs/continuity.md` e `AGENTS.md` citam `data/private/continuity/`, ausente em 31/10.
- **Próxima ação:** corrigir numa entrega de manutenção, sem release do jogo.

## F5 — Validação funcional pública · bloqueada por decisão do proprietário

- Manifestos: `compatibilityVerifiedInGame=false` e `gameplayVerified=false`. Os testes estão dispensados (AGENTS.md).
- Retomar só se o proprietário voltar a autorizar testes. Lista no manual §2.4 e §9.

## F6 — Integração da base de conhecimento · concluída em 31/10/2026

- Contexto mestre e manual movidos sem alteração para `docs/context/`. Os SHA-256 batem com os originais:
  - `bbcc1253…be3`: contexto mestre;
  - `d4c5a7d7…fbc`: manual = linhas 1–884 do mestre.
- Criados: `CLAUDE.md` (raiz), `GUIA-DE-MODULOS.md`, `HISTORICO-E-DECISOES.md` e este arquivo.
- `AGENTS.md` e `docs/current-state.md` passaram a apontar para `docs/context/`.
- Backup do checkout antes da sincronização: `data/private/working-tree-backup-20261031-pre-sync/`.
- Correções do manual que valem sobre o texto original:
  - em §5.5 o destino do bundle é `--output`, não `--destination`;
  - em §7.1 as duas tarefas agendadas estão desabilitadas;
  - em §6.7 a 4.27 foi gerada por completo.
