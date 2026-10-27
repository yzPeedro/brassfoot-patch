# Coleta diária do catálogo

`python -m tools.daily_update` executa coleta real por HTTPS, normalização, snapshot incremental e materialização SQLite. `--offline` usa somente caches existentes e os dados brasileiros já versionados. A execução não modifica `.ban`, saves, instaladores ou o manifesto da release.

O catálogo inicial combina os 156 clubes brasileiros documentados pela CBF e 1.296 observações de nomes/posições B/C já presentes no repositório com oito feeds europeus da temporada 2026–27 do [OpenFootball](https://github.com/openfootball/football.json). O provedor publica os dados sob [CC0](https://github.com/openfootball/football.json/blob/master/LICENSE.md), sem chave de API. São dados comunitários, não uma certificação das federações. Cada feed pode estar incompleto ou atrasado; o timestamp de consulta não é a data de atualização esportiva na origem.

As fontes são explícitas em `config/sources.json`, com identidade de competição separada da temporada. Os IDs de clube dependem do país e nome normalizado, não da divisão. `clubAliases` permite reconciliar uma alteração de nome sem trocar a identidade. Homônimos e renomeações que não possam ser resolvidos exigem reconciliação; nomes de jogadores sem identificador oficial permanecem `roster_observation`, sem inventar identidades globais, transferências, datas de nascimento ou atributos. Esta coleta de partidas não renova automaticamente as observações de elencos B/C de 25/10/2026.

## Execução e recuperação

- Até 25 fontes, 2 MB por resposta, 20 segundos por requisição e duas tentativas por fonte. O host e caminho são restritos ao projeto público configurado; sem cookies, proxies, autenticação ou redirects.
- `ETag` e `Last-Modified` evitam baixar respostas inalteradas. HTTP 429 persiste `Retry-After` e aguarda a próxima execução elegível; não troca de host ou identidade para contornar limites.
- Respostas vazias, JSON inválido e mudanças incompatíveis de esquema não substituem o cache anterior. Falhas são publicadas separadamente da data do último conteúdo recebido.
- Cache e snapshot são substituídos atomicamente após `fsync`. SQLite usa uma transação, inclusive para os métodos públicos de `WorldCatalog`; savepoints permitem transações aninhadas. Identificadores de tabela aceitos são enumerados.
- Um bloqueio do sistema operacional impede execuções concorrentes no mesmo diretório e é liberado mesmo após encerramento abrupto. `journal.jsonl` registra alteração, quantidade de requisições e falhas. Reexecução reaplica upserts idempotentes.

Estado local: `data/private/daily/{cache,snapshot.json,catalog.sqlite,journal.jsonl}`. O JSON público `site/data/world-status.json` informa cobertura, origem, licença, status de cada fonte, hashes e limites conhecidos. Não publica a base SQLite e não anuncia competições jogáveis. Falhas parciais preservam os últimos dados e aparecem como `partial`; não se confundem com atualização completa.

O workflow `Daily public football catalog` executa diariamente às **06:20 de Brasília** (09:20 UTC), restaura/preserva o cache entre execuções, publica o resumo em `main` e `gh-pages` e solicita o build estático do Pages. Ele também pode ser iniciado manualmente. Não contém execução de testes. O cache do GitHub pode ser removido por expiração/limite; nesse caso, os dados voltam a ser coletados, sem usar o resumo público como fonte esportiva.

Esta etapa não entrega cobertura mundial integral, atualização global de jogadores, validação funcional das ligas, nem promoção automática de release do jogo. Nenhum teste foi executado na implementação por instrução explícita do mantenedor.
