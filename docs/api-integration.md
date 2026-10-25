# API-Football

- Endpoint base: `https://v3.football.api-sports.io`.
- Autenticação: header `x-apisports-key` lido de `API_FOOTBALL_KEY` ou DPAPI local.
- Plano Free do usuário: temporada filtrada em `/teams?league=71&season=2026` foi rejeitada com mensagem de acesso restrito.
- `/teams?country=Brazil` funciona como catálogo econômico em princípio, mas falhou na reconciliação anterior de dois clubes e não temos seu JSON real aqui.
- Fallback condicionado: `GET /teams?search=Atletico Mineiro`, `GET /teams?search=Chapecoense` se ausentes do catálogo; nomes sanitizados e correspondência exata obrigatória.
- `/players/squads?team=id` não depende de ano, mas contém elenco atual; não fornece todos os detalhes do Brasfoot.
- Cache do catálogo e pesquisas secundárias: até 30 dias; respostas diárias de elencos reutilizadas no mesmo dia.
- Limite por execução padrão: 25 tentativas de requisição (incluindo retries); ajuste com `-MaxRequests` no PowerShell.
- `-DryRun` reconcilia sem solicitar elencos; `-Offline` não aceita tráfego de rede; `-NoFallback` desliga buscas pontuais; `-Refresh` ignora cache e pode gastar chamadas.
- Quaisquer falhas são apresentadas no `mapping-report.json` sem a chave.

A documentação oficial recomenda IDs persistentes entre temporadas: https://www.api-football.com/documentation_v3
