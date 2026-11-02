# Release e publicação

Uma release transforma os arquivos compilados em um bundle de receitas, compila o hub e os atualizadores das cinco plataformas, publica tudo no GitHub e atualiza o site. Nenhum arquivo publicado contém saves ou o executável original do Brasfoot.

Os usuários não precisam baixar cada release: o hub instalado lê o `release.json` da release *latest*, baixa o pacote da versão e avisa sobre patch ou instalador novos (veja [Hub e instalador](installer.md#como-o-hub-obtém-a-versão-mais-recente)). Por isso, uma release só fica visível para os usuários quando é publicada como final e `latest`.

## Edição

[`config/edition.json`](../config/edition.json) define produto, ano (`PATCH_YEAR`), versão do patch (`AAAA.M.m`), canal e plataformas. Edições de prévia (`channel: local-preview`) ficam em arquivos próprios, como `config/edition-hub-preview.json`, e não são publicadas.

[`config/hub.json`](../config/hub.json) define a versão do hub (`M.m.p`), a versão mínima do hub que o pacote exige (`requiresHub`) e o arquivo de notas do hub em `docs/hub/`. Suba a versão do hub só quando o código em `windows-installer/` mudar; nesse caso escreva `docs/hub/v<versão>.md`, que aparece no modal **O que mudou** do hub. Se o formato do pacote mudar de modo que hubs antigos não consigam aplicá-lo, suba também `requiresHub`.

## Passo a passo

1. **Bundle de receitas.** Gere as receitas dos arquivos de equipe, da configuração nacional e do executável, preservando as origens aceitas das versões anteriores:

   ```bash
   python tools/build_release_bundle.py --original <jogo-original> --base <base> --teams <teams-compilados> \
     --executable <bf22-23.exe-final> --previous <base-anterior> --inherit-bundle <bundle-anterior> --output <bundle>
   ```

2. **Componentes.** Acrescente as variantes do executável para instalação seletiva (Patch 2026, campo animado ou os dois):

   ```bash
   python -m tools.build_component_bundle --inherit-bundle <bundle> \
     --original-executable <original> --patch-executable <patch-2026> \
     --full-executable <patch-2026-com-campo> --live-executable <original-com-campo> \
     --patch-recipe <receita-do-patch-sem-campo> --original-game data/private/vanilla-22-23 \
     --output <bundle-final> --version <versao> --release
   ```

3. **Notas da versão.** Escreva `docs/releases/v<versao>.md` e acrescente a entrada correspondente em `site/data/patch-notes.json`.

4. **Commit.** Faça commit e push do código e das notas. O build registra o commit de origem em cada artefato.

5. **Distribuição.**

   ```bash
   python tools/build_distribution.py --bundle <bundle-final> --output dist/<versao> --snapshot data/private/daily/snapshot.json
   ```

   O build gera:

   - o hub do Windows e os atualizadores de Linux e macOS, sem patch embutido, com a versão de `config/hub.json`;
   - `Brasfoot-Mega-Patch-<versão>-bundle.zip`, com o manifesto e as receitas da versão;
   - `release.json`, com versão, data, notas da versão (`docs/releases/v<versão>.md` ou `--notes`), `requiresHub`, notas do hub e nome, tamanho e SHA-256 de cada arquivo;
   - `distribution.json` e `SHA256SUMS.txt`.

   No Windows também gera ícone, manifesto e informações de versão e, se configurado, assina o executável (veja [Hub e instalador](installer.md#recursos-do-executável-e-assinatura)).

6. **Publicação.**

   ```bash
   python tools/publish_distribution.py --directory dist/<versao> --notes docs/releases/v<versao>.md
   ```

   O publicador cria a tag no commit de origem, sobe os arquivos (inclusive o pacote `.zip` e o `release.json`) para uma release em rascunho, confere o digest de cada arquivo informado pelo GitHub, publica a release como final e `latest` e atualiza `site/data/distribution.json`. Enquanto a release é rascunho, os hubs continuam vendo a anterior; ao virar `latest`, eles passam a avisar a nova versão. Uma falha preserva a release anterior; a mesma pasta permite retomar os envios sem substituir arquivos já publicados.

7. **Site.** Faça commit dos manifestos do site e publique:

   ```bash
   python tools/publish_pages.py
   ```

O script [`release.ps1`](../release.ps1) encadeia coleta, build e publicação (`-Publish`) ou retoma uma publicação existente (`-PublishExisting`).

## Downloads permanentes

Os artefatos são publicados também com nomes sem versão, para que `https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/Brasfoot-Mega-Patch-windows-x64.exe` sempre aponte para a versão mais recente. O site usa esses endereços. O `release.json` tem sempre o mesmo nome, e `releases/latest/download/release.json` é o endereço que os hubs consultam.

## Integridade e estado de verificação

Cada artefato registra versão, plataforma, commit, hash da árvore de fontes, hash do bundle, tamanho e SHA-256. Os manifestos mantêm `compatibilityVerifiedInGame=false` e `gameplayVerified=false` enquanto não houver verificação em jogo; compilação e hashes não substituem essa verificação.
