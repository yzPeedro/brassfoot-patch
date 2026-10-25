# Auditoria inicial da versão 4.2

## Evidências disponíveis

- Base inspecionada: cópia local de `brassfoot-data-v4.2`; a pasta real Windows e seu estado Git não estão montados neste ambiente.
- `api_football_sync.py`: catálogo único de clubes brasileiros; nomes normalizados por remoção de acento/pontuação; somente aliases exatos autorizados.
- Falha trazida pelo usuário: `Catalog reconciliation failed for Atlético-MG, Chapecoense; ... No squad calls were made`.
- **Causa demonstrada no código**: se o nome retornado pelo catálogo não coincide com um nome explicitamente permitido, o sistema falha antes de buscar qualquer elenco.
- **Causa exata dos dois clubes na API**: indeterminada sem `mapping-report.json` e `teams-brazil.json` reais. O erro não prova necessariamente divergência de nome; ausência da entidade no catálogo também é possível.
- `src/app/Main.java`, `src/e/*.java`: codec Java Object Serialization para arquivos de equipes `.ban`; há filtro de classes de desserialização.
- Dados estruturados legados: catálogo SQLite de 703 clubes e manifesto de 20 participantes da Série A.
- `sync-api.ps1`: chave via `API_FOOTBALL_KEY`/DPAPI; nenhuma chave literal presente na cópia analisada.
- Não existe `git` versionado ou remoto verificável na cópia local; nenhum commit ou push realizado.

## Preservado

Codec Java, escopo de 20 clubes, manifesto de Brasfoot IDs, cache do catálogo, cache dos elencos por dia, escrita atômica JSON e testes offline.

## Corrigido/expandido

Correspondência controlada, pesquisa fallback válida, sugestões somente para diagnóstico, IDs persistentes, limite de chamadas, modo offline/dry-run, auditoria de correspondências, prévia `.ban`, instalador local com rollback, calendário conservador e site inicial.

## Pendências/riscos

1. Não há catálogo real que causou a falha em Windows; a correção de produção precisa ser reexecutada pelo usuário.
2. `players/squads` não contém todos os atributos exigidos; prévia estima dados e bloqueia publicação.
3. Validação do arquivo modificado dentro do jogo não executada.
4. Aplicativo gráfico WPF/.NET não implementado nem testado em Windows.
5. Direitos de redistribuição de assets e dados ainda não resolvidos.
6. Repositório remoto, GitHub Pages, release e automação de publicação não configurados.
