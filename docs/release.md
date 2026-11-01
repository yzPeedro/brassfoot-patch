# Release e publicação

Uma release transforma os arquivos compilados em um bundle de receitas, compila os pacotes das cinco plataformas, publica tudo no GitHub e atualiza o site. Os pacotes nunca contêm saves ou o executável original do Brasfoot.

## Edição

[`config/edition.json`](../config/edition.json) define produto, ano (`PATCH_YEAR`), versão (`AAAA.M.m`), canal e plataformas. Edições de prévia (`channel: local-preview`) ficam em arquivos próprios, como `config/edition-hub-preview.json`, e não são publicadas.

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
     --patch-recipe <receita-do-patch-sem-campo> --output <bundle-final> --version <versao> --release
   ```

3. **Notas da versão.** Escreva `docs/releases/v<versao>.md` e acrescente a entrada correspondente em `site/data/patch-notes.json`.

4. **Commit.** Faça commit e push do código e das notas. O build registra o commit de origem em cada artefato.

5. **Distribuição.**

   ```bash
   python tools/build_distribution.py --bundle <bundle-final> --output dist/<versao> --snapshot data/private/daily/snapshot.json
   ```

   O build gera os pacotes das cinco plataformas, `distribution.json` e `SHA256SUMS.txt`. No Windows também gera ícone, manifesto e informações de versão e, se configurado, assina o executável (veja [Hub e instalador](installer.md#recursos-do-executável-e-assinatura)).

6. **Publicação.**

   ```bash
   python tools/publish_distribution.py --directory dist/<versao> --notes docs/releases/v<versao>.md
   ```

   O publicador cria a tag no commit de origem, sobe os arquivos para uma release em rascunho, confere o digest de cada arquivo informado pelo GitHub, publica a release como final e `latest` e atualiza `site/data/distribution.json`. Uma falha preserva a release anterior; a mesma pasta permite retomar os envios sem substituir arquivos já publicados.

7. **Site.** Faça commit dos manifestos do site e publique:

   ```bash
   python tools/publish_pages.py
   ```

O script [`release.ps1`](../release.ps1) encadeia coleta, build e publicação (`-Publish`) ou retoma uma publicação existente (`-PublishExisting`).

## Downloads permanentes

Os artefatos são publicados também com nomes sem versão, para que `https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/Brasfoot-Mega-Patch-windows-x64.exe` sempre aponte para a versão mais recente. O site usa esses endereços.

## Integridade e estado de verificação

Cada artefato registra versão, plataforma, commit, hash da árvore de fontes, hash do bundle, tamanho e SHA-256. Os manifestos mantêm `compatibilityVerifiedInGame=false` e `gameplayVerified=false` enquanto não houver verificação em jogo; compilação e hashes não substituem essa verificação.
