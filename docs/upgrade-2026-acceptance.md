# Upgrade 2026: matriz CAN01–CAN40 (novo escopo)

Os statuses abaixo distinguem trabalho entregue em código de validação real. A release v2026.0.2 permanece limitada aos elencos experimentais de 20 clubes da Série A.

| Critérios | Estado | Evidência / bloqueio |
|---|---|---|
| CAN01–CAN06 (clubes e divisões oficiais) | **catalogado** | 156 IDs distintos, 20/20/20/96 por CBF, grupos A1–A16; testar no jogo ainda pendente |
| CAN07–CAN08 (compatibilidade das divisões) | **bloqueado** | Não há prova de formato/configuração jogável B/C/D |
| CAN09–CAN18 (escudos/uniformes/pipeline) | **parcial** | Auditor somente-leitura criado; imagens/direitos/temporada e integração não validados |
| CAN19–CAN20 (web first/API last) | **parcial** | Catálogo oficial obtido sem API, mas coleta de jogadores adicional não implantada |
| CAN21–CAN22 (quota global, concorrência) | **parcial** | Teto local SQLite 90 + margem 10; coordenação entre hosts e saldo global desconhecidos |
| CAN23 (retomada em vários dias) | **pendente** | Coletor antigo tem cache, pipeline de 156 clubes não está pronto |
| CAN24 (testes offline) | **implementado, execução pendente** | Testes Python e Node criados sem chamadas ao provedor |
| CAN25–CAN27 (instalação e saves) | **bloqueado para a expansão** | Ainda só há validação de 20 clubes na v2026.0.2 |
| CAN28–CAN29 (4 divisões, busca no site) | **implementado, navegador pendente** | Cards, filtros e pesquisa por nome/UF vinculados ao JSON oficial |
| CAN30–CAN31 (assets e cobertura real) | **parcial** | Não exibe imagens não aprovadas; mostra 156 do catálogo e 20 da release |
| CAN32 (download) | **preservado** | Não altera o link nem o checksum da v2026.0.2 |
| CAN33–CAN34 (manifest/commits) | **parcial** | Catálogo oficial e site separados do manifest do instalador vigente |
| CAN35 (execução de testes) | **pendente** | Execução final de testes Python e site ainda requerida |
| CAN36 (automações quota) | **pendente** | Workflows não ligados ao ledger global |
| CAN37 (documentação) | **em andamento** | Atualizações das divisões, quota, assets e progresso |
| CAN38 (sem segredos distribuídos) | **inspeção parcial** | Nenhuma chave incluída no novo catálogo/código; auditoria histórica necessária |
| CAN39 (procedência/direitos assets) | **pendente** | Fontes e licenças ainda não aprovadas |
| CAN40 (validação representativa final) | **bloqueado** | Novo patch 156 clubes não foi gerado nem testado no Brasfoot |

**Gate de release:** não publicar novo instalador até resolver compatibilidade, integração real, direitos das imagens e validação no Windows.
