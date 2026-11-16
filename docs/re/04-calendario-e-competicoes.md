# Calendário, temporada e competições

Este estudo saiu da leitura do código decompilado do executável original (SHA-256 `2fa65476…bb1c`), feita com o Vineflower 1.11.1 a partir de `data/private/re/src/`. Nada foi executado no jogo.

**Resumo**
- O ano tem um calendário fixo de "tipos de data", montado por uma sequência fixa de dias da semana (`best.a.g`). A temporada sempre segue o mesmo desenho: amistosos e regionais em janeiro, estaduais até março, liga nacional de março a dezembro e Mundial de Clubes no Natal.
- Cada competição é uma subclasse de `best.at` no pacote `f`. As fases genéricas são `f.s` (pontos corridos ou grupos) e `f.z`/`f.G` (mata-mata). Os jogos ocupam, em ordem, as próximas datas livres do tipo da competição.
- A virada de temporada (`best.f.aa`) segue esta ordem: passa os campeões entre copas, avança o ano e refaz o calendário, faz o acesso e o rebaixamento e remonta ligas, copas, regionais e continentais. Depois vêm as competições de seleções, em ciclos de 2 e 4 anos.
- As vagas continentais saem de listas fixas por país, preenchidas pela classificação da 1ª e da 2ª divisão e pelo campeão da copa. Não existe ranking ou coeficiente de país, de clube ou de seleção; os potes usam o "nível" estático e um desempate aleatório.
- Os jogos exibidos no dia dependem do tipo do primeiro campeonato da data (`best.s.dx`) e das preferências `verJint`. Em dias de seleções, Recopa, eliminatórias e Supercopa, a tela mostra todos os jogos do dia.

Convenções:
- `c.a.SR` é a instância de `best.f`, o estado da carreira.
- "Ano de carreira" é `best.f.H()` (campo `ae`, começa em 1).
- Os ids de país seguem a ordem de `best.ac` (29 = Brasil). Os nomes de país vêm das siglas que o próprio código usa.
- Tudo que foi deduzido sem leitura direta está marcado "(inferido)".

---

## 1. Tipos de campeonato e classes

`best.at.F(tipo, subtipo)` grava o tipo (`b()`, campo `tR`) e o subtipo (`gg()`/`el()`, campo `dz`). Os nomes vêm de `best.M.getString` (em `arquivos/default_lang.xml`) ou de literais no construtor.

| Tipo | Subtipo | Classe | Nome | Acessor em `best.f` |
|---|---|---|---|---|
| 0 | 0 | `f.a` | Amistoso | — |
| 1 | divisão (1..4) | `f.B` | liga nacional (fase em `f.s`) | `best.Z.eb()` |
| 2 | confederação do país (`Z.gg()`) | `f.f` | "Copa <país> <ano>" | `best.Z.jq()` |
| 3 | estado | `f.o` | `aq.rZ[estado]` (+ " - Nª divisão") | `best.w.eb()` |
| 4 | 0 | `f.v` | Liga dos Campeões | `aI()` |
| 4 | 1 | `f.r` | Copa Libertadores | `aF()` |
| 4 | 2 | `f.t` | Liga Campeões CAF | `aO()` |
| 4 | 3 | `f.u` | Liga Campeões AFC | `aL()` |
| 4 | 4 | `f.w` | Liga Campeões Concacaf | `aP()` |
| 4 | 5 | `f.y` | Liga Campeões OFC | `aQ()` |
| 5 | 7 | `f.A` | Mundial Clubes | `aR()` |
| 6 | 0 | `f.x` | Liga Europa | `aK()` |
| 6 | 1 | `f.H` | Copa Sul-Americana | `aH()` |
| 7 | 0 | `f.p` | Eurocopa | `ba()` |
| 7 | 1 | `f.d` | Copa América | `aZ()` |
| 7 | 2 | `f.c` | Copa Africana | `be()` |
| 7 | 3 | `f.e` | Copa Asiática | `bf()` |
| 7 | 4 | `f.h` | Copa Ouro | `bg()` |
| 7 | 5 | `f.g` | Copa OFC | `bX()` |
| 7 | 7 | `f.q` | Copa do Mundo | `aY()` |
| 8 | 0 | `f.D` | Recopa Europeia | `aW()` |
| 8 | 1 | `f.E` | Recopa Sul-Americana | `aV()` |
| 9 | 0 (70) | `f.l` | Eliminatórias Europa ("Classificatório Eurocopa") | `bL()` |
| 9 | 1 | `f.n` | Eliminatórias América do Sul | `bK()` |
| 9 | 2 | `f.i` | Eliminatórias África | `bM()` |
| 9 | 3 | `f.j` | Eliminatórias Ásia (e repescagem intercontinental) | `bQ()` |
| 9 | 4 | `f.k` | Eliminatórias Concacaf | `bR()` |
| 9 | 5 | `f.m` | Eliminatórias Oceania | `bS()` |
| 10 | 0..3 | `f.F` | regional (`aq.pY[x]`) | `bV()` (vetor `aZ` de 4) |
| 11 | id do país | `f.I` | "Supercopa - <país>" | `bW()` (lista `ar`) |
| 12 | 0 | `f.J` | Conference League | `mj()` |
| 13 | 7 | `f.K` | Finalíssima | `yl()` |
| 14 | 0 | `f.M` | Liga Nações Europa | `sq()` |
| 14 | 4 | `f.N` | Liga Nações Concacaf | `ym()` |
| 15 | 0 | `f.L` | Torneio Amistoso | `yn()` |

**Fontes da tabela:**
- Construtores das classes `f.*`, `best.f.ab()` (nomes das competições de seleções), `best.p.dq/dr/yM` (nomes da Liga dos Campeões, da Libertadores e da Conference).
- Acessores de `best.f`.

**Classes de apoio:**
- `f.s` (extends `best.L`): fase de pontos corridos ou de grupos.
- `f.z` (extends `best.L`): fase de mata-mata.
- `f.G`: montagem e decisão de confrontos.
- `best.G`: tabela de um grupo.
- `best.t`: gerador de rodadas.
- `best.i`: registro de campeão.
- `best.c`: linha de artilharia.
- `components.am`: entrada de vagas, `am(sigla, idPais, vagas[, prioridadeCampeãoCopa])`.
- `components.aq`: sorteio de grupos e confrontos.
- `f.b`: preenchimento de vagas.

**Categorias de menu (`best.at.cw`, usada por `best.at.a(int,boolean,int)`):**
- 0 = nacionais: tipos 1 e 2, e o 15 se não houver copas internacionais de clubes.
- 1 = internacionais de clubes: 4, 5, 6, 8, 12, 15.
- 2 = estaduais: 3.
- 3 = seleções: 7, 9, 13, 14.

Os tipos 10 e 11 não entram em nenhuma categoria. Os regionais entram à parte na categoria 0 quando `bk()` está ativo (`best.at.a`).

---

## 2. Calendário

### 2.1 Estrutura

- O calendário é a lista `best.f.as` de objetos `best.a`, um por dia do ano civil.
- `best.f.r(ano)` cria do dia 1/1 ao dia 31/12 e põe o "dia atual" (`best.f.af`, lido por `J()`) no **primeiro domingo de janeiro**. Em seguida, `best.f.aS()` agenda eventos fixos.
- A data corrente é `best.f.bb()` (o `Calendar` do dia `af`).
- **Ano do calendário:** `best.f.ah()` chama `r(op() + (H() − 1))`. `op()` é o ano inicial (campo `rM`, 2022 ou 2023).
- Cada `best.a` guarda:

| Campo | Conteúdo |
|---|---|
| `w` | tipo da data (`b()`) |
| `s` | partidas `best.I` do dia (`h()`) |
| `u` | campeonatos do dia (`t()`) |
| `t` | fases do dia (`j()`) |
| `q` | eventos "antes" (`r()`) |
| `r` | eventos "depois" (`s()`) |
| `v` | dia já passado (`e()`) |

### 2.2 Montagem dos tipos de data (`best.a.g`)

`best.a.g()` faz 250 chamadas fixas a `b(diaDaSemana, tipo)`. Cada chamada marca com `tipo` o **próximo dia ainda sem tipo**, com aquele dia da semana (1 = domingo … 7 = sábado), procurando a partir do último dia já marcado (ou do dia atual). O resultado é determinístico; só muda o alinhamento com o ano civil.

Os nomes dos tipos de data estão no despejo de depuração `best.a.u()`:

| Tipo | Nome no código | Quantidade | Período (simulação para 2022) | Dias da semana |
|---|---|---|---|---|
| 100 | Amistoso Clube | 11 (10 em 2023) | jan–nov | variados |
| 15 | Torneio amistoso | 5 | 3/1–16/1 | dom, seg, ter, sex |
| 10 | Regional | 12 | 5/1–21/1 | todos |
| 3 | Estadual | 23 | 23/1–20/3 | dom, ter, qui |
| 11 | SuperCopa | 1 | 5/2 | sáb |
| 200 | Amistoso Seleção | 11 | fev–nov | seg, qui, sáb |
| 4 | Int1 (Liga dos Campeões e Libertadores) | 23 | 2/3–28/9 | ter, qua, qui |
| 1 | Nacional (ligas) | 54 | 27/3–22/12 | todos (17 em dezembro) |
| 12 | Int3 (Conference) | 23 | 1/4–9/12 | seg, qua, qui, sex |
| 9 | Eliminatórias | 28 | 11/4–7/12 | seg, qua, qui, sex, sáb |
| 14 | Liga das Nações | 10 | 18/4–29/10 | seg, qui, sex, sáb |
| 2 | Copa nacional | 14 | 26/4–2/11 | ter, qua |
| 6 | Int2 (Liga Europa e Sul-Americana) | 20 | 12/5–30/11 | qua, qui |
| 7 | Seleções (copas) | 8 | 14/7–31/7 | todos, menos ter |
| 13 | Finalíssima | 2 | 8/8 e 5/9 | seg |
| 8 | Recopa | 2 | 8/11 e 15/11 | ter |
| 5 | Mundial | 3 | 23/12, 24/12 e 26/12 | sex, sáb, seg |

**Sobre a tabela:**
- Datas e contagens vêm de uma reprodução do algoritmo de `best.a.g()`/`best.a.b(int,int)` fora do jogo (Python), seguindo a regra de dia da semana do `java.util.Calendar`. É uma reprodução do algoritmo, não uma observação em jogo.
- **Distribuição mensal (2022):**
  - janeiro: regionais, torneio e amistosos;
  - fevereiro–março: estaduais, Supercopa e início da Int1;
  - abril–novembro: liga, copa e continentais;
  - julho: as 8 datas de copas de seleções;
  - dezembro: 17 datas de liga, fim das eliminatórias e da Int3, e o Mundial.
- **Particularidade lida no código:** `best.a.b(int,int)` só grava quando o índice achado é maior que 0. Se 1º de janeiro cai num domingo (2023, por exemplo), a primeira chamada (`b(1,100)`) não marca nada, e o ano fica com um amistoso de clube a menos.

### 2.3 Como as competições usam as datas

- `best.a.a(tipo, pula)` devolve os índices dos dias do tipo ainda não passados (`!e()`). Com `pula` (`LoadLigaOptions.pulaDuasDatas`), descarta os dois primeiros.
- `f.s.a(lista, …)` atribui a rodada *r* ao *r*-ésimo índice dessa lista. Divisões e grupos do mesmo tipo dividem as mesmas datas.
- Ao criar um confronto, o mata-mata pega as duas próximas datas livres do tipo: ida e volta, ou só a primeira (`f.G.a`, conforme o relatório do subestudo de ligas).
- `best.f.aM()` marca como passados todos os dias até o atual.
- Amistosos de clube (`f.a.L(ah)`) e de seleção (`f.a.M(ah)`) usam as datas 100 e 200 posteriores à data atual em que o time ainda não joga. Só a interface os cria (`f.a.b(...)`); não foi encontrada geração automática pela IA (inferido pela busca de chamadores).

### 2.4 Eventos agendados (`best.a.b(int,int,int)` e `best.a.f(int)`)

Cada evento é uma string guardada na lista "antes" ou "depois" do dia. `best.f.q(0|1)` executa os eventos de **todos os dias até o atual**, então os dias pulados também os disparam.

| Código | String | Ação (`best.a.f`) | Onde é agendado |
|---|---|---|---|
| 1 | `cw` | `best.a.p()` → `f.A.zC()`: monta o Mundial | última data Int1 (`a.d(4)`), em `best.p.dg` e `best.f.ae` |
| 2 | `ds` | `best.a.n()` → `ah.kJ()` nos times humanos do mês (`bY(mês)`): salário (inferido) | dia 2 de cada mês (salário mensal) ou todo domingo (semanal), em `best.f.aS` |
| 3 | `aj` | `best.f.aT()`: evolução semanal de jogadores (`F.fV`, `F.fY`) | todo domingo, em `best.f.aS` |
| 4 | `cD` | `best.a.m()` "criaSerieDCopa" (com `bk()`) ou `best.a.l()` "criaCopaBRAposRegionais" (com regionais) | 1ª data Nacional, se `bk()` ou regionais (`best.p.dg`, `best.f.aa`) |
| 5 | `dJ` | `best.a.o()` → `ah.w(kL().eQ(), 4)`: lançamento financeiro mensal (inferido) | dia 2 de cada mês |
| 6 | `cS` | `best.a.b(false)`: convites para técnico humano sem seleção | 4ª data de estadual (com estaduais); 1ª data de seleções; 12ª e 18ª datas Nacional |
| 7 | `cO` | `best.a.k()`: abre a convocação para quem comanda seleção | 1ª data de seleções |
| 8 | `cSempregado` | `best.a.b(true)`: convites de seleção para todos os humanos | 1ª data Nacional |
| 9 | `cPromocao` | `best.ay.zw()`: propostas de clubes a técnicos humanos empregados (inferido) | 20ª data Nacional (21/8 em 2022) |
| 10, 11 | `criaMataMataAscenso`, `criaplayOffRebaixamento` | sem efeito em `f` | — |

O agendamento dos eventos 6 a 9 fica em `best.a.q()`. Os eventos 6, 7 e 8 só são agendados com `isJogaSelecoesAll()`.

### 2.5 O dia de jogo (`best.f.ap` → `at` → `ax`)

1. **`best.f.V()`:** se a temporada acabou (campo `bk`), vai para a virada (`aa`). Senão, `ap()`.
2. **`ap()`:**
   - Se algum time humano joga hoje e ainda não confirmou o time (`I.hc()/hd().jZ() && !kf()`), abre a tela do time (`S.aY(2)`, `a.eg`) e aplica o autossalvamento (`autoSalvar` 1 = a cada 4 dias, 2 = sempre, 3 = condicional).
   - Senão, decide se o dia é exibido. Os flags que ligam `bH` (pular a exibição) são:
     - `isIgnoraLigas()` com o primeiro campeonato do dia de tipo 1 e nenhuma fase de liga com humano (`best.s.dG`);
     - `isIgnoraEstadual()` em dia de estadual ou regional sem brasileiro humano (`best.s.J`);
     - regional sem humano (`best.s.dH`, `regionaisSemHumanos`).
   - Com exibição e `best.s.dw()` verdadeiro, abre a tela de partida (`best.s.dx`). Senão, `at()`.
3. **`at()`:**
   - `as()` prepara e fecha as partidas do dia (`I.a(true)`, `hg`, `hi`, `hf`, `hh`) e atualiza os jogadores (`F.fr`);
   - `an()` e `aC()` processam as fases do dia (`f.s.pO`, `f.z.pO`);
   - `aM()` marca os dias passados;
   - `aB()` limpa caches dos campeonatos;
   - `q(0)` dispara os eventos "antes";
   - depois mostra o resumo (`S.aY(5)`, `a.hk`) ou segue direto para `ax()`.
4. **`ax()`:**
   - em datas de liga ou de estadual, `n(tipo)` trata ofertas a técnicos humanos desempregados (`best.ay.b`) e trocas de técnicos (`Z.A`/`w.A`, aviso em `S.K`);
   - `az()` acha o próximo dia com tipo, não passado e com partidas. Os dias sem jogos são pulados;
   - tarefas aleatórias e de propostas (`au`, `av` com 50% de chance, `aw`);
   - `q(1)`.
   - Se `az()` devolve 0, a temporada acaba (`bk = true`): `best.ay.zw()`, `al()` e a tela de fim de temporada `S.aY(6)` (`a.cR`).

---

## 3. Início de carreira

| Passo | Origem | Efeito |
|---|---|---|
| Tela "Configurações iniciais" | `a.hU` (`S.aY(0)`) | "Temporada de início" 2022/2023 (`best.f.I(ano)`, lembrada em `aq.f("anoinicio")`); jogar estaduais, regionais, copas internacionais de clubes e competições de seleções; ligas nacionais por país (tabela `best.O`, Brasil marcado por padrão); salário mensal ou semanal; força clássica ou individual; "Usar grupos da Copa do Mundo 2022" |
| Versão não registrada | `a.hU.sm` | estaduais, regionais, copas internacionais e seleções desmarcados e bloqueados |
| Países jogáveis | `best.p.dd()` | `best.O` para cada país com ≥10 times no banco; ≥16 para Alemanha (3), Argentina (11), Inglaterra (97), Itália (104) e França (72) |
| Criação do mundo | `best.p.dg()` | ver abaixo |
| Escolha do time | `a.bV` (`S.aY(1)`) | técnico humano (nome, nacionalidade), "Treinar time do país" e combos da 1ª à 4ª divisão. No Brasil com Série D pelos estaduais, a 4ª linha lista os clubes sem divisão ("Jogando estaduais:"). Há "Escolher um time aleatório"; mais de um técnico humano só na versão registrada (`a.bV.om`) |
| Regionais | `a.bV.oq` → `best.p.dh()` | cria os 4 regionais (seção 7) |
| Torneio amistoso | `a.bV.pl` | pergunta "Deseja criar um torneio Amistoso de início de temporada?" e abre `a.jH` (seção 11) |

**Ordem de `best.p.dg()`:**
1. Cria os times (`best.p.x`: até 15 por país, ou todos se o país está ativo).
2. Executa `Z.iT()`.
3. Monta o calendário: `r(op())`, `a.g()` e `a.u()`.
4. Cria as ligas dos países ativos (`best.p.w` → `Z.Ar()`).
5. Agenda o evento "cD" e os de `a.q()`.
6. Cria `new M(false)`, numera os times e prepara jogadores e técnicos.
7. Se `op()==2023`, chama `best.f.rU()`, que desloca os ciclos de seleções.
8. Executa `afQ.zj()`.
9. Se jogar seleções: `ab()` e `ac()`.
10. Se jogar copas internacionais, cria e sorteia (`yq()`) nesta ordem: Concacaf, Libertadores, Liga dos Campeões, AFC, CAF, OFC. Agenda o "cw" do Mundial e depois cria Sul-Americana, Liga Europa e Conference.
11. Sem Série D por estaduais e sem regionais, `Z.ja()` no Brasil.

---

## 4. Virada de temporada (`best.f.aa`)

`aa()` roda quando `V()` encontra `bk == true`. A ordem é:

1. `ah.kI()` em todos os times humanos (`aN()`).
2. `ai()`, se houver copas internacionais (ainda no ano que terminou):
   - o campeão da Liga Europa é posto na Liga dos Campeões (`v.T`) e na Recopa (`x.N`);
   - o campeão da Sul-Americana é posto na Libertadores (`r.O`) e na Recopa (`H.N`);
   - o campeão da Conference é posto na Liga Europa (`x.ab`).
3. `jw()`, se houver seleções: passa os campeões da Eurocopa e da Copa América à Finalíssima (`K.Z`, `K.aa`).
4. `ah()`:
   - avança o ano de carreira (`I()`);
   - apaga o calendário;
   - cria o do novo ano (`r`) e preenche os tipos (`a.g()`).
5. `ag()`: zera históricos de jogo dos times e o moral do técnico (`ka().cj(50)`, `ck(50)`).
6. `iZ()`: `al.kk()` para cada técnico.
7. `ae()`, se houver copas internacionais:
   - limpa o cache de classificação de cada país (`Z.jy`);
   - sorteia de novo (`yq()`) Concacaf, Libertadores, Liga dos Campeões, CAF, AFC, OFC, Sul-Americana, Liga Europa e Conference, nessa ordem, que importa para as exclusões entre competições;
   - agenda o "cw";
   - monta as Recopas (`E.zR`, `D.zR`).
8. `Y()`: `Z.y(true)` no Brasil (prioridades da copa).
9. `Z()`: cria ou remonta as Supercopas nacionais (`f.I.Ab`).
10. `am()`:
    - acesso e rebaixamento nacional (`Z.ee()`);
    - zera a artilharia da copa;
    - refaz a tabela de cada divisão (`f.s.aN(false)`);
    - recria a copa nacional com as divisões em ordem e os demais por força (`Z.a(lista,false,"atualizaLigasNacionais")`). No Brasil com Série D por estaduais ou com regionais, a copa só é criada no evento "cD".
11. `ak()`: acesso e rebaixamento estadual (`w.ee()`) e tabelas estaduais refeitas.
12. `aj()`: regionais remontados com `best.p.di()`.
13. Agenda "cD" (com `bk()` ou regionais) e os eventos de `a.q()`.
14. `af()`: envelhecimento e aposentadoria de jogadores e técnicos (`F.gc`, `gd`, `gf`, `fK`, `fJ`) e geração de novos (`c(true)`). Os detalhes pertencem ao estudo de gestão.
15. A partir do 5º ano, `W()` apaga registros `ap` com mais de 10 anos.
16. `afQ.zi()`/`zj()` (pool de seleções), `best.ag.jO()`/`jQ()`.
17. `ac()`, se houver seleções (seção 9).
18. `f.L.xZ()` (torneio amistoso), um eventual torneio de teste (`iY`, flag `Jc`) e o diálogo de torneio amistoso (`a.cR.AC`) se algum humano tiver clube.
19. `az()` e `V()`: começa o primeiro dia de jogo.

---

## 5. Ligas nacionais

### 5.1 Configuração (`conf_ligas_nacionais`)

- `best.p.ds()` lê os arquivos `<sigla>.cfg`. Cada um é um `est.ArrayLigaType` serializado, com um `est.ConfigLigaType` por divisão, e vai para `SR.bG`. `best.Z.t(país, divisão)` faz a busca.
- Campos usados por `best.Z.Ar()`: nTimes, doisTurnos, nGrupos, jogosDentroGrupo, numeroTimesMataMata, nRebaixados, rebaixadosDireto, vagasSobemPeloMataMata (limitado a 0..2 em `f.B.setVagasSobemPeloMataMata`), duasVoltasMataMata, desempate, classificaPeloGeral, melhoresTerceiros, `formula`→`numeroTurnos`, nome da liga e da divisão.
- `ConfigLigaType.playoffRebaixamento` não é lido fora de `est/`.

Valores da instalação limpa, extraídos pelo subestudo com um leitor de serialização Java:

| Liga | Times | Grupos | Mata-mata | Rebaixados (diretos) | Observação |
|---|---|---|---|---|---|
| BRA A, B | 20 | 0 | 0 | 4 (4) | pontos corridos |
| BRA C | 20 | 0 | código 1020 | 4 (4) | ver 5.3 |
| BRA D | 64 | 8 | 4 por grupo | 4 (4) | substituída pela Série D dos estaduais quando `bk()` |
| ESP 1 | 20 | 0 | 0 | 3 (3) | |
| ESP 2 | 22 | 0 | 0 | 3 (2) | 1 vaga pelo mata-mata de acesso e 1 playoff de rebaixamento |
| ESP 3 | 10 | 0 | 0 | 1 (1) | `formula` 4 (4 turnos) |
| ESP 4 | 30 | 0 | 0 | 2 (2) | turno único (ver 5.4) |

### 5.2 Criação das divisões (`best.Z.Ar`, uma vez por carreira)

1. Os times do país são ordenados por força (`h.a.cN`: nível e depois um aleatório `ah.iS()`). Cabem no máximo 4 divisões.
2. Cada divisão pega os próximos nTimes da lista.
3. **Fallback**, sem configuração ou com times insuficientes: 20 times e 4 rebaixados; ou 18/16/14/12/10 times e 2 rebaixados. Com ≤10 times, no máximo 2 rebaixados.
4. Os clubes que sobram ficam "sem divisão" (`Z.ek()`), ordenados por `h.a.abm` (nível, reputação, aleatório).
5. **Brasil com estaduais:** a 4ª divisão fica vazia e liga `SR.e(true)`, que é o `bk()` "Série D pelos estaduais".

### 5.3 Formatos especiais (`f.s`)

| Código | Uso | Formato |
|---|---|---|
| 1020 | Série C | 20 times em turno único. Os 8 primeiros formam 2 grupos de 4, em ida e volta (`var0` 1022). Os líderes fazem a final. O 1º a subir é o campeão, depois o vice e então os 2º colocados por campanha (`f.s.l`). |
| 1068 | liga de 68 times | Os 8 últimos (posições 60–67) jogam uma preliminar. Depois vêm 8 grupos por região (`h.a.aaV`, `ah.jX()`) (inferido em parte). |
| 1403 | AFC | 10 grupos, avança só o 1º, mais os 6 melhores 2º colocados |
| 7700 | grupo de 4 com tabela fixa (`best.t.v`) | copa do mundo de 32 (`f.q`) |
| 7 / 10 | estaduais com grupos cruzados | ver seção 6 |
| 1801–1805 | comparados, nunca atribuídos | sem uso (inferido) |

### 5.4 Rodadas (`f.s.a`, `best.t`)

- Para 3, 5, 6, 9, 11, 19 e 25 times há tabelas fixas em `best.t`. Para os demais tamanhos, o método do círculo (`best.t.a(s, lista, nTurnos)`):
  - embaralha os times;
  - gera n−1 rodadas;
  - intercala as rodadas da primeira e da segunda metade;
  - alterna o mando do jogo fixo;
  - o returno espelha os mandos;
  - 3 turnos = turno + returno + turno; 4 turnos = T, R, T, R.
- **Turnos em liga nacional (tipo 1):**
  - `doisTurnos` é ignorado e vale 2 turnos, exceto com 26, 28, 30 ou 36 times (turno único);
  - sem grupos: 8 times → 4 turnos; 10 → 4 (ou 2/3 pela `formula`); 12 ou 14 → 3 (ou 2);
  - Série C 1020 → 1 turno.
- A Série A tem `doisTurnos=false` no `.cfg`, mas joga 38 rodadas pela regra acima.

### 5.5 Classificação, desempate e artilharia

- **Pontos:** vitória 3, empate 1 (`best.ah.a(I, f.s)`).
- O vetor de campanha (`best.ak.lB`) é: pontos, jogos, vitórias, empates, derrotas, gols pró, gols contra, saldo.
- **Ordenação** (`h.a.abn` = `h.K`): pontos, vitórias, saldo, gols pró. Não há confronto direto. Os índices 0, 2, 7, 5 de `ah.d(s)` foram interpretados assim (inferido).
- `f.s.pO()` ordena a cada rodada.
- Sem mata-mata, o campeão é o 1º da tabela (`new best.i(…, Zb[0], Zb[1])`).
- **Artilharia** (`best.at.mu/mv`, comparador `at.tX` = `best.au`): mais gols e, no empate, menor `c.A()`, que provavelmente é o número de jogos (inferido).
- **`best.at.mz()`:** lista os 5 jogadores com nota média (`H.F()`) acima de 5.
- **`best.at.my()`:** estatística da edição (`best.m`): média de gols, maior goleada, campeão e times com mais títulos.

### 5.6 Acesso e rebaixamento (`best.Z.ee`, `f.B`)

1. Para cada divisão, `f.s.ah(nSobem, nDescem)` separa:
   - quem sobe: `l(n)`, os primeiros da tabela ou, havendo mata-mata, os que foram mais longe;
   - quem desce: `fG(n)`, os últimos. Com grupos e `rebaixadoPeloGrupo`, sai um por grupo.
2. O número de quem sobe para a divisão *d* é igual ao nRebaixados da divisão *d−1* (`Z.K(int)`).
3. As trocas são posicionais entre as divisões vizinhas. Acontecem só se as listas tiverem o mesmo tamanho, e são puladas para quem venceu o playoff de rebaixamento (`f.B.ac`).
4. Da última divisão, os rebaixados trocam com a fila de clubes sem divisão (`dt`).
5. **Brasil com Série D pelos estaduais:** os rebaixados da Série C vão para `SR.bY()`, e a Série D é esvaziada (`f.s.yJ`).
6. **Mata-mata de acesso** (`f.B.BQ`, disparado ao registrar o campeão de uma liga de tipo 1):
   - só em divisões abaixo da 1ª com `vagasSobemPeloMataMata > 0`;
   - os 4 times logo abaixo das vagas diretas formam pares consecutivos;
   - 2 vagas = 1 rodada; 1 vaga = 2 rodadas;
   - código 1099.
7. **Playoff de rebaixamento** (`f.B.a(B)`, criado quando as duas divisões terminam): existe se nRebaixados ≠ rebaixadosDireto. O melhor da zona enfrenta o N-ésimo de baixo da divisão inferior. É uma rodada, código 1098.

### 5.7 Vagas continentais a partir da liga

- `best.Z.jd()` monta `hD`: a classificação final da 1ª divisão seguida da 2ª (`f.B.yi().yV()`, quem foi mais longe no mata-mata e depois a tabela).
- `best.Z.a(n, destino, excluídos, comCampeãoCopa)` tira os primeiros não excluídos. Com a flag, entra primeiro o campeão da copa do ano anterior (`bk(H()−1)[0]`).
- País sem divisões jogáveis usa `best.Z.je()`: os mais fortes aceitos com probabilidade decrescente (85% … 20%).

---

## 6. Estaduais (`best.w`, `f.o`)

- **Configuração:**
  - `best.w.ef()` lê `conf_estadual/*.ces` (`est.ConfigEstadualType`: estado 0..26, divisão ≤4, `formula`, nRebaixados, desempate 0/1, finaisIdaVolta[3]);
  - `best.w.dZ()` cria um estadual por estado com ≥6 clubes;
  - `w.dY()` monta até 4 divisões, enquanto restarem ≥6 clubes.
- **Fórmulas** (`aq.sL[formula]` = times, grupos, classificados, turnos, rebaixados):

| Fórmula | Formato | Rebaixados |
|---|---|---|
| 0 | 6 times, 2 classificados, ida e volta | 2 |
| 1 | 8 times, 4 classificados, ida e volta | 2 |
| 2, 3, 4 | 10, 11 ou 12 times, 4 classificados, turno único | 2 |
| 5, 6 | 12 ou 14 times, 8 classificados | 2 |
| 7 | 16 times, 4 grupos, 2 por grupo, jogos cruzados entre grupos ("SP 2021") | 2 |
| 8, 9 | 16 times, 4 ou 8 classificados | 2 |
| 10 | 20 times, 4 grupos, 2 por grupo, cruzados | 4 |

- Valores da instalação limpa: SP 1ª divisão fórmula 7, finais [jogo único, jogo único, ida e volta]; RJ 1ª divisão fórmula 4. As demais divisões usam fórmula 0. Os rebaixados vêm de `aq.sL`, não do `.ces`.
- **`usaGrupoPadraoEstadual`:** só na 1ª divisão de SP com fórmula 7. Usa os 16 clubes fixos de `aq.sO`, em grupos sequenciais.
- **Mata-mata:**
  - com grupos cruzados, 1º contra 2º do mesmo grupo (`Zs`/`Zt`);
  - sem grupos, cruzamentos fixos por posição: 8 times `Zu` (1–8, 2–7, 3–6, 4–5 em outra ordem); 4 times `Zo` (1–4, 2–3).
  - `desempate == 1` em estadual significa **sem pênaltis** (`f.z.zA`).
- **Virada** (`best.w.ee`): igual à nacional, sem playoffs. A última divisão troca com os clubes do estado sem divisão.
- Ao fim de cada divisão, `f.s.za()` registra em `SR.bx()` a posição de cada clube sem divisão nacional. Isso alimenta a Série D e a copa.

---

## 7. Regionais e Série D (Brasil)

| Índice | `aq.pY` | Estados (`best.s.d`, `best.p.dh`) |
|---|---|---|
| 0 | Rio-SP | RJ, SP |
| 1 | Sul-Minas | MG, PR, RS, SC |
| 2 | Copa do Nordeste | AL, BA, CE, MA, PB, PE, PI, RN, SE |
| 3 | Copa Verde | AC, AM, AP, DF, ES, GO, MS, MT, PA, RO, RR, TO |

- **Criação:** cada regional só é criado se `jogaRegionaisTodos[i]` e se houver ≥16 clubes brasileiros na região. Nas opções da carreira o padrão é {falso, falso, verdadeiro, falso} (`best.f.jogaRegionaisTodos`), que pode ser substituído pelas opções globais.
- **Participantes** (`best.p.di`):
  1. o time humano, se `conviteRegionais` e houver um só técnico;
  2. os clubes das divisões nacionais;
  3. a partir do 2º ano, com `bk()`, os classificados dos estaduais;
  4. o resto embaralhado.
- **Formato** (`f.F.an`): 16 times em 4 potes por força, 4 grupos de 4 em turno e returno, 2 por grupo. Quartas, semi e final em ida e volta, mapa `Zv`. O rótulo de interface `f.F.yc()` descreve outro cruzamento.
- **Série D pelos estaduais** (`best.a.m`, evento "cD"):
  - a Série D é refeita com `best.w.Q(n)`: primeiro os rebaixados da Série C, depois vagas por faixas de estados (SP/RJ/MG/RS 7 passes; PR/SC/BA/PE/CE 5; dois grupos de 3; ES/TO/RO/AP/RR 1), pegando os melhores colocados de cada estadual;
  - a copa usa as Séries A–C e até 128 classificados estaduais (`best.w.eh()`).
- **Copa após regionais** (`best.a.l`): a copa brasileira é criada só na 1ª data de liga, com todos os clubes por força.

---

## 8. Copas nacionais e Supercopas

**Copa nacional, formato clássico** (`f.f.a`):
- N = maior potência de 2 entre 8 e 128. Os excedentes ficam fora.
- A metade forte enfrenta a fraca, sorteada.
- A 1ª fase é sempre ida e volta; as seguintes seguem `duasVoltasMataMata` (todas verdadeiras por padrão, inclusive a final).

**Formato novo** (`f.f.b`, Brasil com ≥91 times e `Options.novoFormatoCopa`):
- 12 isentos: brasileiros nas continentais e, com regionais, os campeões do Nordeste e da Copa Verde.
- Fase 2129: 80 times em jogo único com o mais fraco em casa. **No empate avança o visitante, sem pênaltis.**
- Fase 2229: 40 times, jogo único com pênaltis.
- Fase 2329: 32 times (com os isentos), ida e volta.
- Oitavas até a final: sorteio livre, ida e volta.

**Supercopa** (`f.I.Ab`, `best.f.Z`):
- Campeão da 1ª divisão do ano anterior contra o campeão da copa. Se for o mesmo time, entra o vice da copa.
- Jogo único na data 11.
- Na 1ª temporada não existe: é criada só na primeira virada (inferido).

---

## 9. Competições continentais e intercontinentais de clubes

**Regras comuns:**
- O preenchimento usa `f.b.a(listaDeAm, destino, excluídos, flag)`.
- A flag de prioridade ao campeão de copa, uma vez ligada por uma entrada, continua ligada para as seguintes (`f.b.a`).
- Vaga sem time é completada dando +1 aos países da lista. Se ainda faltar, a fase não é criada e o jogo escreve "erro" no console.
- Os potes usam `h.a.abm` (nível, reputação, aleatório).
- Grupos sorteados com restrição de mesmo país (`components.aq.a/e`); `aq.f` não tem restrição.
- Mata-mata de chave fixa: os vencedores seguem na ordem, sem novo sorteio (`f.z.zs`).

| Competição | Participantes e vagas | Formato |
|---|---|---|
| Liga dos Campeões (`f.v`) | 26 diretos: Inglaterra, Espanha e Itália 4; Alemanha 3; França e Portugal 2; Holanda, Bélgica, Áustria, Escócia e Ucrânia 1; mais o campeão anterior e o campeão da Liga Europa. 52 em preliminares (lista `YW`). | Preliminares 4000–4004 (mini mata-mata de 4 em jogo único, depois rodadas de ida e volta em dois blocos). Os perdedores vão para a Conference (4000, 4001) ou para a Liga Europa (4002–4004). 8 grupos de 4 em ida e volta, 2 avançam. Oitavas com 2º × 1º (`aq.e`). Final em jogo único. Sede da final em ciclo de 10 cidades (`v.mF`). |
| Libertadores (`f.r`) | 28 diretos: Brasil 5, Argentina 5, os outros 8 países 2 cada, mais o campeão anterior e o da Sul-Americana. 19 em preliminares. | Fases 4101–4103 em ida e volta; os 4 perdedores da 4103 vão para a Sul-Americana. 8×4, 2 avançam; o 3º vai às oitavas da Sul-Americana. Oitavas por sorteio livre (`aq.f`). Final em jogo único. No 1º ano, com `isGruposIntPadrao()`, participantes e grupos são fixos (`aq.sP`/`sQ`, `r.ag`). |
| Sul-Americana (`f.H`) | Brasil 6, Argentina 6; 4 por país dos outros 8 na preliminar. Exclui quem está na Libertadores. | 6100: 16 confrontos entre times do mesmo país. 32 em 8×4, avança só o 1º. Oitavas contra os 3º da Libertadores. Final em jogo único. |
| Liga Europa (`f.x`) | 12 diretos (listas fixas, mais o campeão da Conference a partir do ano 2) e 9 em preliminares. Exclui os times da Liga dos Campeões. | 6001–6002 em ida e volta. 32 em 8×4. Playoff: 2º da Liga Europa × 3º da Liga dos Campeões. Oitavas: 1º × vencedor do playoff. Final em jogo único. |
| Conference (`f.J`) | 134 entradas de 1 vaga, mais perdedores da Liga dos Campeões e da Liga Europa. Exclui os times dessas duas. | 4 preliminares (12001–12004). 32 em 8×4. Playoff: 2º da Conference × 3º da Liga Europa. Oitavas. Final em jogo único. |
| CAF (`f.t`) | 31 por vagas fixas + campeão = 32 | 8×4 por potes de força, sem restrição de país. Mata-mata com o melhor 1º contra o pior 2º. Tudo em ida e volta, inclusive a final. |
| AFC (`f.u`) | 39 + campeão = 40 | 10×4; avançam os 1º e os 6 melhores 2º (1403). Tudo em ida e volta. |
| Concacaf (`f.w`) | 23 + campeão = 24 | 8×3, avança o 1º. Quartas por chave fixa. Tudo em ida e volta. |
| OFC (`f.y`) | 8; o campeão anterior não é usado | 2×4, semis cruzadas, final em ida e volta |
| Mundial (`f.A`) | Campeões do ano das 6 confederações; da Libertadores, o melhor não mexicano (`r.yx`). Se faltar qualquer um, não há Mundial. | Montado no evento "cw" (`A.zC`). CAF, AFC, OFC e Concacaf em 2 jogos (uma de 3 permutações sorteada). Semis contra os campeões da Libertadores e da Liga dos Campeões, final e 3º lugar, tudo em jogo único, nas 3 datas tipo 5 do Natal. |
| Recopas (`f.D`, `f.E`) | Liga Europa × Liga dos Campeões; Sul-Americana × Libertadores | Um confronto em ida e volta nas 2 datas tipo 8 (novembro). Não acontece se os campeões forem o mesmo time ou se faltar um. |

**Calendário:**
- Tipo 4 (Int1): Liga dos Campeões, Libertadores, CAF, AFC, Concacaf e OFC.
- Tipo 6 (Int2): Liga Europa e Sul-Americana.
- Tipo 12 (Int3): Conference.
- As continentais de CAF, AFC, Concacaf e OFC pulam as duas primeiras datas (`pulaDuasDatas`).

**Prêmios lidos:**
- Preliminares da Liga dos Campeões: 1.000.000 (`f.G.c`).
- 1ª fase da Sul-Americana: 300.000.
- Os demais prêmios pertencem ao estudo de economia.

---

## 10. Seleções

### 10.1 Ciclos (`best.f.ac`)

Contadores comparados com o ano de carreira. Valor inicial para 2022; entre parênteses, o de `rU()` para 2023. O número após "+" é a periodicidade.

| Competição | Contador | Ano(s) inicial(is) | Período | Eliminatórias |
|---|---|---|---|---|
| Copa do Mundo (`f.q.ya` no ano 1, `Bu` nos outros) | `bl` | 1 (4) | +4 | todas no ano `bl−1` (América do Sul `ya`; África, Concacaf, Ásia e Oceania `Bj`; Europa `fF(7)`) |
| Eurocopa | `bm` | 3 (2) | +4 | classificatório europeu `fF(0)` no ano `bm−1` |
| Copa América | `bn` | 3 (2) | +4 | — |
| Copa Africana / Asiática | `bo` / `bp` | 2 (1) | +4 | — |
| Copa Ouro | `br` | 2 (1) | +2 | — |
| Copa OFC | `bq` | 4 (3) | +4 | — |
| Finalíssima (`Bs`) | `IZ` | 4 (3) | +4 | campeões da Eurocopa e da Copa América (`jw`) |
| Liga das Nações Europa / Concacaf (`Ar`) | `Ja` / `Jb` | 2/1 (1/1) | +2 | — |

Nos anos sem edição, as copas recebem `p(null)`. Cada `ya()` incrementa o número da edição (`YH`).

### 10.2 Formatos

| Competição | Seleções | Formato |
|---|---|---|
| Copa do Mundo, 1ª edição (`f.q.ya`) | 32 | Com "grupos reais 2022" (`isUsarGruposReaisCopa`), 32 ids fixos. Sem a opção, cotas por confederação (13/4/5/4/3/0, sede Catar se tiver elenco, 70% de +1 Concacaf e 30% de +1 OFC). 8 grupos de 4, turno único, 2 avançam. Oitavas pelo cruzamento `Zw`. Final e 3º lugar. |
| Copa do Mundo seguinte (`f.q.Bu`) | 48 (classificados) | 3 potes de 16 por força. 16 grupos de 3, 2 avançam. 16-avos até a final e 3º lugar, jogo único. |
| Eurocopa (`f.p`) | 24 | 6×4, 2 + 4 melhores 3º, oitavas, 3º lugar |
| Copa América (`f.d`) | 10 | 2×5, 4 por grupo, quartas em diante, 3º lugar (inferido) |
| Africana / Asiática (`f.c`/`f.e`) | 24 | sede (se tiver elenco) + sorteados; 6×4, 2 + 4 melhores 3º |
| Copa Ouro (`f.h`) | 16 | 4×4, quartas |
| Copa OFC (`f.g`) | 8 | 2×4, semis |
| Liga Nações Europa (`f.M`) | 55 | Ligas A, B, C (16 cada, 4×4) e D (7). Final four da Liga A com 3º lugar. Acesso e rebaixamento entre ligas (`BD`). Playoff de rebaixamento na Liga C. |
| Liga Nações Concacaf (`f.N`) | 41 | Ligas A (12), B (16) e C (13). Final four. Acesso e rebaixamento. |
| Finalíssima (`f.K`) | 2 | Jogo único. A sede alterna entre cidade sul-americana e europeia, de país diferente dos finalistas. |

**Fontes e mecanismos da tabela:**
- A seleção dos participantes por confederação usa `best.Z.a(isCopa, confed, n, …)`: as seleções ordenadas por nível (`Z.cN`) entram com probabilidades por faixa, que diferem para Copa do Mundo e para copas continentais. A seleção só entra com elenco suficiente (`Z.jl()`: ≥15 de linha e ≥2 goleiros em clubes).
- A disputa de 3º lugar fica ligada por `O(true)` em todas as copas finais e nas Ligas das Nações.

### 10.3 Eliminatórias e vagas (Copa do Mundo de 48)

| Eliminatória | Formato | Vagas | Repescagem |
|---|---|---|---|
| América do Sul (`f.n`) | 10 seleções (9 se a sede for sul-americana), pontos corridos em ida e volta | 6 | 7º |
| Europa (`f.l`, `fF(7)`) | 55 em 10 grupos (5×5 e 5×6); play-off com 12 (10 segundos + 2 melhores terceiros) | 10 + 6 = 16 | — |
| África (`f.i`) | 54: preliminar com 28; 8 grupos de 5; play-off entre 4 melhores segundos | 9 | finalista do play-off |
| Ásia (`f.j`) | 46: preliminar; 8×5; fase final 2×6; pré-repescagem 5º × 5º | 8 | vencedor da pré-repescagem |
| Concacaf (`f.k`) | 35; preliminar 6×5; intermediária; final com 8 | 6 | 7º e 8º |
| Oceania (`f.m`) | 11; preliminar; 2×4; semi e final | 1 | finalista |
| Repescagem (`f.j.ax`, "Eliminatórias - Repescagem") | 6 seleções em turno único | 2 | — |

Total: 48. O classificatório da Euro (`fF(0)`) usa os mesmos grupos europeus e classifica 1º e 2º de cada grupo, mais 4 do play-off, que somam 24.

### 10.4 Convocação e técnicos

- **IA** (`best.Z.z(bool)`): escolhe técnico (`Z.ji`) e 23 jogadores por cotas de posição. Se o país não tem jogadores suficientes, gera jogadores fictícios (`best.K.r`).
- **Humano:** os convites para dirigir seleção chegam pelos eventos `cS` e `cSempregado` (`best.ay.a(al,bool)`, filtrados pela reputação do técnico). A convocação manual abre no evento `cO` (`best.S.a(…, true)`, tela `a.aP`).
- **Ranking:** não há ranking dinâmico de seleções. A tela "Ranking de Seleções" (`a.jv`) só exibe resultados acumulados (`ah.ld/lb`) (inferido).

---

## 11. Torneio amistoso e amistosos

- **`f.L` (tipo 15):** criado pelo diálogo `a.jH`, oferecido no início da carreira (`a.bV.pl`) e a cada virada em que algum humano tem clube (`a.cR.AC`).
- O usuário escolhe nome, sede (padrão "Juazeiro"), participantes, sorteio de grupos e a fórmula:
  - "2 grupos de 4, semi e final";
  - "1 grupo de 4, final";
  - "1 grupo de 6".
- Fases e datas:
  - grupos em turno único;
  - mata-mata em jogo único (`f.L.a`);
  - joga nas 5 datas tipo 15 de janeiro.
- `best.f.iX()`, que repete a pergunta, não tem chamador (código morto, inferido).
- Amistosos avulsos (`f.a`, tipo 0) são exibidos só quando há time humano (`best.s.dw`: tipo 0 sem humano = não exibe).

---

## 12. Histórico de campeões

- `best.i(at, fase, campeão, vice)` grava:
  - o ano de carreira;
  - campeão e vice (ids de time);
  - os técnicos;
  - o artilheiro da edição (nome, gols, clube).
- O registro entra em `at.mn()` e chama `at.mr()`.
- O artilheiro da 1ª divisão nacional recebe uma marca (`x().a(true)`).
- Se o campeão é humano, `best.S.a(time, at, tipo)` mostra o título.
- Ao registrar o campeão de uma liga (tipo 1), dispara o mata-mata de acesso (`f.B.BQ`).
- `at.cS()` devolve o campeão do ano corrente, `at.mp()` o do ano anterior, `at.cv(ano)` o de um ano qualquer.
- **Mata-mata** (`f.G.b`): o campeão é registrado ao fim da última rodada de um `f.z` com registro ligado. A disputa de 3º lugar é criada quando a rodada tem um jogo só e `at.mq()` está ligado.
- **Decisão de confronto** (`f.G.b`, `best.I.hk`):
  1. vitórias e saldo agregado;
  2. gol fora, só com a flag `aag`, que na prática nenhuma competição liga (inferido);
  3. pênaltis.
- **Não há prorrogação.**
- **Pênaltis em jogo sem humano** (`best.I.V`): dois sorteios de 2 a 8; o mandante vence com a ≥ b, cerca de 57%.
- **Fallback sem pênaltis** (`f.G.b`): compara um campo do mesmo time dos dois lados e avança o 2º do par. Parece defeito.

---

## 13. Quais jogos aparecem na tela do dia

1. `best.s.dw()` decide se o dia é exibido:
   - sempre, se há time humano;
   - senão, pela preferência `verJint[best.f.ae(tipo, subtipo)]` do primeiro jogo do dia;
   - amistoso (tipo 0) sem humano não é exibido.
2. `best.s.dx()` pega os campeonatos do dia (`best.a.t()`) e escolhe o roteiro pelo tipo do **primeiro**:

| Tipo do 1º campeonato | Rotina | O que aparece |
|---|---|---|
| 1 liga | `dI` | Países com humano (`Z.ei`) ou marcados (`Z.jr`) que jogam hoje (`Z.ej`), um bloco por país. Sem nenhum, o país preferido `SR.bz()`. |
| 2 copa | `dF` | Copas de países com humano jogando hoje (`Z.ju`, `Z.jv`). Senão, o país do 1º técnico (`SR.bA()`). |
| 3 estadual | `dE` | Estaduais com humano (`w.ei`, `w.ej`). Senão, o 1º disponível entre `SR.by()`, SP, RJ, RS, PR e MG. Com `verEstaduaisAgrupados`, todos numa tela. |
| 10 regional | `dD` | Todos os regionais do dia |
| 7, 8, 9, 11 | `dA`, `dz`, `dC`, `dB` | Todos os campeonatos do dia, sem filtro |
| demais | `dy` | Um bloco por campeonato com humano ou com `verJint` marcado (`best.s.b(at)`) |

3. `dJ()` mostra o próximo bloco. Sem blocos, segue com `best.f.at()`.

**Índices de `verJint`** (`best.f.ae`):

| Índice | Competição |
|---|---|
| 0–5 | tipo 4, subtipos 0..5 |
| 6 | Liga Europa |
| 7 | Sul-Americana |
| 8 | Copa nacional |
| 9 | Estadual |
| 10 | Regional |
| 11 | Copa do Mundo |
| 12 | Recopa |
| 13 | Supercopa |
| 14 | Conference |
| 15 | Torneio amistoso |
| 16 | outras copas de seleções |
| 17 | Eliminatórias |
| 18 | Liga das Nações |
| 19 | Mundial |
| 20 | Finalíssima |

Valores padrão: falso nos índices 2–5 e 15; verdadeiro nos demais (`best.f.verJint`).

---

## Lacunas

- **Janela de transferências:** não há tipo de data nem evento de calendário com esse papel em `best.a`/`best.f`. A regra de mercado pertence ao estudo de gestão e não foi localizada aqui.
- **Partida com humano:** a simulação do jogo de pênaltis com humano, a semântica exata de `hk()`/`hP()` e a ausência de prorrogação foram vistas só no caminho sem humano.
- **Interpretações não confirmadas:**
  - os índices de `ah.d()` como pontos, vitórias, saldo e gols (no comparador `h.K`);
  - `c.A()` como jogos no desempate da artilharia;
  - o efeito de `ah.kJ()` (salário), `ah.w(…,4)` (lançamento mensal) e `best.ay.zw()` (propostas).
- **Fluxos não seguidos até o fim:**
  - o código 1068 (liga de 68 times);
  - os códigos 1801–1805;
  - a ordem real de preenchimento da reserva de perdedores da Conference e da Liga Europa;
  - a possível falha de `f.q.Bu` quando a sede é sul-americana (47 classificados).
- **Fontes indiretas:**
  - as datas da seção 2.2 vêm da reprodução do algoritmo, não de um calendário observado em jogo;
  - os valores dos `.cfg`/`.ces` foram extraídos pelo subestudo, e só Brasil, Espanha, SP e RJ foram detalhados.
- **Não estudado:** o mapeamento completo de ids de país e de estado para nomes (feito só pelas siglas do código) e os prêmios em dinheiro de cada fase.
- **Encadeamento das telas:** `a.cR.pl`/`AC` no fim da temporada foi lido só no trecho de `best.f.aa`.
