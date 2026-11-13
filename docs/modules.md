# Referência de módulos

Este documento descreve cada módulo do repositório: para que serve, como é chamado, o que lê, o que escreve e quais restrições impõe. As interfaces de linha de comando foram conferidas nas definições `argparse`/`flag` do código. Antes de executar qualquer comando, confirme com `--help`: o código prevalece sobre este texto.

Documentos relacionados:

- [Arquitetura](architecture.md): visão geral dos componentes.
- [Pipeline de dados](data-pipeline.md): coleta, compilação e exportação de elencos.
- [Instalador](installer.md): hub do Windows, atualizadores portáteis, backups e restauração.
- [Campo animado](live-match.md): a tela de partida com o campo 2D.
- [Release](release.md) e [Manutenção diária](scheduled-maintenance.md): build, publicação e ciclo recorrente.
- [Site](site.md): estrutura de `site/` e publicação no GitHub Pages.

## Convenções

- **Legado** indica código mantido no repositório para proveniência ou laboratório, fora do fluxo de produção atual. Não use um módulo legado como ponto de partida sem conferir se ele foi substituído.
- Os scripts Python de `tools/` importam uns aos outros como pacote. Execute-os a partir da raiz do repositório, com `python -m tools.<módulo>` ou `python tools/<módulo>.py`.
- Nenhum módulo deve escrever na instalação do jogo. As ferramentas que recebem a pasta do jogo exigem saída nova e separada.
- `data/`, `dist/` e `output/` são ignorados pelo Git (exceto alguns arquivos de `data/competitions/` e `data/assets/`). Bases privadas, bundles e executáveis gerados existem apenas no disco local.
- Os manifestos gerados registram `tests=not-run-at-owner-request` e `compatibilityTestedInGame=false`. Compilação, hashes e inspeção de bytecode não são testes funcionais.

## Visão do fluxo de produção

```text
fontes públicas ─ collect_live_rosters ─▶ config/rosters-<versão>.json
                                              │ + config/live-rosters-supplement.json
                                              │ + config/player-status-<ano>.json
bases privadas ─ compile_live_rosters (src/app/Main.java) ─▶ <saída>/teams/*.ban + report.json
                                              │
executável transformado (patch_* / patch_live_match_view) ─┐
                                              ▼             │
               build_release_bundle ─▶ bundle (manifest.json + patches/) ◀┘
                                              │ build_component_bundle (componentes opcionais)
               build_distribution (Go) ─▶ dist/<versão>/ (5 pacotes + distribution.json + SHA256SUMS.txt)
                                              │
               publish_distribution (gh) ─▶ GitHub Release + site/data/{distribution,release}.json
               export_release_rosters / export_patch_clubs ─▶ site/data/*.json
               publish_pages ─▶ branch gh-pages
```

Em paralelo, e sem alterar o jogo, `tools/daily_update.py` mantém um catálogo mundial em SQLite e publica um resumo em `site/data/world-status.json`.

---

## 1. Coleta e compilação de dados (`tools/`)

Detalhes de política e formato estão em [Pipeline de dados](data-pipeline.md).

### `tools/collect_live_rosters.py`

Coleta elencos públicos do serviço de elencos do 365Scores, com cache e registro de proveniência.

| Opção | Padrão | Uso |
|---|---|---|
| `--original-catalog PATH` | obrigatório | diretório com os `*.ban.json` exportados por `app.Main export-directory` |
| `--output PATH` | `config/rosters-2026.4.1.json` | snapshot de saída; passe sempre o arquivo da versão nova |
| `--cache PATH` | `data/private/live-roster-cache` | cache de respostas por URL |
| `--mappings PATH` | `config/live-roster-team-map.json` | mapa fixo ID da fonte → arquivo `.ban` |
| `--cache-max-age-hours N` | `18` | validade do cache |
| `--refresh` | desligado | força nova requisição, mantendo o cache como recuperação |

- **Saída:** JSON com `provider`, `collectedAt`, `clubs`, `failures`, `catalogCoverage` e listas de clubes sem correspondência.
- **Restrições:** sem credenciais nem API-Football; resposta limitada a 12 MB; uma falha de rede reaproveita o cache marcado como `stale`, sem novas tentativas nem contorno de limites.

### `tools/compile_live_rosters.py`

Gera os arquivos de equipe `.ban` a partir do snapshot, fora do jogo.

| Opção | Padrão | Uso |
|---|---|---|
| `--base-game PATH` | obrigatório | jogo-base cujos `teams/` são reescritos |
| `--original-game PATH` | obrigatório | jogo original, usado para reconhecer atletas e atributos |
| `--fallback-game PATH` | — | última base publicada; fornece o elenco preservado |
| `--output PATH` | obrigatório | diretório novo, separado das bases |
| `--snapshot PATH` | `config/rosters-<versão>.json` | snapshot coletado |
| `--supplement PATH` | repetível | suplementos (ex.: `config/live-rosters-supplement.json`) |
| `--java`, `--javac` | `java`, `javac` | JDK usado para compilar `src/` |
| `--reference-date AAAA-MM-DD` | hoje em São Paulo | data de cálculo das idades |
| `--version` | `config/edition.json` | versão gravada no relatório |
| `--club-identities PATH` | `config/club-identity-<ano>.json` | fatos aceitos de nome, estádio, técnico, cores e nível de divisão |

- **Saída:** `<output>/teams/*.ban` e `<output>/report.json`, com contagens, provenance por jogador, auditoria de estrela/Top Mundial e limitações. Também ficam no diretório as pastas intermediárias `classes/`, `base-json/`, `original-json/`, `prior-json/` e `roster-tsv/`.
- **Dependências:** `src/app/Main.java` (subcomandos `export-directory` e `batch-rosters`), `tools/roster_position_map.py`, `tools/audit_official_roster_tsv.py` e `config/club-identity-<ano>.json`.
- **Restrições:** aborta se um alvo de `config/player-status-<ano>.json` não casar exatamente uma vez; recusa saída dentro das bases.

### `tools/roster_position_map.py`

Biblioteca sem CLI. Converte rótulos de posição da fonte em códigos do jogo (`0` goleiro, `1` lateral, `2` zagueiro, `3` meio-campo, `4` atacante), extrai o lado do campo de posições explícitas (`position_flank`) e aplica a regra de exibição de nomes em duas palavras (`display_player_name`). Rótulos ambíguos levantam erro em vez de serem adivinhados.

### `tools/export_release_rosters.py`

Exporta as listas compiladas para o site.

```bash
python tools/export_release_rosters.py --report <saída-da-compilação>/report.json
```

Escreve `site/data/published-rosters-2026.json`, `site/data/roster-coverage.json`, `config/roster-build-<versão>.json` e atualiza `site/data/target-abc-2026.json` e `site/data/release-clubs-60.json`. Lê `data/competitions/2026-abc-original-file-map.json`.

### `tools/export_patch_clubs.py`

Gera o explorador público de clubes (`site/data/patch-clubs.json`) com todos os clubes do jogo resultante.

| Opção | Padrão |
|---|---|
| `--report PATH` | obrigatório (o `report.json` da compilação, com `teams/` ao lado) |
| `--output PATH` | `site/data/patch-clubs.json` |

Exige que a versão do relatório, de `config/edition.json` e de `windows-installer/bundled_release/manifest.json` sejam iguais, e que cada `.ban` compilado tenha o SHA-256 registrado no manifesto do pacote. Lê `config/rosters-<versão>.json`, `config/live-rosters-supplement.json` e `config/brasfoot-country-names.json`.

### Catálogo mundial diário

| Módulo | CLI | Função |
|---|---|---|
| `tools/daily_update.py` | `--config` (`config/sources.json`), `--state-dir` (`data/private/daily`), `--offline`, `--report-output` | coleta os feeds configurados, gera snapshot incremental, materializa SQLite e escreve o resumo (padrão `site/data/world-status.json`) |
| `tools/daily_maintenance.py` | sem CLI | executa `daily_update` uma vez por dia a partir de `schedule.hour` de `config/sources.json`, com lock, retry e saída privada em `data/private/daily/world-status.json` |
| `tools/fetch_sources.py` | biblioteca | transporte HTTPS limitado a `raw.githubusercontent.com`, 2 MB por resposta, `ETag`/`Last-Modified` e escrita atômica |
| `tools/daily_sources.py` | biblioteca | ingestão offline de fontes já em cache, sem rede |
| `tools/world_snapshot.py` | biblioteca | snapshots determinísticos, hash de conteúdo e diff |
| `tools/world_catalog.py` | biblioteca | catálogo SQLite (países, associações, competições, temporadas, clubes, partidas) |
| `tools/history_records.py` | biblioteca | registros que separam histórico real, estado atual e simulação |

```bash
python -m tools.daily_update --report-output data/private/daily/world-status.json
```

O catálogo mundial não altera `.ban`, executável ou manifesto de release.

### Elencos B/C de laboratório (legado)

Ferramentas da fase em que as Séries B e C eram montadas a partir de planilhas TSV pesquisadas. Os dados públicos atuais vêm de `collect_live_rosters` e `compile_live_rosters`.

| Módulo | CLI | Função |
|---|---|---|
| `tools/export_researched_rosters.py` | `--check` | gera `site/data/researched-rosters-2026.json` a partir de `tools/team-roster-editor/sources/*.tsv` |
| `tools/audit_official_roster_tsv.py` | `--research`, `--sources` | audita as TSV contra a pesquisa B/C; o compilador importa daqui o mapa `IDENTITIES` |
| `tools/audit_roster_readiness.py` | `--catalog`, `--researched`, `--output` | relatório de prontidão, sem tratar pesquisa como instalada |
| `tools/prepare_bc_2026_source_snapshot.py` | `--target`, `--research`, `--mapping`, `--sources`, `--output`, `--report` | snapshot offline B/C para reconciliação |
| `tools/build_public_rosters_2026.py` | `--ready`, `--manifest`, `--target`, `--output` | converte evidência privada em `published-rosters-2026.json` (substituído por `export_release_rosters`) |
| `tools/build_bc_lab_deltas.py` | `--game-teams`, `--output`, `--club-id`, `--lab-estimates` (obrigatória) | deltas B/C de laboratório |
| `tools/build_v4_roster_deltas.py` | `--original-teams`, `--v4-teams`, `--output` | deltas de laboratório sobre a base V4 |
| `tools/prepare_2026_roster_candidate.py` | `--game-teams`, `--bc-lab`, `--output` | candidato não publicável com 59 clubes |

### Catálogo mundial e Super Update (`tools/world/`)

`python -m tools.world collect --source <fonte>` coleta com cache em `data/private/super-update/cache/` e grava o bruto em `data/private/super-update/raw/`; `build` monta o catálogo em `data/private/super-update/catalog/` e `report` gera `coverage.html`. Fontes: `wikidata`, `fifa`, `uefa`, `365scores` (competições e classificações), `wikipedia` (infobox de ligas e clubes), `365squads` e `wikisquads` (elencos), `365search` (ID do 365Scores por nome), `365lineups` (escalações recentes e seleções), `crests` (escudos dos clubes novos) e `venues` (estádios).

| Arquivo | Uso | Saída |
|---|---|---|
| `tools/world/compile_game.py` | `--base`, `--output`, `--jdk` (obrigatórios), `--countries`, `--date` | `.ban`, `.cfg`, escudos e camisas da América do Sul e `report.json` |
| `tools/world/site_export.py` | `--report` (obrigatório); `--build` com `--java`, ou `--world-snapshot`; `--output`, `--coverage` | `site/data/patch-clubs.json` e `site/data/roster-coverage.json` com os clubes do Super Update; com `--build` e `--world-snapshot`, grava também o retrato |
| `tools/world/world_snapshot.py` | `--game-countries` (obrigatório), `--published-clubs`, `--published-coverage`, `--manifest`, `--core-rosters`, `--file-map`, `--output` | `config/super-update-world-2026.json` reconstruído da tabela e da cobertura publicadas, conferido contra os totais publicados |
| `tools/world/build_preview_bundle.py` | `--inherit`, `--compiled`, `--original`, `--base`, `--output`, `--version`, `--release` | pacote sobre o publicado, com receitas a partir do original, da base publicada e das versões anteriores |
| `src/app/WorldBuild.java` | `<teams-base> <plan.tsv> <rosters> <saída>` | `.ban` com as classes réplica |
| `tools/competition-codec/src/app/WorldLeagues.java` | `<modelo.cfg> <plan.tsv> <saída>` ou `dump <arquivo.cfg>` | `.cfg` por país |

---

## 2. Bundle e receitas de delta (`tools/`)

O projeto distribui somente receitas de delta reconhecidas por SHA-256: operações `copy` (intervalo do arquivo original) e `add` (bytes em Base64). O instalador recusa qualquer arquivo cuja origem não esteja na lista aceita.

### `tools/build_release_bundle.py`

Produz o bundle de release a partir de cópias privadas e licenciadas.

| Opção | Uso |
|---|---|
| `--original PATH` | jogo original (obrigatório) |
| `--base PATH` | base que fornece `conf_ligas_nacionais/BRA.cfg` (obrigatório) |
| `--teams PATH` | diretório com os `.ban` compilados (obrigatório) |
| `--executable PATH` | `bf22-23.exe` final, já transformado (obrigatório) |
| `--output PATH` | diretório novo do bundle (obrigatório) |
| `--previous PATH` | base publicada reconhecida; obrigatório e repetível |
| `--inherit-bundle PATH` | bundle anterior cujas variantes continuam aceitas por encadeamento |
| `--version` | padrão `config/edition.json` |

- **Saída:** `manifest.json` (`schemaVersion=4`, `kind=BRASFOOT_RELEASE_PATCH`, `channel=stable`) e `patches/<arquivo>.json`, com uma variante por origem reconhecida.
- **Restrições:**
  - recusa a receita do executável se os bytes literais passarem de 30% do alvo;
  - variantes legadas do bundle herdado são encadeadas (`schemaVersion: 3`, campo `steps`) até o novo alvo; cadeias com mais de 8 passos têm passos consecutivos compostos por `tools/recipe_chain.py`;
  - variantes cuja origem já é o próprio alvo são descartadas.

### `tools/build_component_bundle.py`

Acrescenta componentes selecionáveis (patch de dados, campo animado ou ambos) a um bundle existente.

| Opção | Uso |
|---|---|
| `--inherit-bundle` | bundle de partida (copiado para `--output`) |
| `--original-executable` | executável original do jogo |
| `--patch-executable` | executável só com o patch de dados |
| `--full-executable` | executável com patch e campo animado |
| `--live-executable` | executável original com apenas o campo animado |
| `--patch-recipe` | receita existente que já tem como alvo o executável de patch |
| `--previous-live-executable` | repetível; outros executáveis com campo animado a reconhecer |
| `--output`, `--version` | destino novo e versão opcional |
| `--release` | marca o bundle como publicável (`channel=stable`); sem ela, `local-preview` |

Grava `patches/bf22-23.exe.patch.json`, `patches/bf22-23.exe.live.json` e a seção `components` do manifesto, lida por `windows-installer/components.go`.

### `tools/build_live_match_preview_bundle.py`

Gera bundles de prévia do campo animado: herda um bundle, acrescenta a ponte do executável publicado para o executável de prévia e encadeia as variantes antigas (até 8 etapas, compondo passos consecutivos com `tools/recipe_chain.py` quando necessário).

| Opção | Padrão |
|---|---|
| `--inherit-bundle`, `--published-executable`, `--preview-executable`, `--output` | obrigatórias |
| `--previous-preview-executable` | repetível |
| `--version` | `2026.4.41` |
| `--release` | sem ela, `kind=BRASFOOT_HOMOLOGATION_PATCH`, `publicationAllowed=false`, `channel=local-preview` |

### Geradores de delta auxiliares

| Módulo | CLI | Situação |
|---|---|---|
| `tools/build_inplace_bundle.py` | `--original`, `--patched`, `--checkout`, `--version` (`2026.3.0`) | fornece `match_ops`, o gerador de operações usado pelos demais; a CLI é legado |
| `tools/build_team_delta.py` | `--original`, `--candidate`, `--original-sha256`, `--filename`, `--output` | delta de um `.ban` isolado (laboratório) |
| `tools/build_bra_delta.py` | `--original`, `--candidate`, `--original-sha256`, `--output` | delta experimental de `BRA.cfg` |
| `tools/build_abc_team_map.py` | `--target`, `--private-audit`, `--output` | reconciliação dos 60 arquivos A/B/C |
| `tools/baselines/2026.0.2/` | — | bundle histórico da primeira release (legado) |

---

## 3. Transformações do executável (`tools/`)

Cada transformador trabalha numa cópia, confere o SHA-256 do executável de origem e das classes que altera, e grava um executável novo. Eles não podem ser encadeados às cegas: quando a base muda, o transformador precisa ser adaptado. Todos exigem JDK.

| Módulo | CLI | Base exigida | O que faz |
|---|---|---|---|
| `tools/patch_world_cup_2026.py` | `--source-exe`, `--output-exe` (obrigatórias), `--java`, `--javac` | `SOURCE_SHA` fixo no código | reconstrói `f/q`, `a/hU`, `a/ia` e `best/f` com os grupos da Copa do Mundo de 2026, a partir dos moldes Java de `tools/world-cup-2026-src/` |
| `tools/patch_continental_cups_2026.py` | igual | `SOURCE_SHA` fixo no código | gera uma classe auxiliar a partir de `config/continental-cups-2026.json` e injeta os participantes iniciais das copas continentais; vagas sem clube no catálogo usam a lógica original |
| `tools/patch_live_match_view.py` | `--source`, `--output` (obrigatórias), `--javac`, `--java` | executável original ou executável público do patch (dois SHA aceitos) e classe `a/dV.class` reconhecida | compila `LiveMatchPanel.java` com `-source 7 -target 7`, transforma a tela de partida com o ASM interno do JDK e acrescenta as classes `mega/*` |
| `tools/patch_official_career_year.py` | `--original-class`, `--output-class` | classe de carreira reconhecida | prova de conceito do seletor de ano 2026 (legado) |
| `tools/build_official_year_candidate.py` | `--original-exe`, `--output-exe`, `--experimental` (obrigatória) | executável oficial reconhecido | candidato experimental separado (legado) |

`patch_live_match_view.py` usa por padrão um `java.exe` de JDK 17 em `C:\Program Files\Microsoft\...`; em outros ambientes, passe `--java`. O funcionamento do painel está em [Campo animado](live-match.md).

### Inspeção somente leitura do jogo

Ferramentas de engenharia reversa que leem o executável ou os `.ban` sem modificar nada.

| Módulo | CLI |
|---|---|
| `tools/inspect_career_years.py` | `--game`, `--output` |
| `tools/inspect_league_model_fields.py` | `--game-exe` |
| `tools/locate_league_original_club_lists.py` | `--game-exe` |
| `tools/trace_career_controls.py` | `--game-exe`, `--class-path` |
| `tools/trace_national_league_routing.py` | `--game-exe` |
| `tools/find_division_ui_candidates.py` | `--game-exe` |
| `tools/year-division-lab/verify_original_division_plan.py` | `--original-teams`; confere o plano de 43 arquivos de `changes.tsv` (rank de divisão por arquivo) |

---

## 4. Distribuição e publicação (`tools/`)

Procedimento completo em [Release](release.md).

### `tools/build_distribution.py`

Compila os instaladores Go a partir de um bundle explícito.

| Opção | Padrão | Uso |
|---|---|---|
| `--bundle` | obrigatório | bundle com `manifest.json` e `patches/` |
| `--output` | obrigatório | diretório de artefatos; recusa sobrescrever um artefato existente |
| `--edition` | `config/edition.json` | identidade da edição e lista de plataformas |
| `--source-commit` | `git rev-parse HEAD` | SHA completo de 40 caracteres |
| `--snapshot` | — | snapshot do catálogo anexado como `...-catalog.json.gz` |
| `--target` | todas de `platforms` | repetível, ex.: `windows/amd64` |
| `--go` | `go` | compilador Go |
| `--sign-thumbprint`, `--signtool`, `--timestamp-url` | variáveis `MEGA_PATCH_SIGN_THUMBPRINT`/`MEGA_PATCH_SIGNTOOL` | assinatura Authenticode opcional |

- **Saída:** `Brasfoot-Mega-Patch-<versão>-<plataforma>-<arquitetura>.exe` (Windows) ou `.tar.gz` (Linux/macOS, com `LEIA-ME.txt`, `build-info.json` e lançador `abrir.sh`/`Abrir.command`), `distribution.json` e `SHA256SUMS.txt`.
- **Restrições:** exige `PATCH_YEAR` inteiro e versão `ANO.N.N`; compila com `CGO_ENABLED=0`, `-trimpath` e, no Windows, `-H=windowsgui` e recursos gerados por `go-winres`.

### `tools/publish_distribution.py`

Publica a release no GitHub com o `gh` autenticado, de forma idempotente.

```bash
python tools/publish_distribution.py --directory dist/<versão> --notes <notas>.md
```

1. Confere tamanho e SHA-256 de cada artefato contra `distribution.json`.
2. Cria os aliases sem versão (`Brasfoot-Mega-Patch-windows-x64.exe` etc.).
3. Exige que o commit de origem exista no GitHub.
4. Cria a tag e a release em rascunho e envia os arquivos, recusando substituir um asset divergente.
5. Marca a release como final e `latest`.
6. Só então escreve `site/data/distribution.json` e `site/data/release.json`.

Aceita apenas `channel=stable`.

### `tools/publish_pages.py`

Sem CLI. Abre um worktree destacado de `origin/gh-pages`, substitui o conteúdo por `site/` (sem `tests/` e `*.test.js`), faz commit e push se houver diferença e solicita um build do GitHub Pages pela API. Veja [Site](site.md).

### Outros

| Módulo | Situação |
|---|---|
| `tools/publish_site_release.py` | **legado**. Reescrevia o HTML por marcadores `data-release-copy`, que não existem mais nas páginas atuais. CLI: `--version`, `--filename`, `--file-size`, `--sha256`, `--published-at`, `--notes-file` |
| `tools/release_traceability.py` | biblioteca; valida que um manifesto de release aponta para versão, commit e hashes, sem consultar o GitHub |
| `tools/engine_acceptance.py` | `evidence` (posicional); valida metadados de evidência de gameplay e falha se faltar algum item; não executa o jogo |
| `release.ps1` (raiz) | orquestra `daily_update`, `build_distribution` e, com `-Publish`/`-PublishExisting`, `publish_distribution`, commit dos manifestos e `publish_pages`. Parâmetros: `-PackagePath` (padrão `windows-installer/bundled_release`), `-OutputDirectory`, `-Publish`, `-PublishExisting`. Exige `docs/releases/v<versão>.md` |

---

## 5. Recursos visuais (`tools/`)

| Módulo | CLI | Saída |
|---|---|---|
| `tools/render_live_match_preview.py` | `--output` (`site/assets/live`), `--width` (900), `--height` (420), `--scale` (2.0), `--condition` (repetível, 0–3), `--javac`, `--java` | `pitch-<condição>.jpg`, um quadro estático do painel do campo animado por condição de gramado |
| `tools/render_brand_assets.py` | `--icons` (`windows-installer/winres`), `--og` (`site/assets/og-card.jpg`), `--banner` (`docs/assets/banner.jpg`), `--pitch` (`site/assets/live/pitch-0.jpg`), `--clubs` (`site/data/patch-clubs.json`), `--javac`, `--java` | ícones `icon-<tamanho>.png` (16 a 256), cartão social 1200×630 e banner 1600×800 |
| `tools/graphics_pipeline.py` | `--registry` (`config/graphics.json`) | conversão offline e endereçada por conteúdo de imagens autorizadas para um diretório privado |
| `tools/crest_audit.py` | `--out` (obrigatório), `--game` (`data/private/vanilla-22-23`), `--catalog` (`original-json` de uma compilação), `--cache` (`data/private/crest-audit-cache`), `--overrides` (`config/crest-source-map.json`), `--delay` (0,5 s), `--same-threshold` (0,10), `--changed-threshold` (0,13) | auditoria somente leitura: associa cada `.ban` ao Transfermarkt (ID pela propriedade P7223 do Wikidata, escudo pelo CDN) e ao 365Scores (IDs dos elencos ou busca), baixa os escudos e grava `audit.json` e `index.html` com o escudo do jogo ao lado das duas fontes |
| `tools/build_crest_bundle.py` | `approve --audit` (`--status`, padrão `provavelmente desatualizado`; `--out` `config/crest-updates-2026.json`) e `bundle --inherit-bundle --output` (`--approved`, `--original-game`, `--version`, `--preview`, `--allow-changed-source`) | lista aprovada de escudos (fonte, ID, URL e SHA-256 da imagem; `excluded` com motivo é preservado) e cópia do pacote herdado com o componente `crests`: PNG 60×60 em `teams/escudos/` e 18×18 em `teams/escudosMini/`, uma receita `crest-<hash>.json` por arquivo sobre o PNG original, `crests.json` com a procedência e PNGs para conferência em `<saída>-png/` |

`crest_audit` não acessa páginas do Transfermarkt (a busca exige desafio anti-robô) nem a API do Sofascore (responde 403). A classificação (`igual ao jogo`, `provavelmente desatualizado`, `desatualizado (uma fonte)`, `conferir`, `fontes divergem`, `revisar associação`, `sem fonte`) compara as imagens com desfoque, em 10×10, somando a diferença de proporção; só indica o que conferir. `config/crest-source-map.json` (opcional, `{"clubs": {"teams/<arquivo>.ban": {"transfermarkt": id|null, "365scores": id|null}}}`) fixa ou remove a associação de um clube.

O cartão social usa o quadro `pitch-0.jpg` como fundo e os totais de `patch-clubs.json`. Gere os quadros do campo antes de gerar a marca.

### `tools/live-match-render/`

`mega/RenderFrame.java` instancia `LiveMatchPanel` em modo headless, posiciona jogadores, bola e árbitro numa cena fixa e grava um JPEG. Argumentos posicionais: `<saída> <largura> <altura> <escala> <condição>`. É chamado por `render_live_match_preview.py`; não precisa do jogo.

### `tools/brand-assets/`

`BrandAssets.java` desenha a marca. Modos: `icon <tamanho> <saída.png>` e `card <largura> <altura> <campo.jpg> <saída.jpg> <clubes> <total> <atualizados>`. É chamado por `render_brand_assets.py`.

---

## 6. Fontes Java auxiliares (`tools/`)

### `tools/live-match-view-src/`

| Arquivo | Função |
|---|---|
| `LiveMatchPanel.java` | painel Swing do campo animado (pacote `mega`), compilado para Java 7. Expõe `install(JPanel)`, `engineStep(...)` e `beforePenaltyKick(...)` |
| `LiveMatchTransformer.java` | transformador ASM: injeta `install` ao fim do construtor de `a.dV`, troca a chamada `best/I.q(II)V` de `a.dV.aa(Z)V` por `engineStep` e insere `beforePenaltyKick` em `a.dV.b(components/v, best/A)` |

### `tools/world-cup-2026-src/` e `tools/continental-cups-2026-src/`

Moldes Java e transformadores usados por `patch_world_cup_2026.py` e `patch_continental_cups_2026.py`. Os moldes de `a/`, `best/` e `f/` reproduzem apenas os métodos transplantados.

### `tools/competition-codec/`

Codec das configurações de competição (`conf_ligas_nacionais/*.cfg`, `conf_estadual/*.ces`), com as classes `est.ArrayLigaType`, `est.ConfigLigaType`, `est.ArrayLigaEType` e `est.ConfigEstadualType`. Modos de `app.CompetitionCodec`: `inspect`, `roundtrip` e `trial-serie-d-96` (simulação isolada). A saída sempre fica fora da instalação. Instruções em `tools/competition-codec/README.md`.

### `tools/team-roster-editor/`

Editor de elencos de laboratório para um único `.ban`.

- **Classes:** `UpdateTeamRoster`, `AdoptTeamRoster`, `InspectTeamRoster`, `OriginalBrazilDivisionProbe` e autotestes.
- **`sources/`:** contém as planilhas TSV pesquisadas dos clubes das Séries B e C (`nome<TAB>posição<TAB>idade<TAB>país`, com a URL de origem em comentário).
- **Uso atual:** o compilador de produção ainda lê essas TSV para clubes B/C sem fonte no snapshot (`curated_clubs`).

Instruções em `tools/team-roster-editor/README.md`.

---

## 7. Instalador Go (`windows-installer/`)

Módulo Go (`go 1.23`, dependência `github.com/jchv/go-webview2`). O mesmo código gera o hub do Windows e os atualizadores portáteis de Linux e macOS. Comportamento detalhado em [Instalador](installer.md).

| Arquivo | Função |
|---|---|
| `engine.go` | estruturas `Manifest`/`ManifestFile`, validação da pasta do jogo (`options.bcf`, `teams/`), `inspect` (plano de instalação), `install` com backup em `%LOCALAPPDATA%\BrassfootPatch2026\backups`, substituição verificada e rollback |
| `bundle.go` | mantém em memória o pacote da versão carregado pelo `feed.go` (`bundled_release/manifest.json` e `bundled_release/patches/*.json`); aplica receitas `schemaVersion` 1 (operações), 2 (variantes) e 3 (cadeia de 2 a 8 etapas), conferindo tamanho e SHA-256 do resultado |
| `components.go` | instalação por componentes `patch`, `live` e `patch+live`: detecta o estado do jogo pelo SHA do executável e monta um manifesto restrito à seleção |
| `snapshots.go` | backups completos da pasta do jogo em ZIP (`...\BrassfootPatch2026\snapshots`, até 4 GiB), listagem, verificação por SHA-256 e restauração; na restauração, só remove arquivos extras dentro de `teams/`, `conf_ligas_nacionais/` e `conf_estadual/` |
| `restore.go` | localiza o backup de instalação compatível e restaura os arquivos anteriores |
| `hub_windows.go` | interface principal: janela WebView2 sem moldura (1040×680) com a página `ui/hub.html` e funções ligadas ao JavaScript (`hubInstall`, `hubCreateBackup`, `hubRestore`, `hubLaunchGame` e outras). Sem WebView2, oferece o download do runtime e cai na interface clássica |
| `main_windows.go` | interface Win32 clássica (`runClassic`), aberta também com o argumento `--classic` |
| `portable.go`, `portable_unix.go` | atualizador portátil (`!windows`) com `--game`, `--yes`, `--restore`, `--inspect`, `--version`, `--only patch\|live`, `--remove`, `--feed` e `--bundle` |
| `portable_windows.go`, `state_dir_hubcli.go` | build de desenvolvimento `hubcli` (fora da distribuição): o mesmo atualizador no Windows e `--state-dir` obrigatório para isolar cofre, backups, cache e temporários (veja [Hub e instalador](installer.md#linha-de-comando-para-regressão)) |
| `diagnostic.go` | tradução de erros em códigos `BF-1xx` com título, causa e ação |
| `edition.go` | `productName`, `productVersion`, `patchYearText` e `sourceCommit`, preenchidos por `-ldflags` em `build_distribution.py` |
| `pix.go`, `pix_windows.go` | contribuição voluntária opcional |
| `replace_windows.go`, `replace_nonwindows.go` | troca atômica de arquivos (`MoveFileExW` no Windows, `os.Rename` nos demais) |
| `ui/` | `hub.html` (interface), `mark.svg` e `pitch.jpg`, embutidos no binário |
| `winres/` | `winres.json` e ícones `icon-*.png` para os recursos do executável Windows |
| `assets/app-icon.svg` | fonte vetorial do ícone |
| `bundled_release/` | bundle da release atual no repositório; `build_distribution.py --bundle windows-installer/bundled_release` o publica como `Brasfoot-Mega-Patch-<versão>-bundle.zip` (não é mais embutido no hub) |
| `feed.go` | lê o `release.json` da release mais recente (ou de `--feed`), baixa e guarda em cache o pacote conferido por SHA-256, compara versões do hub e do patch |
| `hub_setup_windows.go` | instala o hub em `%LOCALAPPDATA%\Programs\Brasfoot Mega Patch`, cria atalhos, registra em Aplicativos, remove (`--uninstall-hub`) e aplica a autoatualização |
| `*_test.go` | testes Go do motor, restauração, preservação e integração |

```bash
./brasfoot-mega-patch --game /caminho/do/Brasfoot --inspect
./brasfoot-mega-patch --game /caminho/do/Brasfoot --only patch
./brasfoot-mega-patch --game /caminho/do/Brasfoot --restore
```

---

## 8. Instalador Python (`installer/`) — legado

Protótipo anterior ao instalador Go: `installer/engine.py` (instalação transacional de bundles de `.ban` certificados por SHA-256) e `installer/gui.py` (interface Tk). `python -m installer` abre a interface. `installer-entry.py` é o ponto de entrada para empacotar com PyInstaller. Não é o atualizador distribuído.

---

## 9. Scripts Python na raiz

Todos são **legado**, mantidos para proveniência e para o histórico de testes. Nenhum faz parte do ciclo de produção atual.

| Script | CLI | Função |
|---|---|---|
| `api_football_sync.py` | `--mapping`, `--output`, `--refresh`, `--no-fallback`, `--offline`, `--dry-run`, `--max-requests` | coletor API-Football da Série A. Exige `API_FOOTBALL_KEY` fora do modo offline. A API fica desativada por padrão |
| `quota_guard.py` | biblioteca | orçamento persistente de requisições da API-Football em SQLite (`API_QUOTA_DB`) |
| `collect_abc_rosters.py` | `--target`, `--cache`, `--output`, `--max-requests` (0), `--offline`, `--allow-network` | identidades B/C a partir do cache da API-Football |
| `catalog.py` | `--archive`, `--out` | JSON exportado do jogo → catálogo SQLite auditado |
| `roster_to_tsv.py` | `--json`, `--out` | elenco JSON → TSV para o comando `replace-roster` de `src/app/Main.java` |
| `build_preview.py` | `--snapshot`, `--game`, `--out`, `--club` | prévia experimental de `.ban` a partir de um snapshot (16 a 40 jogadores) |
| `install_preview.py` | `--preview`, `--game`, `--backup`, `--i-accept-unverified-preview` | instalador transacional de desenvolvimento para essa prévia |
| `transfer_windows.py` | `--calendar` (`config/transfer-windows-2026.json`), `--completed` | verifica janelas de transferência vencidas; não publica |
| `assets_audit.py` | `--game`, `--out` | inventário somente leitura de escudos e uniformes de uma instalação |
| `installer-entry.py` | — | entrada PyInstaller do instalador Python |

---

## 10. Código Java em `src/`

Ferramenta de leitura e escrita de arquivos de equipe `.ban` (serialização Java).

- `src/e/t.java` e `src/e/g.java` reproduzem as classes `e.t` (equipe) e `e.g` (jogador) com `serialVersionUID = 16`. Campos de jogador usados pelo pipeline: `a` nome, `b` estrela, `c` país, `d` idade, `e` posição, `g`/`h` características, `i` lado do campo, `j` Top Mundial.
- `src/app/Main.java` desserializa com filtro de classes permitidas e limites de tamanho.

| Subcomando | Argumentos |
|---|---|
| `inspect` | `<arquivo.ban>` |
| `clone` | `<original.ban> <novo.ban>` |
| `rename-player` | `<original.ban> <nome-antigo> <nome-novo> <novo.ban>` |
| `audit-directory` | `<instalação/teams>` |
| `export-directory` | `<instalação/teams> <diretório-json>` |
| `replace-roster` | `<original.ban> <elenco.tsv> <novo.ban>` |
| `batch-rosters` | `<teams-base> <diretório-tsv> <teams-novo>` |

`batch-rosters` substitui a lista principal de cada equipe que tiver TSV, abrevia os nomes das listas principal e secundária e grava num diretório novo.

O script `brassfoot.ps1` (raiz) compila `src/` em `build/classes` e expõe os comandos `audit`, `export`, `inspect`, `clone`, `rename-player` e `replace-roster` com `-GameRoot`, `-InputFile`, `-OutputPath`, `-OldName`, `-NewName` e `-RosterJson`. `diagnose-install.ps1` (`-GameRoot`, `-OutputPath`) faz um inventário somente leitura da instalação. `sync-api.ps1` envolve o coletor API-Football legado.

---

## 11. Scripts PowerShell (`scripts/`)

| Script | Parâmetros | Função |
|---|---|---|
| `run-daily-data.ps1` | — | executa `python -m tools.daily_maintenance` com log em `data/private/daily/` |
| `install-daily-data.ps1` | — | registra a tarefa agendada `Brasfoot Mega Patch - Daily Data` (a cada 15 min e no logon, usuário atual, sem elevação) |
| `run-continuity.ps1` | `-Config` (obrigatório) | executa `tools/continuity_service.py --config` com log local |
| `install-continuity.ps1` | `-Name`, `-Config` (`config/continuity.local.json`), `-IntervalMinutes` (15) | registra a tarefa `Brasfoot Mega Patch - Continuity` |
| `ciclo-automatico.ps1` | `-DryRun` | ciclo antigo de candidato → build → release → site (**legado**; chama `publish_site_release.py`) |
| `configurar-ciclo-windows.ps1` | `-Horario` (`07:00`), `-Nome` | registra a tarefa diária do ciclo antigo (**legado**) |
| `collect-game-structure.ps1` | `-GamePath`, `-OutputDirectory` | ZIP privado com `.ban` e `.ces` de uma instalação, para análise local |
| `collect-competition-configs.ps1` | `-GamePath`, `-OutputDirectory` | ZIP privado com as configurações de competição |
| `inventory-competitions.ps1` | `-GamePath`, `-OutputDirectory` | inventário das pastas de competição |

Os ZIPs gerados contêm arquivos proprietários do jogo: guarde-os fora do repositório.

### Continuidade local (opcional)

`tools/continuity.py` (`--config`, comando `tick|status|retry|validate-existing`, `--task`) e `tools/continuity_service.py` (`--config`) executam tarefas de manutenção em ondas delimitadas, com estado, orçamento de cota e integração de resultados verificados. A configuração local segue `config/continuity.example.json`. Nunca registre credenciais em logs ou arquivos versionados.

---

## 12. Site (`site/`)

Página estática publicada no GitHub Pages: `index.html`, páginas `como-instalar/`, `compatibilidade/` e `versoes/`, scripts `app.js`, `divisions.js` e `pix.js`, estilos em `styles.css` e dados em `site/data/`. Documentação completa em [Site](site.md).

---

## 13. Testes

Os testes existem no repositório, mas a execução está dispensada na manutenção atual. Rodar compilação ou gerar hashes não equivale a executá-los.

| Local | Conteúdo |
|---|---|
| `tests/test_*.py` | `unittest` dos módulos Python (pipeline, mapeamentos, deltas, continuidade, instalador legado e outros); fixtures em `tests/fixtures/` |
| `site/tests/*.test.js` | testes Node do site: `site.test.js`, `seo-pix.test.js`, `explorer-interaction.test.js` |
| `windows-installer/*_test.go` | testes Go do motor de instalação |
| `tools/*/src/app/*SelfTest.java` | autotestes do codec de competições e do editor de elencos |

---

## 14. GitHub Actions (`.github/workflows/`)

| Workflow | Disparo | Função |
|---|---|---|
| `daily-data.yml` | cron `20 9 * * *` (06:20 em Brasília) e manual | `daily_update`; commit de `site/data/world-status.json` em `main` e cópia para `gh-pages` |
| `distribution.yml` | push de `config/edition.json` em `main` e manual | `daily_update` → `build_distribution` (`--bundle windows-installer/bundled_release`) → `publish_distribution` (notas em `docs/releases/v<versão>.md`) → commit dos manifestos → `publish_pages` |
| `pages.yml` | push em `site/**` e manual | publica `site/` com `deploy-pages` somente se o Pages estiver configurado com fonte "GitHub Actions"; caso contrário, encerra sem publicar |
| `quality.yml` | manual | verificações de código sem API nem publicação |
| `unified-release-gate.yml`, `site-regression.yml`, `collector-regression.yml`, `roster-editor-regression.yml` | push em caminhos específicos e manual | verificações de código (unittest, Node, `go test`, `go vet`, autotestes Java) |
| `publish-researched-rosters.yml` | push em `tools/export_researched_rosters.py` e manual | regenera `researched-rosters-2026.json` (legado B/C) |
| `calendar.yml` | manual | `transfer_windows.py`, sem publicação |
| `inspect-official-game.yml`, `inspect-v4-maranhao.yml`, `roster-candidate-audit.yml` | manual ou push em caminhos específicos | investigações de fases anteriores (**legado**) |
| `finalize-approved-v4-release.yml` | publicação da release `v2026.2.0` | finalização de uma release antiga (**legado**) |

---

## 15. Configuração (`config/`)

| Arquivo | Conteúdo | Lido por |
|---|---|---|
| `edition.json` | `productName`, `PATCH_YEAR`, `version`, `channel`, `releaseNotes`, `repository`, `siteUrl`, `platforms` (5 alvos com `interface` e `gameRuntime`) | build, publicação, compilação, exportação |
| `edition-live-match-preview.json`, `edition-hub-preview.json` | edições `local-preview` só para Windows, passadas com `--edition` | `build_distribution.py` |
| `sources.json` | feeds públicos CC0 do catálogo mundial e `schedule` (`hour`, `timezone`) | `daily_update`, `daily_maintenance` |
| `live-roster-team-map.json` | ID de clube na fonte → `teams/<arquivo>.ban` | `collect_live_rosters` |
| `rosters-<versão>.json` | snapshot coletado por versão | `compile_live_rosters`, `export_patch_clubs` |
| `live-rosters-supplement.json` | clubes coletados à parte, com `identitySources` | `compile_live_rosters` (`--supplement`), `export_patch_clubs` |
| `player-status-2026.json` | marcações de estrela e Top Mundial por atleta e clube, com política, fonte e motivo de remoção | `compile_live_rosters` |
| `roster-build-<versão>.json` | cobertura da compilação por versão | gerado por `export_release_rosters` |
| `brasfoot-country-names.json` | código numérico de país do jogo → nome | `export_patch_clubs` |
| `continental-cups-2026.json` | participantes iniciais das copas continentais, fontes e limitações | `patch_continental_cups_2026` |
| `world-cup-2026.json` | grupos e fontes da Copa do Mundo de 2026 (referência; os grupos usados pelo transformador estão nos moldes Java) | consulta |
| `payload-provenance.json` | proveniência de um payload de release anterior | consulta |
| `graphics.json` | registro de imagens autorizadas e tamanhos | `graphics_pipeline` |
| `transfer-windows-2026.json` | calendário de janelas de transferência | `transfer_windows.py` |
| `continuity.example.json` | modelo da configuração local de continuidade | `continuity_service` |
| `tzdata/` | cópia de `America/Sao_Paulo` para sistemas sem base de fusos | `compile_live_rosters`, `daily_maintenance` |

Dados versionados fora de `config/`:

- `data/competitions/2026-brazil.json`: os 156 participantes das Séries A–D de 2026, com fontes;
- `data/competitions/2026-abc-original-file-map.json`: os 60 clubes A/B/C ligados ao arquivo original e ao SHA-256;
- `data/assets/references-2026.json`: referências de escudos e uniformes, com revisão de licença.
