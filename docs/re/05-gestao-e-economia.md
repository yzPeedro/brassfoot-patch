# Gestão e economia do Brasfoot 22-23

Estudo de engenharia reversa do executável original limpo (SHA-256 `2fa65476…bb1c`), feito sobre a fonte decompilada (Vineflower 1.11.1) em `data/private/re/src/`. Os nomes de classe seguem o código original (`best.ah`, não o nome do arquivo `best/ah.java`). Valores monetários estão em unidades do jogo, exibidas por `best.C.c(long)` como "mil", "milhão", "milhões" etc.

## Resumo

1. O caixa de cada clube fica em `best.ah.nb`. Só os clubes humanos têm livro-caixa (`best.C`), recebem bilheteria, prêmios e patrocínio e pagam salários, juros e obras. Para a IA o dinheiro praticamente não importa.
2. A receita de bilheteria é calculada por setor (geral, arquibancada, cadeira, camarote). Entram na conta a reputação dos dois clubes, o tipo de competição, a confiança da torcida no técnico e a diferença entre o preço escolhido e o sugerido (`best.v.b`).
3. O mercado tem três vias: compra com preço exigido calculado pela carência do vendedor na posição, compra pelo preço de lista e empréstimo de 366 dias. A aceitação do jogador depende da reputação e do continente dos clubes (`best.l`). A IA faz uma janela no fim da temporada (`best.ag.jO`) e outra durante a liga (`best.ag.b`).
4. Salário e valor de mercado seguem fórmulas fixas (`best.F.fJ`, `best.F.fK`) e são recalculados para todos os jogadores no início de cada temporada (`best.f.af`).
5. A carreira do técnico gira em torno de duas confianças, diretoria e torcida (0–100). Com a da diretoria abaixo de 10, o técnico é demitido. A reputação do técnico (1–5) define as ofertas de clubes e seleções (`best.al`, `best.ay`, `best.Z.a`).

## Mapa das classes deste domínio

| Classe | Papel | Evidência |
|---|---|---|
| `best.ah` | Clube: caixa `nb`, reputação `nc` (0–5), nível `hA` (1–25), divisão, elenco `nd`, juniores `ne`, livro-caixa `nx`, estádio `dH`, técnico `mZ` | construtores, `v`/`w`/`f`, `kK`, `kk` |
| `best.C` | Livro-caixa da temporada e empréstimo bancário | `h`, `i`, `b`, `m`, `l`, `eP` |
| `best.v` | Estádio: setores, preços, condição do gramado, cálculo de público e renda | `N`, `b(I)`, `a(int, ah)`, `h(ah)` |
| `best.B` | Obra de expansão em andamento (data de término e lugares) | `ex` |
| `best.F` | Jogador: força `eq`, salário `et`, valor `eu`, preço pedido `ev`, contrato `eJ`, contusão `eI` | `fJ`, `fK`, `a(ah,int,…)` |
| `best.l` | Negociação e busca de clube comprador | `a(F,ah,int)`, `b(F,ah)`, `a(F,ah)`, `c`, `d` |
| `best.ag` | Mercado da IA e demissão de técnicos da IA | `jO`, `jQ`, `jS`, `jT`, `jU` |
| `best.K` | Promoção de juniores e criação de jogadores sem clube | `a(boolean,F,ah)`, `r` |
| `best.al` | Técnico: confiança da diretoria `of` e da torcida `og`, reputação `nc`, pontos de ranking `oc` | `a(I,…)`, `q`, `kk`, `E`, `i` |
| `best.ay` (instância `c.a.afQ`) | Ofertas de emprego de clubes e seleções | `a(al,…)`, `b(al,…)`, `zw` |
| `components.as` | Mensagem da caixa de e-mails (título em `best.ar.tP`, corpo em `best.ar.tQ`) | construtor |
| `components.t` | Empréstimo ativo (366 dias) | `tM`, `tN` |
| `components.an` | Venda de jogador colocado à venda pelo humano | `uZ`, `iy`, `va` |
| `a.cW`, `a.cl`, `a.cq` | Telas de finanças, estádio e expansão | textos e ações |
| `a.cz`, `a.fy`, `a.jm`, `a.iA` | Proposta de compra, renovação, proposta recebida, ficha de jogador alheio | textos e ações |

## Calendário econômico

`best.f.aS` agenda eventos nos dias do calendário (`best.a`), executados por `best.a.f`.

| Evento (código) | Quando | Efeito | Fonte |
|---|---|---|---|
| `ds` (2): salários | Dia 2 de cada mês, com salário mensal; todo domingo, com salário semanal (`isSalarioMensal`) | `best.a.n`: cada clube humano que **joga naquele mês** (`ah.bY(mês)`) paga `kK()` | `best.f.aS`, `best.a.n`, `best.ah.kJ` |
| `dJ` (5): juros | Dia 2 de cada mês | Clube humano com juros > 0 paga `C.eQ()` na categoria "Juros" | `best.a.o` |
| `aj` (3): semana | Todo domingo | Evolução semanal dos jogadores (`F.fV`) e dos juniores (`F.fY`); habilidades individuais | `best.f.aT` |
| Dia com jogos | A cada rodada | Bilheteria, ofertas da IA, vendas de jogadores listados e obras concluídas | `best.f.as`, `best.f.ax`, `best.f.ap` |
| Nova temporada | Virada de ano | Zera o livro-caixa, recalcula reputações, paga patrocínio, envelhece e aposenta jogadores, recalcula salário e valor, gera juniores e roda o mercado da IA | `best.f.aa`, `best.f.ag`, `best.f.af`, `best.ag.jO` |

Observação: pela condição de `ah.bY`, um clube humano sem jogo no mês não paga salários naquele mês (leitura direta de `best.a.n`).

## Livro-caixa (`best.C`)

`ah.v(valor, código)` soma ao caixa e, se o clube for humano, lança como receita. `ah.w(valor, código)` subtrai e lança como despesa. `ah.f(valor)` lança salários. A tela `a.cW` mostra os rótulos.

| Código | Lado | Campo | Rótulo na tela | Quem lança |
|---|---|---|---|---|
| 5 | receita | `dL` | Ingressos | `best.I.hf` |
| 1 | receita | `dN` | Venda de Jogadores | `best.F.a(ah,int,…)`, `F.c(ah,int)` |
| 3 | receita | `dM` | Prêmios | `ah.c(at,int)`, `f.G.V` |
| 6 | receita | `dO` | Patrocinio/Sócio torcedor | `ah.kG`, `ah.kH` |
| 9 | receita | `dP` | Multas/outros | `a.bn.cQ` (multa ao jogador suspenso) |
| 1 | despesa | `dR` | Compras de jogadores | `best.F.a(ah,int,…)` |
| 7 | despesa | `dQ` | Estádio | `a.cq.oI` (expansão) |
| — | despesa | `dS` | Salários | `ah.kJ` → `ah.f` |
| 4 | despesa | `dT` | Juros de empréstimo | `best.a.o` |
| 8 | despesa | `dV` | Multa de rescisão | `best.F.a(ah,int,true,…)` |
| outro (−1) | despesa | `dU` | Diversos | pagamento de empréstimo (`C.l`), cachê de amistoso (`a.h`) |

- Saldo exibido = receitas − despesas (`C.eC`).
- O livro-caixa é zerado no começo de cada temporada para os clubes humanos (`ah.kI` → `C.eA`, chamado em `best.f.aa`). Também é recriado quando um técnico humano assume um clube (`ah.lg`).
- Tomar empréstimo usa o código −1 na receita e não é lançado. Pagar o empréstimo cai em "Diversos" (`C.m`, `C.l`, `C.h`, `C.i`).

## Caixa inicial e patrocínio

| Divisão do clube | Caixa ao assumir (`aq.sC[div][0]`) | Patrocínio anual (`aq.sD[div][0]`) |
|---|---|---|
| 0 (sem divisão nacional, inferido) | 3.500.000 | 3.500.000 |
| 1 | 15.000.000 | 6.000.000 |
| 2 | 12.000.000 | 4.500.000 |
| 3 | 10.000.000 | 2.500.000 |
| 4 | 3.500.000 | 2.000.000 |

- Quando um técnico humano assume o clube (`al.E` → `ah.lg` → `ah.kH`), o caixa passa a ser `sC[div][0]`. O patrocínio entra no livro-caixa, mas não soma ao caixa nesse momento.
- No início de cada temporada (`best.f.ag` → `ah.kG`), clubes humanos recebem `sD[div][0]` como "Patrocinio/Sócio torcedor".
- Clubes fora do Brasil (país ≠ 29), com estaduais ativos, recebem também 3,2 × a folha salarial (`ah.kG`, `ah.kH`). Esse valor vai só para o caixa, sem lançamento.
- A segunda coluna de `sC` e de `sD` não é usada (busca por `aq.sC`/`aq.sD`).
- Quando o técnico humano deixa o clube (`al.i`), o caixa do clube antigo é redefinido por `lg()` e a dívida bancária é zerada (`C.V(0)`).

## Empréstimo bancário

Fonte: `best.C.m`, `best.C.l`, `best.C.eP`; tela `a.cW` ("Pegar 500 mil" / "Pagar 500 mil").

| Divisão | Teto da dívida |
|---|---|
| 1 | 5.000.000 |
| 2 | 3.000.000 |
| 3 | 2.000.000 |
| 4 | 1.500.000 |
| outras | 1.000.000 |

- Cada pedido acrescenta 500.000 à dívida e ao caixa enquanto a dívida estiver abaixo do teto.
- Cada pagamento retira 500.000, se houver dívida e caixa ≥ 500.000.
- Juros mensais = 3% da dívida, recalculados a cada operação e cobrados no dia 2 de cada mês.

## Saldo negativo e consequências

O jogo não bloqueia salários nem juros com caixa negativo. As consequências são indiretas:

- **Confiança da diretoria.** Em cada partida, com caixa < 0, a confiança cai 10 em jogo de liga nacional e 5 nas demais competições (`best.al.a(I,boolean,int)`).
- **Demissão.** Se a confiança da diretoria fica abaixo de 10 e o caixa está negativo, o motivo registrado é "Crise financeira" / "você estava levando o clube para o abismo financeiro" (`f.s.A`, `aq.sg`, `aq.sh`).
- **Compras.** Exigem caixa ≥ preço (`a.cz.oL`, `best.l.b`). Obras também (`a.cq.oI`). No banco, só o pagamento exige caixa ≥ 500 mil; o pedido de empréstimo depende apenas do teto da dívida (`C.l`, `C.m`).

## Estádio (`best.v`)

### Capacidade e setores

`v.N(capacidade)` aceita capacidades entre 1.000 e 120.000; fora dessa faixa, usa 10.000. A divisão por setor é:

| Setor | Fração |
|---|---|
| Geral | 15% |
| Arquibancada | o restante (≈75%) |
| Cadeira | 9% |
| Camarote | 0,9% |

O editor de times aplica a mesma faixa ("O estádio deve ter entre mil e 120 mil lugares", `d.ac`).

### Condição do gramado (`v.dq`)

Índice em `aq.pb`: Excelente, Muito Boa, Ruim, Precária. Sorteio inicial por reputação do clube (`v.h(ah)`):

| Reputação | Distribuição |
|---|---|
| ≥ 4 | 95% Excelente, 5% Muito Boa |
| 3 | 50% Muito Boa, ~6% Ruim, ~44% Excelente |
| 2 | 50% Muito Boa, ~16% Ruim, ~34% Excelente (o ramo de Precária é inalcançável) |
| ≤ 1 | 10% Excelente, 40% Muito Boa, 25% Ruim, 25% Precária |

Quando um técnico humano assume o clube, o gramado é sorteado de novo: 30% Muito Boa, 70% Excelente (`v.i(ah)`, chamado em `al.E`).

### Preço sugerido do ingresso (`v.a(tipo, clube)`)

Tabela `aq.qK[tipo][índice]`, com preços de geral, arquibancada, cadeira e camarote:

| Tipo de competição | Índice | Valores |
|---|---|---|
| 1 Liga nacional, 5 Mundial, 7 Seleções | divisão (0–4) | {3,12,15,30}, {10,15,25,80}, {7,13,20,70}, {5,12,17,40}, {3,12,15,30} |
| 2 Copa nacional (e 10 regional, tratada como 2), 3 Estadual | reputação (0–5) | copa: {3,12,15,30} ×3, {7,13,20,70}, {10,15,25,80} ×2; estadual: {3,5,12,20}, {3,12,15,30} ×2, {5,12,20,50}, {10,15,25,70} ×2 |
| 4 Continental, 6 Segunda continental, 8 Recopa | 0 = Europa, 1 = outros | 4: {30,45,65,200} / {20,35,55,150}; 6 e 8: {20,25,45,150} / {20,25,40,120} |
| demais | — | {10,25,35,50} |

A tela `a.cl` permite usar "sempre os preços sugeridos" (`v.dp`) ou preços manuais. Os limites dos campos de preço são 200, 300, 500 e 1000.

### Público e bilheteria (`best.v.b(I)`)

Calculado para toda partida com estádio (`best.I`, durante a montagem do jogo). Por setor:

1. **Demanda base pela reputação do mandante** (0–5): {200,500,50,0}, {1000,5000,1200,20}, {2000,10000,1500,50}, {4000,20000,2500,300}, {4500,30000,3500,400}, {5000,40000,5500,500}.
2. **Tipo de competição:** estadual (3) e regional (10) × 0,7; amistoso (0) × 0,4.
3. **Fração da capacidade:** soma `capacidade_do_setor × f`, com f = 0,30, mais 0,15 em fase mata-mata (`f.z`), mais 0,30 em continental (4), seleções (7) ou eliminatórias (9), mais 0,15 em segunda continental (6), recopa (8) ou supercopa (11).
4. **Diferença de reputação** (visitante − mandante): ±{0, 5, 10, 15, 20, 25}%. Visitante maior aumenta o público; menor reduz.
5. **Torcida:** × confiança da torcida no técnico do mandante / 100 (80, sem técnico).
6. **Ruído aleatório** pela divisão do mandante: até {10,20,5,0}, {100,500,200,10}, {300,1000,400,20}, {400,1200,500,30}, {500,1500,1000,50}.
7. **Preço manual:** para cada unidade abaixo do preço sugerido, +3% do público do setor; para cada unidade acima, −3%.
8. Limita cada setor entre 0 e a capacidade.

`renda = Σ público_setor × preço_setor`. Em copas de seleções (7), a renda é multiplicada por 3, ou por 5 na Copa do Mundo (`el()==7`). Nas eliminatórias (9), por 2. O público fica gravado na partida (`I.j(int[])`) e a renda em `I.aW`.

**Quem recebe:** `best.I.hf` credita a renda ao mandante só se ele for humano e a competição não for de seleções (7) nem Mundial (5). O visitante não recebe nada.

### Expansão (`a.cq`, `best.B`)

- **Teto por setor** (geral, arquibancada, cadeira, camarote): {18.000, 80.000, 9.000, 700} na primeira temporada e {20.000, 100.000, 10.000, 800} a partir da segunda (`aq.pa`). Os tetos maiores de `pa[2]` e `pa[3]` nunca são usados, porque a condição `H() >= 2` vem antes de `>= 6` e `>= 10`.
- **Custo por lugar:** depende da faixa do total do setor depois da obra.

| Setor | Faixas (total após a obra ≤) | Custo por lugar |
|---|---|---|
| Geral | 1.000 / 2.500 / 3.500 / 10.000 / acima | 80 / 160 / 240 / 500 / 700 |
| Arquibancada | 5.000 / 15.000 / 30.000 / 60.000 / acima | 120 / 380 / 640 / 700 / 1.400 |
| Cadeira | 1.000 / 2.000 / 3.000 / 5.000 / acima | 300 / 600 / 750 / 800 / 1.200 |
| Camarote | 100 / 200 / 500 / 600 / acima | 1.500 / 3.500 / 4.000 / 6.000 / 6.400 |

- **Custo total** = Σ lugares × custo + 100.000 fixos. É pago à vista, na categoria "Estádio", e exige caixa suficiente.
- **Prazo:** menos de 1.000 lugares, 15 dias; menos de 10.000, 20; menos de 30.000, 30; demais, 40.
- **Conclusão:** a cada dia com jogos, obras vencidas acrescentam os lugares (`best.f.aw` → `B.ex`). Só uma obra por estádio de cada vez (`a.cl.oB` esconde o botão).
- **Nome do estádio:** a tela mostra "Nome do estádio - C. 200 mil", mas não foi encontrada cobrança associada (ver Lacunas).

Não há despesa periódica de manutenção do estádio: o código 7 só é lançado pela expansão.

## Premiações

### Classificação final em liga e estadual (`best.ah.c`)

Só para clubes humanos, ao fim da tabela (`f.s.za` → `ah.a(at,int,int)`). Lançado como "Prêmios", com a mensagem "Você recebeu uma premiação de $1 pela classificação final".

| Competição | 1º | 2º | 3º | 4º | 5º | 6º |
|---|---|---|---|---|---|---|
| Liga, 1ª divisão | 5.000.000 | 3.500.000 | 2.000.000 | 1.500.000 | 1.000.000 | 500.000 |
| Liga, 2ª divisão | 2.500.000 | 2.000.000 | 1.000.000 | 500.000 | 250.000 | 100.000 |
| Liga, 3ª divisão | 1.500.000 | 1.000.000 | 500.000 | 300.000 | 150.000 | 75.000 |
| Liga, 4ª divisão | 750.000 | 500.000 | 300.000 | 200.000 | 100.000 | 50.000 |
| Estadual, 1ª divisão (`aq.su`) | 700.000 | 500.000 | 300.000 | 100.000 | — | — |

### Vitória em confronto eliminatório (`f.G.c` e `f.G.V`)

Pago ao vencedor do confronto, se humano. O valor depende do tipo e da fase (`oj`):

| Tipo | Tabela | Valores por fase |
|---|---|---|
| 2 Copa nacional | `aq.ss`, alinhada para que a final caia no último valor (inferido: `zq()` = número de fases) | 1M, 2M, 4M, 5M, 7M, 15M, 20M, 25M |
| 4 Continental | `aq.sw[continente]` | Europa 2M/5M/7M/25M/30M; América do Sul 2M/3,5M/5M/20M/40M; África, Ásia e Concacaf 0,5M/1,5M/2M/4M/40M; Oceania 0,2M/0,5M/1M/2M/20M. Fases preliminares: Libertadores (ids 4101–4103) 500 mil, Liga dos Campeões (4000–4004) 1M |
| 5 Mundial | `aq.sx` | 2M, 5M, 7M |
| 6 Segunda continental e 12 Conference | `aq.sy` / `aq.aeG` (Europa / outros) | 0,5M/0,7M/2M/2,5M/7M; 0,5M/1M/1,5M/5M/5M. Ids 6100: 300 mil; 6000–6004: 500 mil |
| 8 Recopa | `aq.sz[0]` | 1M |
| 10 Regional | `aq.sv` | 100 mil, 100 mil, 400 mil |
| 11 Supercopa | `aq.sA[0]` | 1M |

As tabelas `aq.st`, `aq.sB` (igual a `qK[1]`), `aq.sz[1]` e `aq.sA[1]` não têm uso encontrado.

## Salário, valor e contratos

### Salário (`best.F.fJ`)

Recalculado na criação, na promoção de junior e para todos os jogadores no início de cada temporada (`best.f.af`).

1. **Base pela liga do clube:** nas 5 grandes ligas (`aq.rW` = Alemanha, França, Itália, Inglaterra, Espanha), 750 (div. 1), 550 (2), 500 (3), 450 (4–5). Nas demais, 600, 500, 450, 400. Sem clube ou divisão 0, 350. Nível do clube > 20: +50.
2. **Posição:** goleiro −70, lateral −30, zagueiro −40, meia 0, atacante −50. Depois, a base cai pela metade.
3. **Cálculo:** salário = força × 2 × base. Estrela ou top mundial: + força × 250. Idade ≥ 32: − (idade − 32) × 300. Mínimo de 500.
4. **Multiplicadores:** top mundial × 1,4; junior × 0,1. No sistema mensal, × 4.

Consequência (leitura direta): um aumento negociado na renovação vale só até a virada da temporada, quando `fJ` sobrescreve o salário.

### Valor de mercado (`best.F.fK`)

1. **Base:** `(força × 2)²`.
2. **Multiplicador pelo nível do clube:** ≥ 21: 750; 20: 600; ≥ 18: 500; ≥ 12: 400; demais: 366.
3. **Ajustes do multiplicador:**
   - estrela: × 3 se nível ≥ 22 e o jogador for europeu; × 2 se nível ≥ 21 e europeu; × 1,7 nos demais casos;
   - top mundial × 1,6; atacante × 1,3; `status == 1` × 1,2.
4. **Ajuste por idade:** idade < 20: + (32 − idade) × 27; até 25: × 22; até 31: × 15; 32–33: + (34 − idade) × 10; ≥ 34: − (idade − 34) × 50. Se o resultado ficar ≤ 0, vale 60.
5. **Valor** = base × multiplicador.
6. **Junior:** `round(valor × 0,03) × potencial`, e × 1,5 se o potencial for 10.
7. **Promovido da base:** × 0,18 na temporada da promoção (limitado ao preço pedido), × 0,35 na seguinte e × 0,65 na outra (`F.ff` guarda a temporada da promoção).

### Contrato

| Situação | Duração | Fonte |
|---|---|---|
| Elenco do clube que o humano assume | 180 dias a partir do dia | `al.E` |
| Transferência | 180 dias | `F.a(ah,int,…)` |
| Empréstimo | 365 dias de contrato; o vínculo dura 366 | `F.a(…, true, …)`, `components.t` |
| Junior promovido | 180 dias | `best.K.a` |
| Renovação | 6 meses / 1 / 2 / 3 anos = 180 / 365 / 730 / 1095 dias, somados ao **fim atual** do contrato | `a.fy.dq` |
| Renovação automática (opção) | +180 dias a partir do dia, quando vencido | `a.eg.qr` |

- **Aviso de término:** com a opção ativa, envia "Contrato se encerrando" (menos de 31 dias) ou "Contrato encerrado" (`a.eg.qr`, `getAvisoTerminoContrato`).
- **Contrato vencido:** em clube humano, o jogador deixa de ser elegível para a partida (`F.a(I,boolean)` com o segundo argumento falso).

**Aceite na renovação (`a.fy`):**

- teto = 25% do valor de mercado (acima disso: "Salário maior que o limite");
- com menos de 60 dias de contrato, o mínimo aceito é o salário atual − {1, 3, 5, 12}% para {6 m, 1 a, 2 a, 3 a};
- com 60 dias ou mais, o mínimo é o salário atual + {10, 12, 15, 5}%;
- abaixo do mínimo, o jogador pede o mínimo (limitado ao teto) e o usuário pode aceitar;
- a renovação tira o jogador da lista de venda e redefine o preço pedido para o valor.

**Multa a jogador suspenso:** 10% do salário, lançada como "Multas/outros". Em 50% dos casos gera reclamação do jogador (`a.bn.cQ`, `components.as` com jogador).

## Mercado

### Limites de elenco

- Até 35 profissionais por clube (`ah.a(F,boolean)`, `ah.lh`, `best.l`). As mensagens da interface falam em 30 ou 32, mas o código verifica 35.
- Juniores: geração limitada a 20 (ver Base).

### Compra por proposta do usuário (`best.l.a(F, comprador, oferta)`)

O preço exigido pelo vendedor da IA depende de quantos jogadores ele tem na posição (limites goleiro, lateral, zagueiro, meia, atacante = 3, 4, 4, 5, 4):

| Situação do vendedor | Preço exigido |
|---|---|
| Na posição ≥ limite, jogador com força ≥ 30 e idade ≤ 35 | valor × (1 + {0,5; 0,2; 0,2; 0,2; 0,5}) |
| Na posição ≥ limite, demais | valor × (1 − {15, 20, 20, 10, 10}%) |
| Só 1 jogador na posição | valor × 2,5 (× 3 para atacante) |
| Outros casos | valor × 2 (× 2,5 para atacante) |

**Resultados:**

- oferta ≥ preço e jogador aceita: compra realizada;
- recusa do jogador: "Não deseja se transferir";
- exigência de salário: 2 × o salário atual, que o usuário pode aceitar;
- oferta < preço, com caixa ≥ preço e jogador disposto: **contraproposta** no preço exigido, eventualmente com exigência salarial;
- nos demais casos: "Oferta recusada".

Depois da compra, o vendedor da IA repõe a posição se ficar abaixo do mínimo (`l.a(ah,F)`).

**Vontade do jogador (`best.l.c` e `best.l.d`):**

- comprador europeu: sempre aceita;
- jogador de clube europeu com reputação ≥ 4: aceita se o comprador tiver reputação ≥ 4 ou for da 1ª divisão; exige salário em dobro se a reputação do comprador for 3; recusa nos demais casos;
- demais vendedores: recusa só quando o vendedor tem reputação ≥ 4 e o comprador ≤ 2, ou o vendedor tem reputação 3 e o comprador 0. Leitura direta das condições; a interpretação em palavras é inferida.

### Compra pelo preço de lista (`best.l.b`)

Jogador marcado "à venda" (`F.ft`), pelo preço pedido `F.fl`. Exige caixa, elenco < 35 e vontade do jogador (`l.d`).

### Empréstimo pedido pelo usuário (`best.l.a(F, ah)`)

- **Condições:** o jogador precisa estar "disponível para empréstimo" (`F.fz`), o elenco abaixo de 35 e o clube com menos de 4 emprestados ativos ("Seu time já pegou o limite de quatro emprestados"), além da vontade do jogador.
- **Efeito:** sem custo de transferência. Cria `components.t` com 366 dias. Ao vencer, o jogador volta ao clube de origem; se a origem for humana e estiver com 35 jogadores, o retorno é prorrogado (mensagens 82–84).
- **Na tela:** "Limite de 30 jogadores alcançado".

### Propostas da IA ao usuário (`best.f.ap` → `a.eg.ac`)

A cada dia de jogo, sem diálogo aberto:

- 1% de chance de proposta de **compra** por um jogador aleatório que não esteja emprestado;
- caso contrário, 50% de chance de pedido de **empréstimo** de um jogador marcado como disponível.

O clube interessado é escolhido por `best.l.a(boolean,boolean)`. A oferta exibida é valor × 1,3 (`a.eg.ac`, `a.jm`). Aceitar a compra transfere pelo valor ofertado, sem multa de rescisão.

### Venda de jogador listado pelo humano (`best.f.ax` → `best.f.av` → `components.an`)

- Em 50% dos dias de jogo, cada jogador humano à venda é testado.
- A venda ocorre se o preço pedido for ≤ valor × (1 + HL). HL vale 0,10, ou 0,15 com 20% de chance, sorteado em `a.eg.qs` ao montar a tela principal (inferido).
- O comprador é escolhido por `best.l`.
- A transferência é feita com cobrança de **"Multa de rescisão"** ao vendedor, proporcional ao contrato restante: 12% do preço (≤ 30 dias), 20% (≤ 60), 22% (≤ 90), 25% (≤ 180), 30% (> 180) (`best.F.a(ah,int,true,false,false)`).
- No início de cada temporada, a lista de venda dos clubes humanos é limpa (`F.ge`).

### Como a IA escolhe o clube comprador (`best.l`)

- **Modos (`cs`):**
  - 0: mercado do país ou de ligas europeias, para estrelas, top mundiais ou brasileiros fortes;
  - 1: exportação por continente;
  - 2: clube europeu de reputação ≥ 4.
- **Faixa de divisão** do candidato: divisão do vendedor ± 1. Jogadores com força ≤ 20 abrem todas as divisões.
- **Candidatos excluídos:** clubes humanos, o clube de origem do empréstimo (`F.fA`) e elencos com 32 jogadores ou mais (35 em alguns modos).
- **Aceite do jogador pelo clube** (`ah.a(F,boolean)`):
  - força mínima `aq.qg[div]` = {1, 40, 30, 20, 5} nas ligas, ou `aq.qh[rep]` = {1, 10, 20, 40, 50, 55} fora delas;
  - força máxima `aq.qi[rep]` = {20, 30, 45, 85, 100, 100};
  - teto por posição: goleiro 3, lateral 5, zagueiro 5, meia 10, atacante 5.
- Sem candidato, tenta qualquer clube (`cH`, `cJ`).

### Mercado da IA

**Durante a liga:** ao atingir a rodada `zk()` da liga nacional (inferido: virada de turno) e ao fim da fase, `best.ag.b(f.s)` faz vendas dos clubes da IA daquela liga.

**Fim de temporada (`best.ag.jO`, em `best.f.aa`):**

1. **`jS` (clubes de liga):** cada clube da IA faz 1 a 4 movimentos, conforme a posição na tabela (índice 0–1: 1; 2–5: 2; 6–10: 3; demais: 4). Primeiro vende excedentes em posições com ≥ {4, 5, 5, 10, 8} (ou ≥ {3, 4, 4, 8, 6}); depois, em posições com > {3, 4, 4, 6, 4}. O jogador sai pelo valor, sem multa.
2. **`jU` (clubes sem liga):** idem, com probabilidade de exportação pela força: estrela 70%, ≥ 90: 70%, 80–89: 65%, 70–79: 55%, 60–69: 25%, < 60: 5%.
3. **`jR`:** clubes da IA abaixo do mínimo por posição ({2, 3, 3, 5, 3}) compram de clubes de reputação próxima (força ± 5 da referência `qg`/`qh`) ou criam um jogador novo (`ah.ku` → `l.a(ah,int[])`).
4. **`jT`:** estrelas com força > 50 e menos de 31 anos, em clubes de reputação < 5 fora da Europa (ou < 4 na Europa), vão para clubes europeus de reputação ≥ 4 com 75% de chance.

**Início de temporada (`ah.kp`):** em posições acima de {2, 3, 3, 5, 4}, há 50% de chance de cada clube da IA pôr um jogador à venda (preço = valor). Se a força for < 42, há 30% de chance de ele ficar também disponível para empréstimo.

### Janelas de transferência

Não foram encontradas janelas no jogo original: as negociações do usuário ficam abertas o ano todo (busca por "janela" e "transfer" sem regra de datas). O arquivo `config/transfer-windows-2026.json` é do patch, com datas reais da CBF, e não do jogo.

## Base e juniores

### Geração anual (`best.f.c(true)`, em `best.f.af`)

- Clube com menos de 15 juniores recebe novos: em clubes de liga, 3 a 5 (laço com 2 + sorteio 0–2, inclusivo); nos demais, 1 a 3, +1 com nível ≥ 20. O limite é 18 no total.
- No início do jogo (`c(false)`): clubes de liga com reputação ≥ 3 e menos de 12 juniores recebem 6 (goleiro, lateral, zagueiro, 2 meias, atacante); os outros, com menos de 5, recebem 5.

### Junior novo (`best.F.a(ah,int,F,int,String,Boolean)`)

- **Idade:** 16–19.
- **Posição:** goleiro 10%, lateral 20%, zagueiro 20%, meia 30%, atacante 20%.
- **Potencial `es`** (1–10), pela faixa do clube:

| Clube | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| nível < 15 e reputação ≤ 3 | 4% | 4% | 7% | 10% | 25% | 25% | 20% | 3% | 1% | 1% |
| nível 15–18 e reputação ≤ 3 | 2% | 3% | 0 | 5% | 20% | 35% | 25% | 5% | 3% | 2% |
| nível ≥ 19 ou reputação ≥ 4 | 2% | 3% | 0 | 5% | 15% | 35% | 20% | 10% | 8% | 2% |

O potencial 3 nunca é sorteado nas duas últimas faixas porque o teste "≤ 4" vem depois de "≤ 5".

- **Estrela:** 1% (quando o primeiro sorteio dá 1).
- **Estrangeiro:** em clubes de nível ≥ 18, se o sorteio de posição der 1. Para o Brasil, ids 11, 43, 195, 150, 84 ou aleatório (Argentina, China, Uruguai, Paraguai e Haiti, segundo `default_lang.xml`). Para Alemanha, Portugal, Holanda, Itália e França, um país do mesmo grupo (ids 3, 154, 85, 104, 174, 72). O estrangeiro tem potencial 7–10.
- **Desenvolvimento inicial `fd`:** 15/35/55/70/75 para 16–20 anos, + sorteio de 1–5 + potencial (`F.ga`).
- **Potencial estimado exibido `fc`:** potencial real com 15%; −1 com 45%; +1 com 40% (`F.fZ`, coluna "CPE" em `b.N`, inferido).
- **Evolução semanal (`F.fY`):** até 20 anos, ganho de 20/40, 15/40, 14/40 e 5/40 (≤ 17, 18, 19, 20 anos) + 0,03 a 0,11 pelo potencial; a cada 1,0 acumulado, +1 de desenvolvimento (máx. 100).

### Promoção (`best.F.gf` e `best.K.a`)

- **Automática aos 20 anos ou mais**, se o potencial for ≥ {1, 4, 5, 6, 6, 6}[reputação] e a posição tiver menos de {3, 5, 5, 8, 6} profissionais. Exige elenco < 32. Nos clubes da IA, quem não sobe é substituído por um junior novo.
- **Força ao subir:** potencial + `round(k × desenvolvimento / 100)`, com k pela divisão (22/17/14/7, ou 5 sem divisão) ou pela reputação (20/15/12/7/5), +5 na Europa, + sorteio de 0–4. Potencial ≥ 9 soma + sorteio de 0–9.
- **Contrato** de 180 dias; recalcula valor e salário.
- **Estrela:** fica estrela com chance de 1/3 (se já era); top mundial vira estrela; os demais viram estrela com chance de 1/200. Estrela com potencial < 8 passa a 8.

## Treino e evolução semanal

- **Tela `a.iQ` ("Treino"):** foco semanal em "Habilidades principais (gol/des/arm/fin)" ou "Habilidades secundárias (vel/tec/pas)", ou "Deixar auxiliar técnico decidir semanalmente" (`ah.nt`, `ah.ns`). Vale com as habilidades individuais ativadas (`isHabilidadeIndividual`).
- **Distribuição do ganho (`F.h(double)`):** 100% na habilidade principal da posição, 40% na segunda e 30% na terceira. Goleiro e defesa × 1,2.
- **Força até 31 anos (`F.fW`):** ganho semanal de 1/50 a 8/50, pelo nível do clube e pela idade. Recebe bônus se o jogador atuou (+0,04), se tem potencial alto ou se é estrela/top mundial, e penalidade pela força atual e pelo país.
- **Teto de força** pela divisão × reputação nas ligas: div. 1 de 80 a 100; div. 2 de 50 a 80; div. 3 de 40 a 70; div. 4 de 25 a 60. Fora das ligas, pela reputação: 20/30/40/65–70/100/100. O teto é limitado ainda pelo país (45 a 95) e sobe com potencial 7–10 se o desenvolvimento for ≥ 60 (`F.b(double,int)`).
- **Força a partir de 32 anos (`F.fX`):** declínio. Detalhes no estudo de jogadores.

## Reputação de clubes

`best.ah.d(lugar, tipo, extra)` soma pontos `nu` para campeão e vice; `best.ah.kk` converte esses pontos em reputação no início da temporada (`best.f.ag`).

| Tipo | Campeão | Vice |
|---|---|---|
| 1 Liga (div. 1; demais divisões: 50 fixos) | 500 | 90 |
| 2 Copa nacional | 300 | 50 |
| 3 Estadual | 10 | 5 |
| 4 Continental | 5.000 | 1.000 |
| 5 Mundial | 40.000 | 1.000 |
| 6 Segunda continental | 2.000 | 500 |
| 8 Recopa | 500 | 0 |
| 10 Regional | 50 | 0 |
| 13 | 1.000 | 500 |

Valores acima de 1.000 são multiplicados por 0,6 em clubes sem liga nacional jogável fora da Europa e América do Sul.

**Conversão (`kk`):**

- pontos > 100.000: reputação 5; > 10.000: 4; > 1.000: 3; > 100: 2; > 10: 1. A reputação só sobe por essa conversão;
- desgaste por temporada: reputação 5 perde 6.000 pontos e cai para 4 abaixo de −90.000; reputação 4 perde 600 e cai abaixo de −9.000; reputação 3 (clubes de liga) perde 50 e cai abaixo de −1.000. A reputação 2 nunca cai (o código mantém 2).

O nível do clube (`hA`) não muda durante a carreira: só é lido do arquivo do time.

**Rankings de clubes** (`a.hc`: por reputação, pontos corridos e colocação):

- `ah.nC[tipo]` acumula pontos (3/1), gols pró e gols contra por tipo de competição (`ah.e(I)`);
- `ah.nB[tipo]` acumula pontos de colocação (`ah.b`). Liga div. 1: 15, 10, 8, …, 1. Copa: 12/7/3/3. Continental: 20/15/7/7/3/3 (18/12/3/3/1/1 fora de Europa e América do Sul). Copa do Mundo: 50/35/10/5. Outras de seleções: 20/15/10/5.

## Carreira do técnico (`best.al`)

### Confianças

A diretoria começa em 95 (`of`) e a torcida em 85 (`og`) quando o técnico assume (`al.E`). No início de cada temporada, as duas ganham +50, limitadas a 100 (`best.f.ag`).

**Por partida (`al.a(I,boolean,int)`):**

- **Ajuste prévio:**
  - empate em casa contra adversário de nível igual ou menor: diretoria −1, torcida −1;
  - empate contra adversário mais forte: diretoria +1;
  - derrota em casa contra adversário de nível igual ou menor: −3/−3;
  - derrota fora contra adversário de nível igual ou menor: diretoria −1.
- **Diretoria pela situação na tabela** (líder, G4, meio, perto da zona e zona de rebaixamento; `ah.p(at)`):

| Competição | Resultado | Líder | G4 | Meio | Perto | Zona |
|---|---|---|---|---|---|---|
| Liga e copas gerais | vitória em casa / fora | +5 / +6 | +4 / +5 | +1 / +2 | +1 / +2 | 0 / +1 |
| | empate em casa / fora | +2 / +2 | +1 / +1 | −1 / 0 | −1 / −1 | −3 / −2 |
| | derrota em casa / fora | −2 / −1 | −2 / −1 | −3 / −2 | −5 / −4 | −7 / −5 |
| Continental e segunda continental | vitória em casa / fora | +5 / +7 | +4 / +6 | +3 / +4 | +3 / +4 | +3 / +5 |
| Estadual e regional | vitória em casa / fora | +2 / +3 | +2 / +2 | +1 / +2 | +1 / +2 | +1 / +1 |

Em competições sem tabela, usa a coluna "Líder" (índice 1) quando `I.hS()` é falso. Com `hS()` verdadeiro, não há ajuste da diretoria por tabela, exceto quando o resultado vem de uma decisão (`al.a(…, int)` > 0). O sentido de `hS()` não foi identificado.

- **Torcida:** empate em casa −1, fora +1; vitória em casa +3, fora +4; goleada (≥ 3 gols de diferença) mais +4 em casa / +5 fora; derrota em casa −5, fora −4; goleada sofrida mais −7 em casa / −5 fora.
- **Torcida abaixo de 20:** diretoria −3 a cada partida.
- **Caixa negativo:** diretoria −10 (liga) ou −5 (outras).

**Títulos (`al.q`):**

- liga ou estadual da 1ª divisão: torcida +20, diretoria +15, em dobro na liga nacional;
- outras divisões: +20 / +10;
- supercopa: torcida +10;
- copa nacional, continental, Mundial e segunda continental: +30 / +30.

### Demissão

- **Técnico humano:** depois de cada dia com jogos de liga ou estadual (`best.f.ax` → `best.f.n` → `f.s.A`), é demitido se a confiança da diretoria estiver abaixo de 10. O motivo é "Crise financeira" com caixa negativo; caso contrário, sorteio entre "Pressão torcida" e "Maus resultados". A tela `a.dm` informa o substituto.
- **Pedido de demissão (`a.eg.rr`):** motivo "você solicitou a demissão". É recusado se não houver substituto ("A diretoria ainda não achou um técnico a sua altura").
- **IA durante a liga:** clubes com diretoria abaixo de 10 e da 7ª posição para baixo (índice > 5) trocam de técnico.
- **IA no fim da temporada (`best.ag.jQ`):** técnico com ao menos uma temporada no clube é demitido se um sorteio de 1–90 superar o percentual de vitórias da temporada anterior (`best.j`: vitórias / jogos).
- **Escolha do substituto (`ah.kE` → `best.f.a(ah,int)`):**
  1. técnico livre do mesmo país (de trabalho ou nacionalidade) com a mesma reputação do clube;
  2. com reputação −1 a 0;
  3. em clubes de reputação ≤ 3, com reputação −2 a +1;
  4. para clube humano, qualquer reputação;
  5. qualquer técnico livre;
  6. por fim, para a IA, troca com o técnico de outro clube.

### Reputação do técnico (`al.a(int,int,int,boolean,int)` e `al.kk`)

**Pontos por título e vice:**

| Lugar | Liga | Copa | Estadual | Continental | Mundial | 2ª continental | Recopa | Regional | Tipo 11 | Conference | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Campeão | 600 | 500 | 30 | 6.000 | 10.000 | 2.000 | 500 | 50 | 100 | 3.000 | 3.000 | 20.000 |
| Vice | 150 | 150 | 5 | 1.000 | 1.000 | 500 | — | — | — | 300 | 500 | — |

- Seleções: 23.000 pelo título da Copa do Mundo, 6.000 nos demais casos.
- Liga fora da 1ª divisão: 50.

**Conversão:** pontos > 22.000: reputação 5; > 10.000: 4; > 1.000: 3; > 100: 2; > 10: 1.

**Desgaste:**

- reputação 5: −6.000, cai abaixo de −20.000;
- reputação 4: −600, cai abaixo de −3.000;
- reputação 3: −50, cai abaixo de −500;
- reputação 2: −5, cai abaixo de −50.

Para reputação 3 e 2, o desgaste só vale em clube de liga.

**Pontos de ranking (`oc`, "Ranking de técnicos" em `a.gX`):**

- **Vitória (`al.e`):** liga div. 1: 4; div. 2: 3; div. 3: 2; demais: 1. Copa 4, estadual 1, continental 5, Mundial 7, segunda continental 4, seleções 8, recopa 4, regional 2, supercopa 2, Conference 3, eliminatórias 2, tipo 13: 5, tipo 14: 6. +1 fora de casa, exceto em seleções e Mundial.
- **Empate:** valores menores (2 ou 1). O +1 de visitante é sobrescrito na maior parte dos tipos.
- **Colocação final (`al.b`):** por exemplo, liga div. 1: 25, 10, 8, …, 1; Copa do Mundo: 35/20/10/5.

### Ofertas de emprego

- **Técnico humano empregado:** recebe ofertas no fim da temporada e no evento `cPromocao` (`best.ay.zw`), vindas de clubes da IA em 3º a 6º lugar.
  - No país em que trabalha, as divisões ofertadas dependem da divisão atual: da 1ª, divisões {1, 1, 2, 3} (30%: {1, 3}; 20%: {1}).
  - No país de nacionalidade, ofertas das divisões próximas pelas tabelas `var8`/`var9` de `best.Z.a(ArrayList,al,boolean,boolean)`.
  - Com última divisão 1ª ou 2ª, ou reputação > 3, também de outros países, até passar de 6 ofertas.
- **Técnico humano desempregado:** a cada dia de liga ou estadual, ofertas dos 6 últimos colocados das divisões vizinhas à última em que trabalhou (`best.f.n`, `f.s.b`).
- **Seleções** (eventos `cS` e `cSempregado`, agendados por `best.a.q` antes dos torneios):
  - `best.ay.a` monta até 5 seleções pela reputação do técnico (ou do clube, se maior). A tabela de reputações desejadas vai de {2, 1, 1, 1, 1} (reputação 0) a {5, 4, 4, 3, 2} (reputação 5). Há rodízio de continentes e no máximo uma da Oceania.
  - A seleção do país natal entra se tiver nível < 18 ou se o clube do técnico tiver reputação ≥ 3.
- **Troca de clube (`al.i` e `al.E`):** registro em `best.u`; o clube antigo volta a ser da IA com caixa e livro-caixa redefinidos e dívida zerada; o novo recebe caixa inicial, contratos de 180 dias e novo sorteio do gramado.
- **Jogador aposentado vira técnico:** em clubes de liga, um jogador que se aposenta pode virar técnico. A chance é de 1/25 a 1/125 pela divisão, 1/5 para estrela e 1/2 para top mundial (`F.a(String,int,boolean)`).

## Aposentadoria e recordes

- **Chance anual de aposentadoria (`F.ge`, em `F.gd`):** só a partir de 33 anos, usando a idade efetiva (−1 para estrela, −3 para top mundial, −3 para goleiro).

| Idade efetiva | ≤ 31 | 32 | 33–34 | 35 | 36 | 37–38 | 39 | 40 | 41–42 | 43–48 | > 48 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chance | 0 | 1% | 10% | 45% | 70% | 85% | 95% | 97% | 98% | 99% | 100% |

- No clube humano, a aposentadoria **não é automática**: chega a mensagem "Desejo de aposentadoria". Na IA, o jogador sai e um junior é gerado no lugar.
- **"Melhores de sempre" (`best.b`):** ao se aposentar, o jogador entra na lista de artilheiros históricos se os gols na carreira superarem 0 (temporada 1), 10 (até a 9ª), 30 (até a 19ª) ou 50 (depois).
- **Histórico por competição** (`best.ao`, tabela `b.j`): ano, campeão, vice, artilheiro e técnico campeão. Também há telas de artilheiros e de melhores notas médias (`a.ay`, `a.o`).
- Não foi encontrado prêmio individual com efeito econômico, como "melhor jogador" ou bola de ouro (busca textual).

## Amistosos (`f.a.a`, tela `a.h`)

| Mando | Recusa | Cachê pedido (adversário de reputação 2 / 3 / 4 / 5) |
|---|---|---|
| Fora (na casa do adversário) | — | mesmo país 10 mil / 50 mil / 150 mil / 250 mil; outro país 20 mil / 80 mil / 200 mil / 450 mil |
| Em casa | reputação 5 só aceita outro 5; reputação 4 recusa clube de reputação < 2 | mesmo país 20 mil / 80 mil / 200 mil / 450 mil; outro país 30 mil / 100 mil / 250 mil / 500 mil |

- Exceções fora de casa: adversário de reputação 5 contra usuário < 4 cobra 300 mil; reputação 4 contra usuário < 2 cobra 200 mil.
- O cachê é lançado em "Diversos".
- A bilheteria do amistoso usa 40% da demanda base e vai para o mandante humano.

## Mensagens (e-mails) da gestão

`components.as(técnico, título, corpo, $1, $2)` indexa `best.ar.tP` (título) e `best.ar.tQ` (corpo).

| Título / corpo | Gatilho | Fonte |
|---|---|---|
| 0/73, 0/74 | Início de jogo e novo emprego | `ah.b(String,int)`, `al.E` |
| 26/80, 26/79 | Premiação por classificação e por vitória em confronto | `ah.c`, `f.G.V` |
| 24/77, 25/76, 25/78 | Títulos (liga, copa, segunda continental; continental; Mundial) | `al.q` |
| 27/81 | Goleada sobre o rival | `al.a` |
| 6/46, 5/47–48 | Goleada sofrida do rival / em casa | `al.a` |
| 16/66, 17/67 | Contrato se encerrando / encerrado | `a.eg.qr` |
| 28/82, 29/83, 29/84 | Fim de empréstimo | `best.f.au` |
| 10/16–19 | Reclamação do jogador multado | `a.bn.nQ` |
| 34/89 | Desejo de aposentadoria | `F.ge` |
| 23/75, 30–33/85–88, 35/90 | Pré-classificados da Copa do Brasil; vagas herdadas em Liga Europa, Sul-Americana e Conference | `f.f`, `f.x`, `f.H`, `f.J` |

Textos presentes em `best.ar` **sem gerador encontrado**: racha no elenco (49–50), "sem jogar" (51–52), "sem contrato" (53–54), briga no treino (55–56), torcida briga com jogador (57–59), esforço excessivo (60–61), agradecimento por aumento (62–63), "vendido por" (64), rumores de seleção (65) e vitórias em clássico (69–72). A busca por todos os construtores de `components.as` não achou esses índices. Logo, não há eventos aleatórios de vestiário ativos nesta versão (inferido).

## Classes de outros domínios identificadas

| Classe | Papel |
|---|---|
| `best.f` (instância `c.a.SR`) | Estado do mundo/save: listas globais, calendário, opções da carreira (salário mensal, estaduais etc.). **Corrige a hipótese** de que `best.f` seria "opções" |
| `best.Z` | País: divisões `eb()`, seleção `jn()`, clubes sem liga `ek()`, ofertas de emprego. **Corrige a hipótese** de "mundo/carreira" |
| `est.Options` | Preferências persistentes da interface |
| `c.a` | Contêiner estático de `SR` (`best.f`) e `afQ` (`best.ay`), serialização do save |
| `best.a` | Dia do calendário (partidas, eventos agendados), confirmado |
| `best.I` | Partida (mandante `hc`, visitante `hd`, gols `hu`/`hw`, competição `hy`, fase `ht`, estádio `ev`) |
| `best.at` | Competição base; tipo em `b()` (0 amistoso, 1 liga, 2 copa nacional, 3 estadual, 4 continental, 5 Mundial, 6 segunda continental, 7 copa de seleções, 8 recopa, 9 eliminatórias, 10 regional, 11 supercopa, 12 Conference, 13 e 14 não identificados com certeza, 15 torneio amistoso) |
| `f.s` | Fase de liga/tabela (classificação, demissões e ofertas) |
| `f.z`, `f.G` | Fase mata-mata e confronto eliminatório |
| `f.B`, `f.o`, `f.f` | Divisão nacional, estadual, copa nacional |
| `f.r`, `f.v`, `f.x`, `f.H`, `f.J`, `f.A`, `f.D`, `f.E`, `f.I` | Libertadores, Liga dos Campeões, Liga Europa, Sul-Americana, Conference, Mundial, Recopa Europeia, Recopa Sul-Americana, Supercopa |
| `f.c`, `f.d`, `f.e`, `f.g`, `f.h`, `f.p`, `f.q`; `f.i`–`f.n` | Copas de seleções (África, América, Ásia, OFC, Ouro, Euro, Copa do Mundo); eliminatórias |
| `best.ac` | Enum de países (`P0…`), continente em `gg()` (0 Europa … 5 Oceania) |
| `best.W`, `e.g`, `e.t` | Dados de jogador e time lidos dos arquivos (`isEstrela`, `isTopMundial`, `getHash` = potencial) |
| `best.af` | Filtro da busca de jogadores |
| `best.j`, `best.aj`, `best.ak`, `best.ao`, `best.ap`, `best.u`, `best.b` | Registros: técnico × clube, campanha, estatística por fase, títulos, transferências, trocas de técnico, artilheiros históricos |

## Lacunas

- **Nome do estádio:** o rótulo fala em custo de "200 mil", mas não foi encontrada cobrança nas classes `a.cl`/`a.cm`–`a.cp`. Não verificado se a troca de nome existe ou se é cobrada.
- **Caixa da IA:** não foi rastreado se `nb` dos clubes da IA influencia alguma decisão. As vendas e compras da IA não chamam `v`/`w` para clubes não humanos (`F.a(ah,int,…)`), o que sugere que não (inferido).
- **Sentido de alguns campos:** `ah.mX` (`kn()`, tratado como "clube de liga nacional jogável"), `F.status == 1` (provável titular no arquivo) e o rótulo exato de `F.fc` ("CPE") são inferidos.
- **`f.s.zk()`:** o momento exato da janela da IA no meio da liga não foi confirmado.
- **`a.eg.qs`:** não foi confirmado quando HL é sorteado de novo.
- **Tipos 13 e 14:** não foram identificados com certeza (`f.K` e `f.M`/`f.N`, com textos "Liga A–D").
- **Ids de país:** os estrangeiros da base brasileira (43 = China, 84 = Haiti) seguem `default_lang.xml` e parecem estranhos. A tabela de nomes pode diferir do enum `best.ac`.
- **Seleções:** a regra completa de aceite de convite (`a.gO`) e a passagem do técnico entre clube e seleção não foram lidas em detalhe.
- **Fora do escopo deste documento:** energia, lesões e suspensões além da multa; detalhes do declínio de força após os 32 anos (`F.fX`) e do sorteio de habilidades individuais.
- **Validação:** nada foi testado no jogo. Todas as fórmulas vêm da leitura estática da fonte decompilada.
