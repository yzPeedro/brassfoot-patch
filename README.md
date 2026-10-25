# Brassfoot Patch 2026

Patch comunitário experimental para o Brasfoot 2022–2023 no Windows. O repositório contém a coleta de elencos, um codec de arquivos `.ban`, testes e um site estático.

## Status verificável

- A coleta de 25/10/2026 registrou 20 clubes e 745 atletas na máquina de desenvolvimento; o snapshot privado **não está versionado aqui**.
- O gerador `build_preview.py` é **experimental**; não foi validado em execução no Brasfoot e não constitui um patch público.
- Um **executável experimental de teste offline** foi executado no Windows em 25/10/2026: a simulação reportou backup, SHA-256, rollback e identificação da pasta do jogo. Esse teste não instala elencos e não comprova o funcionamento do instalador real com arquivos `.ban`. Uma GitHub Release jogável **ainda não existe**; o download permanece desabilitado por segurança.
- O site está versionado em `site/` e sua versão estática é mantida na raiz da branch `gh-pages` para publicação por branch, sem workflows personalizados. Em 25/10/2026 foi removida a bola animada do cabeçalho, sem remover o campo.

## Testar sem consumir a API

```sh
python -m unittest discover -s tests -q
node site/tests/site.test.js
```

Execute uma release somente depois de validar todos os arquivos `.ban` dentro do jogo, construir e testar um instalador de verdade e publicar um executável íntegro com checksum. O site só deve anunciar uma release depois dessas evidências.

Veja `docs/acceptance-matrix.md`, `docs/deployment.md` e `docs/release-process.md` para as pendências.
