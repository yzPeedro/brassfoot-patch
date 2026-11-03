# Manutenção diária

O projeto tem um ciclo automático executado todos os dias às 18h (horário de Brasília) que pesquisa os elencos, compila as mudanças, publica uma nova versão quando há alterações materiais e atualiza o site.

## Escopo

- Todos os clubes do patch (atualmente 704), não apenas os que já têm fonte completa.
- Para cada clube é registrada uma situação: consultado com ou sem mudanças, fonte parcial, fonte indisponível ou identificação pendente.
- O mapeamento de fontes confiáveis é ampliado continuamente em `config/live-roster-team-map.json`.

## Etapas

1. **Estado publicado.** Ler `config/edition.json`, os manifestos de `site/data/` e a última release para partir da versão realmente publicada.
2. **Coleta.** Consultar as fontes com dados novos (`tools/collect_live_rosters.py --refresh`), registrando URL, data da consulta e procedência. Falhas de fonte preservam o último dado confiável e ficam registradas.
3. **Comparação.** Comparar o conteúdo normalizado com a versão publicada. Mudanças apenas de data de consulta, ordenação ou metadados não geram release.
4. **Compilação.** Gerar os arquivos de equipe com `tools/compile_live_rosters.py`, usando a data de referência corrente e a última release como base de preservação.
5. **Release.** Havendo mudança material, incrementar a versão, gerar bundle e pacotes e publicar como descrito em [Release e publicação](release.md). O executável publicado mais recente, com o campo animado, é sempre a base das versões seguintes.
6. **Site.** Atualizar dados, contagens, notas de versão (`site/data/patch-notes.json`) e publicar no GitHub Pages. A tabela de clubes sai de `python -m tools.world.site_export`, que junta o relatório diário com os clubes do Super Update.

Os usuários recebem a release diária pelo hub: ao virar `latest`, o `release.json` publicado passa a ser lido por todos os hubs, que mostram o aviso de nova versão com as notas de `docs/releases/v<versão>.md`. Por isso as notas precisam estar corretas antes da publicação. A rotina não sobe a versão do hub (`config/hub.json`); ela só muda quando o código do hub muda, fora da rotina.

## Regras de dados

- Rumores não são transferências confirmadas.
- Um elenco maior não é, por si só, mais recente; ausência de um jogador em uma resposta incompleta não significa saída do clube.
- Laterais permanecem laterais e pontas são tratados como atacantes; o campo de lado do jogador não indica o pé dominante.
- Nomes com três ou mais palavras usam as duas primeiras.
- O site não anuncia cobertura total sem comprovação e registra separadamente a última consulta e a última mudança efetiva.

## Ano da edição

O ano corrente é obtido no fuso de Brasília em toda execução. Na virada de ano, a edição, os textos, os metadados do site e os ajustes do executável são atualizados de forma reproduzível; anos históricos (temporadas, registros, nascimentos e notas antigas) permanecem como estão.

## Registro e recuperação

Cada execução grava um checkpoint local em `data/private/scheduled-maintenance/<data>/` com clubes consultados, fontes, diferenças, lacunas, versão, commit e etapas concluídas, sem segredos. Em falha parcial, a release pública válida é preservada e os envios ou a publicação pendentes são retomados antes de qualquer nova versão.
