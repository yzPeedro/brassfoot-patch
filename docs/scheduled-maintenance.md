# Manutenção diária

O projeto tem um ciclo automático executado todos os dias às 18h (horário de Brasília) que pesquisa os elencos, compila as mudanças, publica uma nova versão quando há alterações materiais e atualiza o site.

## Escopo

- Todos os clubes do patch (957 desde a 2026.6.0), não apenas os que já têm fonte completa.
- Para cada clube é registrada uma situação: consultado com ou sem mudanças, fonte parcial, fonte indisponível ou identificação pendente.
- O mapeamento de fontes confiáveis é ampliado continuamente em `config/live-roster-team-map.json`.

## Etapas

1. **Estado publicado.** Ler `config/edition.json`, os manifestos de `site/data/` e a última release para partir da versão realmente publicada.
2. **Coleta.** Consultar as fontes com dados novos (`tools/collect_live_rosters.py --refresh`), registrando URL, data da consulta e procedência. Falhas de fonte preservam o último dado confiável e ficam registradas.
3. **Aprovação e compilação.** `python -m tools.roster_approval` compila o candidato com `tools/compile_live_rosters.py`, decide clube a clube e recompila só com os aceitos (ver [Aprovação por clube](#aprovação-por-clube)). Mudanças apenas de data de consulta, ordenação ou metadados não geram release.
4. **Preparação.** `python -m tools.daily_release prepare` sobe a versão, monta o pacote na ordem de [Release e publicação](release.md) com herança do pacote anterior, exporta os dados do site, regenera as imagens, escreve as notas a partir das mudanças que estão nos `.ban` e acrescenta as entradas e saídas a `config/roster-facts-2026.json`. O executável publicado mais recente, com o campo animado, é sempre a base das versões seguintes.
5. **Regressão.** `python -m tools.regression_suite` roda as suítes do repositório, a decodificação de todos os `.ban`, as conferências do pacote, a matriz de instalação e remoção pelo `hubcli` (origens: original, release anterior completa, só patch, só campo, um componente só e gerações antigas), saves, renderização do campo e dados do site, e grava um veredito. Só `pass` libera a publicação.
6. **Release.** `python -m tools.daily_release publish` exige o veredito `pass` do mesmo candidato e faz, em ordem, commit, release, manifestos, Pages, conferência pós-publicação e a base nova no `AGENTS.md`. Rodar de novo retoma uma publicação interrompida.
7. **Site.** Atualizar dados, contagens, notas de versão (`site/data/patch-notes.json`) e publicar no GitHub Pages. A tabela de clubes sai de `python -m tools.world.site_export`, que junta o relatório diário com os clubes do Super Update. Sem a compilação do Super Update em `data/private/super-update/build/`, use `--world-snapshot config/super-update-world-2026.json` (ver [Dados](data-pipeline.md#sem-a-compilação-do-super-update)).

Os usuários recebem a release diária pelo hub: ao virar `latest`, o `release.json` publicado passa a ser lido por todos os hubs, que mostram o aviso de nova versão com as notas de `docs/releases/v<versão>.md`. Por isso as notas precisam estar corretas antes da publicação. A rotina não sobe a versão do hub (`config/hub.json`); ela só muda quando o código do hub muda, fora da rotina.

## Regras de dados

- Rumores não são transferências confirmadas.
- Um elenco maior não é, por si só, mais recente; ausência de um jogador em uma resposta incompleta não significa saída do clube.
- Laterais permanecem laterais e pontas são tratados como atacantes; o campo de lado do jogador não indica o pé dominante.
- Nomes com três ou mais palavras usam as duas primeiras, mantendo partículas junto do sobrenome ("Matheus dos Santos", "David de Gea").
- O site não anuncia cobertura total sem comprovação e registra separadamente a última consulta e a última mudança efetiva.

## Aprovação por clube

`tools/roster_approval.py` aceita a mudança de um clube quando a coleta trouxe o elenco completo (`source-complete`) e o clube passa em todos os alarmes, comparado com o `.ban` publicado:

- perde no máximo 5 jogadores e no máximo 20% do elenco;
- tem ao menos 2 goleiros, de 16 a 40 jogadores, posições de 0 a 4 e indicadores 0 ou 1;
- nenhum jogador que já estava passa a ter atributo estimado (quem chega pode ter);
- não muda país, divisão ou nome sem fato no ledger `config/club-identity-2026.json`;
- não desfaz uma entrada ou saída publicada há menos de `holdDays` dias (90) em `config/roster-facts-2026.json`.

O clube que não passa volta ao estado publicado, com o motivo em `approval.json`; os demais seguem para a release. Clubes com fonte parcial ou sem identificação continuam preservados.

## Ano da edição

O ano corrente é obtido no fuso de Brasília em toda execução. Na virada de ano, a edição, os textos, os metadados do site e os ajustes do executável são atualizados de forma reproduzível; anos históricos (temporadas, registros, nascimentos e notas antigas) permanecem como estão.

## Registro e recuperação

Cada execução grava um checkpoint local em `data/private/scheduled-maintenance/<data>/` com clubes consultados, fontes, diferenças, lacunas, versão, commit e etapas concluídas, sem segredos. Em falha parcial, a release pública válida é preservada e os envios ou a publicação pendentes são retomados antes de qualquer nova versão.
