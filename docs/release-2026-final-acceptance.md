# Release final A/B/C 2026 — matriz de aceite

Data de referência: 25/10/2026. A aprovação exige evidência do jogo Windows; um teste de unidade não substitui partidas reais.

| Entrega | Evidência | Status |
|---|---|---|
| Série A | 20 clubes; prévia v2026.0.2 com 730 nomes; atributos esportivos estimados | Prévia A disponível, sem confirmação plena de 2026 |
| Série B | 20 clubes; elencos pesquisados com nomes e posições atribuídas na fonte | Dados pesquisados, arquivos novos não homologados |
| Série C | 20 clubes; elencos pesquisados com nomes e posições atribuídas na fonte | Dados pesquisados, arquivo Maranhão ainda inexistente |
| Dados B/C | 40 listas, 1.296 nomes com papéis 0..4, link de fonte por time | Pesquisa online; NÃO instalada |
| Série D | Sem modificações neste pipeline; proibição de edição de BRA.cfg e times exclusivos D | Código e fixtures cobertos; gameplay D ainda não testado |
| Ano inicial 2026 | Classe da versão oficial 2022/2023 experimental muda UI e método do motor | Laboratório aprovado; executável do usuário 2023/2024 não homologado |
| Seleção de divisão e calendário | Catálogo 20/20/20; ligação real das listas às ligas não identificada | Não aprovado |
| Iniciar carreira 2026 | Sem prova de rodadas, saves, promoção/rebaixamento e transição a 2027 | Não aprovado |
| Instalador | Motor Go testado com rollback, crossbuild Windows em CI | Teste gráfico Windows pendente |
| Website | Tabela, busca, filtro, paginação, ordenação, agrupamento, modal com posições e fontes | Publicado para pesquisa, não como release completa |
| Build/testes | CI unificado Python, Go, Java e site (4 jobs) | Passou após correções |
| Nova release de 60 clubes | Não há instalador homologado com A/B/C e 2026 único | NÃO PUBLICADA |

## Gates para liberar nova versão

1. Resolver transferências, homônimos, posições genéricas e identidade de 2026 para os 40 clubes. Habilidades estimadas devem ser marcadas; não inventar biografias.
2. Recriar os 39 arquivos B/C originais com hash e criar Maranhão por operação de inclusão comprovada; manter a Série D intacta.
3. Identificar a versão real do executável do usuário (seletor 2023/2024), e nunca reutilizar offsets do oficial 2022/2023.
4. Ligar os 60 clubes às ligas nacionais, estaduais, calendário e acessos/rebaixamentos de 2026.
5. Fazer testes reais de carreira nova 2026 nas três divisões, partidas, transição 2027, saves, D e desfazer, em Windows.
6. Só então gerar nova tag, binário, SHA-256, changelog e publicar site e download verificados.

A v2026.1.1 anterior que alterou a Série D é experimental e não satisfaz estes requisitos. A v2026.0.2 é a referência para os 730 atletas A comprovadamente embutidos.
