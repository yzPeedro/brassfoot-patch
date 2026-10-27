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
