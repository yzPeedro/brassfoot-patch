# Engenharia reversa do Brasfoot 22-23

Estudo do funcionamento interno do Brasfoot 22-23 original. Ele serve de referência para o Mega Patch: em que pontos o patch pode se apoiar, o que não pode mudar sem afetar saves ou a simulação, e por que o jogo se comporta como se comporta.

## Base do estudo

- **Executável:** Brasfoot 22-23 original e limpo, SHA-256 `2fa65476a92611419ce28c0cfd158a0c7f741af235aa988b0bed00c44443bb1c`, com 1.038 classes ofuscadas e cerca de 100 mil linhas decompiladas.
- **Ferramentas:** decompilação com Vineflower 1.11.1; nos pontos em que o decompilado esconde métodos de acesso, leitura direta do bytecode com `javap` (JDK 17).
- **Estado:** tudo foi **lido no código**. Nada foi testado em jogo nem medido em partidas. O que não foi lido diretamente aparece marcado como "(inferido)", e cada documento termina com uma seção de lacunas.
- **Nomes:** os nomes de classes, campos e métodos são os ofuscados do próprio jogo, como `best.I` e `c.b.vO`. Eles só valem para este executável; outra versão do jogo pode trocá-los.
- **Conteúdo:** os documentos descrevem comportamento, campos, fórmulas e constantes com palavras, tabelas e pseudocódigo próprios. Não reproduzem código do jogo. O mecanismo de registro e licença ficou de fora de propósito.

## Documentos

| Documento | Conteúdo |
|---|---|
| [01 — Arquitetura e arquivos](01-arquitetura-e-arquivos.md) | Empacotamento, pacotes, inicialização, troca de telas, saves (Kryo), `options.bcf`, formatos `.ban`, `.cfg` e `.ces`, imagens, sons, threads e logs |
| [02 — Modelo de dados](02-modelo-de-dados.md) | Campos de jogador, time, técnico, país e carreira; força, valor, salário, lesões, evolução semanal, juniores, aposentadoria e virada de temporada |
| [03 — Motor de partida](03-motor-de-partida.md) | Ciclo da partida, gerador de lances, fórmulas de posse, ataque e chute, autores, cartões, lesões, IA do técnico, táticas, notas dos jogadores, estatísticas e tela de partida |
| [04 — Calendário e competições](04-calendario-e-competicoes.md) | Calendário anual, eventos agendados, dia de jogo, início de carreira, virada de temporada, cada tipo de competição, acesso e rebaixamento, desempates e jogos exibidos |
| [05 — Gestão e economia](05-gestao-e-economia.md) | Caixa, bilheteria, estádio, patrocínio, empréstimos, prêmios, contratos, mercado e IA de transferências, base, treino, reputação, demissão e propostas de emprego |
| [06 — Interface](06-interface.md) | Telas e diálogos (cerca de 85, com a classe de cada um), navegação, tela do clube, escalação, partida, opções, atalhos, sons e componentes |

## Glossário das classes principais

| Classe | Papel |
|---|---|
| `best.h2` | Ponto de entrada |
| `best.f` | Raiz da carreira e do mundo, acessível em `c.a.SR`; avança os dias |
| `c.a` | Estado global, save e load, sons e opções |
| `best.S` | Janela única e troca de telas (`aY(código)`) |
| `best.a` | Dia do calendário (`t()` traz os campeonatos do dia) |
| `best.s` | Monta os jogos do dia e abre a tela de partida |
| `best.at` | Competição abstrata (`b()` é o tipo, de 0 a 15) |
| `f.*` | Competições concretas: `f.B` liga nacional, `f.f` copa nacional, `f.o` estadual, `f.r` Libertadores, `f.v` Liga dos Campeões, `f.x` Liga Europa, `f.H` Sul-Americana, `f.J` Conference, `f.A` Mundial, `f.I` Supercopa, entre outras |
| `best.I` | Partida: times, escalações, lances e estatísticas |
| `c.b` | Gerador de lances (`vO`) |
| `best.A` | Lance |
| `best.F` | Jogador, inclusive a nota da partida |
| `best.ah` | Time |
| `best.al` | Técnico |
| `best.Z` | País e sua seleção |
| `best.ac` | Enum dos 224 países |
| `best.ay` | Central de empregos |
| `best.C` | Balanço financeiro |
| `best.l` | Mercado da IA |
| `best.H`, `best.k`, `best.J` | Estatística do jogador por competição, por clube e histórico de notas |
| `best.aq` | Tabelas e constantes |
| `best.M` | Textos (`arquivos/default_lang.xml`) |
| `e.t`, `e.g` | Registros de time e jogador nos arquivos `.ban` |
| `est.*` | Opções e configuração de ligas e estaduais |
| `g.b` | Troca de referências por índices no save |
| `a.*` | Telas e diálogos: `a.gq` tela inicial, `a.eg` tela do clube, `a.bz` escalação, `a.dV` partida, `a.hk` fim de rodada, `a.cR` fim de temporada, `a.fB` preferências |
| `components.*` | Componentes reutilizáveis; `components.t`, `as`, `ag` e `ah` entram no save |
| `b.*`, `h.*` | Modelos de tabela, renderizadores e comparadores |
| `d.*` | Editor de times |

## Conclusões que afetam o patch

- **Saves:** o save é Kryo sem registro de classes, com os campos ordenados por nome. Acrescentar, remover ou renomear campo de qualquer classe serializada quebra a compatibilidade dos saves. Isso inclui `best.*`, `f.*` e quatro classes de `components`. Detalhes no [01](01-arquitetura-e-arquivos.md).
- **Estatísticas da partida não são só visuais:** posse, finalizações, chutes no gol, desarmes e erros de passe saem dos mesmos sorteios que geram os lances (`c.b`). Elas entram na nota de cada jogador na partida (`best.F.a(at, I, int, int, ah)`). A nota alimenta médias, destaques da competição e a seleção da liga, e no fim da temporada o melhor jogador da seleção da 1ª divisão vira estrela, o que muda valor e salário. Faltas (`hD`) nunca são preenchidas pelo motor. Detalhes na seção de estatísticas do [03](03-motor-de-partida.md).
- **Simulação:** estilo e foco tático, gramado, clima e torcida não entram no motor, e não há prorrogação nem gol fora na prática. Detalhes no [03](03-motor-de-partida.md) e no [04](04-calendario-e-competicoes.md).
- **Força dos jogadores:** o `.ban` não guarda a força. Ela nasce na criação da carreira a partir do nível do time e de outros fatores, e o campo `hash` do `.ban` é o potencial do jogador. Detalhes no [02](02-modelo-de-dados.md).
