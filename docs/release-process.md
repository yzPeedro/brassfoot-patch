# Publicação da edição Mega Patch

A edição é definida em `config/edition.json`. A entrega 2026.4.0 foi autorizada sem testes e deve permanecer experimental. Os gates de integridade de produção não são testes de gameplay.

1. Faça commit/push dos fontes, pacote e notas em `docs/releases/vVERSAO.md`.
2. Execute `python -m tools.daily_update` para obter o snapshot exato.
3. Construa com `python tools/build_distribution.py --bundle windows-installer/bundled_release --output dist/VERSAO --snapshot data/private/daily/snapshot.json`.
4. Publique com `python tools/publish_distribution.py --directory dist/VERSAO --notes docs/releases/vVERSAO.md`.
5. Faça commit/push de `site/data/distribution.json` e publique com `python tools/publish_pages.py`.

O publicador exige commit no GitHub, associa a tag a esse commit, cria uma release draft experimental, envia arquivos ausentes, confere o digest fornecido pelo GitHub e só então abre a pré-release. Assets existentes com conteúdo diferente são recusados; uma falha preserva a versão anterior. A mesma pasta de saída permite retomar uploads sem substituir artefatos publicados. `--latest=false` mantém a base 2026.3.5 como referência de instalação inicial.

O workflow `distribution.yml` executa esse fluxo ao mudar `config/edition.json` e também permite execução manual. Não contém testes. O site é publicado na branch `gh-pages`, configuração real deste repositório. Uma solicitação de build estático é enviada após o push; não é um teste do site.

`release.ps1 -Publish` coordena coleta/build/publicação local. `-PublishExisting` retoma a publicação de uma pasta de artefatos existente. Nunca gere uma versão nova quando o snapshot não mudou: a coleta diária só atualiza seus dados e resumo; a versão de binário muda por uma edição explicitamente definida.

A release registra estado experimental, commit dos fontes, hashes do conteúdo compilado e bundle, snapshot, plataforma, arquitetura, tamanho e SHA-256. O catálogo de fontes abertas é anexado comprimido. O payload nunca inclui saves ou o executável original do Brasfoot.

A base V4 é preservada em `site/data/release.json`; os novos atualizadores usam `site/data/distribution.json`. São propósitos diferentes. As listas de jogadores continuam com sua versão de origem 2026.3.5.
