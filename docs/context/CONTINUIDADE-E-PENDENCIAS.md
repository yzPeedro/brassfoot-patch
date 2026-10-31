# Continuidade e pendências — Brasfoot Mega Patch

Arquivo carregado automaticamente pelo `CLAUDE.md` da raiz. Registra, por frente ativa, o último estado **verificado** e a próxima ação. Checkpoints antigos não são o estado atual: confira a data de cada frente e revalide no Git e no disco antes de agir.

**Última revisão:** 31/10/2026 ~19h35 (Brasília), pelo Claude Code, após gerar a prévia privada 2026.4.28.

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

**Checkpoint:** 31/10/2026 ~19h35 (Brasília), Claude Code. Estado: prévia **2026.4.28 compilada**, sem teste e sem homologação, aguardando o teste manual do proprietário. **Proibido publicar** (release, tag, asset ou site) sem nova instrução explícita.

- **Objetivo final:** desenhar um campo 2D dentro da tela original de partida, abaixo do placar e acima da tabela de outros jogos, com os 22 jogadores, bola e eventos sincronizados com a engine, **sem alterar o resultado simulado**. A entrega é sempre um instalador local para o proprietário testar.
- **Onde está o código:** branch **local** `live-match-preview` (sem push), commits:
  - `179858b`: máquina de estados;
  - `7844545`: edição 2026.4.28.
  - Para editar: `git switch live-match-preview`. Na `main` esses arquivos não existem.
- **Arquivos:**
  - `tools/live-match-view-src/LiveMatchPanel.java`;
  - `tools/live-match-view-src/LiveMatchTransformer.java` (ASM; injeta `mega/LiveMatchPanel.install(JPanel)` antes de cada `RETURN` de `a.dV.<init>(Ljavax/swing/JFrame;I)V`);
  - `tools/patch_live_match_view.py` (exige base SHA `8193758a…a119`, EXE público da 4.5/4.6/4.7 em `data/private/continental-cups-2026.4.5-final/`);
  - `tools/build_live_match_preview_bundle.py`;
  - `config/edition-live-match-preview.json`;
  - ajustes em `tools/build_distribution.py` (canal lido da edição) e `tools/build_release_bundle.py`.
- **Contexto histórico:** manual §6 e Apêndice A do [contexto mestre](BRASFOOT-MEGA-PATCH-CONTEXTO-MESTRE.md) (transcript do Work, L891–3085).

### Mecânica do motor confirmada por bytecode (a.dV original)

- `GO` é um `javax.swing.Timer` **sem repetição**. Cada disparo chama `qa()`, que soma 1 a `GT` (minuto) e depois `aa(false)`, que processa os lances e, se `GZ` for verdadeiro, chama `oR()` para reagendar o `GO`.
- **Pedido de pausa ou substituição** (clique nos rótulos do placar via `a/dX`, atalho `a/dW` → `qh()`, ou clique na tabela de jogos via `a/ef`) grava `GV >= 0`. No fim do minuto corrente, `aa()` faz `GZ=false`, abre o diálogo modal `e(GV)`, depois volta `GZ=true`, `GV=-1` e chama `oR()`.
- `GU` é o **fim de partida** (definido em `qc()`), não pausa. `dB` é o tempo (1/2); `d` é o intervalo de cada minuto, alterado pelos atalhos de velocidade.
- Os rótulos do placar (`Hr`, até y≈130) ficam fora da área do painel (y≥165).

### O que a 2026.4.28 mudou (sobre a 4.27)

1. **Relógio.**
   - `holdGameClock`/`releaseGameClock` só param o `GO` se ele estava rodando, e só o religam se o painel o parou.
   - Nunca religam após o fim (`GU`) ou com diálogo aberto (`GZ=false`).
   - Se houver pedido de pausa (`GV>=0`) durante uma paralisação visual, o relógio é liberado para o minuto terminar e o Brasfoot abrir a substituição. **Era essa a causa de "não dá para pausar durante a recomposição".**
2. **Posse por contato.**
   - Após um passe, a bola fica **livre** até o receptor tocá-la (`CONTACT = .024`). Só então recebe a posse e um tempo de domínio antes de agir.
   - A condução mantém a bola no pé, na direção do movimento.
   - O passe exige o passador em contato.
3. **Desarme físico** (`startTackle`/`updateTackle`): substitui os passes deliberados ao adversário que causavam o pingue-pongue. Ele é usado:
   - para trocas de posse;
   - para o aumento oficial de desarmes (`hB`);
   - para o início de jogadas planejadas de outro time.
   - Erros de passe oficiais (`hC`) continuam como passe errado ao adversário.
4. **Gol.**
   - O autor recebe a bola livre ou conduz até o ponto planejado.
   - O chute só sai com o autor em contato **e** em posição plausível (90% dentro da área).
   - Prazos de segurança: 7 s, depois a bola rola até o autor; mais 6 s e ele finaliza de onde estiver, sem impasse.
5. **Pênalti e chute defendido ou para fora:** a bola não teletransporta mais para o goleiro. Volta rolando (rebote ou tiro de meta) e o goleiro a domina por contato.
6. **Saída de bola após gol, no início do 2º tempo e no início do jogo:**
   - dois jogadores do time que sofreu o gol (ou do time da vez) vão ao centro;
   - o adversário fica fora do círculo;
   - toque com contato para o companheiro e, em seguida, passe para o meio-campista mais recuado.
   - O relógio só volta quando o companheiro domina, com prazo de 5 s.
7. **Eventos do motor durante paralisações** vão para uma fila e são aplicados ao fim da paralisação. Substituição (6) e assistência (8) são aplicadas na hora.
8. **Substituição, lesão e expulsão:**
   - a escalação é casada pelo **nome completo**;
   - quem entra surge na lateral e corre até a posição;
   - expulsos saem de campo ao fim do lance da falta;
   - quem sai deixa de participar;
   - cartões ficam marcados pela identidade completa;
   - lesão e substituição não passam mais a posse ao jogador que sai.
9. **Estatísticas:** removidos os chutes sintéticos aleatórios. Só os aumentos oficiais de finalizações (`hA`) geram finalização visual. O fallback por texto não move mais a bola.
10. **Tática:**
    - quem tem papel com a bola (receptor, perseguidor, desarmador, condutor, autor do gol, cobradores) é **âncora**: o espaçamento empurra só os outros;
    - os alvos dessas âncoras são recalculados a cada quadro.
    - O `dt` passou a ser o tempo real entre quadros.
11. **Mouse:**
    - sem tooltip;
    - o painel consome os cliques na própria área (embaixo dele só há componentes invisíveis);
    - **cliques na cópia da tabela de outros jogos são repassados à tabela original** com coordenadas convertidas.
12. **Limpeza:** comentários e docstrings removidos dos fontes da prévia; cores e traços pré-alocados no desenho.

### Build 2026.4.28 (verificado em disco em 31/10/2026 ~19h31)

- **EXE de jogo:** `data/private/live-match-preview-20261031-state-machine/bf22-23.exe`, 7.206.683 bytes, SHA-256 `3676b40e2ad2f2aba983912b1965eb25420771c82d48d390846d380609ca4d64`.
- **Bundle:** `…/bundle-2026.4.28`.
  - `BRASFOOT_HOMOLOGATION_PATCH`, `publicationAllowed=false`, `channel=local-preview`, 398 arquivos.
  - **24 origens aceitas**, entre elas a 4.25 instalada (`4c8c46c6…`), a 4.27 e o EXE público `8193758a…`.
  - Cadeias contínuas, com ≤ 8 etapas.
- **Instalador:** `dist/live-match-preview-2026.4.28/Brasfoot-Mega-Patch-2026.4.28-windows-x64.exe`.
  - 7.710.720 bytes, SHA-256 `b7cc5d0e88fd5ca5046e686d36bb659862aacab8509b001897f022292878a1ee`.
  - `SHA256SUMS.txt` confere; subsistema PE 2 (GUI, sem console).
  - `sourceCommit 7844545…`.
- **Comandos** (todos com saída 0):
  1. `python tools/patch_live_match_view.py --source data/private/continental-cups-2026.4.5-final/bf22-23.exe --output <dir>/bf22-23.exe`
  2. `python -m tools.build_live_match_preview_bundle --inherit-bundle data/private/live-match-preview-20261031-fluid-natural/bundle-2026.4.19 --published-executable data/private/live-match-preview-20261031-fluid-natural/bf22-23.exe --preview-executable <dir>/bf22-23.exe` + `--previous-preview-executable` para `tactical-physics`, `tactical-physics-final`, `kickoff-reset`, `possession-kits`, `set-pieces`, `stat-synced-stoppages`, `contact-synced`, `contact-synced-clickthrough` + `--output <dir>/bundle-2026.4.28 --version 2026.4.28`
  3. `python tools/build_distribution.py --bundle <dir>/bundle-2026.4.28 --output dist/live-match-preview-2026.4.28 --edition config/edition-live-match-preview.json --source-commit <commit> --target windows/amd64`
- **Verificações estáticas realizadas (não são testes de jogo):**
  - `javac -source 7 -target 7` sem erro (classfile major 51);
  - carga e inicialização de `mega/*` (6 classes) e de `a.dV` com `-Xverify:all` na JVM 1.8.0_441 do sistema (headless, log redirecionado);
  - nenhum texto de tooltip do painel;
  - manifesto, variantes e hashes conferidos.

### Pendências e riscos

- **Nada foi observado em jogo.** Homologação manual pendente com o checklist do manual §6.8 e os pontos abaixo.
- **Fallback de prazos:**
  - pênalti e falta não têm prazo extra se o cobrador não alcançar a bola (é âncora, deve alcançar);
  - a falta com cartão troca de cobrador após 5 s.
- **Expulsão:** se o motor mantiver o expulso na lista `hl/hm`, ele sai pelo conjunto `redCarded`. O goleiro (posição 0) nunca é desativado.
- **Desfecho de pênalti perdido** (defesa, trave ou fora) continua sorteado, porque a engine não informa.
- **Posse visual:** as trocas sintéticas (a cada 8–14 passes, conforme a posse oficial) são reconstrução visual, não estatística.
- **Layout:** a disposição aprovada nas prévias anteriores foi mantida (campo em y=165 cobrindo a área inferior). O painel original de estatísticas fica sob o campo; a tabela de jogos aparece como cópia clicável.

### Próxima ação recomendada

1. Proprietário instala a 4.28 sobre a 4.25 (jogo fechado) e testa.
2. Corrigir pelo relato no branch `live-match-preview`.
3. Gerar a 4.29 em pasta nova, incluindo `live-match-preview-20261031-state-machine/bf22-23.exe` entre os `--previous-preview-executable`.
4. Ajustar a versão em `config/edition-live-match-preview.json` e o padrão `--version`.

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
  - em §6.7 a 4.27 foi gerada por completo, mas nunca entregue; a 4.28 a substitui como prévia corrente.
