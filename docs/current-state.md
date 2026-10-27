# Estado do Brasfoot Mega Patch

## 2026-10-27 — regressão Java CI corrigida

- Corrigidos os testes sintéticos Java para executar o runtime ao lado do `javac`, usando `java.exe` apenas no Windows e `java` nos demais sistemas. Isso removeu a dependência acidental do Java 8 em Windows e o caminho inválido `java.exe` em runners Linux.
- Validação local: 178 testes Python passaram, incluindo os seis testes Java sintéticos afetados; testes Node do site, `go test ./...`, `go vet ./...` e `git diff --check` passaram.
- Commit/push: `c53077e` em `main`. Os workflows `Unified release readiness gate` e `Research official Brasfoot 22-23 year selector` passaram no GitHub Actions.
- Esta correção melhora a portabilidade dos gates; não acrescenta evidência de jogabilidade, compatibilidade de saves, macOS/Linux funcional ou direitos de redistribuição.

## 2026-10-26 — infraestrutura de continuidade em implementação

Prioridade: instalar e comprovar retomada independente da conversa antes de expandir produto.

- Base Git: `33505c2`, main, remoto `https://github.com/yzPeedro/brassfoot-patch`.
- Release consultada via GitHub CLI: `v2026.3.5`, publicada em 2026-10-26T22:18:17Z. Manifesto local declara edição **experimental**, gameplay não verificado e elencos B/C experimentais. Não promover para estável por inferência.
- Site: `https://yzpeedro.github.io/brassfoot-patch/`. Manifesto local aponta 2026.3.5, instalador de 5.419.520 bytes, SHA-256 `eb546eec17a6e7e20ffb65a32078bccfdea2e2b7f62f429688e698d5a458e45d`.
- Scripts antigos de ciclo/publicação existem; nenhum agendamento Brasfoot/Alethe foi encontrado na inspeção inicial. O ciclo antigo exige árvore limpa, candidato comprovado e preserva a release se não há candidato.
- Python 3.12 e Codex CLI autenticado disponíveis. Alethe perfil savings já configurado, até dois workers. Claude instalado sem login, portanto não utilizado.
- Alteração preexistente do usuário: `.gitignore` ignora `PROMPT.md`. Preservada; especificação integral copiada para `docs/mega-patch-specification.md` com SHA-256.

## Próximas entregas

`world-catalog-contract`, `incremental-snapshot` e `daily-sources` estão concluídos no backlog com checks locais e sem chamadas de rede. O próximo trabalho deve ser escolhido entre os domínios restantes, preservando os gates fail-closed e sem repetir auditorias concluídas.

O commit `7f05b2c` foi enviado para `main` após os gates locais. A consulta read-only ao GitHub confirmou como `success` os workflows `Unified release readiness gate` e `Research official Brasfoot 22-23 year selector` no commit de código `c53077e`; isso não altera os bloqueios de gameplay, saves, licenças ou plataformas ainda sem evidência.

## Bloqueadores conhecidos de produto

- Gameplay/calendário/temporadas e saves não comprovados integralmente para o candidato atual.
- Dados esportivos experimentais não equivalem a plantéis integralmente verificados.
- macOS/Linux sem validação funcional demonstrada.
- Fontes e direitos de redistribuição precisam de evidência por recurso; nenhuma coleta mundial está comprovada.
- A publicação automática só poderá promover builds que satisfaçam seus gates técnicos. A automação não deve transformar ausência de evidência em aprovação.
- Contrato de rastreabilidade offline adicionado em `tools/release_traceability.py` e publicado no commit `e9cf0e8`; a release `v2026.3.5` permanece inalterada porque não há snapshot verificável para preencher retroativamente.
- Go 1.25.4 instalado pelo Scoop para os gates do instalador; `go test ./...` e `go vet ./...` passaram em 2026-10-27.

## Checkpoint operacional 19:38 Bras?lia
Agendador instalado e smoke/reentrada comprovados (docs/continuity.md). Su?te: 153 testes passaram, 3 skips, com Java/Javac 17 alinhados. Tr?s testes Node passaram. Worker Alethe encerrado; 163.273 tokens reportados excederam or?amento, por isso ledger bloqueia novas chamadas hoje. Pr?ximas duas tarefas persistidas; cota real ? consultada a cada tentativa. Coleta mundial di?ria e publica??o integral ainda n?o conectadas. Pr?xima valida??o necess?ria: tarefa econ?mica completa ? checks ? commit/push autom?ticos, ap?s recupera??o de cota e or?amento di?rio.

## 2026-10-27 — retomada autônoma e gates locais

- Retomada feita a partir do backlog persistente; `world-catalog-contract`, `incremental-snapshot` e `daily-sources` continuam concluídos. Nenhuma auditoria desses itens foi repetida.
- Validação local desta retomada: `python -m unittest discover -s tests -q` passou com 178 testes e 3 skips; `node site/tests/site.test.js`, `node site/tests/seo-pix.test.js` e `node site/tests/explorer-interaction.test.js` passaram; `go test ./...` e `go vet ./...` passaram em `windows-installer`; `git diff --check` passou.
- A árvore estava limpa antes deste registro. Os workflows remotos mais recentes consultados permanecem verdes para o commit de código `c53077e` (`Unified release readiness gate` e `Research official Brasfoot 22-23 year selector`).
- Este checkpoint não acrescenta evidência de gameplay, calendário, compatibilidade de saves, macOS/Linux, licenças ou direitos de redistribuição. A promoção de release continua bloqueada pelos gates reais já documentados.

## 2026-10-27 — contrato offline de histórico

- Implementado `tools/history_records.py` com IDs estáveis, separação explícita entre `historical`, `current` e `simulated`, validação fail-closed, HTTPS e confiança obrigatórios para fatos históricos e exportação JSON determinística.
- Testes sintéticos em `tests/test_history_records.py` cobrem separação, proveniência ausente, duplicatas, ordenação determinística e round-trip. Nenhum fato esportivo de produção foi inventado ou coletado.
- Validação desta etapa: 182 testes Python passaram com 3 skips; três testes Node do site, `go test ./...`, `go vet ./...` e `git diff --check` passaram.
- A onda Alethe foi tentada uma vez em perfil savings, mas o worker falhou antes de editar por ausência de `NINEROUTER_API_KEY`; a unidade pequena foi concluída diretamente e a falha operacional permanece registrada no handoff.
- Este contrato não prova resultados reais de Copa/prêmios, gameplay, calendário, saves, macOS/Linux, licenças ou publicação.
