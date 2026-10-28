# Brasfoot Mega Patch 2026

Atualizadores gratuitos para uma instalação própria do Brasfoot 22–23. A **release final 2026.4.1** instala diretamente sobre o jogo original ou bases anteriores reconhecidas. Nenhum teste foi executado, conforme solicitação do mantenedor.

[Site](https://yzpeedro.github.io/brassfoot-patch/) · [Baixar versão mais recente](https://github.com/yzPeedro/brassfoot-patch/releases/latest) · [Instalação](https://yzpeedro.github.io/brassfoot-patch/como-instalar/) · [Compatibilidade](https://yzpeedro.github.io/brassfoot-patch/compatibilidade/)

## O que está disponível

- Atualizador Windows com interface azul, backup, restauração e botão Jogar.
- Ferramentas de atualização para Linux e macOS, x64 e ARM64. Não incluem o jogo ou Wine; execução nessas plataformas não homologada.
- 301 elencos completos substituídos: 60 brasileiros e 241 europeus, com 8.672 jogadores importados das fontes. Laterais têm posição própria; pontas são atacantes.
- Catálogo de 312 clubes, 12 competições e oito países/territórios, com coleta diária de oito fontes abertas OpenFootball e referências brasileiras já documentadas. Catálogo não significa ligas jogáveis.
- Snapshots incrementais, catálogo SQLite, cache condicional HTTPS, proveniência, preservação do último dado e journal durável.
- Site azul interativo, fundo acompanhando o ponteiro, animações e botão Baixar com detecção de sistema e seta para alternativas.
- Pipeline de gráficos com cache, proporções, transparência e registro de origem/licença para recursos locais autorizados.
- Pacotes associados a commit, snapshot, tamanho e SHA-256, com publicação de release final antes do manifesto do site.

## Instalação

Baixe o arquivo do seu sistema, feche o jogo e selecione a pasta onde o Brasfoot 22–23 está instalado. Não é necessário aplicar a V4 antes. O instalador faz backup dos arquivos alterados e permite restauração.

A tela inicial e o seletor de nova carreira mostram 2026. Nomes com três ou mais palavras usam as duas primeiras, nos 704 clubes. Saves não fazem parte das receitas de atualização.

A cobertura europeia não é integral: 54 fontes parciais preservam o elenco existente, e um clube não teve plantel atual obtido. Características de 5.388 atletas novos são derivadas da função; o jogo tem lado direito/esquerdo, sem um campo separado para pé dominante. [Cobertura e fontes](site/data/roster-coverage.json).

## Operação e compilação

A edição central fica em `config/edition.json` (`PATCH_YEAR`, nome, versão e plataformas).

```sh
python -m tools.daily_update
python tools/build_distribution.py --bundle windows-installer/bundled_release --output dist/2026.4.1 --snapshot data/private/daily/snapshot.json
python tools/publish_distribution.py --directory dist/2026.4.1 --notes docs/releases/v2026.4.1.md
python tools/publish_pages.py
```

O build requer Go 1.25 e Python 3.12. Coleta: 06:00 Brasília no agendador local já instalado; 06:20 no GitHub Actions. O workflow de distribuição publica quando a edição muda. Nenhum desses novos comandos executa suítes de testes. Os workflows anteriores de testes foram preservados; os commits desta entrega usam `[skip ci]`.

[Estado atual](docs/current-state.md) · [Especificação integral](docs/mega-patch-specification.md) · [Cobertura por requisito](config/specification-coverage.json) · [Coleta](docs/daily-update.md) · [Distribuição](docs/platform-distribution.md) · [Gráficos](docs/graphics-pipeline.md) · [Histórico anterior](docs/audit/README-before-mega-2026.4.0.md)
