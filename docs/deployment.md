# Publicação do site e Releases

- Repositório: https://github.com/yzPeedro/brassfoot-patch
- GitHub Pages: https://yzpeedro.github.io/brassfoot-patch/
- Branch de conteúdo: `gh-pages` (raiz); fonte espelhada em `main/site/`.
- Release pública atual: **v2026.0.2**, https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.0.2
- Instalador: `Brassfoot-Patch-2026-Setup.exe` dentro dessa release.
- O script `app.js` só libera o botão quando encontra release pública com asset, tamanho, URL e SHA-256 iguais aos declarados no manifesto do site.
- O explorador 2026 apresenta **156 clubes informativos** da CBF, não 156 clubes instaláveis. Somente 20 clubes da Série A estão presentes no patch v2026.0.2.

## Para publicar uma nova versão

1. Passar os gates de código, instalador Windows, Brasfoot, licença de imagens e integridade.
2. Criar tag e release com executável compilado de uma árvore limpa e notas de versão corretas.
3. Confirmar download público, tamanho e digest do asset (GitHub API).
4. Atualizar `main/site/`, sincronizar `gh-pages/`, preservar o frontend atual e verificar no HTTPS público.
5. Não alterar o manifesto para apontar a um link fictício ou a release ainda em rascunho.
6. Quando GitHub Actions estiver indisponível, operar via Git e `gh` autenticados localmente, sem alterar workflows privados.

**O estado real do GitHub deve prevalecer sobre documentos históricos pré-v2026.0.2.**
