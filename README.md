# Brasfoot Mega Patch 2026

Atualizadores gratuitos para uma instalação própria do Brasfoot 22–23. A edição **2026.4.0 é experimental**, publicada sem execução de testes a pedido do mantenedor.

[Site](https://yzpeedro.github.io/brassfoot-patch/) · [Download 2026.4.0](https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.0) · [Instalação](https://yzpeedro.github.io/brassfoot-patch/como-instalar/) · [Compatibilidade](https://yzpeedro.github.io/brassfoot-patch/compatibilidade/)

## O que está disponível

- Atualizador Windows com interface azul, backup, restauração e botão Jogar.
- Ferramentas de atualização para Linux e macOS, x64 e ARM64. Não incluem o jogo ou Wine; execução nessas plataformas não homologada.
- Os mesmos 60 elencos experimentais A/B/C da edição 2026.3.5. As receitas agora estão no Git; o build não volta à antiga prévia de 20 clubes.
- Catálogo de 312 clubes, 12 competições e oito países/territórios, com coleta diária de oito fontes abertas OpenFootball e referências brasileiras já documentadas. Catálogo não significa ligas jogáveis.
- Snapshots incrementais, catálogo SQLite, cache condicional HTTPS, proveniência, preservação do último dado e journal durável.
- Site reconstruído, seleção de plataforma/arquitetura, explorador de clubes e Pix opcional preservado.
- Pipeline de gráficos com cache, proporções, transparência e registro de origem/licença para recursos locais autorizados.
- Pacotes associados a commit, snapshot, tamanho e SHA-256, com publicação automática de pré-release antes do manifesto do site.

## Instalação

Para preparar ano/divisões, use primeiro a [base Windows V4 + elencos 2026.3.5](https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.3.5). Depois abra o atualizador da sua plataforma e selecione a pasta do jogo. Se os mesmos elencos já estiverem instalados, a operação é dispensada. Para restaurar um backup antigo, use o instalador que o criou.

A edição 2026.4.0 não modifica o executável do jogo, seu ano inicial, BRA.cfg ou saves. Não adiciona ligas internacionais à engine. Atributos de parte dos jogadores continuam estimados, e temporadas completas não foram homologadas.

## Operação e compilação

A edição central fica em `config/edition.json` (`PATCH_YEAR`, nome, versão e plataformas).

```sh
python -m tools.daily_update
python tools/build_distribution.py --bundle windows-installer/bundled_release --output dist/2026.4.0 --snapshot data/private/daily/snapshot.json
python tools/publish_distribution.py --directory dist/2026.4.0 --notes docs/releases/v2026.4.0.md
python tools/publish_pages.py
```

O build requer Go 1.25 e Python 3.12. Coleta: 06:00 Brasília no agendador local já instalado; 06:20 no GitHub Actions. O workflow de distribuição publica quando a edição muda. Nenhum desses novos comandos executa suítes de testes. Os workflows anteriores de testes foram preservados; os commits desta entrega usam `[skip ci]`.

[Estado atual](docs/current-state.md) · [Especificação integral](docs/mega-patch-specification.md) · [Cobertura por requisito](config/specification-coverage.json) · [Coleta](docs/daily-update.md) · [Distribuição](docs/platform-distribution.md) · [Gráficos](docs/graphics-pipeline.md) · [Histórico anterior](docs/audit/README-before-mega-2026.4.0.md)
