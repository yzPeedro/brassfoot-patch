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


## Expansão das divisões brasileiras (trabalho em curso)

Em 25/10/2026 foi incluído o catálogo oficial de **156 clubes das Séries A (20), B (20), C (20) e D (96)**, identificado por IDs estáveis e documentado em [divisões 2026](docs/divisions-2026.md). O [site](https://yzpeedro.github.io/brassfoot-patch/) contém um explorador informativo com filtros por série e pesquisa. **A release v2026.0.2 continua contendo apenas 20 clubes da Série A**; não há promessa de novas divisões jogáveis, camisas ou escudos nela.

A coleta do catálogo foi feita via fontes oficiais CBF, sem consumir API-Football. O coletor existente passa a usar o ledger SQLite `quota_guard.py` para contabilização diária conservadora (90 tentativas locais + reserva de 10), com a limitação de coordenação entre hosts descrita em [relatório de quota](docs/api-usage-report.md). Um [auditor offline de assets](assets_audit.py) agora permite inventariar imagens do jogo sem modificá-las nem publicá-las. Consulte [cobertura de assets](docs/assets-coverage.md) e [CANs da expansão](docs/upgrade-2026-acceptance.md).

**Não existe release nova de 156 clubes, elencos B/C/D ou uniformes oficiais.** Próximo gate é investigar suporte real às divisões, validar assets e elencos, executar testes e testar novo instalador no Windows. O download da v2026.0.2 permanece inalterado.
