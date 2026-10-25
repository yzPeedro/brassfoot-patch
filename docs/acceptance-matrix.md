> **MATRIZ HISTÓRICA (anterior à v2026.0.2).** As afirmações antigas de que não existe release pública estão superadas. A versão pública v2026.0.2 existe, mas contém somente 20 equipes com atributos estimados. Consulte `docs/upgrade-2026-acceptance.md` para o novo escopo e `docs/implementation-progress.md` para evidências recentes.

# Matriz objetiva CAN01–CAN40

Critérios baseados no prompt master do projeto. `pass` = verificado no componente implementado; `partial` = implementação ou evidência insuficiente; `blocked` = depende de dado/ambiente externo; `pending` = não implementado. **Status partial não conta como aprovado.**

| Critério | Status | Evidência/pendência |
|---|---|---|
| CAN01 | partial | Algoritmo corrigido offline; nomes reais do catálogo não disponíveis |
| CAN02 | partial | Ambiguidade rejeitada nos testes |
| CAN03 | partial | Cache testado; sync real pendente |
| CAN04 | partial | Orçamento implementado, não medido no provedor |
| CAN05 | partial | Cache resumível testado; interrupção externa não testada |
| CAN06 | blocked | 20 clubes resolvidos só em fixture |
| CAN07 | partial | Validação básica sem todos os atributos |
| CAN08 | partial | Codec testado; jogo não executado |
| CAN09 | blocked | Teste no Brasfoot Windows indisponível |
| CAN10 | partial | Motor e interface GUI implementados em código; build Windows e teste no jogo pendentes |
| CAN11 | partial | Entrada de aplicativo GUI criada; .exe ainda não compilado |
| CAN12 | partial | Progresso da GUI ligado a eventos reais; teste Windows pendente |
| CAN13 | partial | Instalador CLI verifica teams/ e options.bcf |
| CAN14 | partial | Backup automático em CLI testado |
| CAN15 | partial | Rollback por falha injetada testado |
| CAN16 | partial | Testes preservam saves; Windows real pendente |
| CAN17 | pending | Autoexclusão não implementada |
| CAN18 | partial | Landing estática com estilo original; não é site público final |
| CAN19 | partial | Inspecionado em viewport desktop e mobile |
| CAN20 | partial | Redução de movimento e menu implementados; auditoria a11y pendente |
| CAN21 | blocked | Release executável não existe; botão desabilitado |
| CAN22 | partial | Manifest experimental com SHA256; sem release pública |
| CAN23 | partial | Site mostra desenvolvimento sem anunciar release |
| CAN24 | pending | Changelog automático não implementado |
| CAN25 | pending | Deploy GitHub não configurado |
| CAN26 | partial | Código e dados públicos ainda não separados em remotos |
| CAN27 | partial | Nenhuma chave literal localizada; release ausente |
| CAN28 | partial | Janelas principais verificadas, extra não confirmada |
| CAN29 | partial | Sete dias calculados e testados; sem publicação |
| CAN30 | partial | Estado completed evita recálculo local; sem releases reais |
| CAN31 | partial | Prévia bloqueada de publicar; integração real pendente |
| CAN32 | blocked | Não há release anterior |
| CAN33 | partial | 46 testes executados; cobertura parcial |
| CAN34 | partial | Workflow qualidade criado, não rodado no GitHub |
| CAN35 | partial | Documentação de arquitetura e operação criada |
| CAN36 | partial | Prévia determinística em arquivos, build em jogo não verificado |
| CAN37 | pending | Rastreabilidade release/commit não implementada |
| CAN38 | pending | Alertas no GitHub não implementados |
| CAN39 | pass | Frontend estático não possui API-Football |
| CAN40 | partial | Nenhum segredo nos arquivos locais analisados; binário GUI inexistente |


## Novo escopo de 156 clubes (2026)

Este arquivo documenta a **matriz original**. A matriz independente do upgrade Séries A/B/C/D é `docs/upgrade-2026-acceptance.md`. Não reutilize as aprovações CAN deste arquivo para afirmar que o novo escopo foi validado.
