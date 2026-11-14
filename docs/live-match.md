# Campo animado ao vivo

O campo animado desenha um campo 2D dentro da tela de partida original do Brasfoot, entre o placar e a tabela de outros jogos, com os 22 jogadores, a bola e o árbitro acompanhando os lances da partida assistida.

<p align="center"><img src="../site/assets/live/pitch-0.jpg" alt="Campo animado renderizado pelo código do painel" width="90%"></p>

## Princípio: o motor do Brasfoot não muda

- O motor de simulação, as regras, os sorteios e os resultados continuam sendo os do Brasfoot. O painel só segura o relógio por alguns segundos nos lances principais; ele não altera o que acontece na partida.
- O painel apenas **lê** informações que o próprio jogo mantém durante a partida e as representa visualmente.
- Nenhum evento é criado pelo painel: gols, cartões, pênaltis, lesões e substituições só aparecem quando o Brasfoot os registra.

Informações do jogo usadas pelo painel:

| Informação | Uso no campo |
|---|---|
| Lances registrados da partida | Gols, gols contra, cartões, faltas com barreira, pênaltis, lesões, substituições e assistências |
| Estatísticas da partida | Finalizações, desarmes, erros de passe e faltas representados no momento em que entram nas estatísticas |
| Escalações em campo e posições | Formação, entradas, saídas e expulsões |
| Estilo, marcação e foco de ataque | Altura do bloco, pressão e preferência de jogadas |
| Condição do gramado | Textura e desgaste do campo |
| Placar, minuto, tempo e estado do relógio | Saída de bola, intervalo, fim de jogo e pausa |

## Integração com o jogo

O patch é aplicado por [`tools/patch_live_match_view.py`](../tools/patch_live_match_view.py), que compila os fontes de [`tools/live-match-view-src/`](../tools/live-match-view-src/) e altera somente a classe da tela de partida (`a/dV.class`) dentro do executável, além de adicionar as classes do pacote `mega`:

| Ponto de integração | O que acontece |
|---|---|
| Construtor da tela de partida | Instala o painel (`mega.LiveMatchPanel.install`) e abre um espaço próprio no layout original, sem cobrir controles do jogo |
| Passo do minuto | A chamada ao passo de simulação do minuto passa por `LiveMatchPanel.engineStep`. O painel executa o mesmo método do jogo um minuto antes, uma única vez, para conhecer os lances antes de exibi-los; quando o temporizador do jogo chega ao minuto, o passo já executado é pulado. O passo do minuto 0 do 2º tempo, que o jogo roda junto com o intervalo, é adiado para a entrada dos times, sempre antes do minuto 1 e na mesma ordem |
| Exibição do lance | No clímax de cada lance o painel chama o método público da tela de partida que exibe um único lance (placar, som, texto e, quando o jogo prevê, a tela de substituição). É o mesmo método que o jogo usa ao virar o minuto; o lance fica marcado como exibido e o jogo não o repete |
| Cobrança de pênalti | `LiveMatchPanel.beforePenaltyKick` anima a preparação da cobrança; o resultado continua sendo decidido pela tela original de pênalti |

O transformador ([`LiveMatchTransformer.java`](../tools/live-match-view-src/LiveMatchTransformer.java)) usa ASM e confere o SHA-256 da classe original antes de alterar qualquer coisa. O patch aceita dois executáveis de origem:

| Origem | Resultado |
|---|---|
| Executável original do Brasfoot 22-23 | Somente o campo animado |
| Executável do Patch 2026 | Patch 2026 com o campo animado |

```bash
python tools/patch_live_match_view.py --source <bf22-23.exe> --output <pasta>/bf22-23.exe
```

## Velocidade e tempos

- **Movimento sempre no ritmo normal.** Jogadores e bola se movem na mesma velocidade em qualquer configuração do jogo, e cada lance é feito pelo jogador que o Brasfoot registrou.
- **Pausa curta nos lances do jogo.** O painel conhece os lances com um minuto de antecedência. Quando o próximo minuto tem gol, pênalti, cartão ou lesão, o painel segura o relógio da partida enquanto a jogada acontece no campo. No clímax (bola na rede, apito, falta no pênalti, queda do lesionado) o painel exibe aquele lance pelo próprio método do jogo, e só depois deixa o minuto virar. Assim, placar e campo mudam juntos, inclusive quando o mesmo minuto tem mais de um lance.
- **Minutos 0 e 1.** Os lances do primeiro minuto de cada tempo (e do minuto 0 do 2º tempo) são conhecidos durante a entrada dos times. O relógio fica em 0' até o último clímax desses minutos; depois volta ao ritmo normal. Gols nesses minutos usam jogadas de abertura: chute do meio-campo encobrindo o goleiro adiantado, lançamento longo nas costas da defesa, arrancada individual, chute de longe ou recuo errado do adversário interceptado.
- **Depois do gol.** O relógio continua parado enquanto os jogadores voltam às posições e dão a saída de bola. No início de cada tempo vale o mesmo para a entrada em campo.
- **O minuto nunca fica mais curto.** Ao soltar o relógio, o painel executa o próprio passo de minuto do Brasfoot, nunca antes do horário em que o jogo o executaria. Fora dessas pausas, a partida corre na velocidade escolhida pelo jogador, e substituições e lances de estatística não pausam o jogo.
- **Quanto tempo a mais.** Cerca de 3 a 8 segundos por gol (jogada e saída de bola) e de 2,5 a 3 segundos por cartão em média (até cerca de 5, quando o infrator precisa chegar ao lance); numa partida típica, de 15 a 30 segundos a mais. A proporção pesa mais nas velocidades rápidas, em que a partida inteira dura menos.

| Velocidade do jogo | Intervalo por minuto | Lances de estatística encenados |
|---|---|---|
| Lento | 2000 ms | até 2 por minuto |
| Normal | 1200 ms | 1 por minuto; experiência ideal |
| Rápido, Bem rápido, Super rápido, Ultra rápido | 700 a 100 ms | não encenados; gols com jogadas mais curtas |

- **Troca de lado.** No segundo tempo os times invertem o campo de ataque.

## Garantias de execução

- **Nunca travar o jogo:** qualquer erro no quadro do painel zera as animações; cada fase tem prazo máximo. Quando o prazo de um lance vence, o painel não solta o relógio: acelera a jogada em degraus (sem passes opcionais, lance direto, autor recebendo e finalizando de onde está). Só depois de três degraus e de uma repetição do lance o relógio é liberado sem animação, o que fica registrado como `sync_forced_release`.
- **Portão de sincronia:** toda liberação do relógio (fim de jogada, pedido de pausa, vigia, reset de segurança) passa por uma única verificação: o minuto só vira quando todos os lances antecipados chegaram ao clímax. Os prazos e o vigia contam o tempo do painel, que para enquanto há tela do jogo aberta; uma pausa longa não zera a jogada.
- **Nenhum gol perdido:** lances do jogo ficam na fila durante paralisações, na virada de tempo e depois de uma proteção contra travamento; a antecipação do minuto só acontece depois que o painel registra a troca de tempo; um gol pendente do 1º tempo é mostrado antes da entrada para o 2º tempo, e um gol interrompido é refeito uma vez.
- **Faltas no lugar certo:** faltas comuns e com cartão nunca são marcadas dentro da área de quem comete; a falta que gera pênalti é marcada dentro da área.
- **Diálogos e pausa:** com diálogos do jogo abertos o painel não segura o relógio. Um pedido de pausa sem lance pendente libera o relógio na hora; com lance pendente, o painel mostra "Pausa solicitada", acelera a jogada até o clímax (em geral 2 a 3 segundos), exibe o lance e então libera o relógio, e o Brasfoot abre a pausa. A pausa não congela a jogada no meio porque o minuto seguinte já foi simulado: uma substituição feita antes do lance faria o jogo mostrar um lance de quem já saiu.
- **Bola sempre ancorada:** a posse só muda por contato (passe, domínio, desarme, interceptação ou cobrança), e cada fase termina em um estado explícito.
- **Validação central:** antes de confirmar uma ação, o painel recusa desarme em goleiro com a bola, passe cujo destino seja um adversário e chute a partir de uma cobrança de lateral, e decide laterais, escanteios e tiros de meta pelo último toque. Também registra recuo em chance clara e bola esperando o goleiro. Cada ocorrência é registrada no diagnóstico (`rule_*`).
- **Cobrança nunca é cancelada:** um lance do jogo que chega durante um lateral ou escanteio espera a cobrança terminar, com o arremesso ou o cruzamento acelerados.
- **Sem espera parada:** portador parado com a bola por mais de 0,9 s com lance pendente aciona um recurso de futebol (condução, avanço do lance ou chute).
- **Diagnóstico:** eventos de integração são registrados em `%LOCALAPPDATA%\BrassfootPatch2026\live-match-debug.log`.

## Regras do futebol e reconciliação com o motor

O lance do Brasfoot define o destino da jogada; o painel escolhe uma sequência de futebol que leve até ele, sem atalhos visuais. O plano parte do lance e volta no tempo: quem precisa estar onde, e quando, considerando velocidade, aceleração e o tempo que a bola leva até o ponto de contato.

| Situação | Como é representada |
|---|---|
| Último toque | O painel registra quem tocou a bola por último. Lateral e escanteio vão para o adversário de quem tocou por último; tiro de meta, para o goleiro de quem defendeu. Quando o adversário precisa ganhar o lateral, quem pressiona toca na bola antes de ela sair |
| Goleiro com a bola | Nunca é desarmado. Se a posse precisa mudar, o goleiro repõe curto e um adversário que lê a linha intercepta; sem linha interceptável, ele chuta longe e a bola é disputada onde um adversário chega primeiro. A mesma regra vale com a bola nos pés (decisão de apresentação do projeto) |
| Erro de passe e perda de posse | O passe sempre mira um companheiro. O adversário que chega antes a algum ponto da trajetória corre até ele e intercepta no meio do caminho; sem interceptação possível, o passe sai forte ou fraco demais e para onde um adversário chega primeiro |
| Bola solta | Rola e desacelera depois do passe. O mais rápido de cada time vai até ela e quem toca primeiro fica com a posse; nos lances do jogo em que o time certo precisa ficar com a bola, o adversário fecha sem tocar |
| Falta e cartão | O infrator marca a zona da jogada assim que o lance é conhecido e a falta só é apitada com contato. O portador continua no ritmo normal e protege a bola quando o infrator se aproxima. Se a bola não chega perto dele, a falta é sem bola, sobre o adversário mais próximo, e a bola é levada ao local durante a paralisação. O motor não informa o motivo do cartão; a representação é sempre de falta |
| Substituição | Fica pendente até a próxima interrupção (bola fora, falta, gol, lesão, intervalo). Se o jogo não para, a próxima perda de posse sai pela lateral; nas velocidades rápidas, depois de 7 segundos a troca acontece com o jogador sem participação no lance. Quem entra vem pelo meio-campo |
| Gol contra | O atacante chuta ou cruza numa trajetória que não entraria, ao lado da trave; o defensor se coloca na linha da bola e o desvio muda a direção para dentro do gol |
| Passe para o gol | Sai só quando o autor consegue chegar ao ponto (até cerca de 1,9 s). A duração do passe é o tempo de chegada do autor: bola e jogador chegam juntos. Se o prazo vence com o autor longe, o ponto do chute é trazido para onde ele alcança, desde que continue sendo um chute plausível. O chute pode ser de primeira ou depois do domínio |
| Desarme | O desarmador é o que intercepta o caminho do portador mais cedo, com rota de antecipação. O portador não é freado; quando o perseguidor vem por trás, ele corta para dentro. Sem contato no prazo, outro defensor tenta; depois disso, o portador dá um toque longo e a bola é disputada |
| Passe para trás | Antes de passar para trás, o portador desacelera e gira; a bola contorna o corpo até o lado do passe |
| Atacante livre | Sem finalização prevista pelo motor, o atacante livre conduz em direção ao gol em vez de recuar; perto da área, um defensor fecha e desarma ou afasta, ou o cruzamento é cortado |
| Linha defensiva | Escalonada: o zagueiro do lado da bola sobe, o da sobra fica mais recuado e o lateral do lado oposto fecha por dentro, cada jogador com uma pequena variação própria. A linha sobe junta quando o portador adversário recua |
| Defesa do goleiro | No início do chute o painel calcula o ponto da trajetória que o goleiro alcança no tempo da bola. A bola termina no corpo dele no instante do contato e o goleiro dá um salto até o ponto, como a bola quando está no ar (sobe com a sombra no chão e pousa): encaixa, espalma para escanteio (por fora da trave) ou espalma para rebote. Chutes que entram, vão na trave ou para fora têm mergulho que não alcança |
| Gol | A bola atravessa a linha entre as traves desenhadas e sai da área visível; depois de uma pausa curta volta ao centro para a saída |
| Bola fora | Em lateral, escanteio e tiro de meta a bola sai da área visível e reaparece no ponto de cobrança quando o cobrador chega |
| Chance clara | Portador dentro ou na entrada da área, na faixa central, sem defensor entre ele e o gol: ele finaliza. Sem gol previsto pelo motor, o chute é só visual e não entra nas estatísticas: defesa, rebote para ele, trave ou para fora |
| Lesão | O lesionado entra no lance (recebe e sofre a entrada, disputa a bola ou sente na arrancada), cai e o ícone aparece 2,2 segundos (tempo real, igual em todas as velocidades) antes de o jogo exibir a lesão e pausar |
| Gol olímpico | Sempre nasce de escanteio: o goleiro espalma um chute para a linha de fundo, o autor cobra e a bola faz a curva direto para dentro do gol |
| Bola aérea para o gol | O cruzamento ou lançamento só sai quando o autor alcança o ponto no tempo do voo (até cerca de 1,25 s de corrida; 1,6 s no lançamento longo), e o autor entra na área durante a construção |
| Gol contra | O zagueiro do lance acompanha a jogada desde a antecipação, entre a bola e o gol. Se ele está na linha do chute, o chute sai na direção dele; se não, o atacante não espera: o goleiro espalma para escanteio e o desvio acontece no cruzamento. O desvio é mais lento que o chute para ficar visível |

As velocidades e acelerações usadas no planejamento são as mesmas do movimento dos jogadores, por isso o que o plano considera alcançável é o que o jogador consegue fazer em campo.

## Jogo corrido

Fora dos lances do jogo (gol, pênalti, falta, cartão, lesão, lances de estatística e saídas de bola), a movimentação é uma reconstrução visual. Ela não cria finalização, cartão nem placar, e a troca de posse segue a proporção de posse oficial da partida.

**Decisão com a bola.** Quando o portador fica livre para agir, o painel compara as ações possíveis e escolhe a de maior utilidade:

| Ação | O que pesa |
|---|---|
| Passe no pé ou no espaço (para quem já corre) | progressão, espaço do receptor, risco de interceptação na linha de passe (cada adversário, pelo tempo que a bola leva até o ponto), distância e impedimento |
| Inversão de corredor | vale mais quando o lado do receptor está menos povoado que o do portador |
| Condução | espaço livre num cone à frente |
| Drible | marcador à frente, sem dobra de marcação, fora da própria defesa |
| Proteger a bola | pressionado e sem opção segura; perto da lateral, pode terminar em lateral |

Passe para jogador em posição de impedimento no momento do passe é descartado; a posição é a do jogador, não a do ponto onde a bola chega. Devolver a bola a quem acabou de passar, sem ganho de terreno, é penalizado. Sob pressão dupla, recuar ou abrir para o lado ganha peso. Estilo de jogo (equilibrado, ataque total, contra-ataque) e foco de ataque (meio ou laterais) alteram os pesos.

**Sem a bola.**

- **Quem defende:**
  - a linha defensiva fica escalonada em torno de uma profundidade que acompanha a distância da bola ao gol, a marcação e o estilo;
  - meio e ataque se posicionam a partir dessa linha, com o bloco deslizando para o lado da bola;
  - o primeiro pressionador ataca pelo lado do próprio gol; o segundo dobra a marcação perto da lateral ou na própria defesa e, no resto do campo, fecha a linha de passe;
  - os demais marcam por zona, cada defensor com o atacante mais próximo, pelo lado do gol.
- **Quem ataca:**
  - os dois companheiros mais próximos oferecem apoio em ângulo, um atrás e um à frente na diagonal, do lado com menos adversários;
  - pontas abrem o campo, e a defesa sobe com a bola;
  - nenhum jogador fica além da linha de impedimento (penúltimo adversário ou bola, o que estiver mais adiantado, e só no campo de ataque), exceto o autor e os acompanhantes de um gol do jogo.
- **Goleiro:** cobre o ângulo e sai alguns metros quando a bola está longe.

**Contra-ataque.** Quando a posse muda no próprio campo, com poucos adversários entre a bola e o gol e espaço à frente, o time acelera por até 6 segundos: atacantes correm até a linha de impedimento e quem perdeu a bola corre de volta.

**Tabelas, dribles e perdas de bola.**

- A tabela só é devolvida se a linha de volta estiver aberta e o jogador que se desmarcou não estiver impedido.
- Os dribles são corte, arrancada, finta de corpo e giro de costas para o gol. Caneta, chapéu e carretilha são raros e dependem da geometria (marcador de frente e perto, marcador vindo em velocidade, ponta em velocidade no corredor).
- O drible pode falhar, e o marcador desarma.
- Quando a proporção de posse pede a troca, a bola é perdida para quem pressiona, num passe interceptado no meio da trajetória ou num passe forte ou fraco demais; o goleiro nunca perde a bola por desarme.

**Laterais e escanteios.**

- Surgem de afastamentos, de desarmes que terminam em chutão e de bolas perdidas perto da lateral.
- O cobrador vai até a bola (no escanteio, conduz até a bandeira), os companheiros se aproximam e o adversário se organiza na área; no escanteio, o cruzamento termina em corte ou na mão do goleiro.
- Só começam com o jogo corrido livre: nenhum lance do jogo na fila nem iminente, nenhuma antecipação de minuto, nenhuma falta, gol ou pênalti em curso.
- Lateral exige 700 ms ou mais por minuto e escanteio 1200 ms ou mais, exceto o lateral usado para parar o jogo numa substituição pendente.
- Um lance do jogo que chegue durante a cobrança a interrompe na hora; a bola fica onde está, com quem estiver em contato com ela.

**Velocidades.** A tela de partida usa os intervalos de `best/aq.rz` (2000, 1200, 700, 450, 220 e 100 ms por minuto), os de `best/aq.rA` (1200, 700, 300, 100, 70 e 30 ms) e 1 ms no modo instantâneo. Jogadores e bola sempre se movem no ritmo normal; nas velocidades rápidas, laterais e escanteios não são encenados.

### Simulação sem o jogo

[`tools/live_match_simulation.py`](../tools/live_match_simulation.py) roda o painel quadro a quadro sobre uma tela de partida falsa e mede o jogo corrido, cenários táticos e lances injetados:

```bash
python tools/live_match_simulation.py --output <saída.json>
python tools/live_match_simulation.py --ref <commit> --output <base.json>
python tools/live_match_simulation.py --events 12 --speeds 2000,1200,700,220,30 --output <lances.json>
python tools/live_match_simulation.py --audit 8 --output <regras.json>
python tools/live_match_simulation.py --ref <commit> --audit 8 --output <regras-base.json>
```

O modo `--audit` confere as regras da seção anterior com um observador próprio, que não usa o registro de toque do painel: lateral e escanteio para o time do último toque, desarme e perda de bola do goleiro, passe com destino adversário, bola parada sem ninguém indo até ela, apito sem contato, velocidade do portador no desarme, passe para trás atravessando o corpo, recuo de atacante livre, linha defensiva rígida, bola esperando o autor do gol, último toque e trajetória no gol contra, substituição com bola rolando e recusas do validador do painel. Roda jogo corrido com lances de estatística, gols, gols contra, cartões e substituições em todas as velocidades, mais cinco cenários dirigidos (lateral sob pressão, goleiro com a bola, atacante livre, desarme por trás e passe para trás).

O modo `--engine N` mede a sincronia com um Brasfoot falso que imita o laço de minutos do jogo: o passo do minuto, a exibição dos lances, a pausa, as telas de substituição (inclusive uma de 30 segundos) e o intervalo, com o minuto 0 do 2º tempo dentro do mesmo passo. O painel é compilado numa cópia instrumentada (relógio, telas abertas e `invokeLater` controlados pela simulação); o código do produto não tem ganchos de teste. Para cada lance compara o momento em que o jogo o exibe com o momento em que ele aparece no campo (bola na rede, cartão, ícone de lesão, falta do pênalti), em doze cenários: gol, dois gols, amarelo, lesão e pênalti no minuto 1, minuto 0 do 2º tempo, pausa durante gol e durante cartão, vermelho seguido de gols com tela longa, lesão no jogo, gol olímpico e gol contra.

```bash
python tools/live_match_simulation.py --engine 5 --speeds 2000,1200,700,450,300,220 --output <sincronia.json>
python tools/live_match_simulation.py --ref <commit> --engine 5 --speeds 2000,1200,700,450,300,220 --output <sincronia-base.json>
```

A simulação prova propriedades da apresentação (linhas de passe, impedimento, bola sempre ancorada, lances chegando ao clímax, regras acima, ordem entre animação e exibição). Ela não executa o motor do Brasfoot e não substitui partida real.

## Imagens

As imagens do site e da documentação são renderizadas pelo próprio código do painel, com elencos do patch, por [`tools/render_live_match_preview.py`](../tools/render_live_match_preview.py):

```bash
python tools/render_live_match_preview.py
python tools/render_live_match_preview.py --output <pasta> --scale 1 --condition 0
```

São geradas quatro imagens, uma para cada condição de gramado (excelente, muito boa, ruim e precária).

## Desenvolvimento

1. Altere os fontes em `tools/live-match-view-src/`.
2. Gere o executável com `patch_live_match_view.py` a partir de uma cópia do executável de origem em `data/private/`.
3. Gere o bundle de componentes com [`tools/build_component_bundle.py`](../tools/build_component_bundle.py) e o instalador com [`tools/build_distribution.py`](../tools/build_distribution.py) usando uma edição de prévia (`channel: local-preview`).
4. Distribua prévias apenas localmente até a release.

Ao mexer na movimentação ou nos eventos, preserve as regras de sincronização: transições de posse por contato, eventos durante paralisações enfileirados, lance exibido só no clímax, minuto liberado só pelo portão de sincronia e toda fase nova com condição de saída e prazo de segurança. Rode `--engine` e `--audit` antes de gerar uma prévia.
