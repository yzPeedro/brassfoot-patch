# Pipeline de dados

Este documento descreve como os dados de elencos e competições chegam aos arquivos que o jogo carrega, ao bundle de release e ao site. A referência de cada ferramenta está em [Referência de módulos](modules.md). O empacotamento e a publicação estão em [Release](release.md).

## Visão geral

```text
365Scores (público) ──▶ collect_live_rosters ──▶ config/rosters-<versão>.json
                                                    │
config/live-rosters-supplement.json ────────────────┤
tools/team-roster-editor/sources/*.tsv (B/C) ───────┤
config/player-status-<ano>.json ────────────────────┤
                                                    ▼
jogo-base + jogo original + última base publicada ──▶ compile_live_rosters ──▶ <saída>/teams/*.ban
                                                                            └─▶ <saída>/report.json
                                                    │
               ┌────────────────────────────────────┼────────────────────────────┐
               ▼                                    ▼                            ▼
   build_release_bundle (--teams)        export_release_rosters        export_patch_clubs
   manifest.json + patches/              site/data/roster-coverage.json   site/data/patch-clubs.json
                                         site/data/published-rosters-2026.json
                                         config/roster-build-<versão>.json
```

O catálogo mundial (`tools/daily_update.py`) é um fluxo separado: ele não produz `.ban`, não altera o executável e não alimenta o bundle.

## Princípios

- **Nada é inventado.** Um clube sem fonte completa mantém o elenco que já tinha. Jogadores sem posição resolvível ficam de fora e o motivo vai para o relatório.
- **Último dado confiável.** Se uma fonte falha, o cache anterior é reutilizado e marcado como antigo. Uma resposta parcial não é tratada como saída de atletas.
- **Proveniência por campo.** O relatório registra, por jogador, se identidade, posição, idade, nacionalidade, lado e características vieram da fonte, foram preservadas ou são valores padrão.
- **Fora do jogo.** Coleta e compilação trabalham em diretórios novos. A instalação do jogo e os saves nunca são tocados.

---

## 1. Coleta de elencos

### Fonte

`tools/collect_live_rosters.py` consulta o serviço público de elencos do 365Scores (`webws.365scores.com`):

1. **Classificações (`standings`):** uma requisição por competição da lista `LEAGUES`, que cobre primeiras divisões europeias, divisões inferiores espanholas e as Séries A, B e C do Brasil.
2. **Competidores (`competitors`):** clubes do mapa fixo que não aparecem nessas classificações, por exemplo rebaixados ou renomeados.
3. **Elencos (`squads`):** em lotes de 8 clubes.

Não usa credenciais, imagens, biografias nem avaliações. Cada resposta é guardada em cache por URL, com `observedAt` e SHA-256 do corpo.

### Identificação dos clubes

Cada clube da fonte precisa corresponder a exatamente um arquivo `.ban` do jogo:

1. **Mapa fixo:** `config/live-roster-team-map.json` liga o ID do clube na fonte ao arquivo (`"133": "teams/villareal_esp.ban"`). Se o arquivo mapeado não existir no catálogo original, a coleta é interrompida. A exceção é `teams/maranhao_ma.ban`, fornecido pela base.
2. **Nome exato:** sem mapa, o coletor compara o nome normalizado (`name`, `longName`, `shortName`) com os clubes do mesmo país no jogo.
3. **Ambiguidade:** mais de um candidato, ou país divergente, leva o clube para `sourceTeamsWithoutGameMatch`, sem correspondência aproximada.

Os países aceitos estão em `GAME_COUNTRIES`, com os códigos numéricos usados nos `.ban`.

Para ampliar a cobertura, acrescente entradas ao mapa fixo depois de confirmar a identidade do clube. Homônimos (mesmo nome em países ou estados diferentes) sempre exigem entrada explícita.

### Execução

O catálogo original é o diretório de `*.ban.json` gerado por `app.Main export-directory` a partir de uma cópia dos `teams/` originais.

```bash
python tools/collect_live_rosters.py \
  --original-catalog <diretório-de-ban.json> \
  --output config/rosters-<versão>.json \
  --refresh
```

### Cache e falhas

- O cache vale 18 horas (`--cache-max-age-hours`). `--refresh` tenta uma resposta nova mesmo dentro da validade.
- Se a requisição falhar e houver cache, o registro antigo é usado com `stale: true` e `refreshError`. Sem cache, a falha vai para `failures`.
- Não há novas tentativas automáticas, proxy nem troca de identidade para contornar limites.
- O diretório de cache (`data/private/live-roster-cache`) é a recuperação da coleta: não o apague.

### Snapshot

O resultado é `config/rosters-<versão>.json`, com:

| Campo | Conteúdo |
|---|---|
| `provider`, `collectedAt`, `leaguesRequested`, `cachePolicy` | origem e contexto da coleta |
| `clubs[]` | clube, `teamFile`, liga, URL pública do elenco, `observedAt`, SHA-256 da resposta, `players[]` e `staff[]` |
| `players[]` | `sourceId`, `fullName`, `shortName`, `birthDate`, `nationality`, `jersey`, `primaryPosition`, `secondaryPositions`, `positionCode`, `flank`, `provenance` |
| `catalogCoverage[]` | situação de cada clube do catálogo original |
| `failures`, `sourceTeamsWithoutGameMatch`, `originalEuropeanTeamsWithoutCurrentSquad` | lacunas explícitas |

Situações em `catalogCoverage`:

| Situação | Significado |
|---|---|
| `source-complete` | 16 ou mais jogadores e pelo menos 2 goleiros |
| `source-partial-preserve-roster` | elenco obtido, mas incompleto; o elenco existente é preservado |
| `source-unavailable-preserve-roster` | clube identificado, mas o elenco não veio |
| `identification-pending-preserve-roster` | clube ainda sem correspondência na fonte |

Membros da comissão técnica (posição de ID 0 na fonte) ficam em `staff` e não entram no elenco.

### Suplemento

`config/live-rosters-supplement.json` tem o mesmo formato de `clubs[]` e registra em `identitySources` as evidências de identidade de clubes renomeados. O compilador recebe o arquivo com `--supplement`. Pelo código atual, um clube do suplemento substitui o do snapshot quando o snapshot não tem o clube ou quando o suplemento traz mais jogadores. Revise o suplemento sempre que o snapshot for renovado.

---

## 2. Política de elencos

As regras abaixo estão em `tools/roster_position_map.py`, `tools/compile_live_rosters.py` e `src/app/Main.java`.

### Posições

| Código | Posição | Exemplos de rótulos aceitos |
|---|---|---|
| `0` | goleiro | goalkeeper, goleiro |
| `1` | lateral | right back, left back, wing back, lateral, ala |
| `2` | zagueiro | centre back, zagueiro |
| `3` | meio-campo | defensive/central/attacking midfield, volante, meia |
| `4` | atacante | striker, centre forward, left/right winger, ponta, atacante |

- **Função principal:** a posição específica principal tem prioridade. Um lateral que também atua como ponta continua lateral.
- **Pontas:** são contados como atacantes (`4`). O relatório conta esses casos em `sourcedWingersAsAttackers`.
- **Rótulos genéricos:** quando a posição principal é genérica (`defender`, `midfielder`, `forward`, `attacker`), o código vem das posições secundárias. Sem detalhe suficiente, o atleta é excluído com `generic-position-unresolved`, a menos que já exista no jogo com posição conhecida.

### Lado do campo (`i`)

O campo `i` do jogador é o **lado do campo** (`1` esquerdo, `0` direito), não o pé preferido. Ele só é preenchido quando a posição da fonte é explicitamente lateralizada ("Left Back", "Right Winger", "esquerdo", "direito"). O pé preferido não existe como campo separado no formato do jogo e nunca é deduzido.

### Nomes

Nomes com mais de duas palavras são exibidos com as duas primeiras (`display_player_name` no Python e `shortenNames` no Java, aplicado às listas principal e secundária). O nome completo da fonte fica no relatório (`fullNameProvenance`).

### Completude e preservação

| Situação do clube | Resultado |
|---|---|
| fonte com 16+ jogadores elegíveis e 2+ goleiros | elenco substituído (`source-replacement`) |
| fonte incompleta | elenco anterior preservado (`preserve-previous-roster`); jogadores já existentes podem receber correção de posição, lado, idade e nacionalidade (`partialSourceCorrections`) |
| sem fonte | elenco anterior preservado (`unsourcedSquadsPreserved`) |
| resultado fora de 16–40 jogadores | elenco anterior preservado (`preserve-previous-roster-invalid-source-size`) |

O "elenco anterior" vem de `--fallback-game` (a última base publicada). Sem esse argumento, vem do jogo-base.

O jogo aceita até 40 jogadores. Na substituição, os atletas são ordenados com goleiros primeiro e depois por número de camisa. Quem excede o limite é registrado em `excluded` com `game-roster-limit-40`.

### Atributos

O snapshot não traz características individuais. Para cada atleta, o compilador procura, nesta ordem:

1. o mesmo jogador na última base publicada, no mesmo clube (nome completo ou abreviado);
2. o mesmo jogador no jogo original, no mesmo clube;
3. um único jogador com o mesmo nome em outro clube do jogo original, com a mesma nacionalidade e idade compatível (2 a 6 anos mais velho que o registro original).

Se encontrar, os atributos do jogo são preservados (`attributesPreserved`). Se não, usa padrões explícitos de representação, que não são avaliação do atleta:

- características por posição (`DERIVED_TRAITS`);
- idade 25 se não houver data de nascimento;
- nacionalidade do clube;
- lado direito;
- sem estrela.

Cada padrão aplicado é contado em `defaults` no relatório.

Outras regras:

- **Idade:** calculada pela data de nascimento na data de referência (`--reference-date`, padrão hoje em São Paulo).
- **Identificador:** o identificador interno (`tid`) é derivado do SHA-256 de arquivo + ID da fonte, sem colidir com jogadores originais.
- **Registros inválidos:** registros herdados com `f` ou `i` fora de `0/1`, ou com características incompatíveis com a função (goleiro com características de linha e vice-versa), recebem os padrões da posição e são contados no relatório.
- **Ordem estável:** se o elenco final tem os mesmos fatos da base anterior, a ordem anterior é mantida. Mudanças só de ordem ou de numeração da fonte não geram arquivo diferente.

### Estrela e Top Mundial

`config/player-status-<ano>.json` lista atletas por `teamFile` e `playerName`, com `star`, `topWorld`, motivo e fonte. Quando o arquivo do ano de referência existe:

- as marcações `b` (estrela) e `j` (Top Mundial) são aplicadas **nos dois sentidos**: quem está na lista recebe a marcação; quem não está perde a marcação herdada;
- cada alvo precisa casar exatamente uma vez, senão a compilação é interrompida;
- todas as mudanças vão para `playerStatusAudit` no relatório.

### Clubes B/C sem fonte no snapshot

Para clubes das Séries B e C ausentes do snapshot e do suplemento, o compilador usa as planilhas pesquisadas em `tools/team-roster-editor/sources/<clube>-2026-*.tsv` (uma por clube; colunas nome, posição, idade, país). Esses elencos levam `provenance: previous-researched-tsv` e passam pelas mesmas regras de tamanho e preservação.

---

## 3. Compilação dos `.ban`

```bash
python tools/compile_live_rosters.py \
  --base-game <jogo-base> \
  --original-game <jogo-original> \
  --fallback-game <última-base-publicada> \
  --output data/private/compiled-<versão> \
  --snapshot config/rosters-<versão>.json \
  --supplement config/live-rosters-supplement.json \
  --version <versão>
```

Etapas internas:

1. Compila `src/e/g.java`, `src/e/t.java` e `src/app/Main.java` em `<saída>/classes`.
2. Exporta os `teams/` das três bases para JSON (`export-directory`).
3. Aplica a política acima e grava uma TSV por clube em `<saída>/roster-tsv/`.
4. Executa `batch-rosters`, que carrega cada `.ban` do jogo-base, troca só a lista principal de jogadores, abrevia os nomes e grava em `<saída>/teams/`. Todos os demais campos da equipe vêm do jogo-base.
5. Grava `<saída>/report.json`.

O relatório contém `version`, `referenceDate`, `snapshotSha256`, `counts`, `clubs[]` (política aplicada, jogadores, excluídos, padrões e `finalPlayers`), `fullNameProvenance`, `playerStatusAudit` e `limitations`.

Contadores principais de `counts`:

| Contador | Significado |
|---|---|
| `teamsTotal`, `playersTotal` | equipes e jogadores no jogo resultante |
| `sourceSquads` (`brazilSourceSquads`, `internationalSourceSquads`) | elencos substituídos pela fonte |
| `partialSquadsPreserved`, `unsourcedSquadsPreserved` | elencos preservados |
| `attributesPreserved`, `sourcePlayersCompiled` | atletas com atributos do jogo e atletas compilados da fonte |
| `sourcedFlanks`, `sourcedFullbacks`, `sourcedWingersAsAttackers` | lado e posições vindos da fonte |
| `primaryNamesShortened`, `secondaryNamesShortened` | nomes abreviados |
| `default_*` | padrões aplicados, por tipo |

---

## 4. Divisões e competições

### Séries A, B e C

A divisão de cada clube brasileiro é um atributo da própria equipe no `.ban`, um nível numérico. O plano de transição de 2026 em `tools/year-division-lab/changes.tsv` classifica `>= 16` como A, `12–15` como B e `10–11` como C.

Esses campos vêm do **jogo-base** (`--base-game`). Quando `config/club-identity-<ano>.json` contém fatos aceitos, `compile_live_rosters.py` também aplica nome exibido, estádio, técnico, cores e nível de divisão no mesmo passe de `batch-rosters`; campos ausentes preservam a base. Cada valor exige URL, data e nível da fonte.

Arquivos de referência versionados:

| Arquivo | Conteúdo |
|---|---|
| `data/competitions/2026-brazil.json` | os 156 participantes de 2026 (A 20, B 20, C 20, D 96), com ID estável `br-<nome>-<UF>`, estado e fonte oficial |
| `data/competitions/2026-abc-original-file-map.json` | os 60 clubes A/B/C ligados ao arquivo `.ban` original e ao SHA-256; `serieDPolicy: unchanged` |
| `site/data/target-abc-2026.json` | alvo público dos 60 clubes e situação do elenco |

O ID estável inclui o estado para separar clubes homônimos.

### Série D

A Série D usa a configuração original do jogo. `conf_ligas_nacionais/BRA.cfg` é distribuído a partir da base (`--base` de `build_release_bundle.py`). O alvo público registra a configuração original esperada (`nTimes` 64, `nGrupos` 8). O catálogo de 96 participantes oficiais é informativo e não significa uma Série D com 96 clubes no jogo. O codec de competições (`tools/competition-codec/`) lê e reserializa essas configurações apenas em cópias.

### Copa do Mundo e copas continentais

Esses torneios vivem no executável, não nos `.ban`:

- **Copa do Mundo:** `tools/patch_world_cup_2026.py` usa os grupos embutidos nos moldes Java de `tools/world-cup-2026-src/`. `config/world-cup-2026.json` documenta grupos e fontes.
- **Copas continentais:** `tools/patch_continental_cups_2026.py` gera o código a partir de `config/continental-cups-2026.json`: participantes iniciais, fontes e limitações. Clubes ausentes do catálogo do jogo e vagas restantes seguem a lógica original.
- **Site:** `site/data/explorer-cups.json` resume seleções e copas para o explorador e aponta essas duas configurações como fonte.

---

## 5. Exportação para o site

Os dados públicos são gerados a partir do resultado realmente compilado, nunca de planilhas históricas.

### `tools/export_release_rosters.py`

```bash
python tools/export_release_rosters.py --report data/private/compiled-<versão>/report.json
```

| Saída | Conteúdo |
|---|---|
| `site/data/published-rosters-2026.json` | os 60 clubes A/B/C: divisão, arquivo, fonte, data, política, nomes e posições finais |
| `site/data/roster-coverage.json` | `counts`, `limitations` e clubes com fonte; `testsExecuted: false` |
| `config/roster-build-<versão>.json` | cópia da cobertura, versionada por release |
| `site/data/target-abc-2026.json` | versão publicada e situação `included-current-snapshot` |
| `site/data/release-clubs-60.json` | versão da release e totais dos 60 clubes |

### `tools/export_patch_clubs.py`

```bash
python tools/export_patch_clubs.py --report data/private/compiled-<versão>/report.json
```

Gera `site/data/patch-clubs.json` com **todos** os clubes do jogo resultante, inclusive os inalterados:

- `coverage`: `updated` (elenco substituído), `partial` (fonte parcial) ou `preserved`;
- país (`config/brasfoot-country-names.json`), competição, divisão e estado;
- jogadores com posição, lado (`Esquerdo`/`Direito`) e características.

Verificações de consistência:

- versões iguais em relatório, `config/edition.json` e `windows-installer/bundled_release/manifest.json`;
- cada `.ban` compilado com o SHA-256 registrado no manifesto do pacote;
- totais iguais aos `teamsTotal` e `playersTotal` do relatório.

Por isso, execute-o depois de colocar o bundle da versão em `windows-installer/bundled_release/`.

O formato e o uso desses arquivos no site estão em [Site](site.md).

---

## 6. Do compilado ao bundle

`tools/build_release_bundle.py` recebe `<saída>/teams` em `--teams`, o executável final em `--executable`, a base em `--base` (fonte de `BRA.cfg`), o jogo original e as bases publicadas anteriores:

```bash
python tools/build_release_bundle.py \
  --original <jogo-original> \
  --base <jogo-base> \
  --teams data/private/compiled-<versão>/teams \
  --executable <bf22-23.exe-final> \
  --previous <base-publicada-anterior> \
  --inherit-bundle <bundle-anterior> \
  --output data/private/release-bundle-<versão> \
  --version <versão>
```

Para cada arquivo (`bf22-23.exe`, `conf_ligas_nacionais/BRA.cfg` e cada `teams/*.ban`), o bundle guarda receitas de delta a partir de cada origem reconhecida e uma entrada no manifesto com tamanho, SHA-256 do alvo e `acceptedOriginalSha256`. Arquivos idênticos em todas as origens herdam a receita do bundle anterior.

A partir daí, o fluxo de [Release](release.md) compila os instaladores e publica.

---

## 7. Catálogo mundial diário

`tools/daily_update.py` mantém um catálogo de países, competições, temporadas, clubes e partidas para consulta. Ele não representa ligas jogáveis.

- **Fontes:** feeds CC0 do OpenFootball listados em `config/sources.json`, mais registros locais de `site/data/competitions/2026-brazil.json` (participantes brasileiros) e `site/data/researched-rosters-2026.json` (observações de elencos B/C, sem identidade global de pessoa).
- **Transporte:** apenas `raw.githubusercontent.com`; até 25 fontes, 2 MB por resposta, duas tentativas, `ETag`/`Last-Modified`. HTTP 429 grava `retryAt` para a próxima execução.
- **Falhas:** um feed inválido ou indisponível não substitui o cache anterior. O resumo fica `partial`.
- **Estado local:** `data/private/daily/` (`cache/`, `snapshot.json`, `catalog.sqlite`, `journal.jsonl`, `daily.lock`).
- **Resumo público:** `site/data/world-status.json`, com `status` (`changed`, `unchanged` ou `partial`), hash do conteúdo, cobertura e situação de cada fonte. Em execuções locais agendadas, use `--report-output data/private/daily/world-status.json` para não alterar o checkout.

`tools/daily_maintenance.py` executa esse fluxo uma vez por dia após `schedule.hour` (fuso `schedule.timezone`). Após falha, tenta de novo em 30 minutos; com fontes falhando, em 1 hora.

---

## 8. Fluxos legados

- **API-Football:** `api_football_sync.py`, `collect_abc_rosters.py` e `quota_guard.py` coletavam elencos pela API-Football com chave e orçamento de requisições. A integração está desativada por padrão e não faz parte do ciclo atual.
- **Laboratório B/C:** `export_researched_rosters.py`, `build_bc_lab_deltas.py`, `prepare_2026_roster_candidate.py` e `build_public_rosters_2026.py` montavam elencos B/C a partir das planilhas TSV. Hoje as TSV só complementam o compilador de produção para clubes sem fonte.
- **Prévia de `.ban`:** `build_preview.py` e `install_preview.py` geravam e instalavam prévias experimentais a partir de snapshots da API-Football.
