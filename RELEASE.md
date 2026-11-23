# Release completa — manual do agente

Este documento é o roteiro único para publicar uma versão do Brasfoot Mega Patch de ponta a ponta sem quebrar a rotina diária, o hub dos usuários, as carreiras salvas ou o site. Vale para qualquer agente. Leia inteiro antes de começar; os detalhes técnicos de cada ferramenta estão em [`docs/release.md`](docs/release.md), [`docs/scheduled-maintenance.md`](docs/scheduled-maintenance.md) e [`docs/installer.md`](docs/installer.md), e as regras gerais em [`AGENTS.md`](AGENTS.md), que prevalece em caso de conflito.

Uma release não termina quando o GitHub mostra a versão como `latest`. Ela termina quando a próxima rotina diária consegue partir dela (seção 3).

## 1. Tipos de release

| Tipo | Quem dispara | Ferramenta | O que muda |
|---|---|---|---|
| **Diária** | automação local do Codex (roteiro em `data/private/codex/rotina-diaria-prompt.md`) | `tools/daily_release.py prepare` + `tools/regression_suite.py` + `tools/daily_release.py publish` | só elencos e técnicos aprovados; executável, ligas e escudos são herdados |
| **Manual** | pedido explícito do proprietário | sequência da seção 6 | executável (campo animado, competições, juniores), Super Update, escudos, hub, ou qualquer coisa fora dos elencos |

- `daily_release prepare` só gera release quando há mudança aceita nos `.ban` (`material: true`); uma mudança só no executável nunca passa por ele.
- Release manual só com pedido explícito do proprietário para publicar aquela versão. Antes disso, a mudança sai como prévia privada em `dist/` (ver `AGENTS.md`, "Publicação").
- A regressão diária recusa executável diferente das bases (`saves` reprova). Por isso, mudança de executável é sempre release manual, e ao fim dela as bases da rotina precisam apontar para os executáveis novos.

## 2. Regras que não podem ser quebradas

1. **Nada proprietário no pacote.** Só receitas delta reconhecidas por SHA-256. Nunca o `bf22-23.exe`, `.ban` inteiros do jogo original, saves ou o vanilla.
2. **Jogo do usuário intocado.** Nunca escrever em `C:\Brasfoot22-23`, `sav/`, ativação, licenças ou backups do usuário. Toda instalação de teste é feita em cópias em `data/private/`.
3. **Saves compatíveis.** Os campos das classes serializadas (`best/*`, `f/*`) continuam iguais. Executável novo exige a conferência de classes serializáveis e save de referência (a seção `saves` da regressão avisa).
4. **Motor de simulação intacto**, salvo a exceção autorizada do componente Elencos + Competições 2026 (`AGENTS.md`).
5. **Nada inventado.** Dados esportivos, transferências, datas, testes, compatibilidade e porcentagens só com fonte. Notas da versão descrevem só o que está no pacote.
6. **Manifestos honestos.** `compatibilityVerifiedInGame=false` e `gameplayVerified=false` sempre; nenhum agente executa gameplay. Compilação, hashes e leitura de código não são testes.
7. **Segredos fora.** Tokens, `.env` e chaves nunca vão para commit, log, notas ou checkpoint.
8. **Commits** no nome `yzPeedro`, sem linhas de coautoria de ferramentas, a partir de `main`.
9. **Limites do hub:** no máximo 64 origens por arquivo, 8 passos por cadeia de receitas, 16.384 arquivos e 2 GiB por pacote, 25 MB por arquivo. `build_distribution` e `build_component_bundle` recusam pacotes fora do limite; `tools/prune_bundle_origins.py` remove origens de prévias privadas.
10. **Herança obrigatória.** Nunca montar a release sem `--inherit-bundle` (bundle publicado anterior) e `--previous-bundle` (escudos). Sem isso, ligas de outros países, clubes acrescentados, troféus, juniores, escudos e camisas somem do pacote.
11. **Versão do hub** (`config/hub.json`) só muda quando o código em `windows-installer/` muda. Formato de pacote que hubs antigos não entendem exige subir `requiresHub`.
12. **Ordem de publicação:** artefatos verificados → release → manifestos → site → conferência → bases. Nunca manifestos ou site antes da release existir.
13. **Regressão `pass` antes de publicar.** Falha em seção obrigatória bloqueia a publicação; não se substitui seção por opinião.

## 3. Contrato com a rotina diária

A rotina lê a versão publicada em `config/edition.json` (chamada aqui de `<PUB>`) e para no pré-voo se qualquer item abaixo faltar ou divergir. **Toda release, manual ou diária, só está concluída quando todos existem para a versão nova.**

| # | Item | Como a rotina usa |
|---|---|---|
| 1 | `config/edition.json`, `site/data/distribution.json` (`version`), `site/data/release.json` (`publishedVersion`) e o `release.json` da *latest* no GitHub com a mesma versão | pré-voo: versões divergentes param a execução |
| 2 | `data/private/releases-publicadas/v<PUB>/` com `Brasfoot-Mega-Patch-<PUB>-bundle.zip` e `release.json`, SHA-256 do zip igual ao do feed | `--previous-zip` da regressão e conferência do publicado |
| 3 | `data/private/base-publicada-<PUB>/`: cópia do vanilla com o zip publicado aplicado pelo `hubcli`; `bf22-23.exe` igual ao executável completo publicado | exportação do catálogo, `--base-game`, `--fallback-game` e `--previous` do `build_release_bundle` |
| 4 | `data/private/scheduled-maintenance/<dia>/release-bundle-<PUB>-final/`: o `bundled_release/` do zip publicado **mais o `crests.json`** (o índice de escudos nunca vai no zip) | `--previous-bundle`, `--inherit-bundle` e herança de escudos |
| 5 | `data/private/live-match-release-<PUB>/` com `bf22-23.exe`, `bf22-23-live-only.exe` e `bf22-23-patch-only.exe`, os três com SHA-256 presente no manifesto publicado | executáveis da release seguinte e origens anteriores (`previous_live_arguments` varre todas as pastas `live-match-release-*`) |
| 6 | `AGENTS.md`: uma única frase `Base atual (<PUB>, …)` citando a pasta do item 5 com os três SHA-256 e o bundle do item 4 | o roteiro extrai `$PREV` e `$LIVE` dessa frase por expressão regular |
| 7 | Padrões de `tools/daily_release.py` (`--full-executable`, `--live-executable`, `--patch-executable`) e de `tools/regression_suite.py` (`base_dir`) apontando para a pasta do item 5 | a rotina não passa esses argumentos; usa os padrões |
| 8 | `site/data/patch-clubs.json` e `site/data/roster-coverage.json` com `version` = `<PUB>` | a seção `site` da regressão exige versões iguais no site, na edição e no manifesto |
| 9 | `data/private/vanilla-22-23/` (exe `2fa65476…bb1c`) e `data/private/releases-publicadas/v2026.5.3` e `v2026.5.7` (gerações antigas da matriz) | matriz de instalação e remoção |
| 10 | `main` limpa, igual a `origin/main`, `git config user.name` = `yzPeedro` | pré-voo e `publish` |

`daily_release publish` cuida sozinho dos itens 1, 4 (sem o `crests.json` se ele já veio da montagem) e 6 (só o bundle e a versão da frase). O roteiro da rotina cria os itens 2 e 3. **Os itens 5, 6 (executáveis) e 7 só mudam numa release manual de executável, e são responsabilidade de quem a fez.** O item 8 é responsabilidade de toda release manual.

A 2026.6.20 foi publicada manualmente sem os itens 2 a 7 e com o item 8 em 2026.6.19; a rotina de 23/11 parou no pré-voo. A recuperação está em `data/private/scheduled-maintenance/2026-11-23/bases-2026.6.20/PROVENIENCIA.md`.

## 4. Pré-voo (toda release)

```powershell
git status --short --branch
git fetch origin
git log --oneline -5 origin/main
gh release view --json tagName,isDraft,isPrerelease,publishedAt
```

1. Checkout em `main`, sem alterações locais, igual a `origin/main`. Se houver alterações: backup em `data/private/working-tree-backup-<data>/`, comparar com o remoto, avançar com `git merge --ff-only`. Nunca `reset --hard`, `clean` ou `stash pop` às cegas.
2. Não pode haver rotina diária em execução (o roteiro grava `data/private/scheduled-maintenance/active-run.txt` e um checkpoint por execução). Duas publicações simultâneas disputam a mesma versão.
3. Ler o checkpoint mais recente em `data/private/scheduled-maintenance/<data>/` e a frente correspondente em `data/private/knowledge/context/CONTINUIDADE-E-PENDENCIAS.md`. Publicação interrompida é retomada antes de qualquer versão nova.
4. Conferir que todos os itens da seção 3 existem para `<PUB>`. Se faltar algum, recuperar primeiro (seção 6.11) e não seguir.
5. Ferramentas: JDK 17 em `JAVA_HOME` (o Java 8 do sistema vem antes no PATH; use o caminho completo), Go 1.23, Python 3, Node, `gh` autenticado.
6. Definir `<NOVA>` = `<PUB>` com o último número somado de 1. Nunca reutilizar uma versão já usada por prévia publicada ou tag existente (`git tag -l "v<NOVA>"` e `gh release view v<NOVA>` devem falhar).

## 5. Release diária

A rotina é a automação do Codex; um agente só a executa manualmente quando o proprietário pede ou para retomar uma execução interrompida. A ordem, com `<W>` a pasta da execução:

```powershell
python -m tools.roster_approval ... --base-game data/private/base-publicada-<PUB> --version <NOVA> --output data/private/compiled-<NOVA>-<run> --decisions <W>/approval.json
python -m tools.daily_release prepare --version <NOVA> --published <PUB> --compiled data/private/compiled-<NOVA>-<run> --approval <W>/approval.json --previous-bundle <bundle-do-AGENTS> --base-game data/private/base-publicada-<PUB> --work <W>/prepare-work
python -m tools.regression_suite --repo . --candidate-zip dist/<NOVA>-candidato/Brasfoot-Mega-Patch-<NOVA>-bundle.zip --previous-zip data/private/releases-publicadas/v<PUB>/Brasfoot-Mega-Patch-<PUB>-bundle.zip --old-zips <zip v2026.5.3> <zip v2026.5.7> --vanilla data/private/vanilla-22-23 --compiled data/private/compiled-<NOVA>-<run> --jdk $env:JAVA_HOME --work data/private/regression-<dia>-<run> --output data/private/regression-<dia>-<run>/verdict.json
python -m tools.daily_release publish --version <NOVA> --prepare <W>/prepare-work/prepare.json --verdict data/private/regression-<dia>-<run>/verdict.json
```

- `prepare` com `material: false` encerra o dia sem release.
- `publish` exige o veredito `pass` do mesmo zip candidato e executa, com retomada: `commit-prepare`, `push-prepare`, `build-final`, `publish-release`, `commit-manifests`, `push-manifests`, `publish-pages`, `verify-release`, `verify-pages`, `update-agents`, `push-agents`. Rodar de novo retoma do passo pendente; `--dry-run` mostra o plano.
- Depois do `publish`, criar os itens 2 e 3 da seção 3 (seção 6.11, passos 1 a 3).

## 6. Release manual, passo a passo

Use `<PUB>` para a versão publicada e `<NOVA>` para a nova. Guarde tudo em `data/private/release-<NOVA>/` e registre os comandos e hashes num checkpoint em `data/private/scheduled-maintenance/<dia>/release-<NOVA>-checkpoint.md`.

### 6.1 Origem da mudança

1. A mudança foi implementada numa branch, gerada como prévia privada em `dist/`, instalada para o proprietário quando ele pediu e homologada por ele. O pedido de publicar é explícito.
2. Mesclar a branch na `main` (PR com revisão humana; agente não faz merge automático sem pedido) e voltar ao pré-voo.

### 6.2 Executáveis

Os três executáveis partem dos publicados em `data/private/live-match-release-<PUB>/`, nunca de uma prévia ou de um executável instalado:

| Variante | Arquivo | Conteúdo |
|---|---|---|
| completo | `bf22-23.exe` | Patch 2026 (competições, juniores) + campo animado |
| só campo | `bf22-23-live-only.exe` | jogo original + campo animado |
| patch sem campo | `bf22-23-patch-only.exe` | Patch 2026 sem o campo |

- Campo animado: `tools/patch_live_match_view.py --source <executável sem campo> --output <saída>` com o JDK 17; aplicado sobre o patch sem campo gera o completo, sobre o original do vanilla gera o só-campo.
- Competições e juniores: `tools/patch_competitions_2026.py`, depois o campo por cima.
- O que não mudou é copiado da pasta `<PUB>` byte a byte.
- Grave os três em `data/private/release-<NOVA>/` e anote os SHA-256.
- Conferir os campos das classes serializadas contra o vanilla (0 campos alterados) e registrar o resultado.

### 6.3 Versão e notas

1. `config/edition.json`: `version` = `<NOVA>`.
2. `docs/releases/v<NOVA>.md`: só o que mudou de fato, em português, sem prometer gameplay verificado; termina com a frase sobre `compatibilityVerifiedInGame=false` e `gameplayVerified=false`. É o texto que os hubs mostram no aviso de atualização.
3. Entrada nova em `site/data/patch-notes.json`.
4. Hub: se `windows-installer/` mudou, subir `config/hub.json` e escrever `docs/hub/v<hub>.md`; se o pacote exige hub novo, subir `requiresHub`.

### 6.4 Pacote

Sempre nesta ordem, cada etapa herdando a anterior (é a mesma sequência de `daily_release.bundle_commands`). `<PREV>` é o bundle da frase "Base atual" do `AGENTS.md`; `<BASE>` é `data/private/base-publicada-<PUB>`.

```powershell
# 0. só se for preciso remover origens de prévias privadas (limite de 64)
python -m tools.prune_bundle_origins --bundle <PREV> --output <W>/bundle-0-previous-pruned --version <PUB> --drop-executable <exe>

# 1. receitas dos .ban, do BRA.cfg e do executável, herdando o resto
python -m tools.build_release_bundle --original data/private/vanilla-22-23 --base <BASE> --teams <teams> --executable data/private/release-<NOVA>/bf22-23.exe --previous <BASE> --inherit-bundle <PREV> --output <W>/bundle-1-release --version <NOVA>

# 2. variantes do executável para o hub (Patch, campo, os dois)
python -m tools.build_component_bundle --inherit-bundle <W>/bundle-1-release --original-executable data/private/vanilla-22-23/bf22-23.exe --patch-executable data/private/release-<NOVA>/bf22-23-patch-only.exe --full-executable data/private/release-<NOVA>/bf22-23.exe --live-executable data/private/release-<NOVA>/bf22-23-live-only.exe --patch-recipe <W>/patch-recipe.json <para cada pasta data/private/live-match-release-*: --previous-live-executable <pasta>/bf22-23.exe --previous-live-only-executable <pasta>/bf22-23-live-only.exe, sem repetir SHA-256 nem os executáveis novos> --original-game data/private/vanilla-22-23 --output <W>/bundle-2-components --version <NOVA> --release

# 3. escudos e camisas herdados do publicado anterior
python -m tools.build_crest_bundle bundle --inherit-bundle <W>/bundle-2-components --previous-bundle <PREV> --output <W>/bundle-3-crests --original-game data/private/vanilla-22-23 --version <NOVA>
```

- `<teams>`: os `.ban` da release. Sem mudança de elencos, os `teams/` de `<BASE>`; com mudança, a saída aprovada pela `roster_approval`.
- `<W>/patch-recipe.json`: a receita `patches/bf22-23.exe.patch.json` de `<PREV>` sem duplicatas, como em `daily_release.dedupe_patch_recipe` (mantém só variantes cujo destino é o patch sem campo e cuja origem não é o completo).
- Super Update: `python -m tools.world.compile_game` e `python -m tools.world.build_preview_bundle --release`, só quando a ordem de herança em relação ao `build_release_bundle` estiver comprovada no código e registrada no checkpoint.
- Competições e juniores: `tools/build_competitions_preview.py --release`.
- Conferir no manifesto final: `version` = `<NOVA>`, `publicationAllowed=true`, `channel` = `stable`, `kind` = `BRASFOOT_RELEASE_PATCH`, os três SHA-256 novos em `components.variants`, as origens antigas presentes, nenhuma entrada perdida em relação a `<PREV>` (conte arquivos por pasta: `patches/`, `teams/escudos`, `teams/camisas`, `trofeus/`, `conf_ligas_nacionais/`), `crests.json` presente na pasta.

### 6.5 Site e candidato

1. Copiar o bundle final para `windows-installer/bundled_release/`.
2. `python -m tools.export_release_rosters --report <report.json>` e `python -m tools.world.site_export --report <report.json> --world-snapshot config/super-update-world-2026.json` (com a compilação do Super Update, `--build` e `--java`). Resultado obrigatório: `site/data/patch-clubs.json` e `site/data/roster-coverage.json` com `version` = `<NOVA>`.
3. `python -m tools.render_live_match_preview --java <JDK17>/bin/java.exe --javac <JDK17>/bin/javac.exe` quando o campo mudou.
4. Candidato: `python -m tools.build_distribution --bundle <W>/bundle-3-crests --output dist/<NOVA>-candidato --snapshot data/private/daily/snapshot.json`.

### 6.6 Regressão

```powershell
python -m tools.regression_suite --repo . --candidate-zip dist/<NOVA>-candidato/Brasfoot-Mega-Patch-<NOVA>-bundle.zip --previous-zip data/private/releases-publicadas/v<PUB>/Brasfoot-Mega-Patch-<PUB>-bundle.zip --old-zips <zip v2026.5.3> <zip v2026.5.7> --vanilla data/private/vanilla-22-23 --compiled <pasta com teams/> --jdk $env:JAVA_HOME --base-executables data/private/release-<NOVA> --work data/private/regression-<NOVA> --output data/private/regression-<NOVA>/verdict.json
```

- Seções: `suites`, `ban`, `bundle`, `matrix`, `saves`, `render`, `site`. Todas `pass`.
- `--base-executables` aponta para os executáveis **novos**; sem ele, `saves` compara com a base antiga e reprova.
- `matrix` instala e remove pelo `hubcli` em cópias descartáveis, a partir do original, da release anterior completa, só patch, só campo, um componente só e gerações antigas. Feche o jogo instalado antes (o painel do campo grava `%LOCALAPPDATA%\BrassfootPatch2026\live-match-stats.json` e já derrubou uma matriz).
- Executável novo: anexar ao checkpoint a conferência de campos serializados (0 alterados) e, quando possível, save de referência.
- Reprovou: corrigir e voltar à 6.4. Não publicar com seção reprovada nem trocar seção por conferência informal sem registrar o motivo e o substituto.

### 6.7 Commit de preparação

Commit em `main` com o código, `config/edition.json`, `docs/releases/v<NOVA>.md`, `site/data/patch-notes.json`, os dados do site, `windows-installer/bundled_release/` e as imagens renderizadas. Mensagem `release: preparar <NOVA>`. Push para `origin/main`. Nada de `data/private/`, `dist/` ou segredos.

### 6.8 Distribuição final e publicação

```powershell
python -m tools.build_distribution --bundle <W>/bundle-3-crests --output dist/<NOVA> --snapshot data/private/daily/snapshot.json --source-commit <commit da 6.7>
python -m tools.publish_distribution --directory dist/<NOVA> --notes docs/releases/v<NOVA>.md
```

- O zip, o hash da árvore e o hash do bundle do build final têm de ser iguais aos do candidato testado (`SHA256SUMS.txt` e `distribution.json`). Diferença = voltar à regressão.
- `publish_distribution` cria a tag no commit de origem, sobe os anexos para um rascunho, confere o digest de cada um, publica como final e `latest` e atualiza `site/data/distribution.json`, `site/data/release.json` e o `softwareVersion` de `site/index.html`. Uma falha preserva a release anterior; rodar de novo retoma sem substituir anexos já enviados.

### 6.9 Manifestos e site

```powershell
git commit -m "release: publicar manifestos <NOVA>" -- site/data/distribution.json site/data/release.json site/index.html
git push origin HEAD:refs/heads/main
python -m tools.publish_pages
```

### 6.10 Conferência pós-publicação

1. `https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/release.json` com `patchVersion` = `<NOVA>` e `bundle.sha256` igual ao local.
2. O zip baixado de `releases/latest/download/` tem o mesmo SHA-256.
3. Cada anexo com nome versionado e o alias sem versão (`Brasfoot-Mega-Patch-windows-x64.exe` etc.) têm o mesmo digest no GitHub.
4. `https://yzpeedro.github.io/brassfoot-patch/data/distribution.json` e `data/patch-clubs.json` servem `<NOVA>` (o Pages pode levar alguns minutos).
5. `gh release view v<NOVA>`: não é rascunho nem pré-release.

### 6.11 Bases para a rotina

Sem esta etapa, a próxima rotina para no pré-voo. Rode do diretório do repositório, com `V=<NOVA>` e `<dia>` a data de Brasília:

1. **Publicado:**
   ```powershell
   New-Item -ItemType Directory -Force data/private/releases-publicadas/v$V
   gh release download "v$V" --repo yzPeedro/brassfoot-patch -p "Brasfoot-Mega-Patch-$V-bundle.zip" -p release.json -D data/private/releases-publicadas/v$V
   ```
   Conferir o SHA-256 do zip contra `bundle.sha256` do `release.json`.
2. **Bundle de referência:** extrair o zip e mover `bundled_release/` para `data/private/scheduled-maintenance/<dia>/release-bundle-$V-final/`; copiar para dentro o `crests.json` do bundle montado (ou do bundle anterior, se os escudos não mudaram, conferindo que `teams/escudos*` e `teams/camisas*` são idênticos). Usar sempre o conteúdo do zip publicado, não uma pasta intermediária: só ele é garantidamente igual ao que os hubs baixam.
3. **Base do jogo:** nunca sobrescrever uma base existente.
   ```powershell
   Copy-Item data/private/vanilla-22-23 data/private/base-publicada-$V -Recurse
   <hubcli> --state-dir <pasta de estado descartável> --game data/private/base-publicada-$V --bundle data/private/releases-publicadas/v$V/Brasfoot-Mega-Patch-$V-bundle.zip --yes
   ```
   O `hubcli` é o `brasfoot-mega-patch-cli.exe` compilado pela regressão (`data/private/regression-*/bin/`). Conferir: `base-publicada-$V/bf22-23.exe` tem o SHA-256 do executável completo publicado.
4. **Executáveis** (só se o executável mudou): criar `data/private/live-match-release-$V/` com os três executáveis da 6.2 e conferir que os três SHA-256 aparecem no manifesto publicado.
5. **`AGENTS.md`**: atualizar a frase "Base atual" com a versão, a pasta e os três SHA-256 do item 4 e o bundle do passo 2. A frase tem de continuar única (o `update_agents_base` e o roteiro da rotina dependem disso).
6. **Padrões das ferramentas** (só se o executável mudou): `tools/daily_release.py` (`--full-executable`, `--live-executable`, `--patch-executable`) e `tools/regression_suite.py` (`base_dir`) apontando para `live-match-release-$V`.
7. Commit `docs: registrar base <NOVA> [skip ci]` com `AGENTS.md` e os dois arquivos de `tools/`, push para `main`.
8. Simular o pré-voo da rotina: todos os caminhos da seção 3 existem, as quatro versões concordam e o SHA-256 do zip de `releases-publicadas/v$V` confere com o feed.

### 6.12 Registro

1. Checkpoint `data/private/scheduled-maintenance/<dia>/release-<NOVA>-checkpoint.md`: versão, commits (preparar, manifestos, base), URL da release, SHA-256 dos três executáveis, do zip, do bundle e de cada anexo, veredito da regressão e o que não foi verificado (gameplay).
2. Atualizar a frente em `data/private/knowledge/context/CONTINUIDADE-E-PENDENCIAS.md` e as decisões novas em `HISTORICO-E-DECISOES.md`.
3. Instalar no jogo do proprietário só quando ele pedir, pelo hub, com o jogo fechado.

## 7. Recuperação de falhas

| Falha | O que fazer |
|---|---|
| Regressão reprovou | Nada foi publicado. Corrigir a causa, remontar o pacote, rodar a regressão de novo. |
| Caiu entre o commit de preparação e a release | Retomar do passo seguinte com os mesmos arquivos; `daily_release publish` faz isso sozinho na diária. Não gerar outra versão. |
| Release em rascunho ou com anexos faltando | Rodar `publish_distribution` de novo na mesma pasta `dist/<NOVA>`; ele não substitui anexos já enviados. Nunca apagar a release anterior. |
| Release publicada, manifestos do site não | `git commit` dos três arquivos de manifesto, push e `publish_pages`. |
| Pages sem atualizar | Conferir o workflow do Pages no GitHub Actions; `publish_pages` só pede build quando o push saiu do Actions (evita build cancelada). |
| Bases da rotina ausentes | Seção 6.11 a partir do zip publicado. |
| Pasta `dist/<NOVA>` de um build que não corresponde ao commit | Conferir antes de apagar; o `publish` recusa reaproveitar. |
| Versão errada publicada como `latest` | Parar e chamar o proprietário. Não apagar tags nem releases públicas sem confirmação explícita. |

## 8. Lista final

- [ ] Pedido explícito do proprietário (manual) ou rotina diária.
- [ ] Pré-voo limpo e seção 3 completa para `<PUB>`.
- [ ] Executáveis partindo de `live-match-release-<PUB>`, campos serializados iguais.
- [ ] Pacote montado com herança (`--inherit-bundle`, `--previous-bundle`), dentro dos limites do hub.
- [ ] Notas da versão fiéis ao pacote; `patch-notes.json` atualizado; hub só se o código do hub mudou.
- [ ] Dados do site com `version` = `<NOVA>`.
- [ ] Regressão `pass` nas sete seções, com `--base-executables` correto.
- [ ] Build final igual ao candidato testado.
- [ ] Release final e `latest`, manifestos commitados, Pages servindo `<NOVA>`.
- [ ] `releases-publicadas/v<NOVA>`, `release-bundle-<NOVA>-final` com `crests.json`, `base-publicada-<NOVA>`, `live-match-release-<NOVA>` (se o executável mudou), `AGENTS.md` e padrões das ferramentas atualizados e commitados.
- [ ] Checkpoint e base de conhecimento atualizados.
- [ ] Manifestos com `compatibilityVerifiedInGame=false` e `gameplayVerified=false`.
