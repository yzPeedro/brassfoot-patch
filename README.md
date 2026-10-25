# Brassfoot Patch 2026

Patch comunitário experimental para o Brasfoot 2022–2023 no Windows. O repositório contém a coleta de elencos, um codec de arquivos `.ban`, testes e um site estático.

## Status verificável

- A coleta de 25/10/2026 registrou 20 clubes e 745 atletas na máquina de desenvolvimento; o snapshot privado **não está versionado aqui**.
- O gerador `build_preview.py` é **experimental**; não foi validado em execução no Brasfoot e não constitui um patch público.
- O instalador gráfico Windows e uma GitHub Release jogável **ainda não existem**. O botão de download permanece desabilitado por segurança.
- A pasta `site/` está pronta para deploy estático, mas a publicação depende de GitHub Pages configurado para **GitHub Actions**.

## Testar sem consumir a API

```sh
python -m unittest discover -s tests -q
node site/tests/site.test.js
```

Execute uma release somente depois de validar todos os arquivos `.ban` dentro do jogo, construir e testar um instalador de verdade e publicar um executável íntegro com checksum. O site só deve anunciar uma release depois dessas evidências.

Veja `docs/acceptance-matrix.md`, `docs/deployment.md` e `docs/release-process.md` para as pendências.
