# Publicação do site

Endereço: https://yzpeedro.github.io/brassfoot-patch/

A configuração real do GitHub Pages usa a raiz de `gh-pages`. Os fontes ficam em `main/site/`. `python tools/publish_pages.py` publica uma cópia do site sem a pasta de testes, faz push sem force e solicita a reconstrução estática. A versão anterior da branch permanece no histórico Git.

O publicador de distribuição cria os assets primeiro, confirma seus tamanhos/digests no GitHub e gera `site/data/distribution.json`. Só depois esse manifesto é commitado e o site publicado. Uma falha antes disso não troca os links de produção.

A instalação inicial V4 continua em `site/data/release.json`, versão 2026.3.5. Os atualizadores 2026.4.0 são experimentais, com seleção manual de sistema e arquitetura. A detecção automática é uma sugestão; os outros downloads permanecem visíveis.

Nesta entrega o mantenedor pediu expressamente que não fossem executados testes. Os commits usam `[skip ci]`, e a publicação é direta por Git/GitHub CLI. `pages.yml` e as suítes anteriores foram preservados, mas não executados. Compilação, hash de arquivo e resposta de publicação não comprovam acessibilidade, funcionamento visual ou gameplay.

O workflow diário atualiza apenas `world-status.json`, conservando o site e a edição binária. O workflow de distribuição constrói os cinco alvos ao mudar `config/edition.json`.

Consulte `docs/release-process.md`, `docs/platform-distribution.md` e `docs/releases/v2026.4.0.md`.
