# Motor de partida do Brasfoot 22-23

Estudo de engenharia reversa do executável original limpo (SHA-256 `2fa65476…bb1c`), feito sobre a fonte decompilada com Vineflower 1.11.1. Todas as referências usam os nomes ofuscados originais (`pacote.Classe.método` ou `Classe.campo`). O que não foi lido diretamente está marcado como **(inferido)**. Nenhuma partida foi executada: os números de exemplo são cálculos feitos a partir das constantes do código.

## Resumo

1. A partida é o objeto `best.I`; o gerador de lances é `c.b`, que a cada minuto sorteia um duelo de posse, um duelo de ataque contra defesa e, se houver chute, o resultado do chute (gol, defesa ou fora).
2. As estatísticas da partida (posse, finalizações, no gol, fora, desarmes, erros de passe) não são sorteadas à parte: são subprodutos diretos desses duelos, gravados em `best.I` pelo próprio `c.b.vO`.
3. Cartões, lesões e substituições da IA são sorteados por outra rotina (`best.I.a(I,int,int)`), independente da força dos jogadores; faltas nunca são contadas e escanteios não existem.
4. Nenhuma estatística retroalimenta o gerador, mas posse, desarmes, finalizações e chutes no gol entram na **nota** de cada jogador (`best.F.a(at,I,int,int,ah)`), que alimenta médias por competição e listas de destaques.
5. A tela `a.dV` só executa ao vivo as partidas com time humano; as demais são pré-simuladas inteiras por `best.I.V()` e apenas reveladas minuto a minuto.

## 1. Mapa das classes

| Classe | Papel no motor |
|---|---|
| `best.I` | Partida: times, escalações, placar, lances, estatísticas, regras de mata-mata, disciplina, IA de substituição |
| `c.b` | Gerador de lances por minuto (duelos, chute, gol, autor, assistência) |
| `best.A` | Lance (gol, cartão, lesão, substituição, pênalti perdido, assistência) |
| `best.F` | Jogador (força, atributos, características, energia, nota da partida) |
| `components.s` | Estatísticas do jogador na partida (transitórias, `F.fo`, acesso `F.gB()`) |
| `best.ah` | Time (táticas `kj()`, escalação automática, batedores) |
| `best.aq` | Constantes (formações, tabelas de posição, textos de tática, gramado) |
| `a.dV` | Tela de partida (temporizador, minuto, placar em destaque, tabela de jogos) |
| `components.v` | Linha da tela de partida: partida + placar exibido + último lance |
| `a.gh` / `a.gb` | Escolha do batedor e cobrança de pênalti durante o jogo |
| `a.C` / `a.bg` | Ordem dos batedores e disputa de pênaltis de desempate |
| `a.cD` | Diálogo de escalação/substituição/tática aberto durante a partida |
| `best.s` | Agrupa as partidas do dia por competição e abre `a.dV` |
| `best.f` (`c.a.SR`) | Estado global; processa o dia e o pós-jogo (`f.as`) |

### 1.1 Campos de `best.I`

| Campo | Acesso | Conteúdo |
|---|---|---|
| `fz` / `fA` | `hc()` / `hd()` | mandante / visitante (`best.ah`) |
| `fB` / `fC` | `hu()`/`hv()` ; `hw()`/`hx()` | gols reais do mandante / visitante |
| `fx` | `hy()` | competição (`best.at`); `fx.b()` é o tipo da competição |
| `fw` | `ht()` | fase ou rodada (`best.L`; `f.z` em mata-mata) |
| `dH` | `ev()` | estádio (`best.v`) |
| `dq` | `dX()` | condição do gramado, índice em `aq.pb` (Excelente, Muito Boa, Ruim, Precária) |
| `fD` / `fE` | `hT()` / `hN()` | público por setor (G, A, Cd, Cm) / renda |
| `fF` / `fG` | `hl()` / `hm()` | titulares iniciais |
| `fH` / `fI` | `hn()` / `ho()` | reservas |
| `fJ` / `fK` | `hp()` / `hq()` | jogadores em campo agora |
| `fL` / `fM` | `ie()` / `if()` | jogadores que entraram |
| `fN` | `hE()` | lista de lances (`best.A`) |
| `fQ` | `ib()` | acréscimos `[1º tempo, 2º tempo, -1]` |
| `fR` | `aR(i)` / `aS(i)` | substituições restantes, início `{5, 5}` |
| `fS`, `fT`, `fU` | privados | amarelos, vermelhos e lesões já sorteados na partida |
| `fW` | `hz()` | **posse de bola em %**, início `{50, 50}` |
| `fX` | `hY()` | duelos de posse vencidos |
| `fY` | `hA()` | **finalizações** |
| `fZ` | `hZ()` | **finalizações no gol** (inclui gols) |
| `ga` | `ia()` | **finalizações para fora** |
| `gb` | `hB()` | **desarmes** |
| `gc` | `hC()` | **erros de passe** |
| `gd` | `hD()` | **faltas** (nunca escrito; ver §9) |
| `ge`, `gf`, `gj` | `hS()`, `hP()`, `hO()` | partida decisiva de mata-mata, pênaltis permitidos, jogo de volta |
| `gg`, `gh` | `hK()`, `hL()` | placar do jogo de ida |
| `gi`, `gk` | `hQ()`, `hR()` | placar e vencedor da disputa de pênaltis |
| `gl` | `id()` | casas (slots) dos titulares `[2][11]` |
| `gm`, `gn` | privados | minutos programados de substituição da IA |
| `go` | `hW()` | gerador `c.b` (transitório) |

Os nomes `hA`…`hD` são os **getters**; os campos reais são `fY`, `gb`, `gc`, `gd`.

### 1.2 Tipos de lance (`best.A.w`, getter `b()`)

| `w` | Lance | Subtipo `dz` (`el()`) | Ícone (`A.es`) |
|---|---|---|---|
| 1 | Gol | 1 normal, 2 contra, 3 pênalti, 4 falta, 5 olímpico (`A.er`) | `egol` / `egolc` |
| 2 | Cartão amarelo | — | `eca` |
| 3 | Segundo amarelo (expulsão) | — | `ecacv` |
| 4 | Vermelho direto | — | `ecv` |
| 5 | Lesão | — | `ect` |
| 6 | Substituição (`eo` sai, `ep` entra) | — | `esubs` |
| 7 | Pênalti perdido | — | `egolc` |
| 8 | Assistência (lance-espelho do gol) | — | — |

Outros campos: `dy` time (`cu()`), `dA` minuto (`em()`), `dB` tempo (`en()`), `dC`/`dD` jogadores (`eo()`/`ep()`), `dE` já exibido (`isDone()`), `dF` lado 0/1 (`et()`), `dG` pênalti já resolvido (`eu()`).

### 1.3 Casas (slots) e posições

A escalação usa casas 1–25 (`F.fT()`, campo `F.eR`). A tabela `aq.sE[casa] = {posição, lado, perfil}` liga a casa à posição natural (0 goleiro, 1 lateral, 2 zagueiro, 3 meia, 4 atacante):

| Casas | Função | Uso no gerador |
|---|---|---|
| 1 | goleiro | `c.b.eB` |
| 2, 9 | laterais | defesa (`c.b.eE`) |
| 3–8 | zagueiros | defesa; contagem de zagueiros (`c.b.eD`) |
| 10, 17 | alas | meio (`c.b.ez`) |
| 11–13 | meias de contenção | meio |
| 14–16 | meias ofensivos | meio |
| 18, 25 | pontas | 25 conta no ataque; **18 não** (`c.b.eA` usa 19–25) |
| 19–24 | atacantes | ataque (`c.b.eA`) |

Jogador fora da posição natural: `F.gF()` (casa ≠ `aq.sE[casa][0]`, com exceção das alas 10/17).

## 2. Ciclo de vida de uma partida

### 2.1 Criação

- Construtor `best.I(L,int,ah,ah,int,at,v)`: guarda fase, times, dia e competição; escolhe o estádio (`ah.ev()` do mandante, estádio da seleção em eliminatórias `fx.b()==9`, estádio da final em continentais tipos 4/6/12); registra a partida no dia do calendário (`best.a.a(I)`); competições tipo 5 e 15 ficam sem estádio. Lê a condição do gramado (`dq = dH.dX()`).
- `best.I.hb()` sorteia o **roteiro de substituições da IA** de cada lado:
  - `gn` (substituições por placar): dois minutos distintos entre 19 e 38; um terceiro com 69% de chance;
  - `gm` (substituições por cansaço): dois minutos num de três intervalos (9%: 5–15; 40%: 16–35; 51%: 36–42); um terceiro entre 43 e 47 com 79% de chance; um quarto com 49%.

### 2.2 Escalação

- Times humanos: definidos pelo jogador na tela de escalação (fora deste domínio). Se a lista em campo estiver vazia quando o gerador nasce, `c.b.<init>` imprime "erro escala" e escala automaticamente.
- Times da IA: `best.ah.kh()` roda no início do processamento do dia (`best.f`, antes de `I.he()`) e chama `ah.a(ah,I,int,int,boolean)` para cada time não humano ainda não escalado (`ah.kf()`):
  1. jogadores elegíveis (`F.a(I,false)`: sem lesão `F.fP()` e sem suspensão `F.c(at)`), ordenados pelo comparador `h.a.abh`;
  2. formação sorteada (índice em `aq.sJ`, nomes em `aq.rB`):

| Índice | Formação | Chance IA |
|---|---|---|
| 1 | 5-4-1 | 2% |
| 2 | 5-3-2 | 2% |
| 3 | 4-5-1 | 3% |
| 4 | 4-4-2 | 31% |
| 5 | 4-4-2 defensivo | 11% |
| 6 | 4-4-2 ofensivo | 11% |
| 7 | 4-3-3 | 5% |
| 8 | 4-3-3 defensivo | 7% |
| 9 | 3-5-2 | 18% |
| 10 | 3-4-3 | 2% |
| 11 | 4-2-3-1 | 8% |
| 12 | 4-2-3-1 Alas | 0% (só humano) |

  3. para cada casa da formação, `ah.a(ArrayList,int,boolean,boolean)` procura o jogador cuja posição, lado e perfil batem, relaxando os critérios em ordem (`aq.sH`); 7 reservas pelas casas de `aq.sI`;
  4. táticas sorteadas a cada partida: estilo 70% Equilibrado, 10% Ataque total, 20% Contra-ataque; marcação 65% Leve, 30% Pesada, 5% Muito pesada; foco 70% Pelo meio, 30% Pelas laterais. Gravadas em `ah.nq` = `kj()` = `{formação, estilo, marcação, foco}`.
- `best.ah.a(I,ah,int)` calcula uma "força da escalação" em `I.fO`/`fP` (penaliza fora de posição e excesso de zagueiros/meias/atacantes), mas não encontrei chamador dela nem leitor de `hr()`/`hs()`.

### 2.3 Preparação do dia (`best.I.he()`)

Para cada partida do dia: define o texto da rodada (`I.o(hG())`), troca o estádio em sedes rotativas (tipos 7, 13, 14, 15 e repescagem `ze()==7701`) e chama `I.V()`.

`I.V()` faz, para **todas** as partidas:
- calcula público e renda pelo estádio (`best.v.b(I)` → `I.j(fD)`, `I.aW(fE)`);
- configura o mata-mata (`f.z`): se for jogo de volta (`zr()==2`), lê o placar da ida (`f.z.o(I)`) para `gg`/`gh` e marca `gj`; se for jogo único, marca `ge`; `gf = !f.z.zA()` (pênaltis permitidos).

Se nenhum dos times for humano, `V()` **simula a partida inteira** (§2.4). Depois, `best.f` decide se a tela de partida aparece (`best.s.dw()`: sempre que houver humano no dia; senão, conforme a opção por competição `getVerJint`). Em caso positivo `best.s.dx()` agrupa as competições e abre `a.dV.Y(lista)`; ao fim de todos os grupos (`best.s.dJ`) chama `best.f.at()` (pós-jogo). Sem tela, `best.f.at()` é chamado direto.

### 2.4 Partida não assistida (pré-simulada) — `best.I.V()`

```
fQ[0] = aleatório 0..2 ; fQ[1] = aleatório 1..5
para minuto = 0 .. 44+fQ[0]:  disciplina(I, 1º tempo, minuto); lance = gerador.vO()
substituições de intervalo da IA: I.m(2, 0)
para minuto = 0 .. 44+fQ[1]:  disciplina(I, 2º tempo, minuto); lance = gerador.vO()
se mata-mata decisivo, pênaltis permitidos e empate (I.hk()): disputa sorteada
```

- 1º tempo: 45 a 47 passos; 2º tempo: 46 a 50 passos (os acréscimos são sorteados).
- Cada lance recebe minuto e tempo; um gol com assistente gera também o lance tipo 8.
- Os lances ficam em `hE()` e são revelados na tela à medida que o relógio passa (§10).

### 2.5 Partida assistida (ao vivo) — `a.dV`

Só as partidas com time humano (`components.v.ei()`) são simuladas ao vivo:

```
temporizador GO dispara (sem repetição) → qa():
  GT += 1
  1º tempo e GT > 48  → intervalo qg(): GT = 0, dB = 2
  2º tempo e GT >= 51 → fim qc()
  senão aa(false):
     para cada partida com humano: se ib()[dB] <= GT: I.q(GT, dB)
     revela todos os lances pendentes com tempo == dB e minuto <= GT
     se houver pedido de pausa (GV >= 0): abre a.cD (modal), depois GV = -1
     se GZ: reagenda GO (oR)
```

- `best.I.q(minuto, tempo)` cria o gerador na primeira chamada, roda a disciplina (`I.a(I,tempo,minuto)`) e um `c.b.vO()`.
- Ao vivo, o 1º tempo tem os minutos 1–48 (48 passos) e o 2º tem 0–50 (51 passos); `fQ` fica `{0,0,-1}`, então a condição `ib()[dB] <= GT` é sempre verdadeira. O rótulo mostra o minuto até 44 e "Acréscimos" de 45 em diante (`a.dV.qa`).

### 2.6 Intervalo

`a.dV.qg()`: zera o minuto, passa ao 2º tempo; se a opção `getVerJanelaSubs()==1`, toca o som de intervalo e abre `a.cD` para cada partida com humano; em seguida chama `I.m(2,0)` (substituições de intervalo da IA) **apenas nas partidas com humano** (as outras já fizeram isso em `V()`).

### 2.7 Fim, prorrogação e pênaltis

- `a.dV.qc()`: marca `GU` (fim), toca o som, chama `qe()` (se o placar real `hu()` divergir do exibido `tT()`, recalcula `fB`/`fC` contando os lances tipo 1 por `I.hF()`), monta a lista de disputas `qd()` e abre os diálogos de pênaltis, e chama `best.s.dJ()`.
- **Não há prorrogação**: nenhuma rotina do motor simula tempo extra (a palavra só aparece em texto de empréstimo, `best.ar`).
- Critério de empate em mata-mata (`best.I.hk()`, inferido em parte pela ordem das comparações): vitórias nos dois jogos, depois gols agregados, depois gols fora (se `f.z.zv()`); persistindo, vai aos pênaltis (exceto a competição `BI()==2129`, que nunca decide por pênaltis).
- **Disputa sem tela** (`I.V()`): dois números de 2 a 8; se o do mandante for maior ou igual, ele vence por `x × (x−1)`; senão o visitante vence por `x × (x+1)`. O mandante vence com 4/7 ≈ 57% (cálculo). Resultado em `gi` e vencedor em `gk`.
- **Disputa com tela** (`a.dV.qd` → `a.dV.g(I)`): partidas com humano sempre; sem humano só se `getVerDecisaoPenNaoHumano()==1`, e então o resultado sorteado em `V()` é substituído. O humano ordena os batedores em `a.C`; a IA usa a ordem do comparador `h.a.abg`. Em `a.bg.nM` cada cobrança converte com **70% fixos**, sem atributos; cinco cobranças por lado com decisão antecipada, depois alternadas até desempatar (`a.bg.cP`). O resultado vai para `I.i(gi)` e `I.u(vencedor)`.

### 2.8 Pós-jogo — `best.f.as()`

Para cada partida do dia:

| Chamada | Efeito |
|---|---|
| `I.a(true)` | marca como jogada |
| `I.hg()` | confronto direto (`best.T`), campanha do time por competição (`ah.e(I)`: jogos, gols, vitórias, pontos), avaliação do técnico (`al.e(I)` e, nos tipos 1–6, 8, 10, `al.a(I,false,-1)`) |
| `I.hi()` | zera o contador de amarelos da partida (`F.aw(0)`) e cumpre suspensão (`F.f(at)`) |
| `I.hf()` | renda para o mandante humano (`ah.v(fE,5)`), exceto tipos 5 e 7 |
| `I.hh()` | presença e nota de titulares e de quem entrou (§8); credita gols (exceto contra) e cartões por competição |
| `ah.I(false)` | libera os times para a próxima escalação |
| `I.a(null)` | descarta o gerador |

Depois, `F.fr()` recupera a energia de todos os jogadores (§8.3).

## 3. Gerador de lances (`c.b`)

### 3.1 Força de um jogador — `c.b.B(F)`

- Modo padrão: `F.fi()` (força, campo `eq`).
- Modo "habilidade individual" (`SR.isHabilidadeIndividual()`): soma ponderada dos atributos conforme a casa (Gol `gK`, Desarme `gN`, Armação `gO`, Finalização `gP`, Velocidade `gJ`, Técnica `gL`, Passe `gM`; nomes em `a.dz`):

| Casas | Pesos |
|---|---|
| 1 | Gol 0,60; Téc 0,15; Vel 0,15; Pas 0,10 |
| 3–8 | Des 0,50; Téc 0,10; Vel 0,25; Pas 0,10; Arm 0,05 |
| 2, 9 | Des 0,40; Vel 0,10; Téc 0,10; Pas 0,30; Arm 0,05; Fin 0,05 |
| 11–13 | Des 0,40; Vel 0,15; Téc 0,10; Pas 0,20; Arm 0,10; Fin 0,05 |
| 14–16 | Des 0,05; Vel 0,10; Téc 0,10; Pas 0,25; Arm 0,40; Fin 0,10 |
| 10, 17 | Des 0,05; Vel 0,25; Téc 0,15; Pas 0,25; Arm 0,20; Fin 0,10 |
| 19–24 | Vel 0,25; Téc 0,25; Pas 0,05; Arm 0,05; Fin 0,40 |
| 18, 25 | Vel 0,25; Téc 0,15; Pas 0,15; Arm 0,05; Fin 0,40 |

- Fora de posição (`F.gF()`): ×0,5. Mínimo 1.
- Redutores por competição (zebra controlada):
  - tipo 7 (seleções): jogador da nacionalidade do time com reputação < 3 ×0,65, = 3 ×0,85, = 4 ×0,95;
  - tipo 4 (inferido: continental principal): clube com reputação < 3 ×0,75, = 3 ×0,85, país 29 ×0,9;
  - tipo 5: reputação < 3 ×0,55, = 3 ×0,75, `gg()≠0` ×0,9;
  - tipo 1 (liga nacional): reputação < 3 ×0,85, = 3 ×0,95;
  - tipos 2 e 3 (copas e estaduais): se o mandante tem reputação < 3 e o visitante ≥ 3, os jogadores do visitante ×0,8.
- Resultado final ÷ 10 (força 75 → 7,5).

### 3.2 Força dos setores

| Método | Setor | Regra |
|---|---|---|
| `c.b.ez(t)` | meio | (bônus de marcação + soma de até 5 jogadores nas casas 10–17) ÷ 5; menos de 3 → 0,01. Bônus: Leve 0, Pesada 0,04, Muito pesada 0,08 (`kj()[2]`) |
| `c.b.eE(t)` | defesa | soma de até 5 jogadores nas casas 2–9 ÷ 5; menos de 3 → 0,01 |
| `c.b.eA(t)` | ataque | soma de até 3 jogadores nas casas 19–25 ÷ 3; nenhum → 0 |
| `c.b.eB(t)` | goleiro | força do jogador na casa 1; fora de posição → ×0,2 arredondado para inteiro |
| `c.b.eC(t)` | finalizador | força do jogador sorteado por `vU()` |
| `c.b.eD(t)` | zagueiros | quantidade nas casas 3–8 |

Os primeiros jogadores da lista em campo dentro de cada faixa entram na conta; a ordem da lista importa quando há mais jogadores que o limite.

Diferenças viram pesos por `c.b.a(x,y) = (x−y)/k` com `k = 8` (11 a partir da 5ª temporada, `SR.H() >= 5`) e `c.b.b(x,y) = (x−y)/k` com `k = 8` (10 a partir da 5ª temporada). `SR.H()` é o contador de temporadas (`best.f.ah` incrementa; usado para girar sedes em `f.v.yD`) **(inferido)**. O ramo `H() >= 9 → 12` é inalcançável.

### 3.3 Passo do minuto — `c.b.vO()`

O gerador guarda `TB`, o time com a iniciativa no minuto: sorteado no início (`vN`) e **alternado a cada minuto** (`vP`). Cada time ataca em metade dos minutos.

```
vencedor = duelo_de_posse()                       (vR)
se vencedor == TB:
    se duelo_ataque_defesa() == ataque:            (vS)
        finalizações[TB] += 1 ; lance = chute()    (vT)
    senão 50%: desarmes[outro] += 1 ; 50%: erros_de_passe[TB] += 1
senão 50%: desarmes[outro] += 1 ; 50%: erros_de_passe[TB] += 1
TB = outro time
```

**Duelo de posse (`vR`)**: pesos `55·(1 + Δmeio/k)` para `TB` e `45·(1 − Δmeio/k)` para o outro (mínimo 0,2 no fator). Mandante com iniciativa em campo não neutro: +0,3 no fator. Quem vence soma 1 em `I.fX` e a posse `I.fW` é recalculada como porcentagem dos duelos vencidos (`c.b.eF`, `aq.A`). O estilo (`kj()[1]`) é lido em `vR` e descartado.

**Duelo de ataque (`vS`)**: fator do ataque `1 + (ataque − defesa)/k`, da defesa `1 + (defesa − ataque)/k`; pesos 50/50. Sem atacantes, o ataque vale 0,1; sem defesa, a defesa vale 0,1 — mas o piso 0,2 aplicado depois anula esses 0,1. Mandante com iniciativa em campo não neutro: +0,3 no ataque. **Só quando um dos times é humano**: se o time que defende não tem zagueiro (casas 3–8), defesa = 0,1; com um só zagueiro, 0,05 (esses valores ficam, pois vêm depois do piso).

**Campo neutro**: `TD = I.hX()`, verdadeiro para competições dos tipos 5 e 7 (a expressão tem precedência ambígua: `fx != null && tipo==5 || tipo==7`).

### 3.4 Chute — `c.b.vT()`

| Resultado | Peso base (`TU`) | Fator |
|---|---|---|
| gol | 5,5 | 1 |
| no gol, defendido | 35,55 | `1 + (goleiro − finalizador)/k` |
| para fora | 15,0 | `1 + (defesa − ataque)/k` |

- Saturação por gols do mesmo time na partida (`c.b.zA`): ≥ 3 gols → peso do gol 4,5 e defesa 40,55 (`TV`); ≥ 5 → 3,0 (`TW`); ≥ 6 → 0,5 (`TX`). Com ≥ 2 gols e adversário com reputação 2+ acima, usa `TW`.
- Partida com humano: sem zagueiro no time que defende, o fator de defesa do goleiro é multiplicado por 0,2; com um zagueiro, por 0,4 (ambos arredondados para inteiro, depois piso 0,2).
- Campo não neutro: mandante chutando soma 0,1 ao fator do goleiro e **substitui** o fator de "fora" por (fator do goleiro + 0,1); visitante chutando subtrai 0,1 e usa (fator do goleiro − 0,1). Com isso a força da defesa deixa de influir no chute fora quando o campo não é neutro.
- Saídas: gol → cria o lance (§3.5) e soma em `I.fZ`; defendido → `I.fZ` e `components.s.tL()` do finalizador; fora → `I.ga`. `c.b.TG` conta os chutes.

**Escolha do finalizador (`c.b.vU`)**, sem goleiro: peso por casa (`c.b.Tx`) 2–9 → 1; 10 → 8; 11–13 → 4; 14–17 → 8; 18–25 → 22; característica Finalização (9) +4; Cabeceio (5) +2, e +2 se for zagueiro. Características em `aq.qM`.

### 3.5 Montagem do gol — `c.b.a(A,F)`

Subtipo sorteado em mil: 90% normal, 5% pênalti, 3% falta, 1% contra, 0,5% olímpico, 0,5% normal.

| Subtipo | Autor do lance | Observação |
|---|---|---|
| normal | finalizador | pode ter assistência |
| pênalti | batedor de faltas `ah.ke()` se em campo | em partida com humano o gol **não** é somado: vira cobrança na tela (§7) |
| falta | batedor de faltas `ah.ke()` se em campo | — |
| olímpico | batedor de escanteios `ah.lq()` se em campo; se o finalizador for goleiro, vira normal | — |
| contra | defensor sorteado por `c.b.vV` | sem candidato, vira normal |

- **Assistência (`c.b.C`)**, só no gol normal: 19% sem assistência; senão sorteio no próprio time (exceto o autor) com peso por casa (`c.b.Ty`: goleiro 1; 2 e 9 → 10; 3–8 → 2; 10 e 17 → 10; 11–13 → 4; 14–16 → 20; 18–25 → 10) mais características: Passe +10 (+5 com Armação); Armação +2 (+2 se a 1ª for Drible); Drible +2 (+2 se a 1ª for Velocidade); Velocidade +1 ou +2 (as duas passadas do sorteio usam valores diferentes; +2 se lateral); Cruzamento +5 (+2 se lateral); marcação Pesada (`kj()[2]==1`) dá +20 a laterais (provável troca do índice do foco pelo da marcação, **inferido**). Assistência soma em `components.s.gV()` e na estatística da competição (`F.a(8,ah,at)`).
- **Gol contra (`c.b.vV`)**: peso por casa no time que defende (`c.b.Tz`): goleiro 1; 2 e 9 → 5; 3–8 → 18; 11–13 → 5; demais 1. O defensor recebe `components.s.tE()`.
- **Contagem**: salvo o pênalti em partida com humano, soma `c.b.zA` (saturação) e o placar real (`I.hv()`/`hx()`).
- **Gols do jogador na partida** (`components.s.z()`, usado só na nota): o finalizador original recebe `z()` duas vezes nos gols normais, de falta e olímpicos, uma vez no pênalti, e uma vez no gol contra (mesmo sem ser o autor do lance).

`best.I.a(F,int,int)` tem outra tabela de subtipos por tempo, mas não encontrei chamador.

### 3.6 Ordem de grandeza (cálculo, sem execução)

Times de mesma força, sem humano:

| Situação | Duelo de posse | Ataque vence | Gol por chute | Gol por minuto de iniciativa |
|---|---|---|---|---|
| Campo neutro | 55% | 50% | 9,8% | 2,7% |
| Mandante com iniciativa | 61,4% | 56,5% | 8,8% | 3,05% |
| Visitante com iniciativa | 55% | 50% | 11,1% | 3,05% |

Com cerca de 47 minutos de iniciativa por time, isso dá perto de 13 finalizações e 1,4 gol por time. O mando aumenta o volume de chutes e reduz a eficiência por chute, e os dois efeitos quase se anulam para times iguais. Exemplo de desnível: meio-campo 7,0 × 5,0 (k = 8) leva o duelo de posse de 55% a 67%.

### 3.7 O que não entra no gerador

| Fator | Situação no código |
|---|---|
| Energia/cansaço | não entra em `c.b.B`; só decide substituições da IA (§5.2) e duração de lesão (§5.1). `F.fU()` (força × energia) só é usado na "força da escalação" sem chamador |
| Gramado | `I.dX()` só é lido por telas (`a.bz`, `a.cD`, `a.dq`) |
| Clima | não existe |
| Torcida/público | define renda (`best.v.b`), não o jogo |
| Moral do jogador | não existe campo de moral no jogador; o técnico tem confiança da diretoria e da torcida (`al.of`/`al.og`) |
| Capitão (`ah.kd()`) | sem efeito no gerador |
| Estilo e foco | sem efeito (§4) |
| Sementes | cada sorteio usa `new Random()` ou os `Random` da instância, sem semente fixa; a mesma partida não se reproduz |

## 4. Táticas

| Tática | Valores (`aq`) | Efeito no motor |
|---|---|---|
| Formação (`kj()[0]`) | `aq.rB`/`aq.sJ` | indireto: define quais casas estão ocupadas e, com isso, quem conta em meio (10–17, até 5), defesa (2–9, até 5) e ataque (19–25, até 3); menos de 3 no meio ou na defesa derruba o setor para 0,01. Não há leitura de `kj()[0]` durante a partida |
| Estilo (`kj()[1]`) | Equilibrado, Ataque total, Contra-ataque (`aq.rC`) | **nenhum**: lido em `c.b.vR` e descartado |
| Marcação (`kj()[2]`) | Leve, Pesada, Muito pesada (`aq.rE`) | meio-campo +0, +0,04, +0,08 (`c.b.ez`); amarelo mais provável: o denominador do sorteio recebe +30, +10, +0 (`I.a(I,int,int)`); Pesada dá +20 ao peso de assistência dos laterais (`c.b.C`) |
| Foco (`kj()[3]`) | Pelo meio, Pelas laterais (`aq.rD`) | **nenhum** no motor (só telas `a.bz`, `a.cD`, `a.hF`) |

Mudanças feitas pelo humano em `a.cD` durante a partida (`a.cD.pc`, trocas de casa) valem a partir do minuto seguinte, porque o gerador lê `kj()` e as casas a cada chamada.

## 5. Disciplina, lesões e IA do técnico — `best.I.a(I,int,int)`

Chamada a cada minuto, antes de `c.b.vO()`, nas partidas pré-simuladas e ao vivo.

### 5.1 Cartões e lesões

1. Lado: mandante com 44% (`nextInt(100) > 55`), visitante com 56%; a marcação considerada é a do lado sorteado.
2. Faixa do minuto: < 15, < 30, resto.
3. A cada minuto múltiplo de 7 (inclusive o 0), `I.l` desconta energia de todos em campo (goleiro só no 2º tempo).
4. Denominadores (1 chance em N):

| Evento | 1º tempo (faixas) | 2º tempo (faixas) |
|---|---|---|
| Amarelo | 70 / 40 / 30 + marcação | 45 / 40 / 30 + marcação |
| Vermelho direto | 1200 / 900 / 800 | 800 / 700 / 550 |
| Lesão | 1500 / 1000 / 800 | 800 / 600 / 600 |

   Ajustes ao amarelo: mais de 5 amarelos na partida → ×2; 2 ou mais vermelhos → passa a 2× o denominador do vermelho; 1 ou mais lesões → passa a 5× o denominador da lesão (o ramo "> 10 amarelos" é inalcançável).
5. Sorteio em cascata: amarelo; senão vermelho; senão lesão; senão, no 2º tempo a partir do minuto 5, substituições da IA (`I.m`).
6. Quem recebe (grupos de casas `aq.sS`): amarelo (`I.H`) 25% casas 10–13, 15% 14–17, 25% 3–8, 8% 2–3, 9% 8–9, 15% 19–24, 3% goleiro; vermelho (`I.J`) 40% / 15% / 25% / 5% / 10% / 5% / 0,5% goleiro; lesão (`I.I`) 30% / 20% / 14% / 8% / 12% / 16% / 0,2% goleiro. Grupo vazio = sem cartão, mas o contador de amarelos sobe mesmo assim.
7. Amarelo: `F.gj()` soma; no segundo vira lance tipo 3. O jogador recebe `tG` (e `tH` no tipo 3/4).
8. Expulsão (tipos 3 e 4): o jogador sai da lista em campo. IA com substituições e casa ≤ 13 recompõe: tira um atacante (18–25), senão um meia (14–17), e põe um reserva da posição do expulso; goleiro expulso libera qualquer casa 2–25.
9. Lesão (tipo 5): `F.p(ah)` define os dias (base 0–13; +1 a +3 por idade até 35; acima de 35 soma 5–24, e acima de 45 mais 10; extras de 70 dias com 1%, 40 com 3% e 20 com 6%; energia < 10 ou < 50 soma 5 ou 1, mas para jovens até 20 anos esse acréscimo é descartado). Jogador de 35+ perde 5 de força. Na IA, sai e é trocado por reserva da mesma casa (sem pôr goleiro no lugar de linha).
10. Suspensão por vermelho (`F.a(int,at,ah)`, no pós-jogo): 70% 1 jogo, 20% 2, 7% 3, 2% 5, 1% 10.

### 5.2 Substituições da IA durante o jogo — `best.I.m(2, minuto)`

Só no 2º tempo e para lados não humanos com substituições restantes:

| Momento | Mandante | Visitante |
|---|---|---|
| Intervalo (minuto 0) | perdendo por 1+: 50% de troca aleatória | perdendo por 2+: 50% de troca aleatória |
| Minutos `gn` (19–38) | perdendo **ou empatando**: troca aleatória | perdendo por 1+: troca aleatória |
| Minutos `gm` (5–47) | troca por cansaço | troca por cansaço |

- Troca aleatória (`I.a(int,int,int,int,ArrayList)` tipo 2): sorteia um jogador em campo; se ele já entrou, sorteia de novo uma vez; goleiro ou quem já entrou cancelam. A conferência de "já entrou" usa sempre a lista do mandante (`fL`), também para o visitante.
- Por cansaço (tipo 1): primeiro jogador de linha com energia < 60 (a partir do minuto 41: < 90, começando de posição aleatória).
- O substituto é o reserva que melhor encaixa na casa (`ah.a(ArrayList,int,boolean,boolean)`); a troca grava lance tipo 6, consome `fR` e registra em `fL`/`fM`.
- Mudanças táticas da IA durante o jogo: **não há**; as táticas da IA só são sorteadas na escalação (§2.2).
- `best.I.o(int,int)` (troca por energia < 75 com chance crescente no fim) não tem chamador.

## 6. Velocidade, energia e recuperação

- Energia (`F.eK`, `fp()`, 1–100). Perda por tique (`F.fq`): até 20 anos 1; até 25, 2; até 31, 3; até 36, 4; acima, 5. Há 7 a 8 tiques por tempo.
- Recuperação após o dia (`F.fr`), para quem foi relacionado (`F.eL`): time humano +13/+24/+37/+40/+30 por faixa de idade; IA +20/+30/+50/+52/+42; não relacionados +30 a +35.

## 7. Pênalti durante o jogo (partida com humano)

1. O gerador cria o gol subtipo 3 sem somar o placar (`c.b.a`).
2. Quando o minuto do lance chega (`a.dV.a(v,I,A,int)`): toca o som de pênalti; se o time cobrador é humano, abre `a.gh` (escolha do batedor, `A.f(F)`); depois `a.dV.b(v,A)` abre `a.gb`.
3. `a.gb.nO` decide: 70% base; batedor com Finalização (9) ou `F.gm()` → 80%; batedor `F.ff()` +5; goleiro com Defesa Penalty (1) −10; goleiro `gm()` −10; goleiro `ff()` −5.
4. Gol: placar exibido (`v.dJ`), placar real (`hv`/`hx`), saturação (`c.b.eG`), `hA` +1, `hZ` +1, `z()` do batedor.
5. Perda: `hA` +1; `tF()` do batedor; 7 textos; "fora" e "arquibancada" somam em `ia`, os demais em `hZ`; o lance vira tipo 7; nas defesas (textos 0, 3, 5) o goleiro vira `ep()` e recebe `tJ()`.
6. O chute já tinha sido contado em `hA`/`hZ` pelo gerador, então **cada pênalti em partida com humano soma duas finalizações** e, se convertido, dois chutes no gol.

Em partidas sem humano, o pênalti é um gol comum no gerador; a tela só mostra o lance.

## 8. Notas dos jogadores — `best.F.a(at,I,int,int,ah)`

Chamada por `I.hh()` para titulares iniciais e para quem entrou.

| Componente | Regra |
|---|---|
| Minutos jogados | parte de 90; **qualquer** lance em que o jogador é autor (`eo`) ou segundo jogador (`ep`) redefine os minutos como se ele tivesse saído ou entrado naquele minuto (inclusive gols, cartões e assistências) |
| Base (resultado × força) | empate 5,5/5,8/6,2/6,8; vitória 6,0/6,0/6,7/7,2; derrota 5,0/5,2/5,5/6,0 (força ≤ 30, ≤ 60, ≤ 90, > 90) |
| Fora de posição | −1; goleiro fora de posição −2 |
| Meio-campistas (10–17) e **posse** `hz()` | posse maior: +0,3 ou +0,8 (+0,3 se perfil defensivo `F.fF()==0`; +0,5 com Passe ou Armação); posse menor: −0,3 ou −0,8 (−0,5 se perfil defensivo) |
| Estatísticas individuais | gols +0,9; gols contra −1,5; pênalti perdido −1,2 × gols contra (usa o contador errado); amarelos −0,2; vermelhos −0,8; assistências +0,4; chutes defendidos +0,3 |
| Casas 1–13 e **desarmes** `hB()` | mais desarmes que o rival: +0,9 ou +0,6, extras de +0,6 para defensores e volantes; menos: −0,5 e chances de −0,6 |
| Goleiro e **finalizações/chutes no gol** do rival `hA()`/`hZ()` | −0,8; +0,2 por chute no gol sofrido; +1,2 por pênalti defendido; +0,2 se o rival finalizou mais de 10 vezes; por gols sofridos −2 (5+), −1 (2–4), −0,5 (1), +1 (0); −1 se o rival não acertou o gol |
| Casas 1–13 e gols sofridos | sem gols +0,5 (+0,5 defensores; +0,5 com 1/3 de chance para volantes); 2+ gols −0,1 por gol; −0,4 com 1/3 de chance para casas 2–13 |
| Destaques | `F.ff()` +0,4; `F.gm()` +0,6 |
| Limites | máximo 10; < 15 minutos −2,5; < 45 minutos −1; mínimo 2; < 20 minutos com nota 2 → 0 (sem nota) |

Destino da nota: `F.eN` (`gk()`), histórico `F.eU` (`best.J`, média em `F.gn()`), estatística do jogador no clube (`best.k.b`), média por competição (`best.H.i`, `F.a(at,double)`), seleção do torneio quando a competição é `f.B` (`f.B.E`/`F`) e lista de destaques da competição (`best.at.mz`, média > 5).

Pós-jogo do técnico (`best.al.a(I,boolean,int)`): confiança e apoio variam só pelo resultado, pela diferença de nível e pelo mando; não leem estatísticas.

## 9. Estatísticas da partida

### 9.1 Estatísticas do time (`best.I`)

| Estatística | Campo | Escrita | Leitura | Classificação da leitura |
|---|---|---|---|---|
| Posse de bola (%) | `fW` / `hz()` | `c.b.eF` (cada duelo de posse) | `I.ha()` (texto da tela); `a.hk.k` (detalhes); `F.a(at,I,…)` nota dos meias | exibição; **lógica (nota)** |
| Duelos de posse vencidos | `fX` / `hY()` | `c.b.eF` | `c.b.eF` (base da posse) | lógica interna da posse |
| Finalizações | `fY` / `hA()` | `c.b.vO` (ataque vence); `a.gb.nO` (pênalti, gol e perda) | `I.ha()`; `a.hk.k`; `F.a(at,I,…)` nota do goleiro (rival > 10) | exibição; **lógica (nota)** |
| No gol | `fZ` / `hZ()` | `c.b.vT` (gol e defesa); `a.gb.nO` | `I.ha()`; `a.hk.k`; `F.a(at,I,…)` nota do goleiro (+0,2 por chute; −1 se zero) | exibição; **lógica (nota)** |
| Para fora | `ga` / `ia()` | `c.b.vT`; `a.gb.nO` | `I.ha()`; `a.hk.k` | exibição |
| Desarmes | `gb` / `hB()` | `c.b.vO` (defesa vence ou posse perdida, 50%) | `I.ha()`; `a.hk.k`; `F.a(at,I,…)` nota das casas 1–13 | exibição; **lógica (nota)** |
| Erros de passe | `gc` / `hC()` | `c.b.vO` (outros 50%) | `I.ha()`; `a.hk.k` | exibição |
| Faltas | `gd` / `hD()` | **nenhum ponto** | só a primeira string de `I.ha()`, que é montada e descartada (o método devolve a segunda, sem faltas) | nenhuma; sempre 0 |
| Escanteios | — | não existem | — | — |
| Cartões | lances 2/3/4 em `hE()` | `I.a(int,int,I,ah,F,F,int,int)` | tela (último lance), `I.hh` (cartões por competição e suspensão), nota (via `components.s`) | **lógica** |
| Placar | `fB`/`fC` | `c.b.a`, `a.gb`, `I.hF` | resultado, tabela, mata-mata, técnico, nota | lógica |

Pontos de exibição de `I.ha()`: `a.dV.aa` (a cada minuto, só a partida em destaque), `a.cD.mK` e `a.dq`. Exibe posse, finalizações, no gol/fora, desarmes e erros de passe. `a.hk` é a tela de detalhes da partida (mesmos números, com "no gol (fora)").

Ninguém usa os setters `I.d/e/f/g/h(int[])`. As estatísticas ficam no objeto `best.I`, que é serializável (campos não transitórios), e acompanham o save enquanto a partida existir no calendário **(inferido)**.

### 9.2 Estatísticas do jogador na partida (`components.s`, transitório)

Zeradas na criação do gerador (`c.b.<init>` → `F.fe()`).

| Contador | Escrita | Leitura |
|---|---|---|
| `V` gols / `Pd` finalizações (`z()`) | `c.b.a`, `a.gb` | `y()` na nota |
| `Pe` chutes defendidos (`tL`) | `c.b.vT` | `tK()` na nota |
| `Ph` gols contra (`tE`) | `c.b.a` | `tx()` na nota |
| `Pi` pênaltis perdidos (`tF`) | `a.gb` | `ty()` na nota (desconta pelo contador `tx`) |
| `Pj` amarelos (`tG`) / `Pk` vermelhos (`tH`) | `I.a(int,int,I,…)` | `tz()`/`tA()` na nota |
| `cc` assistências (`gV`) | `c.b.a` | `cD()` na nota; `b.aD` (tela) |
| `Pl` pênaltis defendidos (`tJ`) | `a.gb` | `tI()` na nota |
| `Pf`, `Pg` (`tC`, `tD`, `tB`) | nunca chamados | `tu`, `tv`, `tw` nunca lidos |

### 9.3 Contadores internos do gerador (`c.b`)

`zA` (gols, usado na saturação do chute), `TG` (chutes), `TM`/`TP` (duelos de ataque vencidos pelo ataque/defesa), `TN`/`TO` (posse ganha com/sem iniciativa), `TQ` e o `fX` próprio. Fora `zA`, só são lidos pela tela de teste `a.hF`, que simula N partidas entre dois times e mostra "Venceu meio", "Avanços no meio", "Desarmes defesa" e "Chutes totais".

### 9.4 Veredito

- **Origem**: as estatísticas de time são geradas pelos mesmos sorteios que produzem os lances. Cada minuto de iniciativa termina em exatamente uma destas: finalização (que vira gol, no gol ou fora), desarme ou erro de passe. Não há sorteio à parte para as estatísticas, salvo os 50/50 entre desarme e erro de passe e a contagem duplicada dos pênaltis em partida com humano.
- **Influência no resultado**: nenhuma. Nenhum ponto de leitura de `hz`, `hY`, `hA`, `hB`, `hC`, `hD`, `hZ` ou `ia` está no gerador, na disciplina ou nas substituições. O que retroalimenta o gerador é só o número de gols (`c.b.zA`) e os contadores de cartões e lesões (`I.fS/fT/fU`).
- **Influência fora da exibição**: posse, desarmes, finalizações do rival e chutes no gol do rival entram na **nota** dos jogadores. A nota segue para médias por clube e por competição, seleção do torneio (`f.B`) e lista de destaques (`best.at.mz`). Não encontrei leitura das estatísticas de time em finanças, moral, evolução, histórico de confrontos, recordes ou técnico.
- Faltas: sempre zero e não exibidas; escanteios: inexistentes.

## 10. Tela de partida — `a.dV`

| Elemento | Campo | Função |
|---|---|---|
| Temporizador | `GO` (`javax.swing.Timer`, sem repetição) | cada disparo chama `qa()` via `a.ee`; `oR()` reagenda |
| Minuto / tempo | `GT` / `dB` (estáticos) | `qj()` / `en()` |
| Intervalo entre minutos | `d` (ms) | com humano `aq.rz` = 2000, 1200, 700, 450, 220, 100; sem humano `aq.rA` = 1200, 700, 300, 100, 70, 30; `SR.bD()` força 1 ms |
| Rodando | `GZ` | falso enquanto um diálogo de pausa está aberto |
| Pedido de pausa | `GV` | índice da partida cujo `a.cD` abre ao fim do minuto |
| Fim | `GU` | definido em `qc()` |
| Partida em destaque | `GW` (e cópia estática `Hc`) | primeira partida com humano; o painel de placar só aparece se houver uma. **Não existe campo `KS`** |
| Linhas | `vK` (`components.v`) | cabeçalhos por competição e partidas |
| Placar em destaque | `Hn`, `Hp`/`Ho` (nomes), `Hh`/`Hi` (escudos), `Hj`/`Hk` (último lance de cada lado), `Hl`/`Hm` (estádio e público), `Ht` (fase), `xI` (estatísticas `ha()`) | painel `Hr` |
| Cabeçalho | `Hg` (rodada), `uh` (minuto, "Acréscimos", "Intervalo", "Fim de jogo"), `Hf` (barra até 45) | painel `Hq` |
| Tabela de jogos | `Hs` (`b.M`, render `b.aG`) | colunas: estádio e público, mandante, gols, gols, visitante, último lance com ícone |

- **Atalhos** (`a.dV.a(JComponent)`): Espaço e Enter → pausa (`qh()`: `GV = Hc`); F1–F5 → velocidades 0–4 (`setVelocidade`, sempre pela tabela `aq.rz`); na versão registrada, F5 passa à velocidade 5.
- **Cliques**: placar em destaque (`a.dX`) pede pausa da partida em destaque; linha da tabela (`a.ef`) pede pausa daquela partida. A pausa abre `a.cD` (escalação, substituições restantes, táticas, batedores) ao fim do minuto corrente (`a.dV.aa`).
- **Substituição pelo humano**: `a.cD.K` chama `I.a(lado, sai, entra, tempo, minuto, -1)` (no intervalo, minuto 1).
- **Lesão ou expulsão do time humano**: `a.dV.a(v,I,A,int)` abre `a.cD` na hora.
- **Placar exibido** (`components.v.tT/tU`) só sobe quando o lance de gol é revelado; o real (`I.fB/fC`) já está somado.
- **Narração**: não há narração contínua; a tela mostra o último lance de cada linha (`A.er()`). Há textos só no pênalti (`a.gb`) e na disputa (`a.bg`).
- **Sons** (`c.a.dj`, pasta `sons/`): intervalo, fim de jogo, gol a favor do humano, gol contra o humano, pênalti, expulsão, contusão.
- **Outros jogos**: todas as competições do grupo aberto por `best.s` aparecem; partidas sem humano mostram lances pré-simulados conforme `GT` alcança o minuto.

## 11. Comportamentos que parecem erros do original

| Ponto | Efeito |
|---|---|
| `c.b.vT`, campo não neutro | fator de "fora" substituído pelo do goleiro ± 0,1 |
| `c.b.vS` | os valores 0,1 de setor vazio são anulados pelo piso 0,2 |
| `c.b.a` | gols normais contam duas vezes na estatística individual (nota) |
| `a.gb.nO` | pênalti em partida com humano conta duas finalizações |
| `I.a(I,int,int)` | grupo sem jogador ainda soma no contador de amarelos |
| `I.a(int,int,int,int,ArrayList)` | visitante compara com a lista de entradas do mandante |
| `F.a(at,I,…)` | minutos jogados redefinidos por qualquer lance; pênalti perdido desconta pelo contador de gols contra; faixas de finalizações do rival > 15 e > 20 inalcançáveis |
| `c.b.C` | marcação Pesada usada como foco nas laterais (provável); somas diferentes nas duas passadas do sorteio |
| `I.hX` | precedência ambígua na verificação de campo neutro |
| `best.I.hD` | faltas declaradas, nunca contadas |

## 12. Lacunas

- Não li a construção do calendário nem quem cria `best.I` (domínio de competições); os tipos de competição 2, 4, 5, 6, 12–15 estão nomeados por indício.
- `best.I.fV` (lista de `best.E`) e o método estático `I.a(I,int,int,int)` que a consulta não foram rastreados.
- `best.I.hk()`: a ordem de desempate foi lida, mas o significado exato de `gg`/`gh` (lado de cada placar da ida) é inferido.
- A natureza de `F.ff()` e `F.gm()` (destaques, provavelmente craque e jogador de nível mundial) é inferida.
- `SR.H()` como contador de temporadas é inferido.
- Não verifiquei se a média de notas (`F.ab`, `best.H.F`) alimenta evolução de força, valor de mercado ou convocações; achei só a lista de destaques e a seleção do torneio.
- Não verifiquei por quanto tempo os objetos `best.I` (e suas estatísticas) permanecem no save.
- Não há leitura direta de "moral" de jogador no código; se existir sob outro nome fora do motor, não foi encontrada.
- Nada foi executado: as probabilidades da §3.6 são cálculos sobre as constantes.
