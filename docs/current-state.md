# Estado do Brasfoot Mega Patch — 27/10/2026

## Entrega 2026.4.0

Implementação: site reconstruído, identidade azul, atualização Windows renovada, utilitários Linux/macOS, cinco pacotes, 60 receitas restauradas, coleta HTTPS real, catálogo e snapshots, pipeline de gráficos, edição central e publicação rastreável. Ver notas em `docs/releases/v2026.4.0.md`.

Validação: **nenhum teste executado nesta entrega por pedido explícito do mantenedor**. Somente leitura/revisão de código, execução produtiva da coleta, compilação dos artefatos e cálculo de hashes. Não reaproveitar a aprovação dos testes de commits antigos para estes arquivos.

Operação: coletor produtivo registrou oito fontes sem falha, 312 clubes, 12 competições, oito países/territórios, 2.916 partidas e 1.296 observações de elencos. O serviço local já instalado ganhou `dailyCommand` de coleta privada; workflow diário publica cobertura às 06:20 Brasília. `distribution.yml` constrói/publica pré-releases ao mudar a edição. Os agendamentos novos não foram exercitados como testes.

## Decisões e origem

- `config/edition.json` é a edição do produto e orienta o build.
- `windows-installer/bundled_release` contém as receitas efetivamente distribuídas pela 2026.3.5, agora versionadas como atualizador 2026.4.0. Origem e hashes: `config/payload-provenance.json`. Não há jogo proprietário incorporado.
- A base histórica de 20 clubes foi preservada em `tools/baselines/2026.0.2` para os geradores antigos.
- `site/data/release.json` continua identificando a base V4 de instalação inicial; `site/data/distribution.json` descreve os novos atualizadores e só é gerado após publicação dos assets.
- A edição 2026.4.0 preserva os elencos existentes. Não altera ano, divisões, executável, BRA.cfg ou saves.
- O processo Windows agora exclui o PID do instalador e reconhece nomes reais do jogo.
- Alethe registrou a orquestração; delegação executada pelos agentes disponíveis, em dois worktrees, devido aos erros de credencial de CLI já documentados e telemetria desatualizada. Nenhuma credencial foi contornada ou substituída.

## Próximos trabalhos reais

O status por seção da especificação está em `config/specification-coverage.json`. Cobertura mundial de jogadores/treinadores, seleções, Copa/prêmios em produção, expansão da engine, fontes tipográficas dentro do jogo, acervo oficial autorizado e migração de saves continuam incompletos. Linux/macOS não foram executados. O site não deve anunciar esses objetivos como já entregues.

O histórico anterior foi preservado em `docs/audit/state-before-mega-2026.4.0.md`. Não repetir auditorias concluídas nem marcar toda a especificação como completa pela existência de contratos de dados.
