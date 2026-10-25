# Brassfoot Patch 2026

> **Escopo atual (25/10/2026):** 60 clubes das Séries A, B e C, com elencos reais de 2026 como objetivo. A **Série D permanece original do Brasfoot**, sem mudança de equipes, jogadores ou configurações. A prévia pública de elencos v2026.0.2 inclui 730 nomes da Série A, extraídos dos arquivos instaláveis; os 40 elencos B/C ainda não estão validados. O site exibe esses nomes em um [explorador paginado com modais](https://yzpeedro.github.io/brassfoot-patch/#clubes-2026). A v2026.1.1 anterior alterava a Série D e não deve ser confundida com o escopo atual. Detalhes em [docs/rosters-abc-2026.md](docs/rosters-abc-2026.md).


Patch comunitário experimental para o Brasfoot 2022–2023 no Windows. O repositório contém a coleta de elencos, um codec de arquivos `.ban`, testes e um site estático.

## Status verificável

- A coleta de 25/10/2026 registrou 20 clubes e 745 atletas na máquina de desenvolvimento; o snapshot privado **não está versionado aqui**.
- O gerador `build_preview.py` é **experimental**; não foi validado em execução no Brasfoot e não constitui um patch público.
- A **release pública v2026.0.2 (experimental)** foi criada em 25/10/2026 com instalador Windows em Go, após teste de instalação de elencos no Brasfoot relatado pelo usuário. [Baixe a versão publicada](https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.0.2). O pacote tem 20 clubes da Série A e 730 jogadores, dos quais 713 têm atributos estimados; não inclui as Séries B, C e D.
- O site está versionado em `site/` e sua versão estática é mantida na raiz da branch `gh-pages` para publicação por branch, sem workflows personalizados. Em 25/10/2026 foi removida a bola animada do cabeçalho, sem remover o campo.

## Testar sem consumir a API

```sh
python -m unittest discover -s tests -q
node site/tests/site.test.js
```

**Uma nova release** só deverá ser criada após gerar e testar todos os novos arquivos e confirmar no Windows e dentro do Brasfoot os clubes/divisões efetivamente anunciados, a integridade e os direitos sobre os assets. Preserve a v2026.0.2 enquanto a expansão estiver em implementação.

Veja `docs/acceptance-matrix.md`, `docs/deployment.md` e `docs/release-process.md` para as pendências.


## Expansão das divisões brasileiras (trabalho em curso)

Em 25/10/2026 foi incluído o catálogo oficial de **156 clubes das Séries A (20), B (20), C (20) e D (96)**, identificado por IDs estáveis e documentado em [divisões 2026](docs/divisions-2026.md). O [site](https://yzpeedro.github.io/brassfoot-patch/) contém um explorador informativo com filtros por série e pesquisa. **A release v2026.0.2 continua contendo apenas 20 clubes da Série A**; não há promessa de novas divisões jogáveis, camisas ou escudos nela.

A coleta do catálogo foi feita via fontes oficiais CBF, sem consumir API-Football. O coletor existente passa a usar o ledger SQLite `quota_guard.py` para contabilização diária conservadora (90 tentativas locais + reserva de 10), com a limitação de coordenação entre hosts descrita em [relatório de quota](docs/api-usage-report.md). Um [auditor offline de assets](assets_audit.py) agora permite inventariar imagens do jogo sem modificá-las nem publicá-las. Consulte [cobertura de assets](docs/assets-coverage.md) e [CANs da expansão](docs/upgrade-2026-acceptance.md).

**Não existe release nova de 156 clubes, elencos B/C/D ou uniformes oficiais.** Próximo gate é investigar suporte real às divisões, validar assets e elencos, executar testes e testar novo instalador no Windows. O download da v2026.0.2 permanece inalterado.


### Implementação Go V3 em andamento (não distribuída)

A implementação em `windows-installer/` ganhou manifesto `schemaVersion: 3`, operações explícitas `add` e `replace`, suporte a lotes variáveis (1–512 clubes), receitas de criação de equipes, rollback, preservação de saves e testes sintéticos com 156 substituições. Os testes de integração com os **20 originais privados da v2026.0.2** passaram. Isso não comprova suporte de quatro divisões jogáveis no Brasfoot. Consulte `docs/windows-installer.md`.

Para investigar os vínculos com os 136 clubes restantes, existe um coletor **privado** em `scripts/collect-game-structure.ps1`. Ele coleta apenas `.ban`, arquivos de competição `.ces` e inventário de imagens com hashes, nunca saves. O ZIP resultante não deve ser enviado ao GitHub nem publicado.

### Estrutura das competições (nova descoberta)

A análise dos **27 arquivos privados `.cfg`/`.ces`** fornecidos em 25/10/2026 comprovou que `BRA.cfg` registra quatro divisões nacionais A/B/C/D, com 20/20/20/64 clubes e oito grupos na Série D original. Foi implementado o codec Java em [`tools/competition-codec/`](tools/competition-codec/README.md), com round-trip exato 27/27 e um laboratório que produz, fora da instalação, uma configuração de 96 clubes/16 grupos. **A estrutura serializada permite representar os valores, mas a jogabilidade real da Série D com 96 não foi testada.** A expansão de jogadores/clubes e o instalador v2026.0.2 não mudaram nesta análise.


### Site publicado e cobertura real — 25/10/2026

O painel de cobertura do [site público](https://yzpeedro.github.io/brassfoot-patch/) distingue **156 clubes oficiais catalogados**, **103 correspondências de arquivo resolvidas**, **7 ainda candidatas**, **46 sem arquivo na instalação auditada** e **20 elencos experimentais disponíveis na v2026.0.2**. Não anuncia Série D 96/16 como jogável. O download público da v2026.0.2 continua igual e usa verificação SHA-256/asset via GitHub API, com link alternativo para a release. [Evidência de publicação e testes](docs/site-publication-2026-10-25.md).


### Nova alfa experimental v2026.1.0-alpha.1

Uma **pré-release separada e não homologada** está publicada:
https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.1.0-alpha.1

- **20 clubes Série A:** aproveita elencos experimentais da v2026.0.2.
- **90 clubes existentes B/C/D:** verifica arquivos históricos da instalação 2022–23; não atualiza esses elencos.
- **46 clubes ausentes:** instala arquivos sintéticos com **18 atletas fictícios por clube**, não jogadores reais.
- **Série D:** experimento `BRA.cfg` com 96 clubes e 16 grupos; serialização, backup e rollback aprovados em ambiente isolado, mas **sem teste do motor real do jogo**.
- **Segurança:** instalador exige confirmação, valida hashes, cria backup e permite desfazer. A instalação em cópia isolada com 703 arquivos fornecidos pelo usuário foi testada; a execução gráfica no Windows e o calendário do Brasfoot não foram validados.
- **Código-fonte e build:** branch `experimental/2026-1-0-156-clubes`; pipeline GitHub Actions compilou executável Windows 64 bits e publicou a pré-release em 25/10/2026.
- **Integridade do executável alfa:** `SHA-256 c30f124d4e8f9134d2c44b0a6fd6e73d5e688f2f4b05e34f2541d8f72571850f`.
- **Importante:** a alfa não equivale a 156 elencos de 2026 nem a 156 clubes comprovadamente jogáveis. **Use somente em cópia separada do jogo**, sem carreiras importantes.

O site mantém o download da v2026.0.2 como versão principal e oferece a alfa em uma seção própria.
