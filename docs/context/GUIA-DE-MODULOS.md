# Guia de módulos — Brasfoot Mega Patch

Complemento verificado do [manual operacional](BRASFOOT-MEGA-PATCH-MANUAL-OPERACIONAL.md) (§3 mapa do repositório, §5 playbooks). As interfaces de CLI abaixo foram conferidas em 31/10/2026 lendo os `add_argument` do código em `main@61511cc`, além das ferramentas locais da prévia. **Antes de executar, confirme com `--help`**: o código prevalece sobre este guia.

Nenhum comando aqui foi executado para produzir este documento. Os padrões (`default=`) estão citados como aparecem no código.

## Fluxo geral

```text
fontes públicas ──collect_live_rosters──▶ config/rosters-<versão>.json (snapshot)
                                              │  + config/live-rosters-supplement.json
                                              │  + config/player-status-<ano>.json
base privada reconhecida ──compile_live_rosters (Java src/app/Main.java)──▶ data/private/compiled-<versão>/teams/*.ban
                                              │
EXE transformado (patch_world_cup / patch_continental_cups / patch_live_match_view) ─┐
                                              ▼                                       │
                 build_release_bundle ──▶ data/private/release-bundle-<versão>/ (manifest + patches) ◀┘
                                              │
                 build_distribution (Go) ──▶ dist/<versão>/ (5 instaladores + aliases + SHA256SUMS + distribution.json)
                                              │
                 publish_distribution (gh) ──▶ GitHub Release final/latest + site/data/{release,distribution}.json
                                              │
                 export_release_rosters / export_patch_clubs ──▶ site/data/*.json
                                              │
                 publish_pages ──▶ gh-pages + solicitação de build do Pages
```

Catálogo mundial, em paralelo e sem alterar o jogo: `daily_update` → SQLite/snapshot em `data/private/daily/`.

---

## 1. Coleta de elencos — `tools/collect_live_rosters.py`

- **Objetivo:** obter plantéis públicos atuais por clube mapeado.
- **CLI:** `--original-catalog PATH` (obrigatório), `--output` (padrão `config/rosters-2026.4.1.json`; **sempre passar o da versão nova**), `--cache` (padrão `data/private/live-roster-cache`), `--mappings` (padrão `config/live-roster-team-map.json`), `--cache-max-age-hours` (padrão 18), `--refresh`.
- **Entradas:** catálogo original exportado; mapa estável fonte→arquivo `.ban`. **Saída:** snapshot JSON versionado, com `provider`, `collectedAt` e clubes.
- **Fonte:** serviço público de elencos do 365Scores. A política está em `docs/365scores-roster-policy.md`.
- **Riscos:** homônimos, respostas parciais (ausência não é saída) e cache antigo usado como atual. Não apagar o cache de recuperação.
- **Conferir:** contagens de clubes e atletas, falhas e uso de fallback registrados no snapshot e no checkpoint diário.

## 2. Compilação de elencos — `tools/compile_live_rosters.py`

- **Objetivo:** gerar os `.ban` que o jogo carrega a partir do snapshot, sem tocar na instalação.
- **CLI:** `--base-game` e `--original-game` (obrigatórios, diretórios de jogo privados reconhecidos), `--fallback-game` (última base publicada), `--output` (obrigatório), `--snapshot`, `--supplement` (repetível), `--java`, `--javac`, `--version` (padrão: `config/edition.json`).
- **Dependências:** JDK; `src/app/Main.java` (subcomandos `export-directory` e `batch-rosters`); `tools/roster_position_map.py`.
- **Comportamento verificado no código:**
  - A data de referência é a de hoje em São Paulo (`sao_paulo_today`).
  - A idade é calculada pela data de nascimento quando existe.
  - Lê `config/player-status-{ano}.json` quando o arquivo existe e aplica as flags `b` (estrela) e `j` (Top Mundial) nos dois sentidos.
  - Aborta se um alvo de status não casar exatamente uma vez.
- **Saída:** `teams/` compilado e relatório `config/roster-build-<versão>.json`, com contagens, auditoria de status e limitações.
- **Riscos:** cruzar homônimos; suplemento antigo sobrescrever snapshot novo; posições (0 goleiro, 1 lateral, 2 zagueiro, 3 meio, 4 ataque); `i` é lado, não pé.

## 3. Dados públicos do site — `tools/export_release_rosters.py`, `tools/export_patch_clubs.py`

- **CLI:** os dois exigem `--report PATH` (o `roster-build` da versão). `export_patch_clubs` aceita `--output` (padrão `site/data/patch-clubs.json`).
- **Regra:** gerar a partir do compilado real, nunca de planilhas históricas.

## 4. Catálogo mundial diário — `tools/daily_update.py`, `tools/daily_maintenance.py`

- **CLI `daily_update`:** `--config` (padrão `config/sources.json`), `--state-dir` (padrão `data/private/daily`), `--offline`, `--report-output`. O agendamento local usa `--report-output data/private/daily/world-status.json` para não sujar o checkout (AGENTS.md).
- **`daily_maintenance`:** wrapper com lock, janela de horário (`config/sources.json` → `schedule.hour = 6`) e retry. Não tem CLI própria.
- **Não altera** `.ban` nem EXE. Sem mudança material, não há release.

## 5. Transformações do executável (Java/bytecode)

| Ferramenta | CLI | Base exigida | Observações |
|---|---|---|---|
| `tools/patch_world_cup_2026.py` | `--source-exe`, `--output-exe` (obrigatórios), `--java`, `--javac` | SHA exato da 4.2 | reconstrói 4 classes; o bug da 4.3 (`VerifyError`) foi corrigido na 4.4 com método transplantado de molde compilado |
| `tools/patch_continental_cups_2026.py` | idem | EXE da 4.4 | usa `config/continental-cups-2026.json`; o fallback é a lógica original |
| `tools/patch_live_match_view.py` (**local, não commitado**) | `--source`, `--output` (obrigatórios), `--javac`, `--java` (padrão: JDK 17 Microsoft em `C:\Program Files\Microsoft\jdk-17.0.11.9-hotspot`) | constante `EXECUTABLE_SHA256 = 8193758a…a119`; classe `a/dV.class` com SHA `658d5d03…62f5` | compila `LiveMatchPanel.java` com `-source 7 -target 7` e usa ASM interno do JDK para transformar a tela de partida. Ver frente F1 em [CONTINUIDADE](CONTINUIDADE-E-PENDENCIAS.md) |

- **Regras:** trabalhar em cópia; cada transformador confere o SHA da base e deve ser adaptado explicitamente quando a base muda. Não encadear às cegas. A 4.7 manteve o EXE da 4.5.
- **Apoio:** `tools/world-cup-2026-src/`, `tools/continental-cups-2026-src/`, `tools/competition-codec/`, `tools/team-roster-editor/`, `tools/inspect_career_years.py`, `tools/trace_*`.

## 6. Bundle de delta — `tools/build_release_bundle.py`

- **CLI:** `--original`, `--base`, `--teams`, `--executable`, `--output` (todos obrigatórios), `--previous` (obrigatório, repetível: cada base publicada reconhecida), `--inherit-bundle` (bundle anterior cujas variantes continuam válidas por deltas encadeados), `--version` (padrão `edition.json`). Atenção: o destino é `--output`, não `--destination` como no exemplo conceitual do manual §5.5.
- **Saída:** `manifest.json` + `patches/*.json`, com variantes aceitas por `originalSha256` → `targetSha256`.
- **Salvaguardas verificadas:** recusa receita do `bf22-23.exe` cujos literais passem de 30% do alvo (o EXE proprietário não é redistribuído). Encadeia variantes legadas para manter original, V4, 3.5/4.0, 4.1 e sucessoras.
- **Alteração local não commitada:** ignora a variante legada cujo `originalSha256` já é o próprio alvo. Isso evita receita com origem igual ao destino, uma das causas do BF-199 nas prévias.
- **Prévia:** `tools/build_live_match_preview_bundle.py` (local), com CLI `--inherit-bundle`, `--published-executable`, `--preview-executable`, `--previous-preview-executable` (repetível), `--output` e `--version` (padrão `2026.4.27`). Mantém as receitas de clubes byte a byte e marca o resultado como não publicável.

## 7. Distribuição — `tools/build_distribution.py`

- **CLI:** `--bundle`, `--output` (obrigatórios), `--edition` (padrão `config/edition.json`), `--source-commit` (40 hex), `--snapshot`, `--target` (repetível, ex. `windows/amd64`), `--go`.
- **Verificado no código:**
  - Exige `PATCH_YEAR` inteiro e versão `ANO.N.N`.
  - Compila com `CGO_ENABLED=0`; no Windows usa `-H=windowsgui`, sem console.
  - Gera `distribution.json` e `SHA256SUMS.txt`.
- **Alteração local não commitada:** o canal vem de `edition.channel` em vez de `"stable"` fixo, para que a prévia saia com `local-preview`.
- **Alvos da release:** `windows/amd64`, `linux/amd64`, `linux/arm64`, `darwin/amd64`, `darwin/arm64`.

## 8. Instalador — `windows-installer/` (Go)

- **Módulo:** `go.mod` declara `go 1.23`. Arquivos principais:
  - `engine.go`: aplicação das receitas.
  - `bundle.go`: pacote embutido.
  - `restore.go`, `replace_windows.go` e `replace_nonwindows.go`: backup, substituição e rollback.
  - `main_windows.go`: GUI.
  - `main_other.go`: console/seletor para Linux e macOS.
  - `diagnostic.go`: códigos de erro.
  - `pix.go` e `pix_windows.go`: PIX opcional.
- **Códigos de diagnóstico (verificados em `diagnostic.go` / `main_windows.go`):**
  - BF-100: pasta não selecionada.
  - BF-101 a BF-103: pasta inválida ou estrutura não reconhecida.
  - BF-104: arquivos diferentes da versão suportada.
  - BF-105: falta arquivo de clube.
  - BF-106: pacote embutido inválido; aparece também com versão fora de `ANO.N.N`.
  - BF-107: sem permissão.
  - BF-108: interrompido, com originais restaurados.
  - BF-109: restauração incompleta.
  - BF-110: instalação anterior incompleta.
  - BF-111: pouco espaço em disco.
  - BF-112: Brasfoot aberto.
  - BF-199: verificação de segurança ou falha inesperada.
- **Legado:** `installer/` (Python/Tk) é protótipo histórico, não o instalador vigente.

## 9. Publicação

- **`tools/publish_distribution.py`:**
  - CLI: `--directory` e `--notes` (obrigatórios).
  - Cria a tag e uma release em draft técnico e faz upload dos versionados e dos aliases, conferindo o digest.
  - Só então marca final/latest e atualiza `site/data/release.json` e `site/data/distribution.json`.
- **`tools/publish_pages.py`:**
  - Sem CLI.
  - Abre um worktree destacado de `origin/gh-pages` e copia `site/`, ignorando `tests` e `*.test.js`.
  - Faz commit e push em `gh-pages` e chama `POST repos/yzPeedro/brassfoot-patch/pages/builds`.
- **`release.ps1`:**
  - Parâmetros: `-PackagePath`, `-OutputDirectory`, `-Publish`, `-PublishExisting`.
  - **Exige `docs/releases/v<versão>.md`**, que só existe até `v2026.4.2`.
  - Sem `-PublishExisting`, roda `daily_update` e `build_distribution`; com publicação, faz commit dos manifestos, push e Pages.
- **Ordem obrigatória:** commit e push da fonte → build vinculado ao SHA → assets conferidos → manifestos → site.

## 10. Site — `site/`

- **Arquivos:**
  - `index.html`.
  - `styles.css`: identidade celeste.
  - `app.js`: busca, filtros, paginação, download e modal.
  - `coverage.js` e `divisions.js`.
  - `pix.js`.
  - `data/*.json`: release, distribuição, patch notes, cobertura, clubes e `explorer-cups.json`.
  - Páginas `como-instalar/`, `compatibilidade/` e `versoes/`.
- O download aponta para `releases/latest/download/Brasfoot-Mega-Patch-<plataforma>`.
- As regras de UX vigentes estão em [HISTORICO-E-DECISOES](HISTORICO-E-DECISOES.md), linha "Site".

## 11. Continuidade e automações

- **`tools/continuity_service.py`:** recebe `--config` (obrigatório; local `config/continuity.local.json`, baseado em `config/continuity.example.json`). É chamado por `scripts/run-continuity.ps1`, que lê a variável `NINEROUTER_API_KEY`; **nunca registrar o valor**.
- **`tools/continuity.py` e `tools/codex_quota.py`:** ondas, checkpoints e quota.
- **Tarefas do Windows:** `Brasfoot Mega Patch - Continuity` e `Brasfoot Mega Patch - Daily Data` estavam **`Disabled`** em 31/10/2026. A manutenção das 18h roda no app Codex (rotina `atualizar-brasfoot-e-site`, segundo `docs/current-state.md`) e registra checkpoints em `data/private/scheduled-maintenance/<data>/checkpoint.md`.
- Não criar agendamentos duplicados nem reativar tarefas sem pedido.

## 12. Riscos de regressão transversais

- **Bump de versão:** sem atualizar `edition.json`, as notas e os manifestos, a release fica inconsistente.
- **Edição local paralela:** a rotina das 18h usa worktree limpo. Se este checkout estiver sujo, ele fica atrás de `origin/main`; sincronize com backup antes de commitar.
- **CRLF:** `core.autocrlf=true`. Comparar arquivos com o remoto ignorando o fim de linha.
- **`data/` e `dist/`:** são ignorados pelo Git (`.gitignore`). Bases, bundles e prévias só existem localmente; perder o disco é perder a proveniência.
