# Publicação estática via branch (sem workflow personalizado)

A pasta `site/` é publicada como arquivos HTML/CSS/JS na branch `gh-pages`, em sua raiz. Foi criada a partir do commit `473c0ff8aa5a883591e0f0123d050ccf34274f7f` da `main` e contém `.nojekyll`, `index.html`, `styles.css`, `app.js`, `assets/mark.svg` e `data/release.json`.

Para servir esse conteúdo, o administrador deve selecionar no GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch → gh-pages → /(root) → Save**. O conector disponível não possui permissão/operação para atualizar a configuração GitHub Pages. **Não afirmar que o site está publicado até validar HTTPS no endereço real.**

Os três workflows personalizados em `.github/workflows/` estão temporariamente em modo **workflow_dispatch** para poupar a cota de Actions até a retomada autorizada. O mecanismo interno do GitHub Pages ainda poderá usar um workflow gerenciado pelo GitHub, mesmo quando a fonte é uma branch. Ao retomar a automação, reabilitar os gatilhos de CI, calendário e Pages após revisar limites e permissões.

O manifesto público em `site/data/release.json` continua em `status: development`, com download desabilitado. Não criar release de instalador nem ativar o botão até existir um `.exe` realmente construído e validado no Windows e dentro do Brasfoot.
