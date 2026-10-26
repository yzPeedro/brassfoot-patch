# Publicação manual da release v2026.3.4

**Status:** artefato preparado pelo ChatGPT com base no instalador V4 v2026.3.4 aprovado pelo mantenedor. **A release ainda não foi publicada.**

## Preenchimento do GitHub Releases

- Tag: `v2026.3.4` (criar a partir de `main`)
- Title: `Brasfoot Patch 2026.3.4 — V4 com backup e restauração`
- Label: `Latest`, não `Pre-release`
- Asset: somente `Brasfoot-Patch-2026-Setup-v2026.3.4.exe`
- Tamanho exato: **5.045.760 bytes**
- SHA-256: `bf12ad06b664b562a23dd23450c9440e5050327fd732839c72d63b96c2dc2c82`

## Notas da release

Patch gratuito e independente para uma instalação já existente do Brasfoot 22–23 Windows.

- Atualização da instalação no mesmo caminho, incluindo o conteúdo da V4 fornecida e homologada pelo mantenedor.
- Backup integral da instalação existente, incluindo saves, configurações e personalizações, antes da aplicação do patch.
- Botão **Restaurar Brasfoot original** para desfazer a atualização.
- Seletor de ano 2026 e Série A/B/C com 20 clubes cada, de acordo com a V4 testada.
- Progresso e histórico de operações, relatório e notificações de sucesso/erro.
- Apoio opcional via Pix com QR Code.
- Ícone permanente com a letra **B**, sem o número do ano.

**Requisito:** possuir o Brasfoot 22–23 original. Faça backup dos saves e teste em uma nova carreira. Ainda não foi validada toda a duração de uma temporada nem a progressão de anos. Elencos B/C, uniformes e escudos não são apresentados como inteiramente atualizados para 2026.

## Como o site ativa o botão

O site em `site/` utiliza `data/release.json` e `app.js` para consultar o GitHub Releases. O botão só é liberado quando a tag, o asset enviado, o tamanho e o digest SHA-256 correspondem exatamente aos dados acima. Não altere o nome do arquivo enviado ao release. A página deve passar automaticamente do estado aguardando publicação para disponível quando a API pública do GitHub refletir a publicação, após atualização da página.

## Histórico

A v2026.2.0 pública anterior distribuía um utilitário com cópia isolada. A v2026.3.4 mudou o fluxo de instalação para a pasta existente e incluiu o backup integral. O repositório mantém testes e códigos de ferramentas anteriores; este documento registra precisamente o nome e hash do instalador distribuído.
