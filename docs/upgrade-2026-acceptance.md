# Upgrade 2026: matriz CAN01–CAN40 (novo escopo)

Os statuses abaixo distinguem trabalho entregue em código de validação real. A release v2026.0.2 permanece limitada aos elencos experimentais de 20 clubes da Série A.

| Critérios | Estado | Evidência / bloqueio |
|---|---|---|
| CAN01–CAN06 (clubes e divisões oficiais) | **catalogado** | 156 IDs distintos, 20/20/20/96 por CBF, grupos A1–A16; testar no jogo ainda pendente |
| CAN07–CAN08 (compatibilidade das divisões) | **CAN07 estrutural demonstrado; CAN08 pendente** | BRA.cfg possui configurações explícitas A/B/C/D (20/20/20/64); 27/27 roundtrips exatos. Série D 96/16 apenas serialização laboratorial, jogabilidade e participantes não comprovados. |
| CAN09–CAN18 (escudos/uniformes/pipeline) | **parcial** | Auditor somente-leitura criado; imagens/direitos/temporada e integração não validados |
| CAN19–CAN20 (web first/API last) | **parcial** | Catálogo oficial obtido sem API, mas coleta de jogadores adicional não implantada |
| CAN21–CAN22 (quota global, concorrência) | **parcial** | SQLite protege no mesmo banco: 90 por dia e rolling 24h; coordenação entre hosts e saldo global desconhecidos |
| CAN23 (retomada em vários dias) | **pendente** | Coletor antigo tem cache, pipeline de 156 clubes não está pronto |
| CAN24 (testes offline) | **implementado, execução pendente** | Testes Python e Node criados sem chamadas ao provedor |
| CAN25–CAN27 (instalação e saves) | **implementado parcialmente; jogo pendente** | Go schema 3 cria/substitui arquivos e permite desfazer com backup; testes sintéticos (1, 156) e integração com os 20 originais passaram. Faltam IDs/arquivos de 136 clubes e teste no Brasfoot. |
| CAN28–CAN29 (4 divisões, busca no site) | **implementado, navegador pendente** | Cards, filtros e pesquisa por nome/UF vinculados ao JSON oficial |
| CAN30–CAN31 (assets e cobertura real) | **parcial** | Não exibe imagens não aprovadas; mostra 156 do catálogo e 20 da release |
| CAN32 (download) | **preservado** | Não altera o link nem o checksum da v2026.0.2 |
| CAN33–CAN34 (manifest/commits) | **parcial** | Catálogo oficial e site separados do manifest do instalador vigente |
| CAN35 (execução de testes) | **parcial** | `go test -race` passou na cópia local incluindo 20 originais e casos v3; smoke test local de quota passou. Execução integral das suítes Python/Node do checkout atual ainda necessária. |
| CAN36 (automações quota) | **pendente** | Workflows não ligados ao ledger global |
| CAN37 (documentação) | **em andamento** | Atualizações das divisões, quota, assets e progresso |
| CAN38 (sem segredos distribuídos) | **inspeção parcial** | Nenhuma chave incluída no novo catálogo/código; auditoria histórica necessária |
| CAN39 (procedência/direitos assets) | **pendente** | Fontes e licenças ainda não aprovadas |
| CAN40 (validação representativa final) | **bloqueado** | Novo patch 156 clubes não foi gerado nem testado no Brasfoot |

**Gate de release:** não publicar novo instalador até resolver compatibilidade, integração real, direitos das imagens e validação no Windows.
