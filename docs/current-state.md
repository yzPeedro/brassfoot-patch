# Estado do Brasfoot Mega Patch — 28/10/2026

## Entrega corretiva 2026.4.1

Release final. Instalador único com 398 receitas (397 equipes e executável), bases original/V4/3.5/4.0 identificadas por SHA-256, menu inicial 2026 e seletor 2026. Nenhum arquivo de `C:/Brasfoot22-23` foi alterado durante a produção.

Coleta de plantéis em `tools/collect_live_rosters.py`, snapshots rastreados em `config/rosters-2026.4.1.json` e `config/live-rosters-supplement.json`. Compilador batch em `tools/compile_live_rosters.py`, codificação original Java em `src/app/Main.java`. Mapa de países extraído do enum original e registrado em `config/brasfoot-country-names.json`.

301 plantéis completos substituídos (60 Brasil, 241 Europa), 8.672 jogadores importados, 1.320 laterais, 1.221 pontas como atacantes, 2.584 lados observados. 54 fontes parciais preservaram o plantel anterior e produziram 82 correções pontuais. A regra de nomes com até duas palavras alcança os 704 clubes, incluindo a lista secundária.

O campo `i` é lado, não há pé dominante separado no formato. 5.388 atletas novos usam pares de características derivados da função; não afirmar verificação individual de atributos. O relatório público identifica os clubes preservados. Não afirmar que todos os clubes europeus foram atualizados.

Site interativo com animações, iluminação seguindo o mouse e botão Baixar com seta. `release.json` e `distribution.json` passam a apontar para a mesma release final. Os cinco aliases `releases/latest/download/Brasfoot-Mega-Patch-*` impedem que a página encaminhe o usuário para a base antiga.

Nenhum teste foi executado. Foram realizadas leitura de código, coleta produtiva, geração de arquivos, compilação e conferência de integridade de pacotes. A publicação final foi solicitada explicitamente pelo proprietário, independentemente de homologação de gameplay. Histórico preservado em `docs/audit/state-before-mega-2026.4.1.md`.

## Operação

`tools/build_release_bundle.py` constrói receitas de múltiplas bases; `tools/build_distribution.py` compila cinco plataformas; `tools/publish_distribution.py` publica final/latest com aliases e metadados; `tools/publish_pages.py` publica o site após os assets.

A tarefa local diária de dados existente permanece ativa. Ela coleta o catálogo; a coleta de plantéis também está implementada, mas sua publicação não é automaticamente atribuída ao agendamento do catálogo. Não confundir catálogo com plantéis instalados.

A especificação integral ainda tem requisitos de expansão da engine e cobertura mundial pendentes; esta entrega trata os dez pontos da correção solicitada.
