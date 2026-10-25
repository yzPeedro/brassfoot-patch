# Estado observado — 2026-10-25

- Dados: sincronização real no Windows confirmou 20 clubes, 745 jogadores e zero falhas de API. Snapshot privado não foi commitado.
- Reconciliador: correção do Atlético-MG ID 1062 aprovada no Windows; testes completos do hotfix v5.0.4 executados (52 aprovados, 3 ignorados).
- Gerador `.ban`: serialização e roundtrip locais testados; atletas novos ainda herdam atributos estimados e IDs internos zerados. **Não adequado para publicação.**
- Instalador: novo motor offline com backup, SHA-256, restrições de caminho, idempotência, rollback e 11 testes sintéticos do motor aprovados, interface gráfica Tk implementada e smoke test de abertura/navegação no Linux/Xvfb aprovado. **Sem teste gráfico no Windows nem compilação Windows.**
- Site: publicado por branch `gh-pages` com release em desenvolvimento e botão de download desabilitado. Nova seção de instalação diferencia funcionalidades em código das já publicadas.
- GitHub: source `main` e branch `gh-pages` públicas. Workflows personalizados em `workflow_dispatch` para economizar cota; GitHub Pages usa mecanismo interno de publicação.
- Distribuição: **nenhum instalador .exe foi validado e nenhuma release foi criada**. `release.ps1` bloqueia builds sem pacote previamente marcado e evidenciado como validado no jogo; `-Publish` permanece bloqueado até testes independentes.
- Direitos: arquivos originais do Brasfoot e dados proprietários não são distribuídos pelo repositório.

**Validação conjunta:** 65 testes Python executados em ambiente isolado (62 aprovados, 3 ignorados), além dos testes estáticos do site. **Bloqueador da primeira release:** criar arquivos .ban com atributos e identificadores corretos, testar no Brasfoot real, construir e executar o instalador no Windows. Não marcar requisitos não testados como aprovados.
