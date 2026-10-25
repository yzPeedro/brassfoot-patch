# Publicação do site — 25/10/2026

## Estado efetivamente publicado

- URL: https://yzpeedro.github.io/brassfoot-patch/
- Branch de Pages: `gh-pages` (raiz), sincronizada com `main/site/`.
- Commit do deploy: `3675c5f382b42bb65bbd12d9d375235f7f0fc5e4`.
- GitHub Pages build: https://github.com/yzPeedro/brassfoot-patch/actions/runs/40226645585 — **completed / success**; head SHA coincide com o commit publicado.
- Os oito arquivos HTML/CSS/JS/JSON principais foram comparados por conteúdo entre `main/site/` e `gh-pages/`: **8/8 idênticos**.
- Testes estáticos do conteúdo remoto: **14 verificações aprovadas**; testes completos em navegador ainda não executados neste ambiente.

## Download disponível

- Release: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.0.2
- Executável: `Brassfoot-Patch-2026-Setup.exe`, 2.799.616 bytes.
- SHA-256: `a20885eeb164e9952266da91d575103b6fc784e49e6ce031f81ed9bdd8812b00`, confirmado com o digest da API GitHub Releases.
- `data/release.json` agora reflete a publicação já realizada (`status=published`). O navegador somente habilita o botão de download após confirmar tag, nome, URL, tamanho e SHA-256 do asset público; existe link alternativo para a release em caso de indisponibilidade da API.

## Dados públicos de cobertura

Os valores publicados em `data/coverage-2026.json` são agregados, derivados da inspeção privada de **703 equipes**, sem divulgar arquivos do jogo nem identificadores internos:

| Divisão | Catálogo oficial | Correspondências resolvidas | Candidatas | Sem arquivo | Elencos publicados |
|---|---:|---:|---:|---:|---:|
| A | 20 | 18 | 2 | 0 | 20 |
| B | 20 | 18 | 2 | 0 | 0 |
| C | 20 | 18 | 1 | 1 | 0 |
| D | 96 | 49 | 2 | 45 | 0 |
| **Total** | **156** | **103** | **7** | **46** | **20** |

**Importante:** correspondência de arquivo histórico NÃO significa elenco atualizado, jogabilidade comprovada nem divisão instalada. A Série D 96/16 só passou em teste de serialização e transação de laboratório, não no jogo.

## Garantias e limitações

- Nenhuma nova release de 156 clubes foi criada.
- Não houve substituição do executável v2026.0.2.
- Um motor Go v3 de QA foi compilado e aprovado em testes de cópia isolada, mas **não foi executado interativamente no Windows**; portanto não pode substituir a release pública.
- Os elementos gráficos da expansão continuam sem direitos e compatibilidade comprovados.
- API-Football: **zero chamadas** durante esta publicação.
- Para este agente, a leitura direta via navegador do endereço Pages retornou indisponibilidade na ferramenta; o build bem-sucedido do GitHub Pages e os arquivos remotos sincronizados são as evidências objetivas do deploy, não prova de execução visual no navegador.
