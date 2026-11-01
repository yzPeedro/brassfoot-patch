# Site

O site do projeto é uma página estática em `site/`, publicada no GitHub Pages a partir do branch `gh-pages`:

https://yzpeedro.github.io/brassfoot-patch/

Ele não tem etapa de build, framework nem dependências externas. Os scripts são JavaScript puro, os dados são arquivos JSON em `site/data/` e todos os caminhos são relativos, para funcionar sob o prefixo `/brassfoot-patch/`.

Documentos relacionados: [Pipeline de dados](data-pipeline.md) (origem dos JSON de elencos), [Release](release.md) (publicação dos instaladores) e [Referência de módulos](modules.md).

## Estrutura

```text
site/
├── index.html              página principal
├── como-instalar/index.html
├── compatibilidade/index.html
├── versoes/index.html
├── app.js                  downloads, contadores, notas de versão, campo animado (todas as páginas)
├── divisions.js            explorador de clubes e seleções
├── pix.js                  contribuição voluntária
├── coverage.js             painel de cobertura antigo (não carregado)
├── styles.css              estilos e tokens de design
├── assets/                 marca, imagens do campo, cartão social
├── data/                   JSON consumidos pelas páginas
├── robots.txt, sitemap.xml
└── tests/                  testes Node (não publicados)
```

## Páginas

### `index.html`

| Seção (`id`) | Conteúdo |
|---|---|
| `inicio` | apresentação e botão de download principal |
| `campo-ao-vivo` | campo animado, com troca entre as quatro condições de gramado (`data-pitch`) |
| `clubes-2026` | explorador de clubes e jogadores, com diálogo `club-dialog` |
| `cobertura` | contadores de elencos (`data-roster-count`) e princípios de dados |
| `atualizacoes` | notas de versão (`patch-notes-list`) |
| `downloads` | os cinco pacotes por sistema e arquitetura (`data-download-platform`) |
| `faq` | perguntas frequentes |

Também contém metadados Open Graph/Twitter (com `assets/og-card.jpg`), `link rel="canonical"`, dados estruturados `SoftwareApplication` em JSON-LD e o diálogo de contribuição `pix-dialog`.

### Páginas internas

| Página | Conteúdo |
|---|---|
| `como-instalar/` | passo a passo: preparar o jogo, baixar, escolher o que instalar, backup e restauração |
| `compatibilidade/` | sistemas, arquiteturas e requisitos; Linux e macOS precisam de Wine ou outra camada de compatibilidade já configurada |
| `versoes/` | resumo da versão e do conteúdo do pacote |

As páginas internas são HTML estático. Elas usam o mesmo `styles.css` e carregam `app.js`, que só age sobre os elementos presentes em cada página.

## Scripts

### `app.js`

Comportamento da página principal:

- **Downloads:** detecta o sistema pelo navegador (`navigator.userAgentData`/`userAgent`) e destaca o pacote correspondente. Quando o sistema não é identificado, inclusive em telefones e tablets, a página pede que o visitante escolha o pacote. O menu ao lado do botão permite escolher outro sistema ou arquitetura.
- **Manifesto de distribuição:** carrega `data/distribution.json` e, se ele passar na validação (ver [Downloads](#como-os-downloads-são-resolvidos)), mostra versão, tamanho e SHA-256 de cada pacote.
- **Contadores:** preenche os elementos `data-roster-count` com os `counts` de `data/roster-coverage.json`.
- **Catálogo mundial:** lê `data/world-status.json` só se a página tiver o elemento `world-countries`. A página principal atual não tem esse elemento.
- **Notas de versão:** carrega `data/patch-notes.json` e exibe as entradas válidas (`kind` igual a `site` ou `patch`, `date` válida, `changes` em lista).
- **Interações:** menu móvel, animações de entrada, contadores animados (`data-countup`) e troca de imagem do campo animado entre `assets/live/pitch-0.jpg` e `pitch-3.jpg`. As animações respeitam `prefers-reduced-motion`.

Os textos estáticos do HTML servem de fallback: se um JSON não carregar, a página continua funcional com os links permanentes.

### `divisions.js`

Explorador de clubes e seleções. Na carga da página, busca `data/patch-clubs.json` e `data/explorer-cups.json` em paralelo, com tempo limite de 25 segundos, e valida a estrutura antes de exibir.

- **Busca:** por nome de clube, apelido ou jogador, sem diferenciar acentos.
- **Filtros:** país, competição e cobertura do elenco (`Atualizado`, `Parcial`, `Preservado`, `Sem elenco catalogado`), com atalhos `data-country-filter` e `data-coverage-filter`.
- **Tabela:** ordenação por nome, país, competição, cobertura ou número de jogadores, e paginação com tamanho de página configurável.
- **Diálogo do clube:** elenco com posição (Goleiro, Lateral, Zagueiro, Meio-campo, Atacante), lado e características, link da fonte e data de consulta.
- **Falhas:** se o catálogo não carregar, a tabela mostra o erro e um botão "Tentar novamente".

### `pix.js`

Contribuição voluntária. O código PIX e a matriz do QR Code são constantes no próprio arquivo e o QR é desenhado localmente: sem bibliotecas remotas, cookies, analytics ou chamadas a provedores de pagamento. O script controla o diálogo, o botão flutuante e a cópia do código.

### `coverage.js`

Painel de cobertura de uma fase anterior. Lê `data/coverage-2026.json` e só age se a página tiver o elemento `coverage-2026`. Nenhuma página atual carrega este script.

## Estilos e identidade visual

`styles.css` define os tokens de design em `:root`:

| Grupo | Tokens |
|---|---|
| Marca | `--brand` `#0b4be0`, `--brand-strong` `#0837b5`, `--brand-bright` `#2f6bff`, `--brand-soft` `#eaf0ff` |
| Céu e ciano | `--sky` `#4aa3ff`, `--cyan` `#2fd4ff` |
| Azul profundo | `--navy` `#071c55`, `--navy-deep` `#030c2b` |
| Texto | `--ink` `#0b1633`, `--ink-2` `#2c3a5c`, `--muted` `#5b6885` |
| Superfícies | `--white`, `--surface` `#f4f7fd`, `--line` `#e1e7f3` |
| Estado | `--ok` `#0e9f6e`, `--warn` `#b7791f` |
| Tipografia | `--font` (Segoe UI Variable Display, Segoe UI, system-ui), `--mono` (Cascadia Code, JetBrains Mono, Consolas) |
| Forma e movimento | `--radius` `20px`, `--ease` `cubic-bezier(.22,1,.36,1)` |
| Aliases semânticos | `--fg`, `--fg-muted`, `--border`, `--panel`, `--accent` |

- **Tema:** claro, com fundo branco (`color-scheme: light`, `theme-color` `#ffffff`). A interface do hub do instalador (`windows-installer/ui/hub.html`) usa a mesma paleta.
- **Responsividade:** pontos de quebra em 1150, 850, 600, 480, 430 e 370 px.
- **Acessibilidade e impressão:** blocos para `prefers-reduced-motion` e `print`; foco visível em `--brand-bright`.
- **Cache:** os arquivos CSS e JS são referenciados com sufixo de versão (`?v=...`). Atualize o sufixo nas páginas quando mudar esses arquivos.

## Recursos (`site/assets/`)

| Arquivo | Origem |
|---|---|
| `mark.svg` | marca do projeto; também é o favicon. O hub do instalador usa uma cópia idêntica (`windows-installer/ui/mark.svg`) |
| `live/pitch-0.jpg` … `pitch-3.jpg` | quadros do campo animado, um por condição de gramado, gerados por `tools/render_live_match_preview.py` |
| `og-card.jpg` | cartão social 1200×630, gerado por `tools/render_brand_assets.py` |
| `og-card.svg`, `celestial-ball.svg` | artes vetoriais sem referência nas páginas atuais |

Os quadros do campo são desenhados pelo próprio código do painel (`tools/live-match-view-src/LiveMatchPanel.java`) por meio de `tools/live-match-render/mega/RenderFrame.java`, em modo headless e sem o jogo:

```bash
python tools/render_live_match_preview.py
python tools/render_live_match_preview.py --condition 0 --width 900 --height 420 --scale 2.0
```

O cartão social usa `pitch-0.jpg` como fundo e os totais de `data/patch-clubs.json`. Por isso, gere os quadros do campo antes:

```bash
python tools/render_brand_assets.py
```

O mesmo comando também regrava os ícones de `windows-installer/winres/` e o banner `docs/assets/banner.jpg`. Os dois scripts exigem JDK (`javac` e `java`).

## Dados (`site/data/`)

| Arquivo | Conteúdo | Gerado por | Lido por |
|---|---|---|---|
| `distribution.json` | manifesto público da release: versão, commit, canal, `status: published`, cinco artefatos com tamanho, SHA-256 e `downloadUrl` | `tools/publish_distribution.py` | `app.js` |
| `release.json` | resumo do pacote Windows: versão, data, arquivo, tamanho, SHA-256, `compatibilityVerifiedInGame: false`, `gameplayVerified: false`, notas | `tools/publish_distribution.py` | consulta e testes |
| `patch-clubs.json` | todos os clubes do jogo resultante, com cobertura, país, competição e jogadores | `tools/export_patch_clubs.py` | `divisions.js` |
| `explorer-cups.json` | seleções e copas exibidas no explorador; aponta `config/world-cup-2026.json` e `config/continental-cups-2026.json` como fonte | mantido com base nessas configurações (sem gerador no repositório) | `divisions.js` |
| `roster-coverage.json` | contadores da compilação, limitações e clubes com fonte | `tools/export_release_rosters.py` | `app.js` |
| `published-rosters-2026.json` | os 60 clubes A/B/C com nomes e posições finais | `tools/export_release_rosters.py` | `export_patch_clubs.py`, testes |
| `target-abc-2026.json` | alvo dos 60 clubes A/B/C e situação de cada elenco | `tools/export_release_rosters.py` (atualização) | ferramentas de exportação e auditoria |
| `release-clubs-60.json` | versão e totais dos 60 clubes | `tools/export_release_rosters.py` (atualização) | consulta |
| `patch-notes.json` | entradas de notas de versão (`id`, `date`, `title`, `kind`, `summary`, `changes`, `url`) | editado manualmente | `app.js` |
| `world-status.json` | resumo do catálogo mundial: status, hash, cobertura e situação de cada fonte | `tools/daily_update.py` | `app.js` (se houver `world-countries`) |
| `competitions/2026-brazil.json` | participantes das Séries A–D de 2026 | mantido manualmente | `tools/daily_update.py` |
| `researched-rosters-2026.json` | observações de elencos B/C pesquisados | `tools/export_researched_rosters.py` (legado) | `tools/daily_update.py`, auditorias |
| `coverage-2026.json` | cobertura de uma fase anterior | legado | `coverage.js` (não carregado) |
| `published-rosters-2026-0-2.json` | elencos da primeira release | legado | testes |

Regras:

- **Origem dos elencos:** os arquivos de elenco e cobertura são gerados a partir do relatório real da compilação. Não edite os números à mão. O fluxo está em [Pipeline de dados](data-pipeline.md#5-exportação-para-o-site).
- **Mesma release:** `distribution.json` e `release.json` sempre descrevem a mesma release final mais recente. Os dois são escritos juntos, depois que os artefatos foram enviados e conferidos.
- **Sem alegações não observadas:** os manifestos públicos registram `tests: not-run-at-owner-request`, `compatibilityVerifiedInGame: false` e `gameplayVerified: false`.

## Como os downloads são resolvidos

1. **Links permanentes no HTML.** Cada botão aponta para um alias sem versão em `releases/latest/download`:

   ```text
   https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/Brasfoot-Mega-Patch-windows-x64.exe
   https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/Brasfoot-Mega-Patch-linux-x64.tar.gz
   https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/Brasfoot-Mega-Patch-linux-arm64.tar.gz
   https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/Brasfoot-Mega-Patch-macos-x64.tar.gz
   https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/Brasfoot-Mega-Patch-macos-arm64.tar.gz
   ```

   O GitHub redireciona `latest` para a release final marcada como mais recente.

2. **Aliases criados na publicação.** `tools/publish_distribution.py` envia cada pacote duas vezes: com o nome versionado (`Brasfoot-Mega-Patch-<versão>-windows-x64.exe`) e com o alias. Os dois têm o mesmo SHA-256. Se já existir um alias com conteúdo diferente, a publicação é recusada.

3. **Metadados opcionais.** `app.js` lê `data/distribution.json` e só o aceita se:
   - a versão segue `ANO.N.N` e não é anterior à versão mínima fixada no script;
   - `status` é `published` e `channel` é `stable`;
   - há exatamente os cinco pacotes esperados, cada um com nome seguro, SHA-256 de 64 caracteres, tamanho positivo e `downloadUrl` igual ao alias permanente ou ao endereço versionado da tag.

   Se a validação passar, a página mostra versão, tamanho e hash. Se falhar, os links permanentes continuam valendo. Um manifesto em cache nunca leva a um arquivo inexistente.

## Publicação

O site é publicado no branch `gh-pages` por `tools/publish_pages.py`:

```bash
python tools/publish_pages.py
```

1. `git fetch origin gh-pages` e criação de um worktree destacado temporário.
2. Remoção do conteúdo anterior, exceto `.git`.
3. Cópia de `site/`, sem `tests/` e `*.test.js`.
4. Commit `publish: Brasfoot Mega Patch website [skip ci]` e push para `gh-pages`, só se houver diferença.
5. Remoção do worktree e pedido de build ao GitHub Pages (`POST repos/yzPeedro/brassfoot-patch/pages/builds`), necessário quando o push vem do GitHub Actions.

O script precisa do Git com permissão de push e do `gh` autenticado. Ele publica o estado atual de `site/` no checkout: faça commit das alterações em `main` antes, para que o site publicado corresponda ao código versionado.

### Outras rotas de publicação

- **Release:** `release.ps1 -Publish` e o workflow `distribution.yml` chamam `publish_pages.py` depois de gravar `distribution.json` e `release.json`.
- **Catálogo diário:** o workflow `daily-data.yml` copia só `site/data/world-status.json` para `gh-pages/data/` e pede um novo build do Pages.
- **Workflow `pages.yml`:** publica `site/` com `actions/deploy-pages` apenas se o Pages estiver configurado com a fonte "GitHub Actions". Com a fonte em branch (`gh-pages`), ele encerra sem publicar.

Ordem obrigatória numa release: artefatos enviados e conferidos → `distribution.json`/`release.json` → commit em `main` → `publish_pages.py`. O site nunca deve apontar para downloads que ainda não existem.

## SEO

- `robots.txt` libera todo o site e aponta o sitemap.
- `sitemap.xml` lista a página principal e as três páginas internas. Atualize `lastmod` quando o conteúdo mudar.
- Cada página tem `title`, `description` e `link rel="canonical"` próprios.

## Testes do site

`site/tests/` contém `site.test.js`, `seo-pix.test.js` e `explorer-interaction.test.js`, executados com Node pelos workflows de verificação. Eles não são publicados. A execução está dispensada na manutenção atual.
