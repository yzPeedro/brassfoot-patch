# Modelo de dados do Brasfoot 22-23: jogador, time, técnico, país e carreira

Estudo de engenharia reversa do executável original limpo (SHA-256 `2fa65476…bb1c`), feito sobre a decompilação Vineflower 1.11.1. Os nomes de classe, campo e método são os ofuscados do jogo; o significado ao lado é a interpretação deste estudo.

**Resumo.**
1. O mundo da carreira é um único objeto `best.f` (acessado como `c.a.SR`), gravado em `.s22` com Kryo 4.0.2 junto de `best.ay`; os arquivos de time `.ban` usam serialização Java nativa (`e.t`/`e.g`).
2. O jogador (`best.F`) tem força geral `eq` (1–100), sete habilidades individuais (`eA`–`eG`), duas características (`ey`/`ez`, 14 tipos), potencial `es` (1–10) e maturação de júnior `fd` (0–100).
3. A força **não vem do `.ban`**: é gerada na criação da carreira (`F.fI`) a partir do nível do time (1–25), divisão ou reputação, titularidade, estrela e país.
4. A evolução é semanal (todo domingo, `f.aT`): jogadores com menos de 32 anos sobem até um teto que depende da divisão, da reputação e do país; a partir de 32 anos eles caem. Na virada de temporada, os jogadores envelhecem, se aposentam e são substituídos por juniores gerados.
5. O time (`best.ah`) guarda o elenco, os juniores, as táticas `[formação, estilo, marcação, foco]`, a grade tática de 25 casas, capitão e batedores, o estádio, o dinheiro, a reputação de 0 a 5 e o histórico. O nível do time (1–25) é fixo durante a carreira.

---

## 1. Convenções

- Origem: `data/private/re/src/` (local). O arquivo de uma classe tem `_` antes de cada maiúscula (`best.F` → `best/_F.java`). As citações usam o nome original (`best.F.fI`).
- "Campo" é o nome ofuscado do atributo; "getter/setter" são os métodos que o leem e o escrevem.
- `rand(a..b)` indica um inteiro sorteado no intervalo fechado. "d100" é `nextInt(100)+1`.
- **(inferido)** marca o que foi deduzido do uso, sem rótulo explícito no código. O que não foi resolvido está em [Lacunas](#14-lacunas).
- Códigos de país são os índices `P<id>` de `arquivos/default_lang.xml` (ex.: 29 Brasil, 11 Argentina, 3 Alemanha, 65 Espanha, 72 França, 97 Inglaterra, 104 Itália).

---

## 2. Visão geral e persistência

### 2.1 Grafo de objetos

| Classe | Papel | Serializável | `serialVersionUID` |
|---|---|---|---|
| `best.f` | Mundo da carreira (raiz do save): listas globais, calendário, opções, competições | sim | 1 |
| `best.ay` | Segundo objeto do save: filas de países e vagas de técnico em seleções (inferido por `ay.L`, `ay.a(al, boolean)`) | sim | 1 |
| `best.F` | Jogador | sim | 1 |
| `best.ah` | Time (clube ou seleção) | sim | 1 |
| `best.al` | Técnico (humano ou IA) | sim | 1 |
| `best.Z` | País no mundo da carreira (ligas, copa, seleção) | sim | 1 |
| `best.ac` | Enum estático de 224 países (nome, sigla, continente, nível, cores) | enum | — |
| `best.v` | Estádio | sim | 1 |
| `best.C` | Finanças do time (campos na §6.10; regras ficam para o estudo de economia) | sim | 1 |
| `best.H` | Estatística do jogador por competição (cartões, suspensão, gols, notas) | sim | 1 |
| `best.k` | Estatística do jogador por temporada e time | sim | 1 |
| `best.J` | Nota de uma partida do jogador | sim | 1 |
| `best.j` | Campanha do técnico por time e temporada | sim | 1 |
| `best.aj` | Campanha do time por competição e temporada | sim | 1 |
| `best.ak` | Estatística do time por tabela (`f.s`) na temporada | sim | 1 |
| `best.ao` | Título (time ou técnico) | sim | 1 |
| `best.ap` | Registro de transferência | sim | 1 |
| `best.u` | Registro de troca de técnico | sim | 1 |
| `best.b` | Hall de aposentados ilustres (nome, gols, jogos) | sim | 1 |
| `best.W` | Molde de jogador para geração (não serializável) | não | — |
| `e.t` / `e.g` | Formato do arquivo `.ban` (time / jogador) | sim | 16 |

Ligações entre objetos serializados usam **id inteiro + cache `transient`**: `F.bW`/`F.eo` (time do jogador), `ah.na`/`ah.mZ` (técnico do time), `al.bW`/`al.nV` (time do técnico), `al.nX`/`al.nW` (time anterior). Os caches são refeitos sob demanda por `f.x(int)` (time por id) e `f.y(int)` (técnico por id) (`best.F.fg`, `best.ah.ka`, `best.al.fg`, `best.al.lF`).

### 2.2 Identificadores

| Entidade | Campo | Atribuição |
|---|---|---|
| Time de clube | `ah.mU` (`lk()`) | índice em `f.aj` na criação da carreira (`best.p.dj`); o contador `f.bg` continua dali (`f.w`, `f.bH`, `f.bI`) |
| Seleção | `ah.mU` | próximo valor de `f.bg` ao ser criada (`best.Z.jo`) |
| Time no arquivo | `ah.mY` (`kl()`) | `e.t.getId()` (`best.ah.<init>(e.t)`) |
| Técnico | `al.nU` (`lT()`) | contador `f.bt` (`best.f.bU`, `best.al.<init>(String)`) |
| Jogador | `F.ei` (`gD()`), `F.ej` (`gI()`) | renumerados a cada gravação: `ei` sequencial, `ej` = 1 (lista de profissionais) ou 2 (juniores) (`g.b.Ai`); servem para religar `ap.U` na carga (`ap.mb`, `ap.me`, `g.b.Aj`) |
| Competição | `at.ei` (`gD()`) | renumerada na gravação; `H.ft` guarda o id para religar `H.Y` (`g.b.Ag`, `g.b.Af`, `H.gY`) |

### 2.3 Arquivos

| Arquivo | Formato | Conteúdo | Origem |
|---|---|---|---|
| `sav/<nome>.s22` | Kryo 4.0.2, `setRegistrationRequired(false)`, `writeClassAndObject` | `best.f` (`c.a.SR`) seguido de `best.ay` (`c.a.afQ`) | `c.a.ae`, `c.a.c(String, boolean)` |
| `sav/<nome>.sbck` | cópia do `.s22` | reserva; lida se o `.s22` falhar | `c.a.ae`, `c.a.c` |
| `sav/<nome>.info` | serialização Java | `est.InfoArquivoSalvoType` (resumo do save) | `c.a.ad`, `c.a.ae` |
| `options.bcf` | serialização Java | `est.Options` (opções globais) | `c.a.vI` |
| `teams/*.ban` | serialização Java | `e.t` com listas de `e.g`; só é aceito com `vid == 185` e `valid` verdadeiro | `best.U.a(String, String, boolean)` |
| `teams2/*` | XML | times legados lidos para `W`/`ah` | `best.P.iD`, `best.P.a` |

A versão do Kryo vem do `MANIFEST.MF` do jar (`Rsrc-Class-Path: kryo-4.0.2.jar minlog-1.3.0.jar objenesis-2.1.jar reflectasm-1.10.1-shaded.jar`).

**Compatibilidade de save (inferido, comportamento padrão do `FieldSerializer` do Kryo 4):** o Kryo não usa `serialVersionUID`; ele grava os campos não `transient` de cada classe, em ordem determinística por nome. Renomear, acrescentar, remover ou mudar o tipo de um campo de `best.*`/`f.*` torna o save ilegível. Campos `transient` podem mudar livremente.

---

## 3. Jogador — `best.F`

### 3.1 Campos persistidos

| Campo | Tipo | Getter / setter | Significado | Faixa / observação |
|---|---|---|---|---|
| `ei` | int | `gD` / `az` | id sequencial na gravação | −1 até gravar (§2.2) |
| `ej` | int | `gI` / `aC` | lista de origem do id | 1 profissional, 2 júnior |
| `dm` | String | `getNome` / `setNome` | nome | `null` ou `"TESTE"` → nome gerado (`au`) |
| `ek` | Boolean | `ff` / `a(Boolean)` | estrela | forçado a `true` se `el` |
| `el` | Boolean | `gm` / `j(Boolean)` | top mundial | perdido acima de 34 anos (`ay`) |
| `em` | int | `getIdade` / `setIdade` | idade | setter: 16–48 (senão 35); júnior 16–20 (senão 18) |
| `pais` | int | `getPais` / `setPais` | nacionalidade | id `P<n>` |
| `en` | int | `getPosicao` / `setPosicao` | posição | 0 goleiro, 1 lateral, 2 zagueiro, 3 meia, 4 atacante (`aq.rH`, `aq.rI`) |
| `bW` | int | via `n(ah)` / `fh()` | id do time atual | −1 sem time |
| `ep` | int | `gE` / `aA` | sem uso encontrado | — |
| `eq` | int | `fi` / `ad` | **força** geral | 1–100 |
| `er` | int | `getLado` / `setLado` | lado | 0 direito, 1 esquerdo (`aq.rK`, `aq.rL`) |
| `es` | int | `fH` / `aq` | **potencial** | 1–10; estrela com valor > 8 vira 10 (`aq`) |
| `et` | int | `fj` / `ae` | salário | §3.8 |
| `eu` | int | `fk` / `af` | valor de mercado | §3.7 |
| `ev` | int | `fl` / `ag`, `fm` | preço pedido / último valor pago | `fm()` copia `eu`; transferência grava o valor pago |
| `status` | int | `getStatus` / `setStatus` | titular de origem | 1 titular no `.ban` (`e.t.getNumeroTitulares`), 0 reserva |
| `ew` | int | `fn` / `ah` | número da camisa | zerado na transferência; `toString` exibe "nº - nome" |
| `ex` | int | `fF` / `fG()` | perfil derivado das características | §3.3 |
| `ey`, `ez` | int | `getCr1`/`setCr1`, `getCr2`/`setCr2` | características 1 e 2 | 0–13 (§3.2) |
| `eA`…`eG` | int | `gK`, `gJ`, `gL`, `gM`, `gN`, `gO`, `gP` (setters `aJ`, `aI`, `aK`, `aL`, `aM`, `aN`, `aO`) | habilidades individuais | 0–100 (§3.2) |
| `eH` | double[7] | `aE`, `c(double,int)`, `aD` | acumuladores de evolução das 7 habilidades | fração; ganha 1 ponto ao passar de 1,0 |
| `eI` | long | `fo` / `d(long)` | fim da lesão (ms da data do jogo) | lesionado se `eI` > hoje (`fP`) |
| `eJ` | long | via `a(long, boolean)` | fim do contrato (ms) | `fR()` dá os dias restantes; `fQ()` exibe |
| `eK` | int | `fp` / `ai`, `aj`, `ak` | condição física | 1–100; inicia em 100 |
| `eL` | Boolean | `fs` / `b(Boolean)` | jogou desde a última evolução | marcado na escalação (`ah.a(ah,I,int,int,boolean)`), zerado em `fV` |
| `eM` | double | `fu` / `d(double)` | acumulador de evolução da força | — |
| `eN` | double | `gk` / `g(double)` | nota da última partida | 0 ou 2–10 |
| `eO`, `eQ` | Boolean | `fv`/`d(Boolean)`, `fx`/`f(Boolean)` | sem leitura encontrada | (inferido: legado) |
| `eP` | Boolean | `fw` / `e(Boolean)` | transferido entre dois times humanos | gravado em `a(ah,int,boolean,boolean,boolean)`; sem leitura encontrada |
| `eR` | int | `fT` / `as` | casa da grade tática (1–25; ≥ 26 banco) | −1 fora da escalação; §6.5 |
| `eS` | ArrayList&lt;H&gt; | `gH` / `B` | estatística por competição | esvaziada na virada de temporada |
| `eT` | ArrayList&lt;k&gt; | `gr` / `C` | estatística por temporada e time (carreira) | preservada |
| `eU` | ArrayList&lt;J&gt; | `gv` / `D` | notas partida a partida | esvaziada na virada de temporada |
| `eV` | int | `fy` / `al` | sem leitura encontrada | — |
| `eW` | Boolean | `fz` / `g(Boolean)` | disponível para empréstimo | UI "Pôr para empréstimo" (`a.eg.qt`) |
| `eX` | Boolean | `gl` / `i(Boolean)` | está emprestado | UI "Emprestado até:" (`a.eg.qt`) |
| `eY` | Boolean | `ft` / `c(Boolean)` | à venda | aceita oferta ≥ `ev` (`a.cz`) |
| `eZ` | int | `fA` / `am` | id do time anterior | evita recompra pela IA (`best.l`) |
| `fa` | int | `fB` / `an` | sem leitura encontrada | — |
| `fb` | Boolean | `fC` / `h(Boolean)` | é júnior | — |
| `fc` | int | `fD` / `ao` | potencial exibido | `es` ± 1 (`fZ`); desenhado como 0,5 a 5 estrelas (`b.aI`) |
| `fd` | int | `fE` / `ap` | maturação do júnior | 0–100; barra verde (`go`) |
| `fe` | double | — | acumulador de `fd` | — |
| `ff` | int | `fL` / `ar` | temporada em que subiu da base | reduz o valor por 3 temporadas (§3.7) |
| `fh` | int | `gy` | gols na carreira | +1 em `a(at, ah)` |
| `fi` | int | `gz` | jogos na carreira | +1 em `b(at, ah)` |

### 3.2 Campos `transient` (não vão para o save)

| Campo | Uso |
|---|---|
| `eo` | cache do time (`fg`) |
| `fg` | contador de cartões na partida (`gi`, `gj`, `aw`; `best.I`, por volta da linha 501) |
| `fj`, `fl`, `fm` | ícones de lesão e cartão (`fS`) |
| `fk` | barra de progresso da condição ou da maturação |
| `fn` | gols no campeonato exibido (`gA`, `ax`; `a.eg` linha 885) |
| `fo` | `components.s`, contadores da partida em curso (`gB`) |
| `fp` | contador de "melhor da liga" usado para virar top mundial (`fd()`, `ay`) |
| `fq` | duração do último contrato em dias (`gG`, `aB`); aviso quando < 30 (`b.aH`) (inferido) |
| `ab` | média de notas calculada (`F()`, `gn`, `k(at)`) |
| `fr` | aviso de fim de contrato já mostrado (`gQ`, `r`; `a.eg` linha 346) |

### 3.3 Códigos

**Características** (`ey`, `ez`; nomes em `aq.qM`, siglas em `aq.qN`):

| Código | Nome | Sigla | Código | Nome | Sigla |
|---|---|---|---|---|---|
| 0 | Colocação | Col | 7 | Desarme | Des |
| 1 | Defesa Penalty | DPe | 8 | Drible | Dri |
| 2 | Reflexo | Ref | 9 | Finalização | Fin |
| 3 | Saída Gol | SGo | 10 | Marcação | Mar |
| 4 | Armação | Arm | 11 | Passe | Pas |
| 5 | Cabeceio | Cab | 12 | Resistência | Res |
| 6 | Cruzamento | Cru | 13 | Velocidade | Vel |

Características sorteadas por posição para jogadores gerados (`F.at`):

| Posição | Pares possíveis (cr1, cr2) |
|---|---|
| Goleiro | (0,3) (0,1) (2,0) (1,2) (3,1) (0,2) |
| Lateral | (6,10) (6,13) (10,11) (10,13) (10,6) (10,9) (6,11) |
| Zagueiro | (7,10) (7,12) (7,5) (10,13) (7,13) (7,10) (7,5) (7,13) (7,12) (7,9) (7,10) (5,12) |
| Meia | (4,11) (4,9) (9,11) (11,9) (4,8) (4,13) (7,10) (7,11) (7,5) (7,13) (10,13) (10,11) (9,4) (10,12) (4,11) (8,11) (7,9) (11,13) (7,11) |
| Atacante | (9,5) (13,9) (9,5) (8,9) (9,13) (9,5) (9,8) (5,13) (8,11) (9,11) (9,12) (13,8) |

**Habilidades individuais** (rótulos da ficha em `a.eg.qt` e do editor em `components.O`):

| Índice em `eH` | Campo | Getter | Rótulo |
|---|---|---|---|
| 0 | `eA` | `gK` | Goleiro |
| 1 | `eB` | `gJ` | Velocidade |
| 2 | `eC` | `gL` | Técnica |
| 3 | `eD` | `gM` | Passe |
| 4 | `eE` | `gN` | Desarme |
| 5 | `eF` | `gO` | Armação |
| 6 | `eG` | `gP` | Finalização |

A tela de treino separa "Habilidades principais (gol/des/arm/fin)" de "Habilidades secundárias (vel/tec/pas)" (`a.iQ`). As habilidades só existem quando a opção `f.habilidadeIndividual` está ligada; com ela desligada, a ficha mostra apenas "Força" (`a.eg.qt`).

**Perfil `ex`** (`F.fG`), recalculado a partir de posição e características (não vem do arquivo):

| Posição | Regra (primeira que casar) | Interpretação (inferido) |
|---|---|---|
| Goleiro, zagueiro | sempre 0 | — |
| Lateral | cr1 ∈ {13, 6} → 1; cr1 ∈ {7, 10} → 0; cr2 = 13 → 1; cr2 ∈ {7, 10} → 0; cr1 ∈ {8, 9, 11, 4} → 1; senão 0 | 0 defensivo, 1 ala ofensivo |
| Meia | cr1 ∈ {11, 9, 8, 4} → 1; cr1 ∈ {7, 10} → 0; cr2 ∈ {11, 9, 8, 4} → 1; cr2 ∈ {7, 10} → 0; senão 1 | 0 volante, 1 meia ofensivo |
| Atacante | cr1 ∈ {7, 10} → 0; cr1 ∈ {8, 13, 6} → 2; senão 1 | 0 atacante que marca, 1 centroavante, 2 ponta |

Na regra do lateral, o terceiro teste compara `cr1 == 6` de novo em vez de `cr2 == 6`, como está no decompilado.

### 3.4 Do arquivo `.ban` ao jogador

`e.g` (jogador no arquivo, `serialVersionUID` 16) tem os campos `a` nome, `b` estrela, `c` país, `d` idade, `e` posição, `f` status, `g` cr1, `h` cr2, `i` lado, `hash`, `j` top mundial, `tid`, `sid`, `aid`. O construtor `F(e.g, boolean júnior, ah)` copia:

| `e.g` | `best.F` | Observação |
|---|---|---|
| `getNome` | `dm` | — |
| `getPais` | `pais` | — |
| `getPosicao` | `en` | — |
| `getLado` | `er` | 0 → 0, qualquer outro → 1 |
| `isTopMundial` | `el` | — |
| `isEstrela` | `ek` | vira verdadeiro se `el` |
| `getHash` | `es` (potencial) | estrela com valor > 8 → 10 |
| `getStatus` | `status` | — |
| `getCr1`, `getCr2` | `ey`, `ez` | — |
| (parâmetro) | `fb` | lista de juniores do `.ban` |
| `getIdade` | `em` | regras do setter |
| — | `ex` | `fG()` |
| `tid`, `sid`, `aid` | — | não copiados |

O arquivo **não tem força, habilidades, valor, salário nem contrato**. Esses dados nascem em `fI` (§3.5), chamado para todos os profissionais e juniores na criação da carreira (`best.f.aU`, chamado por `best.p.dg`). Para profissionais vindos do arquivo, `fd` = 0, então o potencial `es` quase não influi na evolução (§3.11).

### 3.5 Força inicial — `F.fI`

Executado só com o jogador em um time. Passos:

1. **Base e bônus de habilidade** pelo time:
   - clube em país com ligas simuladas (`ah.kn()`): 1ª divisão 20/7, 2ª 15/3, 3ª 5/1, demais 1/1;
   - fora disso, pela reputação do clube: 1–3 → 5/1, 4 → 15/4, 5 → 22/7.
2. **Nível ajustado** `n` do time: igual ao nível até 15; acima disso, 16→17, 17→18, 18→19, 19→21, 20→25, 21→26, 22→27, 23→28, 24→29, 25→30.
3. `força = n + base + rand(0..2)`.
4. Bônus: titular de origem (`status` 1) soma `8 + rand(0..1)`; estrela ou top mundial soma `9 + rand(0..2)`.
5. Júnior: subtrai 23 (resultado < 5 vira 10) e gera `fd` inicial (`ga`) e potencial exibido (`fZ`).
6. Escala pelo nível do país do time (`ac.fn`):
   - país com nível ≤ 13: nível do time ≤ 5 → ×0,4; < 10 → ×0,65; demais → ×0,75;
   - país mais forte, time de nível < 10: < 3 → ×0,5; < 5 → ×0,6; < 10 → ×0,7.
7. Limite 100. Contrato de `rand(210..239)` dias a partir de hoje. `eq` = força.
8. Com habilidades ligadas, gera as sete habilidades com `j(n − 4 se n > 4, bônus)` (§3.6). Depois calcula valor (`fK`) e salário (`fJ`).

### 3.6 Habilidades iniciais — `F.j(base, bônus)`

Cada valor é limitado a 100. A habilidade principal sai da força; as outras saem de `base`, `bônus` e `base/3` (divisão inteira) mais um sorteio pequeno.

| Posição | Habilidade principal | Valor |
|---|---|---|
| Goleiro | Goleiro | força + rand(0..1) |
| Lateral perfil 0 | Desarme | round(0,8 × força) + rand(0..5) |
| Lateral perfil 1 | Armação | round(0,5 × força) + rand(0..4) |
| Zagueiro | Desarme | round(0,9 × força) + rand(0..1) |
| Meia perfil 0 | Desarme | round(0,7 × força) + rand(0..5) |
| Meia perfil 1 | Armação | força + rand(0..1) |
| Atacante | Finalização | round(0,8 × força) + rand(0..1) |

A habilidade "Goleiro" de jogadores de linha fica em 1 + rand(0..3) (lateral e meia), 1 + rand(0..6) (zagueiro) ou 1 + rand(0..5) (atacante).

Bônus por característica (cr1 ou cr2): o goleiro com Colocação ou Saída Gol ganha Técnica (+2..6 se for cr1, +0..1 se for cr2), com Reflexo ganha Velocidade, com Defesa Penalty ganha Goleiro. Nos jogadores de linha:

| Característica | Habilidades bonificadas |
|---|---|
| 4 Armação | Armação e Passe |
| 5 Cabeceio | Finalização (e Desarme em laterais e meias) |
| 6 Cruzamento | Passe |
| 7 Desarme | Desarme |
| 8 Drible | Técnica |
| 9 Finalização | Finalização |
| 10 Marcação | Desarme |
| 11 Passe | Passe |
| 12 Resistência | Desarme (e +2 em Finalização no zagueiro e no atacante) |
| 13 Velocidade | Velocidade |

### 3.7 Valor de mercado — `F.fK`

Recalculado na criação, na virada de temporada (`best.f.af`) e quando um júnior sobe (`K.a`).

```text
nivel  = nível do time (10 sem time)
fator  = 750 se nivel ≥ 21; 600 se 20; 500 se 18–19; 400 se 12–17; 366 abaixo
estrela: ×3 se nivel ≥ 22 e nacionalidade europeia; ×2 se nivel ≥ 21 e europeia; senão ×1,7
top mundial ×1,6 · atacante ×1,3 · titular de origem ×1,2
idade:  <20 → fator += (32−idade)×27   20–25 → +(32−idade)×22   26–31 → +(32−idade)×15
        32–33 → +(34−idade)×10          ≥34 → −(idade−34)×50     (fator ≤ 0 vira 60)
valor  = (2×força)² × fator
júnior: valor = round(valor×0,03) × potencial   (×1,5 se potencial 10)
recém-promovido da base: ×0,18 na temporada da promoção (limitado a ev se ev > 0),
                         ×0,35 na seguinte, ×0,65 na outra
```

"Europeia" é o continente da **nacionalidade** do jogador (`ac.gg() == 0`), não o do clube. Idade abaixo de 16 é corrigida para 16 dentro do cálculo.

### 3.8 Salário — `F.fJ`

```text
base = 350 (sem time ou divisão 0)
clube de Alemanha, França, Itália, Inglaterra ou Espanha (ah.ki, aq.rW):
      div 1 → 750, 2 → 550, 3 → 500, 4–5 → 450
demais clubes: div 1 → 600, 2 → 500, 3 → 450, 4–5 → 400
nível do time > 20 → +50
posição: goleiro −70, lateral −30, zagueiro −40, atacante −50, meia 0
base = round(0,5 × base)
sal  = força × 2 × base + (estrela ou top: força × 250)
idade ≥ 32: sal −= (idade − 32) × 300
mínimo 500 · top mundial ×1,4 · júnior ×0,1
opção "salário mensal" (f.salarioMensal): ×4
```

### 3.9 Contrato, venda e empréstimo

| Operação | Método | Efeito no jogador |
|---|---|---|
| Definir contrato | `a(long dias, boolean desdeHoje)` | `eJ` = hoje (ou o fim atual) + dias |
| Criação da carreira | `fI` | 210–239 dias |
| Subida da base | `K.a` | 180 dias |
| Técnico assume o time | `al.E(ah)` | todos os jogadores do time com 180 dias novos |
| Transferência definitiva | `a(ah, valor, boolean, false, false)` | `eZ` = time anterior; camisa, `eW` e `eY` zerados; 180 dias; `ev` = valor (`fm`); deixa de ser capitão ou batedor de faltas no time antigo; gera `best.ap` |
| Empréstimo | `q(ah)` | cria `components.t` e chama a transferência com `eX` verdadeiro e 365 dias |
| Volta de empréstimo | `r(ah)` | `eX` e `eW` falsos; 180 dias |
| Outra transferência | `c(ah, int)` | grava `best.ap` e `ev` = valor (inferido: leilão ou proposta direta) |

Na transferência definitiva com contrato vigente e o terceiro parâmetro verdadeiro, o time vendedor paga uma parcela do valor de acordo com os dias restantes: até 30 dias 12%, até 60 dias 20%, até 90 dias 22%, até 180 dias 25% e acima disso 30% (lançada como despesa de categoria 8 em `ah.w`). O significado econômico fica para o estudo de economia.

**Elegibilidade para jogar** (`F.a(I, boolean)`): não lesionado (`fP`), não suspenso na competição da partida (`c(at)`); em time humano, contrato não vencido.

### 3.10 Condição física, lesões, cartões e notas

**Condição física `eK`.**
- Perda a cada 7 minutos de jogo para quem está em campo (`I.l`, chamado em `best.I` quando `minuto % 7 == 0`; inferido que a variável é o minuto). O goleiro da casa 1 só perde no 2º tempo. A perda depende da idade (`F.fq`): até 20 anos −1, até 25 −2, até 31 −3, até 36 −4, acima disso −5. Valor negativo vira 1.
- Recuperação depois de cada dia de jogos, para todos os profissionais (`F.fr` em `best.f.as`); juniores voltam a 100. Os valores somados (limite 100) são:

| Situação | Ganho por idade |
|---|---|
| Jogou (`eL`), time humano | ≤ 20: +13 · 21–25: +24 · 26–31: +37 · 32–36: +40 · > 36: +30 |
| Jogou (`eL`), time da IA | ≤ 20: +20 · 21–25: +30 · 26–31: +50 · 32–36: +52 · > 36: +42 |
| Não jogou | < 26: +30 · 26–44: +35 · ≥ 45: +30 |

`F.fU()` (força × condição) faz `eK / 100 * eq` em aritmética inteira: o resultado é a força com condição 100 e zero abaixo disso. O único consumidor é `ah.a(I, ah, int)`, que não tem chamadores conhecidos (§6.7).

**Lesão** (`F.p(ah)`, chamada pelo evento de lesão da partida, `I`, por volta da linha 741):

```text
dias = rand(0..13) para idade ≤ 20
     = (condição < 10 ? 5 : condição < 50 ? 1 : 0) + rand(0..13) + k
       com k = 1 (≤25), 2 (≤30), 3 (≤35), rand(5..24) (≤45), 10 + rand(5..24) (>45)
idade ≥ 35: força −5 (mínimo 1)
extra: 1% +70 dias; 3% +40; 6% +20
fim da lesão = data do dia + dias; registra lesão na estatística da temporada (k.cd)
```

Em time humano, lesões de 8 dias ou mais geram uma mensagem ao técnico (`components.as`, tipo 3), com código escolhido pela faixa de dias (< 15, < 22, < 29, < 43, < 55, < 70, ≥ 70). A cura não muda força nem habilidades.

**Cartões e suspensão** (`F.a(int tipo, at, ah)`; juniores não recebem; a competição amistosa `f.bv()` não gera `best.H`, mas a estatística da temporada é atualizada):

| Tipo | Significado | Efeito em `best.H` da competição |
|---|---|---|
| 2 | amarelo | `ca` +1 |
| 3 | segundo amarelo (expulsão) | `ca` +1 e `cb` +1 |
| 4 | vermelho direto | `cb` += 1 (70%), 2 (20%), 3 (7%), 5 (≈2%) ou 10 (≈1%) jogos |

Suspenso quando `ca ≥ 3` ou `cb ≥ 1` (`H.gT`). Cumprir um jogo (`H.gU`) zera `ca` (se ≥ 3) ou desconta 1 de `cb`. A suspensão é por competição e some na virada de temporada, porque `eS` é esvaziada.

**Nota da partida** (`F.a(at, I, int lado, int adversário, ah)`):

| Componente | Regra |
|---|---|
| Base (vitória / empate / derrota) × força ≤30, ≤60, ≤90, >90 | vitória 6,0 / 6,0 / 6,7 / 7,2; empate 5,5 / 5,8 / 6,2 / 6,8; derrota 5,0 / 5,2 / 5,5 / 6,0 |
| Fora de posição (`gF`) | −1 (−2 se a casa for a 1) |
| Casas 10–17 | posse maior ou menor que a do rival (`I.hz`): ±0,3 ou ±0,8; ajustes por perfil 0 e por cr1 Passe/Armação |
| Contadores da partida (`components.s`) | gol +0,9; amarelo −0,2; vermelho −0,8; assistência +0,4; `tK` +0,3; `tx` −1,5 (e mais −1,2 × `tx` se `ty` > 0) |
| Casas 1–13 | desarmes maiores ou menores (`I.hB`): de +0,6 a +0,9 ou −0,5; ajustes aleatórios |
| Goleiro (casa 1) | −0,8; +0,2 por chute no gol do rival (`I.hZ`); +1,2 por `tI`; +0,2 se o rival finalizou mais de 10 vezes; gols sofridos 0 → +1, 1 → −0,5, 2–4 → −1, ≥5 → −2; −1 se o rival não chutou no gol |
| Casas 1–13, gols sofridos | sem gols +0,5 (mais bônus nas casas 2–9 e 11–13); mais de 1 → −0,1 por gol |
| Estrela / top mundial | +0,4 / +0,6 |
| Limites | máximo 10; minutos < 15 → −2,5; < 45 → −1; mínimo 2,0; menos de 20 minutos com nota ≤ 2 → 0 (sem nota) |

A nota vai para `eN`, `eU` (`best.J`), `best.k` (só notas ≥ 2,0), `best.H` da competição e a seleção da liga (`f.B.E/F`). Os minutos jogados saem dos eventos de substituição `best.A` da partida (`I.hE`).

### 3.11 Estatísticas guardadas no jogador

| Estrutura | Chave | Campos | Atualização |
|---|---|---|---|
| `best.H` (lista `eS`) | competição (`Y`, id em `ft`) | `ca` amarelos acumulados, `cb` jogos de suspensão, `T` jogos, `V` gols, `cc` assistências, `fu` soma das notas, `fv` nº de notas | `F.b(at,ah)` jogo, `F.a(at,ah)` gol, `k.a(F,at)` assistência, `F.a(int,at,ah)` cartões, `F.a(at,double)` nota |
| `best.k` (lista `eT`) | temporada `ae` + id do time `bW` | `T` jogos, `V` gols, `cc` assistências, `ca` amarelos, `cb` vermelhos, `cd` lesões, `ab`/`ce` soma/contagem de notas | `F.a(int código, ah, double, at)` com código 0 jogo, 1 gol, 2 amarelo, 3 vermelho por 2º amarelo, 4 vermelho, 5 lesão, 8 assistência, 100 nota |
| `best.J` (lista `eU`) | partida | `Z` nota, `fy` dia do calendário, `gx` índice da partida no dia | `F.a(at, I, …)` |
| `fh`, `fi` | carreira | gols, jogos | gol e jogo (não contam para júnior: `fC()` bloqueia) |
| `components.s` (transient) | partida em curso | `V` gols, `Pd` finalizações, `Pj` amarelos, `Pk` vermelhos, `cc` assistências; `Ph`, `Pi`, `Pe`, `Pl` sem rótulo (§14) | motor da partida (`c.b`, `best.I`) |

Agregados: `F.gw()` soma a carreira (jogos, gols, amarelos, vermelhos, lesões, assistências); `gs`, `gt` e `gu` somam a temporada atual; `gx` dá a média de notas da carreira; `gn` dá a média de `eU`.

### 3.12 Evolução semanal

Agendamento: o evento `"aj"` é posto em todos os domingos do calendário (`best.f.aS` → `best.a.c(1)`, `DAY_OF_WEEK == 1`) e chama `best.f.aT`, que:
1. na semana em que o contador `f.bh` vale 3, sorteia o foco de treino secundário de cada time (`ah.lj`: `nr[posição] = rand(1..3)`, ou seja, Velocidade, Técnica ou Passe);
2. executa `F.fV` para cada profissional e `F.fY` para cada júnior;
3. com habilidades ligadas, zera `bh` se ele valia 3 e, senão, soma 1. O ciclo é de 4 semanas.

`F.fV`: abaixo de 32 anos chama `fW` (crescimento); com 32 ou mais chama `fX` (declínio). Depois zera `eL`.

**Crescimento da força — `fW`.** Ganho semanal `g` (pontos de força):

| Nível efetivo do time | Faixas de idade → ganho |
|---|---|
| ≥ 19 | < 20: 0,16 · 20–22: 0,12 · 23–28: 0,10 · ≥ 29: 0,08 |
| 15–18 | < 18: 0,12 · 18–20: 0,10 · 21–28: 0,08 · ≥ 29: 0,06 |
| 11–14 | < 18: 0,10 · 18–20: 0,08 · 21–28: 0,06 · ≥ 29: 0,04 |
| ≤ 10 | < 18: 0,08 · 18–20: 0,06 · 21–28: 0,04 · ≥ 29: 0,02 |

O nível efetivo é o nível do time quando `kn()`; senão 20 (reputação ≥ 4), 18 (reputação 3) ou 12, e o ganho recebe +0,03 no fim.

Ajustes, em ordem:
- jogou (`eL`): +0,04;
- força 30–40: −0,02; 41–50: −0,03; 51–70: −0,04; 71–100: −0,05;
- se `fd` > 0 (veio da base): `fd` < 50 → −0,05, 50–69 → −0,02; potencial ≥ 9 → +0,07, 7–8 → +0,05;
- top mundial +0,02, ou estrela +0,01;
- continente do clube, aplicado quando o ganho passa de 0,06: América do Sul −0,02; África e Ásia −0,02; Concacaf −0,03 (exceto México); Oceania −0,04. Europa: Alemanha, França, Itália, Espanha e Inglaterra +0,01 (sem condição); Portugal, Holanda e Bélgica −0,01; demais −0,02. Na América do Sul o teste de exceção (Brasil, Argentina, Chile, Uruguai) é uma disjunção sempre verdadeira, então todos os clubes sul-americanos recebem −0,02;
- ganho negativo vira 0,01.

Aplicação: `eM += g`. Se `eM > 1` e força < 100: com força abaixo do teto, força +1 e `eM −= 1`; no teto, `eM = 1,0`.

**Teto da força.** É o menor entre o teto do clube e o do país, mais o bônus de potencial:

| Teto do clube (`kn()`): divisão × reputação 0–5 | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| divisão 0 | 30 | 30 | 30 | 30 | 30 | 30 |
| 1 | 80 | 85 | 90 | 95 | 100 | 100 |
| 2 | 50 | 60 | 60 | 65 | 80 | 80 |
| 3 | 40 | 40 | 40 | 45 | 70 | 70 |
| 4 | 25 | 30 | 30 | 30 | 50 | 60 |
| 5 | 30 | 30 | 30 | 30 | 30 | 30 |

Sem `kn()`, o teto é pela reputação: 5 e 4 → 100, 3 → 65 (70 para as habilidades), 2 → 40, 1 → 30, 0 → 20. Reputação fora de 0–5 é corrigida para 1.

| Teto do país do clube | Valor |
|---|---|
| Alemanha, França, Itália, Espanha, Inglaterra | 95 |
| Portugal, Holanda | 90 |
| Bélgica, Rússia | 80 |
| Outros europeus | 70 |
| Brasil, Argentina | 90 |
| Uruguai, Colômbia, Chile | 80 |
| Paraguai, Peru | 70 |
| Outros sul-americanos | 60 |
| Argélia, Marrocos, Egito | 75 |
| Nigéria, Senegal, Tunísia | 70 |
| Outros africanos | 60 |
| Japão, Coreia do Sul | 75 |
| Irã, Arábia Saudita, Emirados Árabes, China | 70 |
| Outros asiáticos | 60 |
| México / EUA / Costa Rica / outros Concacaf | 80 / 70 / 65 / 55 |
| Nova Zelândia / outros Oceania | 60 / 45 |

Bônus de potencial, só com `fd ≥ 60`: potencial 7 → +5..9; 8 → +15..19; 9 → +25..29; 10 → +30..34 (teto máximo 100).

**Crescimento das habilidades** (`F.f`, chamado por `fW` com habilidades ligadas, usando o mesmo ganho `g`):
- Modo padrão: distribui `g` na habilidade principal da posição e frações nas secundárias (`F.h`).
- Modo foco (semana 4 do ciclo, ou time humano com treino em "habilidades secundárias" sem delegar ao auxiliar, `ah.lm() == 1` e `!ah.ll()`): soma `2g` à habilidade `nr[posição]` do time (Velocidade, Técnica ou Passe).
- Goleiro e Desarme recebem ×1,2 no acumulador (`F.c(double,int)`).
- Cada habilidade com acumulador > 1 sobe 1 ponto se estiver abaixo do teto (`F.b(double,int)`, mesmo teto da força com reputação 3 → 70) e de 100.

| Posição (perfil) | Principal (×1) | ×0,4 | ×0,3 |
|---|---|---|---|
| Goleiro | Goleiro | — | — |
| Lateral 0 | Desarme | Armação | Finalização |
| Lateral 1 | Passe | Finalização | Desarme |
| Zagueiro | Desarme | Passe | Armação |
| Meia 0 | Desarme | Armação | Finalização |
| Meia 1 | Armação | Finalização | Desarme |
| Atacante | Finalização | Armação | Desarme |

**Declínio — `fX` (32 anos ou mais).**
- `x = idade − 31`, menos 2 se o nível do time for ≥ 20.
- Perda semanal: `0,7x/50` com força ≤ 50, `1,0x/50` com 51–70 e `1,2x/50` com 71–100.
- Quando `eM` passa de 1, a força cai 1 até o piso da divisão (1ª → 35, 2ª → 25, 3ª → 10, outras → 1). Sem `kn()`, a divisão é a da reputação: ≥ 4 → 1ª, 3 → 2ª, outras → 3ª. A força mínima é 1.
- Com habilidades ligadas, `F.e` reduz a habilidade principal da mesma forma. Na semana 4 do ciclo, o acumulador usado é sempre o de "Goleiro", com o ganho multiplicado por 10, como está no código.

### 3.13 Juniores: geração, maturação e promoção

**Geração** (`F.a(ah time, int posição, F reaproveitar, int, String nome, Boolean)`):

| Atributo | Regra |
|---|---|
| Lista | nova: `f.bA` (temporada) ou `f.Q()` (criação); é sempre posta nos juniores do time (o teste de duplicidade compara o time consigo mesmo) |
| Potencial `es` | d100 em três tabelas (abaixo) |
| Estrela | só se o d100 do potencial der 1 |
| Idade | rand(16..19) |
| Posição | d100: ≤10 goleiro, ≤30 lateral, ≤50 zagueiro, ≤80 meia, senão atacante; a posição pedida tem prioridade |
| Características | `F.at(posição)` |
| País | o do time; se o d100 da posição for 1 e o nível do time ≥ 18: clube brasileiro sorteia 11, 43, 195, 150, 84 ou um id de 0 a 199; clube de 3, 154, 85, 104 ou 72 sorteia 3, 154, 85, 104, 174 ou 72. Estrangeiro recebe potencial rand(7..10) |
| Nome | `au(país)` ou o informado |
| Demais | lado aleatório, status 0, `fG`, `ga`, `fI`, `fJ`, `fZ` |

| d100 → potencial | 1–2 | 3–4 | 5 | 6–8 | 9–10 | 11–15 | 16–25 | 26–30 | 31–50 | 51–60 | 61–65 | 66–75 | 76–80 | 81–90 | 91–95 | 96–98 | 99 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nível 15–18 e reputação ≤ 3 | 1 | 2 | 2 | 4 | 4 | 5 | 5 | 5 | 6 | 6 | 6 | 7 | 7 | 7 | 8 | 9 | 10 | 10 |
| Nível < 15 e reputação ≤ 3 | 1 | 1 | 2 | 2 | 3 | 3 | 4 | 5 | 5 | 6 | 6 | 6 | 7 | 7 | 7 | 8 | 9 | 10 |
| Nível ≥ 19 ou reputação ≥ 4 | 1 | 2 | 2 | 4 | 4 | 5 | 5 | 6 | 6 | 6 | 7 | 7 | 7 | 8 | 9 | 9 | 10 | 10 |

Na primeira e na terceira tabela o potencial 3 é inalcançável (o teste `≤ 4` vem depois de `≤ 5`).

**Quantos juniores** (`best.f.c(boolean)`):
- Na criação da carreira: clubes `kn()` com reputação ≥ 3 e menos de 12 juniores ganham 6 (posições 0, 1, 2, 3, 3, 4); outros com menos de 5 ganham 5 (0–4).
- Em cada virada de temporada, clubes com menos de 15 juniores ganham `k + 1` novos. `k` vale `2 + rand(0..2)` com `kn()`, ou `rand(0..2)` (+1 com nível ≥ 20) sem `kn()`. Se `k` + juniores ≥ 20, `k = 20 − juniores − 2`.

**Maturação semanal** (`F.fY`, idade ≤ 20): `fe += a + b`. `a` vale 0,5 (≤ 17 anos), 0,375 (18), 0,35 (19) ou 0,125 (20). `b` vem do potencial: ≤ 3 → 0,03; ≤ 6 → 0,04; ≤ 8 → 0,07; 9 → 0,10; 10 → 0,11. Quando `fe > 1`, `fd` +1 (limite 100). O `fd` inicial (`ga`) por idade é 16 → 15, 17 → 35, 18 → 55, 19 → 70, 20 → 75, mais rand(1..5) e o potencial (máximo 95).

**Potencial exibido** (`fZ`): 15% `es`, 45% `es − 1`, 40% `es + 1`, limitado a 1–10.

**Virada de temporada do júnior** (`F.gf`): idade +1. Com 20 anos ou mais:
- Promove se o potencial for ≥ `{1, 4, 5, 6, 6, 6}[reputação]` e o elenco tiver menos que `{3, 5, 5, 8, 6}` jogadores na posição. A promoção só ocorre com elenco < 32 (`K.a`) e repõe um júnior se houver menos de 20.
- Sem promoção, em time da IA, o júnior é regerado no lugar (`F.a(..., this, ...)`, novo nome e 16–19 anos). Em time humano ele fica.

**Promoção** (`K.a(boolean, F, ah)`):

```text
p = kn(): div <1 → 5, 1 → 22, 2 → 17, 3 → 14, outras → 7
    senão: reputação 5 → 20, 4 → 15, 3 → 12, 2 → 7, outras → 5
p += 5 se o clube for europeu; p += rand(0..4)
força = potencial + round(p × fd/100) (+ rand(0..9) se potencial ≥ 9)
habilidades: j(força − 5 (mín. 5), bônus 7/3/1 por divisão ou 1/1/1/4/7 por reputação)
deixa de ser júnior; ff = temporada; eM = 0; contrato 180 dias; fK; fJ
estrela de base: 1/3 de chance de manter; top mundial vira só estrela; outros: 1/200 de virar estrela
estrela com potencial < 8 → potencial 8
```

### 3.14 Envelhecimento, aposentadoria e reposição

Na virada de temporada (`best.f.af`), para cada profissional (`F.gd`), a idade sobe 1, `eS` e `eU` são esvaziadas e `ge` decide a aposentadoria. Jogadores sem time ou emprestados não passam por `ge`.

**Chance de aposentar** (`F.ge`, só com idade real > 32). A idade efetiva é a real menos 1 (estrela), menos 3 (top mundial) e menos 3 (goleiro):

| Idade efetiva | < 32 | 32 | 33–34 | 35 | 36 | 37–38 | 39 | 40 | 41–42 | 43–48 | > 48 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chance | 0% | 1% | 10% | 45% | 70% | 85% | 95% | 97% | 98% | 99% | 100% |

Em time humano a aposentadoria vira mensagem ao técnico (`components.as`, código 89). Pela leitura, o jogador não é removido nesse ponto (§14). Em time da IA, `a(null, −1, true)` aposenta:

1. **Vira técnico** só em clube `kn()`, com chance 1/n: n = 25 (div. 1), 50 (2), 60 (3), 100 (4), 120 (div. 0), 125 (outras); 5 para estrela e 2 para top mundial. O novo `best.al` entra na lista global de técnicos. Como o jogador já foi desvinculado do time quando `al.b(ah, F)` é chamado, só a nacionalidade e a temporada de estreia são copiadas; país, divisão e reputação do clube ficam nos valores iniciais.
2. Sai do elenco; `eT` e `eS` são apagadas.
3. **Hall de aposentados** (`best.b`, lista `f.az`): na temporada 1, com mais de 0 gols na carreira; nas temporadas 2–9, mais de 10; nas 10–19, mais de 30; depois, mais de 50.
4. Zera gols e jogos de carreira; vai para `f.bz` (removido de `f.ag` ao fim de `af`).
5. **Reposição:**
   - Gera um júnior na mesma posição, salvo se o clube já tiver juniores ≥ 20 − m sem necessidade; m = 2, ou 5 se divisão > 2 ou reputação < 3, ou 0 em time humano.
   - O novo júnior sobe na hora (`K.a`) se o clube da IA ficou abaixo de `{2, 3, 3, 6, 4}` na posição ou com menos de 16 profissionais, ou se um time humano tiver 20 ou mais juniores.

### 3.15 Estrela e top mundial

| Evento | Regra | Origem |
|---|---|---|
| Arquivo | `isEstrela`, `isTopMundial` do `.ban`; top implica estrela | `F.<init>(e.g,…)`, `F.a(Boolean)` |
| Melhor da 1ª divisão | ao fechar a temporada, o melhor jogador da seleção da liga entra em `f.B.ZX`; na 1ª divisão ele vira estrela | `f.B.fi` |
| Top mundial | no início da temporada (`best.f.al`), `fp` é zerado e cada ocorrência do jogador em `ZX` da 1ª divisão soma 1 (`ZX` não é esvaziada pelos métodos de limpeza da liga, então acumula temporadas; inferido). Com idade < 35 e sem ser top, vira top se o clube for europeu de Espanha ou Inglaterra (fp ≥ 2), Itália, França ou Portugal (fp ≥ 3), ou do Brasil (fp ≥ 4). O código também aceita o país 1 (África do Sul) no grupo europeu | `F.fd`, `F.ay` |
| Perda do top | ao zerar `fp`, top mundial com mais de 34 anos perde o título | `F.ay` |
| Promoção da base | ver §3.13 | `K.a` |

### 3.16 Nomes e agentes livres

- **Nomes** (`F.au` → `best.M.au`): sorteia um nome em `/arquivos/names/<SIGLA>.txt` e, conforme o nome, um sobrenome em `/arquivos/surnames/<SIGLA>.txt` (sigla do país via `best.n.G` e `best.ad.jE`). Com 1000 nomes ou mais, há 50% de chance de sortear entre os 500 primeiros. Sem arquivo, `F.av` usa faixas fixas da lista global `f.aX()` por país ou continente.
- **Agentes livres** (`f.ai`, `bN()`): jogadores criados por `F(int país)`. `K.r(país, nível)` cria 20 de uma vez (3 GOL, 4 LAT, 4 ZAG, 5 MEI, 4 ATA) quando um país não tem atletas para a seleção (`Z.z`):
  - força = nível ajustado − 5 + rand(0..7);
  - potencial rand(7..10), idade rand(18..29);
  - contrato de 180 dias.

  Na virada de temporada (`F.gc`), cada agente livre envelhece; acima de 35 anos renasce com rand(18..27) anos, nome novo e estatísticas apagadas.

---

## 4. Seleções nacionais e uso do jogador fora do clube

`Z.z(boolean)` monta a seleção (`Z.hy`, um `ah` sem arquivo):
- Escolhe um técnico (`Z.ji`): sem clube nem seleção, com prioridade para reputação 5, 4 e 3 da mesma nacionalidade.
- Junta os profissionais com clube e os agentes livres da nacionalidade, ordenados por força e, no empate, estrela (`best.aa`).
- Preenche cotas por posição e lado: `{3, 4, 4, 5, 4, 3}` no total, com cotas separadas para lado direito, lado esquerdo e volantes.
- Completa até 23 se faltar gente e ordena por `h.a.abe`.
- Escolhe capitão e batedor de faltas automaticamente (`kz`, `kA`).

`Z.hz` (`jl`) indica que o país tem pelo menos 15 jogadores de linha e 2 goleiros (`Z.jj`).

---

## 5. Força efetiva na partida (referência)

O motor usa por jogador `c.b.B(F)`. Sem habilidades individuais é a força. Com elas, é uma soma ponderada que depende da casa tática:

| Casa | Goleiro | Velocidade | Técnica | Passe | Desarme | Armação | Finalização |
|---|---|---|---|---|---|---|---|
| 1 (goleiro) | 0,6 | 0,15 | 0,15 | 0,1 | — | — | — |
| 3–8 (zaga) | — | 0,25 | 0,1 | 0,1 | 0,5 | 0,05 | — |
| 2, 9 (laterais) | — | 0,1 | 0,1 | 0,3 | 0,4 | 0,05 | 0,05 |
| 11–13 (volantes) | — | 0,15 | 0,1 | 0,2 | 0,4 | 0,1 | 0,05 |
| 14–16 (meias ofensivos) | — | 0,1 | 0,1 | 0,25 | 0,05 | 0,4 | 0,1 |
| 10, 17 (alas) | — | 0,25 | 0,15 | 0,25 | 0,05 | 0,2 | 0,1 |
| 19–24 (atacantes) | — | 0,25 | 0,25 | 0,05 | — | 0,05 | 0,4 |
| 18, 25 (pontas) | — | 0,25 | 0,15 | 0,15 | — | 0,05 | 0,4 |

Fora de posição (`F.gF`) a força efetiva cai à metade; o mínimo é 1. Há redutores adicionais por tipo de competição e reputação (seleções, continentais, mundial de clubes), que ficam para o estudo da partida. **A condição física não entra nessa conta** (pela leitura de `c.b.B`).

---

## 6. Time — `best.ah`

### 6.1 Campos persistidos

| Campo | Tipo | Getter / setter | Significado |
|---|---|---|---|
| `mU` | int | `lk` / `bX` | id do time na carreira (§2.2) |
| `ei` | int | `gD` / `az` | sem uso encontrado além do getter |
| `mV` | String | `jY` | `fileRef` (nome do arquivo `.ban` sem extensão); usado nos clássicos (`aq.pe`) |
| `mW` | Boolean | `jZ` / `k` | time humano |
| `mX` | Boolean | `kn` / `l` | clube de país com ligas nacionais simuladas (marcado em `Z.Ar`) |
| `mY` | int | `kl` | id do arquivo (`e.t.id`) |
| `pais` | int | `getPais` / `setPais` | país |
| `dr` | int | `getEstado` | estado brasileiro (índice de `aq.rX`: 0 AC … 25 SP, 26 TO); `jV`, `jW` e `jX` agrupam estados em regiões para torneios regionais |
| `hA` | int | `getNivel` / `setNivel` | **nível** 1–25 (fora disso vira 10); fixo na carreira (só o editor muda) |
| `divisao` | int | `getDivisao` / `setDivisao` | divisão nacional (0 = fora das divisões) |
| `na` | int | via `h(al)` | id do técnico (`mZ` é o cache transient) |
| `nb` | long | `kb` / `e`, `v`, `w`, `f(long)` | dinheiro em caixa |
| `nc` | int | `getReputacao` / `setReputacao` | reputação 0–5 |
| `nd` | ArrayList&lt;F&gt; | `kc` / `N` | elenco profissional (máx. 35) |
| `ne` | ArrayList&lt;F&gt; | `ky` / `S` | juniores |
| `nf`, `ng` | ArrayList&lt;F&gt; | `kY`, `kZ` | titulares e reservas da última escalação automática |
| `nh` | F | `kd` / `j` | capitão |
| `ni` | F | `ke` / `k(F)` | batedor de faltas |
| `nj` | F | `lq` / `n(F)` | batedor de escanteios |
| `nk` | F | `lr` / `o(F)` | falso 9 |
| `nl` | int | `li` | cor base (`e.t.corBase`) |
| `cor1`, `cor2` | String | `kB`/`c(Color)`, `kC`/`d(Color)` | cores principal e secundária em `#rrggbb` (`nm`, `nn` são cache) |
| `no` | ArrayList&lt;ak&gt; | `km` | desempenho por tabela `f.s` na temporada; esvaziada na virada |
| `np` | ArrayList&lt;aj&gt; | `le` | campanha por competição e temporada |
| `dH` | v | `ev` / `a(v)` | estádio |
| `nq` | int[4] | `kj` / `k(int[])` | táticas: formação, estilo, marcação, foco |
| `nr` | int[5] | `bQ` / `u` | foco do treino secundário por posição (1–3) |
| `ns` | int | `lm` / `bZ` | modo de treino: 0 principais, 1 secundárias |
| `nt` | boolean | `ll` / `M` | auxiliar técnico decide o treino |
| `nu` | int | — | pontos acumulados de reputação |
| `nv` | boolean | `kf` / `I` | escalação já definida para a rodada |
| `hr` | int | `iS` / `bR` | número aleatório 1–1000 para desempates de ordenação |
| `nw` | ArrayList&lt;ah&gt; | `kD`, `A(ah)` | lista de rivais consultada pelo técnico; nunca preenchida no código lido |
| `nx` | C | `kL` | finanças |
| `ny` | ArrayList | `kV` | táticas salvas (`components.ag`) |
| `nz` | components.ag | `kX` / `a(ag)` | escalação padrão |
| `nA` | int | `kW` / `bV` | opção 0, 1 ou 2 gravada pela tela de tática (`a.bG`, `a.bH`, `a.bI`); rótulo não confirmado |
| `nB` | int[15] | `la`, `lb` | pontos de ranking por tipo de competição (§6.9) |
| `nC` | int[15][3] | `lc`, `ld`, `e(int,int,int)` | por tipo de competição: pontos (3/1), gols pró, gols contra |
| `nD` | int | `lf` / `bW(int)` | sem uso identificado |
| `cA` | ArrayList&lt;ao&gt; | `cT` | títulos |
| `dm` | String | `getNome` | nome |

Transient: `mZ` (técnico), `nm`, `nn` (cores), `nE`–`nI` (escudo e camisas), `Kb`.

### 6.2 Do arquivo `.ban` ao time

`e.t` (time no arquivo, `serialVersionUID` 16) traz `valid`, `id`, `a` país, `b` estado, `c` nível, `d` fileRef, `e` nome, `f` estádio, `g` capacidade, `h` técnico, `i` nacionalidade do técnico, `l` jogadores, `m` juniores, `n` reputação, `o` cor base, `tid`, `sid`, `aid`, `vid` (precisa ser 185), `cor1` e `cor2`.

O construtor `ah(e.t)`:
- copia nome, fileRef, id, país, estado, reputação, cores e nível;
- cria o estádio `v(estádio, capacidade, this)` e o técnico `al(nome)` com nacionalidade e reputação do time;
- converte jogadores e juniores (§3.4);
- escolhe batedor de faltas e capitão (`kA`, `kz`).

Na criação da carreira, entram até 15 times por país, salvo países com liga configurada (`best.p.x`). Os países com 10 times ou mais (16 para Alemanha, Argentina, Inglaterra, Itália e França) recebem configuração de liga (`best.p.dd`).

### 6.3 Elenco e limites

| Regra | Valor | Origem |
|---|---|---|
| Elenco máximo | 35 | `ah.a(F,boolean)`, `ah.lh` |
| Contratação pela IA: força mínima | `aq.qg[divisão]` = {1, 40, 30, 20, 5} com `kn()`; senão `aq.qh[reputação]` = {1, 10, 20, 40, 50, 55} | `ah.a(F,boolean)`, `ah.b(F,boolean)` |
| Contratação pela IA: força máxima | `aq.qi[reputação]` = {20, 30, 45, 85, 100, 100} | `ah.a(F,boolean)` |
| Contratação pela IA: limite por posição | recusa se já houver mais de 3 GOL, 5 LAT, 5 ZAG, 10 MEI ou 5 ATA (sem contar emprestados) | `ah.a(F,boolean)` |
| Mínimos para repor (IA) | GOL 2, LAT 3, ZAG 3, MEI 5, ATA 3; abaixo disso chama `best.l.a(ah, [posição, força mínima da divisão ou reputação])` | `ah.ku` (via `best.ag.jR`) |
| Excedente posto à venda | acima de {2, 3, 3, 5, 4}, com 50% de chance, um reserva não estrela e não emprestado vai à venda (`ev = eu`); 30% também para empréstimo se força < 42 | `ah.kp` (início da carreira e de cada temporada, só IA) |

### 6.4 Táticas

`nq = [formação, estilo, marcação, foco]` (`a.bz.od`):

| Índice | Valores |
|---|---|
| 0 formação | índice de `aq.sJ` (1–12), na ordem de `aq.rB` sem as duas primeiras entradas: 1 5-4-1, 2 5-3-2, 3 4-5-1, 4 4-4-2, 5 4-4-2 def, 6 4-4-2 Ofen., 7 4-3-3, 8 4-3-3 def, 9 3-5-2, 10 3-4-3, 11 4-2-3-1, 12 4-2-3-1 Alas |
| 1 estilo | 0 Equilibrado, 1 Ataque total, 2 Contra-ataque (`aq.rC`) |
| 2 marcação | 0 Leve, 1 Pesada, 2 Muito pesada (`aq.rE`) |
| 3 foco | 0 Pelo meio, 1 Pelas laterais (`aq.rD`) |

**Escalação automática** (`ah.a(ah, I, int lado, int formação, boolean sortearTáticas)`, usada pela IA em `ah.kh` e pelo motor):
1. Filtra aptos (`F.a(I,false)`) e ordena por força e, no empate, condição (`h.a.abh`).
2. Para cada uma das 11 casas de `aq.sJ[formação]`, procura o melhor jogador com a posição, o lado e o perfil exigidos (`ah.a(ArrayList,int,boolean,boolean)`). O teste relaxa o lado e depois o perfil, e percorre posições alternativas na ordem de `aq.sH`.
3. Grava `eR` e `eL`; preenche o banco com as casas de `aq.sI` = {1, 1, 2, 4, 4, 12, 15, 15, 20, 20, 23}.
4. Sorteio da IA:
   - formação: 4-4-2 31%, 3-5-2 18%, 4-4-2 def 11%, 4-4-2 Ofen. 11%, 4-2-3-1 8%, 4-3-3 def 7%, 4-3-3 5%, 4-5-1 3%, 5-4-1 2%, 5-3-2 2%, 3-4-3 2%;
   - estilo: Equilibrado 70%, Ataque total 10%, Contra-ataque 20%;
   - marcação: Leve 65%, Pesada 30%, Muito pesada 5%;
   - foco: meio 70%, laterais 30%.

### 6.5 Grade tática (casas 1–25)

`F.eR` guarda a casa. As exigências de cada casa estão em `aq.sE` (posição, lado, perfil; −1 = qualquer) e as coordenadas da tela em `components.ao.RJ` (x de 35 a 345; y menor = mais perto do ataque):

| Casa | Exigência (posição, lado, perfil) | Posição na tela | Setores (`aq.sF`) |
|---|---|---|---|
| 1 | goleiro | gol (190, 565) | 1 |
| 2 | lateral, esquerdo | lateral esquerda (35, 425) | 3, 6 |
| 3, 4, 5 | zagueiro esq., qualquer lado, dir. | linha recuada (y 485) | 2/3, 2, 2/1 |
| 6, 7, 8 | zagueiro esq., qualquer lado, dir. | linha avançada (y 405) | 2/3, 2, 2/1 |
| 9 | lateral, direito | lateral direita (345, 425) | 1, 4 |
| 10 | lateral, esquerdo, perfil 1 | ala esquerda (35, 265) | 6, 9 |
| 11, 12, 13 | meia perfil 0 (esq., qualquer, dir.) | volantes (y 315) | 5/6, 5, 5/4 |
| 14, 15, 16 | meia perfil 1 (esq., qualquer, dir.) | meias ofensivos (y 205) | 8/9, 8, 8/7 |
| 17 | lateral, lado 1, perfil 0 | ala direita (345, 265) | 4, 7 |
| 18 | atacante esquerdo perfil 2 | ponta esquerda (35, 55) | 12 |
| 19, 20, 21 | atacante esq., qualquer, dir. | ataque (y 115) | 11/12, 11, 11/10 |
| 22, 23, 24 | atacante esq., qualquer, dir. | ataque avançado (y ≈ 30) | 11/12, 11, 11/10 |
| 25 | atacante direito perfil 2 | ponta direita (345, 55) | 10 |
| ≥ 26 | banco de reservas | (470+, 30) | — |

A casa 17 exige lado 1 (esquerdo), embora fique à direita da tela. Por isso as regras de "fora de posição" (`F.gF`) e da seleção da liga (`f.B`) tratam 10 e 17 como exceções. `F.gF` considera fora de posição quem não tem casa, ou cuja posição difere de `aq.sE[casa][0]`.

### 6.6 Capitão e batedores

Os papéis foram confirmados pelo menu da tela tática (`a.bz.oc`: "Batedor de faltas", "Capitão", "Batedor de escanteios", "Falso 9") e pelos ícones (`components.ao`: `kicker.png` para `ke`, `captain.png` para `kd`, `escanteiosicone.png` para `lq`, `falsonove.png` para `lr`, este só nas casas > 14 exceto 17).

| Papel | Campo | Escolha automática |
|---|---|---|
| Capitão | `nh` | mais forte e, no empate, mais velho (`best.ai`) (`kz`, `P`) |
| Batedor de faltas | `ni` | entre os titulares de origem ordenados por força, o primeiro com cr1 Finalização; senão o primeiro titular de linha; senão o primeiro de linha (`kA`, `R`) |
| Batedor de escanteios | `nj` | sem escolha automática |
| Falso 9 | `nk` | sem escolha automática; alterna no menu |

Os getters descartam o papel se o jogador mudou de time, salvo em seleções (`lp`). O motor usa `ke()` nos lances de código 3 e 4 e `lq()` no código 5, quando o jogador está em campo (`c.b`, linhas 1021 e 1049). Pelos rótulos do menu, 3 e 4 são faltas e 5 é escanteio (inferido).

### 6.7 Força do time

- **Nível `hA` (1–25):** é a medida de força do clube usada fora da partida. Entra na força inicial dos jogadores, no valor, no salário, no ritmo de evolução e nas ordenações (`h.a.cN`: nível, depois `hr`; `h.a.abm`: nível, reputação, `hr`). Não muda durante a carreira.
- **Na partida:** força efetiva por jogador e casa (§5).
- **`ah.a(I, ah, int)`** soma, por setor (`aq.sF`), a força × condição (`fU`) dos titulares. Aplica reduções se faltar meio-campo (×0,2 ou ×0,7), sobrar volantes ou laterais (×0,7) ou houver mais de 5 meias (×0,5), e grava o total em `I.aP`/`I.aQ`. Não foram encontrados chamadores nem leitores desses totais (`I.hr`, `I.hs`). Pela leitura, é código sem uso.

### 6.8 Reputação

`ah.kk()`, no fechamento da temporada (`best.f.ag`):
- Desgaste: reputação 5 perde 6000 pontos de `nu` por temporada e cai para 4 abaixo de −90000. A 4 perde 600 e cai abaixo de −9000. A 3 (`kn()`) perde 50 e cai abaixo de −1000. A 2 (`kn()`) perde 5 e é zerada abaixo de −1000, sem cair.
- Subida (nunca rebaixa): `nu` > 10 → 1, > 100 → 2, > 1000 → 3, > 10000 → 4, > 100000 → 5 (com teto em 100001).
- Pontos de `nu` por campeão ou vice (`ah.d`, por tipo de competição): por exemplo, liga nacional 500/90, copa nacional 300/50, estadual 10/5, continental de clubes 5000/1000, mundial de clubes 40000/1000. Valores acima de 1000 caem 40% para clubes sem `kn()` de África, Ásia, Concacaf ou Oceania (continente > 1), e ligas abaixo da 1ª divisão dão 50.

### 6.9 Histórico do time

| Estrutura | Conteúdo | Atualização |
|---|---|---|
| `aj` (`np`) | temporada, tipo e subtipo da competição, divisão, jogos, vitórias, derrotas, gols pró e contra, posição final (`nM`), fase alcançada (`nN`), `nO` | `ah.e(I)` por jogo; `ah.a(at,int,int)` no fechamento |
| `ak` (`no`) | por tabela `f.s`: jogos, vitórias, derrotas, gols, pontos | `ah.a(I, f.s)` |
| `ao` (`cA`) | títulos: temporada, tipo, divisão/país/continente, time, competição | `ah.q(at)` quando termina em 1º |
| `nB` | soma de pontos por colocação até a 10ª posição, por tipo (ex.: liga da 1ª divisão 15, 10, 8, 7, 6, 5, 4, 3, 2, 1) | `ah.b(at,int,int)` |
| `nC` | 3 pontos por vitória e 1 por empate, gols pró e gols contra, por tipo | `ah.e(I)` |

Os tipos de competição (`at.b()`, gravados em `at.F`) que aparecem nesses índices são: 0 amistoso, 1 liga nacional (`f.B`), 2 copa nacional (`f.f`), 3 estadual (`f.o`), 4 continental de clubes (`f.v`, `f.r` e outros), 5 mundial de clubes (`f.A`), 6 segunda continental (`f.x` Liga Europa, `f.H` Sul-Americana), 7 seleções, 8 recopas (`f.D`, `f.E`), 9 eliminatórias, 10 regionais (`f.F`), 11 supercopa nacional (`f.I`), 12–15 outros torneios (`f.J`, `f.K`, `f.M`/`f.N`, `f.L` "Torneio Amistoso").

### 6.10 Estádio e finanças (somente campos)

`best.v`:

| Campo | Significado |
|---|---|
| `dm` | nome |
| `dn[4]` | lugares por setor: Geral, Arquibancada, Cadeira, Camarote (`a.cq`) = 15%, resto, 9%, 0,9% da capacidade; capacidade fora de 1000–120000 vira 10000 (`v.N`) |
| `do[4]` | preços dos ingressos por setor (padrão 20, 35, 55, 80) |
| `dp` | sem rótulo identificado |
| `dq` | condição do gramado 0 Excelente, 1 Muito Boa, 2 Ruim, 3 Precária (`aq.pb`), sorteada pela reputação (`v.h`, `v.i`) |
| `pais` | país |

`best.C` (finanças) tem os campos `dK`, `dN`, `dR`, `dS` (long) e `dL`, `dM`, `dO`, `dP`, `dQ`, `dT`–`dX` (int). O dinheiro em caixa fica em `ah.nb`. Na criação, `kH` define o caixa por `aq.sC[divisão][0]` e lança a receita inicial `aq.sD`; os clubes fora do Brasil, com estaduais ligados, recebem 3,2 × a folha. O significado de cada campo de `C` fica para o estudo de economia.

### 6.11 Treino

| Campo | Efeito |
|---|---|
| `ns` = 0 / 1 | "Habilidades principais" / "Habilidades secundárias" (`a.iQ`) |
| `nt` | "Deixar auxiliar técnico decidir semanalmente" |
| `nr[posição]` | habilidade secundária (1 Velocidade, 2 Técnica, 3 Passe) sorteada a cada 4 semanas |

Efeito na evolução em §3.12.

---

## 7. Técnico — `best.al`

| Campo | Getter / setter | Significado |
|---|---|---|
| `dm` | `dS` / `i(String)` | nome |
| `mW` | `jZ` / `k` | humano |
| `nU` | `lT` | id |
| `bW` (+ `nV` transient) | `fg` / `n(ah)` | time atual |
| `nX` (+ `nW` transient) | `lF` / `B(ah)` | último time |
| `nY` | `lG` / `ch` | divisão − 1 do último time |
| `bf` | `bz` / `v` | país do último time |
| `nZ` | `lE` / `cg` | nacionalidade |
| `hy` | `jo` / `z` | seleção que dirige |
| `oa` | `lH` / `ci` | temporada de estreia |
| `ob` | `lO` | campanhas (`best.j`: temporada, time, jogos, vitórias, derrotas, pontos de ranking, títulos) |
| `oc` | `lI` | pontos de ranking do técnico |
| `W` | `A()` | jogos |
| `od` | `lJ` | vitórias |
| `oe` | `lK` | derrotas |
| `of` | `lL` / `cl`, `cj` | confiança da diretoria, 0–100 (inicia em 95) |
| `og` | `lM` / `cm`, `ck` | confiança da torcida, 0–100 (inicia em 85) |
| `nc` | `getReputacao` | reputação 0–5 |
| `nu` | — | pontos de reputação |
| `cA` | `cT` | títulos (`best.ao`) |
| `oh` | `lQ` / `T` | lista sem conteúdo identificado; zerada ao deixar time humano |
| `oi` | `lR` / `cn`, `lS` | contador zerado ao assumir um time (inferido: rodadas no cargo) |
| `bZ` | `cr` | número de títulos |

Os rótulos de `of`/`og` vêm da ficha do técnico ("Confiança diretoria:", "Confiança torcida:", `a.eg` linhas 1857 e 1862).

**Por partida** (`al.a(I, boolean, int)`), a confiança muda pelo resultado (vitória, empate, derrota), pelo mando, por goleada (diferença ≥ 3), pela diferença de nível entre os times e pela situação na tabela (`ah.p(at)`: 1 campeão, 2 zona de classificação, 3 meio, 4 risco, 5 rebaixamento). Há tabelas próprias para liga, estadual/regional, copa nacional/continental e demais. Caixa negativo em time humano tira de 5 a 10 pontos. Torcida abaixo de 20 tira 3 da diretoria. As regras de demissão ficam para o estudo de carreira e economia.

**Ranking** (`al.e(I)`): soma em `oc` e em `best.j` de 1 a 8 pontos por vitória, conforme o tipo de competição (liga: 4/3/2/1 pela divisão; seleções 8; mundial de clubes 7), com +1 em vitória fora de casa, exceto em seleções e no mundial de clubes. Empate dá 1 ou 2 pontos.

**Títulos** (`al.b(at,int,int)`, `al.q(at)`): os pontos por colocação também vão para `oc`. Confiança por título:
- liga ou estadual da 1ª divisão: +20 torcida e +15 diretoria, aplicado duas vezes se for liga;
- liga ou estadual de outra divisão: +20 torcida e +10 diretoria;
- supercopa nacional (tipo 11): +10 torcida;
- copa nacional, continentais (tipos 4 e 6), mundial de clubes e tipo 12: +30 e +30.

O título também gera `best.ao` e a mensagem.

**Reputação** (`al.kk`): a mesma mecânica do time, com limiares > 10, > 100, > 1000, > 10000 e > 22000 para as reputações 1 a 5. O desgaste é mais rápido: 5 → 4 abaixo de −20000; 4 → 3 abaixo de −3000; 3 → 2 abaixo de −500; 2 → 1 abaixo de −50, sendo 3 e 2 só em clube `kn()`. Pontos por campeão ou vice em `al.a(int,int,int,boolean,int)`; em seleções (tipo 7), o título da Copa do Mundo (subtipo 7) vale 23000 e as demais colocações premiadas, 6000.

**Ciclo do cargo:**
- `al.E(ah)` assume o time: diretoria 95, torcida 85; se humano, marca o time como humano e renova os contratos.
- `al.i(al)` sai e é substituído: grava `best.u` e devolve um time humano à IA.
- `ah.kE()` procura o substituto (`f.a(ah, nível)`, desempregados, `ay`).
- `al.lP()` move o técnico para a lista de removidos `f.an`.
- `al.c(String, int)` cria um técnico humano novo com reputação 3.

---

## 8. País

### 8.1 `best.ac` (enum estático, 224 valores)

| Atributo | Getter | Exemplo (Brasil) |
|---|---|---|
| nome | `getNome` | texto de `P29` |
| sigla | `jA` | `BRA` (também nomeia os arquivos de nomes) |
| id | `getId` | 29 |
| continente | `gg` | 1 (0 Europa, 1 América do Sul, 2 África, 3 Ásia, 4 Concacaf, 5 Oceania, `aq.sa`) |
| nível | `getNivel` (`ac.fn(id)`) | 20 |
| cores da seleção | `jB`, `jC` | RGB |

A busca é por nome `"P<id>"` (`ac.valueOf`). As constantes aparecem renomeadas no decompilado (`hG`, `hH`…), o que indica que o nome original de cada constante era `P<id>` (inferido).

### 8.2 `best.Z` (país na carreira)

| Campo | Getter | Significado |
|---|---|---|
| `pais` | `jc` | id |
| `hB` | `jp` | nome |
| `ds` | `eb` | ligas nacionais (`f.B`), da 1ª divisão para baixo |
| `dt` | `ek` | clubes do país fora das divisões (divisão 0) |
| `hv` | `jg` | todos os clubes do país |
| `hw` | `jh` | lista sem uso identificado |
| `hu` | `jq` | copa nacional (`f.f`) |
| `duasVoltasMataMata` | — | ida e volta por fase da copa (7 fases) |
| `hy` | `jn`, `jo` | seleção (criada sob demanda com reputação `jt()`: nível ≥ 20 → 5, 19 → 4, 17–18 → 3, 15–16 → 2, senão 1) |
| `hz` | `jl` | tem jogadores suficientes para a seleção |
| `hA` | `getNivel` | nível (12 por padrão; `jm()` copia do enum) |
| `hr` | — | número aleatório 0–49999 |
| `dw` | `ec` | contador sem rótulo identificado |
| `hC` | `jr` | sinalizador sem rótulo identificado |
| `hD`, `hE` (transient) | — | caches de clubes classificáveis e de estádios |

`best.f.aG()` tem um `Z` para cada um dos 224 países (`best.p.de`). `best.f.N()` tem só os países com ligas montadas (`best.p.w` → `Z.Ar`). `Z.Ar` cria até 4 divisões a partir da configuração `ConfigLigaType` do país ou, sem ela, de um padrão de 16 a 20 times. Os detalhes de formato de liga ficam para o estudo de competições.

---

## 9. Mundo e carreira — `best.f`

### 9.1 Campos principais

| Campo | Getter | Conteúdo |
|---|---|---|
| `ad` | `bs` | `est.InfoArquivoSalvoType`, gravado também no `.info` |
| `ae` | `H` / `k`, `I()` | temporada atual (começa em 1) |
| `rM` | `op` | ano inicial (2022); o calendário da temporada usa `rM + ae − 1` (`f.ah`) |
| `af` | `J` / `l` | índice do dia atual em `as` |
| `as` | `R` | calendário: dias `best.a` (data, partidas, competições e eventos agendados) |
| `ag` | `O` | todos os profissionais |
| `ah` | `Q` | todos os juniores |
| `ai` | `bN` | agentes livres |
| `aj` | `P` | todos os times de clube |
| `ak` | `aN` | times humanos |
| `al` | `L` | todos os técnicos |
| `am` | `M` | técnicos humanos |
| `an` | `bu` | técnicos removidos (`al.lP`) |
| `ao` | `N` | países com ligas (`Z`) |
| `ap` | `aG` | todos os países (`Z`) |
| `aq` | `aE` | estados (`best.w`) |
| `ar` | `bW` | supercopas nacionais (`f.I`) |
| `at` | `bn` | trocas de técnico (`best.u`) |
| `au` | `bo` | transferências (`best.ap`) |
| `av` | `bt` | empréstimos (`components.t`) |
| `aw` | — | objetos `best.B` com data de vencimento (inferido: propostas ou eventos agendados) |
| `ax` | `bd` | objetos `best.T` |
| `ay` | `bx` | histórico de estaduais (`aD`: estado, divisão, time, posição) |
| `az` | `bJ` | hall de aposentados (`best.b`) |
| `bu` | `bY` | lista de times preenchida em `Z.ee` (inferido: promovidos/rebaixados) |
| `aA`…`aY`, `GC`, `GI`, `IX`, `IY`, `Gy` | `aI`, `aF`, … | instâncias das competições internacionais e de seleções |
| `aZ` | `bV` | 4 torneios regionais (`f.F`) |
| `bh` | `bO` / `bP`, `A` | semana do ciclo de treino (0–3) |
| `bt` | `bU` | contador de ids de técnico |
| `bg` | `bH` / `w`, `bI` | contador de ids de time |
| opções | `isHabilidadeIndividual`, `isSalarioMensal`, `isJogaEstadual`, `isAutoRenovaContrato`, `getVelocidade`… | cópia de `est.Options` no início da carreira (`f.<init>`) |

Transient: `bx` (lista global de nomes, `aX`), `by`, `bz` (aposentados da virada), `bA` (juniores novos), `bB` (juniores promovidos), `bC` (`e.t` lidos), `bD`/`bE` (times por país e estado), `bF` (países com liga, `O`), `bG` (`ConfigLigaType`), `X`, `bv` (estáticos da partida corrente).

### 9.2 Ciclos que mexem no modelo

| Ciclo | Onde | O que faz com jogadores, times e técnicos |
|---|---|---|
| Criação da carreira | `best.p.dd`, `p.dg` | lê os `.ban`; cria `ah`, `F`, `al`; numera times (`dj`); gera força, habilidades, valor e salário (`f.aU` → `F.fI`); põe excedentes à venda (`ah.kp`); define caixa (`ah.kH`); cria juniores (`f.c(false)`) |
| Dia de jogos | `best.f.as` | recuperação física (`F.fr`); juniores com condição 100 |
| Domingo | evento `"aj"` → `best.f.aT` | evolução semanal (§3.12) |
| Início de temporada | `best.f.al` | seleção da liga e top mundial (`f.B.fi`, `F.fd`, `F.ay`) |
| Virada de temporada | `best.f` (por volta das linhas 380–460): `aa` → `ah()` (temporada +1, novo calendário) → `ag()` → `iZ()` → … → `af()` | `ag`: reputação dos times (`kk`), venda de excedentes, capitão e batedor automáticos na IA, +50 de confiança para todos os técnicos, receita dos humanos (`kG`). `iZ`: reputação dos técnicos. `af`: agentes livres (`gc`), profissionais (`gd`/`ge`), juniores (`gf`), novos juniores (`c(true)`), valor e salário de todos (`fK`, `fJ`) |
| Gravação | `c.a.ae` | renumera ids (`g.b.Ag`, `g.b.Ai`) e grava `.info`, `.s22` e `.sbck` |
| Carga | `c.a.c` | lê o `.s22` (ou o `.sbck`); religa competições (`g.b.Af`), transferências (`g.b.Aj`) e caches (`g.b.Ah`) |

---

## 10. Registros auxiliares

| Classe | Campos | Significado |
|---|---|---|
| `best.ap` | `d`, `on`, `y`, `ei`, `ej`, `oo`, `op`, `oq` (+ `U` transient) | transferência: dia, mês (1–12), ano, id e lista do jogador, time de origem, time de destino, valor |
| `best.u` | `bW`, `di`, `dj`, `dk` (+ data) | troca de técnico: time, técnico que saiu, técnico que entrou |
| `best.b` | `n`, `g`, `T` | aposentado ilustre: nome, gols, jogos |
| `best.ao` | `ae`, `w`, `dz`, `bW`, `Y` | título: temporada, tipo, divisão/país/continente, time, competição |
| `best.J` | `Z`, `fy`, `gx` | nota, dia, índice da partida |
| `best.j` | `ae`, `bW`, `T`, `bX`, `d`, `bY`, `bZ` | técnico por time e temporada: jogos, vitórias, derrotas, pontos, títulos |
| `best.W` | `dm`, `em` (20), `hk` status, `hl` estrela, `hm` top, `en`, `pais`, `er`, `hn`/`ho` cr1/cr2, `hp` júnior, `es` (1), `ff`, `eq` | molde de jogador para geração e para os times XML; não é gravado |

---

## 11. Erros e particularidades observados no código

Comportamentos que estão no decompilado e podem parecer erro. São registrados como lidos, sem correção:

1. `F.fU`: divisão inteira faz a força × condição valer 0 abaixo de condição 100 (sem efeito prático conhecido; §6.7).
2. `F.fG` (lateral): `var1 == 6` repetido onde se esperaria `cr2 == 6`.
3. `F.fW` (América do Sul): a exceção para os países fortes é uma disjunção sempre verdadeira.
4. `F.fd`: o país 1 (África do Sul) aparece no grupo de clubes europeus que podem gerar top mundial.
5. `F.a(ah, …)` (geração): o teste de duplicidade em `ky()` compara o time consigo mesmo; o potencial 3 é inalcançável em duas tabelas.
6. `F.p`: para menores de 21 anos, a penalidade por condição física baixa é descartada.
7. `F.a(at, I, …)` (nota): o ramo de `ty() > 0` usa `tx()`.
8. `F.e` (declínio de habilidade): na semana 4 do ciclo, o acumulador usado é sempre o de "Goleiro".
9. `aq.sE[17]`: a ala direita exige lado esquerdo.
10. `ah.nw` (rivais) nunca é preenchida; os clássicos vêm da tabela fixa `aq.pe` de pares de `fileRef`.
11. `best.f.c(true)`: o laço cria `k + 1` juniores (limite inclusivo).

---

## 12. Implicações para o projeto

- O pipeline que reescreve `.ban` controla força **só de forma indireta**: nível do time, reputação, divisão, `status` (titular +8), estrela e top mundial (+9). Idade, posição, lado e características entram no valor, no salário e nas habilidades. O campo `hash` é o potencial, que importa para juniores e para quem veio da base. O compilador atual usa `hash = 0` como padrão para jogadores sem dados anteriores (`tools/compile_live_rosters.py`), o que lhes dá potencial 0, fora da faixa 1–10 que o jogo gera.
- Saves não carregam se mudarem nome, tipo ou presença de campos não `transient` em `best.*`/`f.*` (Kryo, §2.3). O motor do campo animado pode ler os campos acima sem alterá-los.
- O campo animado pode usar, sem inventar dados, a casa (`F.fT`), o perfil (`F.fF`), o lado, as características, as habilidades, o capitão e os batedores (`ah.kd`, `ke`, `lq`, `lr`) e as táticas (`ah.kj`).

---

## 13. Classes de outros domínios identificadas de passagem

| Classe | Papel |
|---|---|
| `c.a` | E/S de save e opções; guarda `SR` (`best.f`) e `afQ` (`best.ay`) |
| `c.b` | motor da partida: força efetiva (`B(F)`), escolha de batedores, eventos |
| `best.I` | partida: placar (`hu`/`hw`), escalações (`hl`–`hq`), estatísticas (posse `hz`, finalizações `hA`, chutes no gol `hZ`, desarmes `hB`, erros de passe `hC`, faltas `hD`), eventos `hE` |
| `best.A` | evento da partida (substituição, minuto, tempo) |
| `best.a` | dia do calendário: data, partidas, competições, eventos agendados (`"cw"`, `"ds"`, `"aj"`…) |
| `best.at` | base das competições (tipo `tR`, subtipo `dz`, id `ei`) |
| `f.B`, `f.s`, `f.f`, `f.o`, `f.v`/`f.r`/`f.t`/`f.u`/`f.w`/`f.y`, `f.x`, `f.H`, `f.A`, `f.D`, `f.E`, `f.F`, `f.I`, `f.J`, `f.K`, `f.L`, `f.M`, `f.N`, `f.a`, `f.c`–`f.q`, `f.i`–`f.n` | competições (liga, tabela, copa, estadual, continentais, mundial, recopas, regionais, supercopa, torneios, amistoso, seleções, eliminatórias) |
| `best.e`, `best.am` | entrada e lista da seleção da liga |
| `best.l` | mercado da IA (contratações e reposições) |
| `best.p` | criação da carreira |
| `best.U`, `best.P` | leitura de `.ban` e de times XML |
| `best.M`, `best.n`, `best.ad` | nomes e textos; tabela de siglas de país |
| `best.K` | promoção de júnior e geração de agentes livres |
| `best.w` | estado brasileiro e estaduais |
| `best.C` | finanças do time |
| `best.ar` | mensagens da diretoria e da torcida |
| `g.b` | preparação de ids antes de gravar e depois de carregar |
| `h.a` e `h.*` | comparadores de ordenação |
| `components.ao` | desenho da grade tática |
| `components.as` | mensagens ao técnico |
| `components.s` | contadores da partida por jogador |
| `components.t` | registro de empréstimo |
| `components.ag` | tática salva ou escalação padrão |
| `a.bz`, `a.c_D` | telas de tática |
| `a.eg` | ficha do jogador e do técnico |
| `a.iQ` | tela de treino |
| `components.O` | editor de jogador |
| `d.*` | editor de times do jogo |
| `est.*` | opções, configuração de ligas e estaduais, resumo do save |

---

## 14. Lacunas

- **Aposentadoria em time humano:** `F.ge` só gera a mensagem 89. Não foi localizado onde o jogador é efetivamente removido, nem se o usuário escolhe.
- **`components.s`:** `Ph` (`tx`, somado em `c.b` quando um desarmador é sorteado), `Pi` (`ty`), `Pe` (`tK`) e `Pl` (`tI`, usado só para goleiro; talvez defesas) não têm rótulo confirmado.
- **Campos sem uso identificado:** `F.ep`, `F.eO`, `F.eQ`, `F.eV`, `F.fa`, `ah.ei`, `ah.nD`, `ah.nw`, `al.oh`, `Z.hw`, `Z.dw`, `Z.hC`, `v.dp`. Podem ser lidos por caminhos não percorridos, como acessores sintéticos ou telas.
- **`best.C`:** os campos foram listados, mas não interpretados (estudo de economia).
- **`f.aw`, `f.ax`, `f.bu`:** os papéis são inferidos e não estão confirmados.
- **Valores de `hash` nos `.ban` originais:** não foi verificada a distribuição real do potencial nos arquivos do jogo.
- **Ordem exata de serialização do Kryo:** a afirmação de ordem por nome é comportamento padrão inferido, sem teste neste estudo.
- **Teto com divisão > 5:** a matriz de teto tem 6 linhas (divisões 0–5); não foi verificado se o jogo cria clube `kn()` em divisão maior.
- **Cumprimento de suspensão:** o lugar exato em que `F.f(at)`/`H.gU` é chamado (fim de rodada ou partida sem o jogador) pertence ao estudo da partida e não foi conferido.
- **Constantes de `ah.d` e `al.a(int,int,int,boolean,int)`:** só alguns tipos de competição foram mapeados para os índices das tabelas de pontos de reputação.
