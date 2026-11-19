# Competições brasileiras 2026

Parte do componente **Elencos + Competições 2026**. Altera o motor de competições do Brasfoot 22-23 por transformação de bytecode, com autorização do proprietário registrada no `AGENTS.md`. Nenhum campo de classe serializada é criado ou alterado, e o motor de partidas não muda.

## O que é implementado

| Competição | Formato oficial 2026 | No jogo |
|---|---|---|
| Série A | 20 clubes, 38 rodadas | composição oficial na carreira iniciada em 2026 |
| Série B | 20 clubes; 1º e 2º sobem; 3º x 6º e 4º x 5º em ida e volta, volta na casa do melhor, empate no agregado classifica o melhor colocado (sem pênaltis) | igual |
| Série C | 20 clubes em turno único; 8 melhores em dois quadrangulares; 4 sobem; 2 caem | igual; em 2027 tem 24 clubes e, a partir de 2028, 28, com 6 rebaixados |
| Série D | 96 clubes em 16 grupos de 6; 4 por grupo; mata-mata em ida e volta com chaveamento do Anexo B; quartas reordenadas pela campanha; 4 eliminados nas quartas em 2 playoffs (1º x 4º e 2º x 3º); 6 acessos; 610 jogos | igual |
| Supercopa Rei | campeão da Série A x campeão da Copa do Brasil; com o mesmo clube nos dois títulos, o adversário é o vice da Série A; jogo único | igual (a partida não usa sede neutra) |
| Copa do Brasil | 126 clubes; 9 fases; fases 1–4 e final em jogo único; 5ª a 8ª em ida e volta; 155 jogos | igual |

## Estaduais e regionais

Cada estadual é descrito por uma ficha em `config/estaduais/<UF>.json`, gerada por `tools/build_estaduais_config.py` a partir dos regulamentos de 2026 (pesquisa em `data/private/competitions-sources/estaduais-2026/`, fora do Git). Os regionais usam o mesmo esquema em `config/regionais/`. Só as fichas com `"engine": "ready"` entram no executável. Uma ficha fica `pending` quando falta clube no jogo ou quando alguma regra não cabe no esquema, e o motivo fica em `pending`.

| Elemento | O que o motor faz |
|---|---|
| 1ª fase | `league` (pontos corridos), `groups` (dentro do grupo), `crossed` (cada clube enfrenta os grupos indicados em `opponents`, ou todos os outros, e a classificação é dentro do grupo) ou `fixtures` (tabela oficial com mandante e visitante de cada jogo) |
| vagas do mata-mata | `N` (colocação geral), `A1`, `B2`… (colocação no grupo), `W<k>`/`L<k>` (vencedor e perdedor do k-ésimo confronto da fase anterior), `R<k>` (k-ésimo por campanha acumulada entre os vivos) |
| desempate | `aggregate-then-penalties`, `penalties`, `points-then-penalties` (pontos nos dois jogos e pênaltis, sem saldo), `aggregate-then-better-campaign` |
| mando | `better-second` (melhor campanha manda a volta), `better-single` (melhor campanha manda o jogo único) e `neutral` (ordem da ficha) |
| rebaixamento | número de rebaixados diretos; o acesso e o descenso seguem a rotina do jogo (`best.w.ee`) |

Estado em 19/11/2026:

- **Prontos:** Alagoano (tabela oficial com os mandos), Carioca (1ª fase cruzada, quartas em jogo único, semifinal em ida e volta e final), Copa do Nordeste (grupos A×B e C×D, quartas com mando do 1º, semifinal e final em ida e volta) e Copa Verde (Copa Norte e Copa Centro-Oeste com 2 grupos de 6 cada, quartas e finais regionais, final geral).
- **Regras prontas, aguardando clubes:** os demais estados, menos AM, CE e MG.
- **Regras sem suporte:** AM (dois turnos com final entre campeões de turno), CE (2ª fase em grupos cruzados) e MG (semifinal pela classificação geral por posição no grupo).

Pontos de injeção:

| Ponto | Classe e método | Efeito |
|---|---|---|
| formato do estadual | `best.w.dY()`, antes de criar o `f.s` da 1ª divisão | participantes, grupos e opções da ficha; código de liga 2700 |
| tabela da 1ª fase | `f.s.a(ArrayList, boolean, boolean, ArrayList)` | gera a tabela cruzada ou aplica a tabela oficial |
| mata-mata | início de `f.s.yP()` e de `f.G.b(z, ArrayList, …)` | cria as fases pela ficha e resolve as vagas de cada fase |
| desempate por pontos | `f.G.b(boolean, boolean)`, código de confronto 2701 | pula o critério de saldo agregado |
| regionais | início de `f.F.an(ArrayList)` | Copa do Nordeste (código 2702) e Copa Verde (2703) |

Os participantes, os grupos e a tabela oficiais só valem na temporada 2026. Nas seguintes, os estaduais mantêm o formato e trocam clubes pelo acesso e descenso do jogo. Os regionais escolhem os clubes pela ordem do jogo (divisões nacionais primeiro) dentro de cada região ou bloco.

Verificação: `tools/competitions-src/harness/EstaduaisHarness.java`, numa cópia isolada da base 2026.6.14, conferiu por estado participantes, grupos, número de jogos, ausência de jogo dentro do grupo na fase cruzada, mandos da tabela oficial, fases do mata-mata e campeão, por 3 temporadas (2026–2028), sem falhas. É simulação automatizada, não homologação em partida.

## Outros países

Cada país tem um modelo em `config/countries/<país>-2026.json` (divisões oficiais, regras de play-off, desempate e nível estimado por divisão) e clubes gerados por `tools/build_country_clubs.py` a partir dos elencos pesquisados. Os `.cfg` das ligas são montados pelo codec (`app.CompetitionCodec set … count=N`).

| País | Divisões | Regras |
|---|---|---|
| Inglaterra (2026/27) | Premier League 20, Championship 24, League One 24, League Two 24 | play-off de 6 clubes na Championship (5×8 e 6×7 em jogo único; semifinais 3º e 4º contra os vencedores em ida e volta; final); League One 3º a 6º e League Two 4º a 7º; saldo antes de vitórias; clubes galeses com país País de Gales |
| Itália (2026/27) | Serie A 20, Serie B 20, Serie C 60 em 3 grupos oficiais | Serie B: 2 sobem direto, o 3º sobe direto com mais de 14 pontos sobre o 4º, senão play-off 5×8 e 6×7 em jogo único (empate classifica o mandante), semifinais 3º × vencedor de 6×7 e 4º × vencedor de 5×8 e final em ida e volta (empate classifica o melhor colocado); play-out 17º × 16º em ida e volta, dispensado com mais de 4 pontos de diferença; Serie C: sobem os 3 campeões de grupo e o vencedor do play-off de 28 clubes (fase de grupo, fase nacional com sorteio e Final Four, em `config/ligas/italia-serie-c.json`) |

Códigos de confronto usados na partida (`best.I.hk` e `f.G.b(boolean, boolean)`): 2129, o original (empate classifica quem joga a volta em casa, sem pênaltis); 2130 (empate classifica o mandante do jogo único, sem pênaltis); 2701 (pontos nos dois jogos e pênaltis, sem saldo).

Limitações da Itália: a Serie D não existe no jogo, então a Serie C não tem rebaixamento nem play-out; o campeão da Coppa Italia Serie C não é simulado, e a vaga dele na fase nacional fica com o melhor 11º colocado; a prorrogação não é disputada; o confronto direto (classifica avulsa) não entra no desempate; a Coppa Italia e a Supercoppa não foram adaptadas ao formato oficial. Os grupos da Serie C das temporadas seguintes seguem a distribuição do jogo.

## Fontes

Documentos oficiais da CBF, com SHA-256 registrado em `config/competitions/brasil-2026.json`:

- regulamentos específicos da Série C, da Série D e da Copa do Brasil;
- tabela detalhada da Série D (grupos);
- RNF 2026 e RNC 2026.

O regulamento da Série B não foi localizado no site da CBF. As regras dos playoffs vêm de reportagens concordantes e devem ser conferidas quando o documento for encontrado.

## Como funciona

`tools/patch_competitions_2026.py` gera `best/CompBrasil2026Data` a partir da configuração e compila `tools/competitions-src/best/CompBrasil2026.java`. Em seguida, injeta chamadas com `tools/competitions-src/CompetitionsTransformer.java` (ASM interno do JDK) e grava um executável novo e um `BRA.cfg` novo pelo codec.

| Ponto | Classe e método | Efeito |
|---|---|---|
| participantes da Série D | `best.w.Q(int)` | 2026: os 96 oficiais, na ordem dos grupos A01–A16; depois: critérios do regulamento (rebaixados da C, vagas por federação pelo RNF e residual) com grupos regionais de até 3 clubes por estado |
| divisões oficiais | `best.Z.Ar()`, depois da ordenação por força | coloca as Séries A, B e C oficiais à frente da lista em 2026 |
| chaveamento | início de `f.G.b(z, ArrayList, …)` | Série D: Anexo B, quartas pela campanha, volta na casa do melhor, playoffs; Série B: 6º x 3º e 5º x 4º |
| desempate sem pênaltis | código de confronto 2129 | playoffs das Séries B e D: saldo agregado e depois o melhor colocado (o `best.I.hk` original já dispensa pênaltis nesse código) |
| acesso e descenso | início de `best.Z.ee()` | Brasil com Série D pelos estaduais: listas assimétricas (6 sobem da D, 2 ou 6 caem da C) |
| rodadas por temporada | fim de `f.s.aN(boolean)` | recalcula o total de rodadas quando a divisão muda de tamanho |
| turno único da Série C | `f.s.a(ArrayList, …)` | turno único com 20 ou mais clubes no formato 1020 |
| Supercopa Rei | início de `f.I.Ab()` | escolhe o adversário pela regra da CBF (o original usava o vice da Copa) |
| tela da Série D | início de `f.B.mB()` | com os playoffs criados, a tela principal continua no mata-mata principal |
| Copa do Brasil | início de `f.f.a/b`, fim de `f.G.b(boolean, boolean)` e `f.f.b(L)` | monta as 9 fases, avança cada fase e dá nome às fases |

O estado novo cabe nos objetos que o jogo já salva:

- os playoffs da Série D ficam no campo `agA` de `f.B`;
- os clubes que esperam fases futuras da Copa ficam em `afU` de `f.f`.

## Verificação

`tools/competitions-src/harness/CompHarness.java` cria uma carreira sem interface em uma cópia isolada do jogo e joga temporadas inteiras. É simulação automatizada, não homologação em partida.

Resultado em 18/11/2026, numa cópia da base 2026.6.14 com o executável transformado, 3 temporadas e `-Xverify:all`, sem falhas:

- Série D com 610 jogos;
- 6 acessos por temporada;
- Série C crescendo de 20 para 24 e depois para 28 clubes;
- playoffs da Série B sem pênaltis;
- Copa do Brasil com 9 fases e 155 jogos.

Comandos (JDK 17 para montar; Java 8 é o runtime do jogo):

```bash
python -m tools.patch_competitions_2026 --source-exe <exe publicado> --output-exe <novo>/bf22-23.exe \
  --source-cfg <base>/conf_ligas_nacionais/BRA.cfg --output-cfg <novo>/conf_ligas_nacionais/BRA.cfg \
  --java "$JAVA_HOME/bin/java.exe" --javac "$JAVA_HOME/bin/javac.exe"
javac --release 8 -cp <novo>/bf22-23.exe -d <out> tools/competitions-src/harness/CompHarness.java
java -Djava.awt.headless=true -cp "<out>;<novo>/bf22-23.exe" CompHarness <cópia do jogo> 3 2026
```

## Carreiras existentes

Uma carreira criada antes do componente carrega e continua normalmente. A temporada em andamento termina no formato antigo. Na virada para 2027, `best.Z.ee()` ajusta os campos já salvos (Série D com 96 clubes e 16 grupos, Série B com 2 vagas por playoff, Série C com 2 rebaixados), e o formato de 2026 vale a partir da temporada seguinte. A Copa do Brasil muda já na próxima edição. Testado no harness com um save gravado pelo executável publicado.

## Lacunas conhecidas

- **Supercopa Rei com o mesmo campeão nos dois títulos:** a regra está implementada, mas o caso não apareceu nas temporadas simuladas.

- **Clubes ausentes:** os 96 clubes oficiais da Série D estão no jogo; 37 deles foram criados por `tools/build_brazil_new_clubs_2026.py` a partir das súmulas da CBF, com posição, data de nascimento e nacionalidade conferidas no oGol. Nível e reputação do clube (mediana da Série D) e características dos jogadores (padrão da posição) são estimativas. Os 126 clubes oficiais da Copa do Brasil também estão no jogo: 11 deles foram criados com elencos das súmulas da Copa do Brasil e do oGol.
- **Duplicatas:** dois clubes publicados têm duas cópias (Brasil de Pelotas e Inter de Limeira). As seleções do motor ignoram a cópia antiga, mas os estaduais do jogo ainda podem incluir as duas.
- **Desempate na fase de grupos da Série D:** o jogo ordena por pontos, vitórias, saldo e gols pró. Confronto direto, cartões e sorteio não são aplicados.
- **Sorteios da Copa do Brasil:**
  - a 1ª fase segue o RNC (1º x 28º);
  - a 5ª fase é Bloco I x Bloco II pelo RNC;
  - as demais fases são sorteadas.
  - O sorteio real de 2026 e os mandos do Anexo B não são reproduzidos.
- **RNC e RNF:** ficam fixos nos valores de 2026 em todas as temporadas da carreira. O critério 3 da Série D (5º a 32º da Série D anterior) não é aplicado nas temporadas seguintes.
- **Formato da Série C de 2027 e 2028:** não há regulamento publicado. A carreira mantém o formato de 2026 com mais clubes.
- **Calendário:** as datas seguem os tipos de data do jogo, não a tabela oficial.
- **Estaduais e regionais:**
  - desempates por confronto direto, cartões e sorteio não são aplicados; a classificação usa pontos, vitórias, saldo e gols pró;
  - torneios paralelos (Taça Rio, Troféu Inconfidência, Taça ACESC, Copa Grão-Pará e outros), disputas de 3º lugar e quadrangulares de rebaixamento não são disputados;
  - o mando pela campanha usa a campanha acumulada no torneio, mesmo quando o regulamento conta só uma fase;
  - os títulos da Copa Norte e da Copa Centro-Oeste não viram troféus próprios.
- **Fases de pontos dentro do mata-mata:** uma fase de grupos posterior à 1ª fase (como a 2ª fase do Cearense) é disputada como rodadas do mata-mata; a vaga `T<grupo><posição>` classifica os membros do grupo somando só os jogos dessas rodadas (pontos, vitórias, saldo e gols pró). O mata-mata do jogo comporta no máximo 7 rodadas, por isso o Amazonense (dois turnos e final entre campeões de turno, 10 rodadas) não foi adaptado.
- **Prorrogação:** o motor original não tem tempo extra e, por decisão do proprietário (19/11/2026), ela não será implementada. Nas regras que exigem prorrogação (playoffs e copas inglesas), o empate segue direto para o critério seguinte do jogo.
- **Interface:**
  - o nome da rodada dos playoffs vem da tabela genérica do jogo.
