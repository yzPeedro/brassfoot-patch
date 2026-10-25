# Progresso atual — Brasfoot Patch 2026

## Implementação do motor Go v3 — 25/10/2026

- **Release existente:** v2026.0.2 publicada e aprovada pelo usuário em teste no Brasfoot; contém 20 clubes da Série A, 730 jogadores com limitações relatadas. Não foi substituída nesta execução.
- **Catálogo:** 156 clubes distintos nos dados oficiais (20 A, 20 B, 20 C, 96 D) e explorador de clubes publicado; 136 clubes adicionais ainda não estão no instalador.
- **Motor Go:** manifesto v3 com `operation: add` / `replace`; suporte a quantidades de 1 a 512; empacotador sem limite hardcoded de 20; validação de operações, caminhos, hashes, destinos existentes e duplicações. Mantido v2 para compatibilidade com a release atual.
- **Transações:** inclusão de novas equipes com criação exclusiva; backup para substituições; rollback de inclusões sem apagar arquivos modificados externamente; desfazer somente o que a transação instalou, preservando arquivos já modificados antes dela.
- **Testes reais executados localmente:** `go test -race -count=1 ./...` passou, incluindo 20 originais privados da release, testes sintéticos de 1 e 156 equipes, adição, restauração, colisões, idempotência, saves e rollback. O comando foi executado no motor Go reconstruído localmente a partir do código-fonte da release e evoluído nesta execução. **É necessária uma execução final dos testes após `git pull` na árvore atual do GitHub.**
- **Build:** compilação cruzada Go para Windows amd64 concluída; **não houve execução interativa em Windows nem prova de jogabilidade das novas 136 equipes**.
- **Quota:** ledger SQLite local ganhou proteção de janela móvel de 24h para evitar surtos no reset UTC; smoke tests locais de concorrência, persitência, teto 90 e transição de dia passaram. Não há prova de coordenação de múltiplos hosts externos.
- **Evidências e insumos:** o upload privado anterior possui apenas 20 `.ban`; criado `scripts/collect-game-structure.ps1` para coletar de forma privada arquivos de equipes e competições sem copiar saves/executáveis. Precisa ser executado em uma instalação real com os 703 clubes antes do mapeamento confiável de 156 IDs e competições.
- **Escudos/uniformes:** pipeline de inventário somente leitura já existe; não há aprovação de direitos/formato para redistribuição de novos assets.
- **Publicação:** código atualizado em `main`. **Nenhuma release de 156 clubes foi criada**, e não se alterou o arquivo publicado v2026.0.2 nem o hash do seu download.

## Histórico anterior (mantido como registro; não representa o estado atual)


- Dados: sincronização real no Windows confirmou 20 clubes, 745 jogadores e zero falhas de API. Snapshot privado não foi commitado.
- Reconciliador: correção do Atlético-MG ID 1062 aprovada no Windows; testes completos do hotfix v5.0.4 executados (52 aprovados, 3 ignorados).
- Gerador `.ban`: serialização e roundtrip locais testados; atletas novos ainda herdam atributos estimados e IDs internos zerados. **Não adequado para publicação.**
- Instalador: motor offline com backup, SHA-256, restrições de caminho, idempotência, rollback e 11 testes sintéticos do motor aprovados; interface Tk implementada e smoke test Linux/Xvfb aprovado. Em 25/10/2026, usuário apresentou evidência visual de **outro executável experimental para Windows**, cujo teste offline reportou backup, cópia, hashes, rollback e localização da pasta do jogo aprovados. **Essa evidência não valida o instalador real do repositório, a compilação definitiva nem a instalação de elencos no Brasfoot.**
- Site: `main/site/` e raiz da branch `gh-pages` sincronizadas; em 25/10/2026 foram removidos o elemento `.ball` e seus estilos/animação, mantendo campo e varredura. Página informa resultado do protótipo offline. Release permanece em desenvolvimento com botão desabilitado. A propagação pública em GitHub Pages não foi confirmada por consulta HTTP nesta execução.
- GitHub: source `main` e branch `gh-pages` públicas. Workflows personalizados em `workflow_dispatch` para economizar cota; GitHub Pages usa mecanismo interno de publicação.
- Distribuição: **nenhum instalador .exe com patch real foi validado e nenhuma release foi criada**. `release.ps1` bloqueia builds sem pacote previamente marcado e evidenciado como validado no jogo; `-Publish` permanece bloqueado até testes independentes.
- Direitos: arquivos originais do Brasfoot e dados proprietários não são distribuídos pelo repositório.

**Validação conjunta:** 65 testes Python executados em ambiente isolado (62 aprovados, 3 ignorados), além dos testes estáticos do site. **Bloqueador da primeira release:** criar arquivos .ban com atributos e identificadores corretos, testar no Brasfoot real, construir e executar o instalador no Windows. Não marcar requisitos não testados como aprovados.


## Expansão 156 clubes — atualização em 25/10/2026

- Catálogo CBF: **156 clubes únicos**, Séries A/B/C/D = **20/20/20/96**, Série D em 16 grupos A1–A16. IDs estáveis com UF. Fontes em `docs/divisions-2026.md`.
- Site: filtro por Série A/B/C/D, pesquisa de clube ou UF e cards com totais extraídos do catálogo; texto diferencia catálogo oficial de instalação real. Alterações em `main/site/` e `gh-pages/`.
- API: **0 chamadas API-Football nesta execução**. Novo `quota_guard.py` com ledger SQLite local conservador, integrado às tentativas de rede de `api_football_sync.py`. Coordenação multi-host e saldo externo não comprovados.
- Assets: criado `assets_audit.py` para inspecionar escudos e camisas em modo leitura, sem redistribuir materiais de terceiros. Nenhuma imagem da expansão aprovada ou instalada ainda.
- Testes: arquivos novos `tests/test_competitions_2026.py`, `tests/test_quota_guard.py`, `tests/test_assets_audit.py` e verificações estáticas do site. **Execução das novas suítes pendente** neste ambiente.
- Instalação: **não modificada**. A v2026.0.2 permanece como única release jogável experimental, com elencos de 20 clubes. Divisões B/C/D, escudos e uniformes novos ainda não instalados nem verificados no jogo.
- Documentos: `docs/api-usage-report.md`, `docs/assets-coverage.md`, `docs/divisions-2026.md`, `docs/upgrade-2026-acceptance.md`.
- Gate: não publicar nova release até obter dados confiáveis, rights clearance, compatibilidade de arquivos e teste no Brasfoot Windows.

- Auditoria de publicação: HTML, CSS, JS e catálogo das branches `main`/`gh-pages` conferidos com equivalência exata; 156 IDs únicos, contagem 20/20/20/96 e 16 grupos Série D de seis equipes confirmados em inspeção estrutural. JavaScript do explorador, app e testes passou em validação sintática.
- Regressão do instalador legado: `go test ./...` passou no código-fonte da release v2026.0.2 extraído do kit anterior; compilação cruzada GOOS=windows/GOARCH=amd64 passou. **Não é teste da expansão e não substitui execução dos testes Python recém-adicionados.**
