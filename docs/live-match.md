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
| Passo do minuto | A chamada ao passo de simulação do minuto passa por `LiveMatchPanel.engineStep`. O painel executa o mesmo método do jogo um minuto antes, uma única vez, para conhecer os lances antes de exibi-los; quando o temporizador do jogo chega ao minuto, o passo já executado é pulado |
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
- **Pausa curta nos lances do jogo.** O painel conhece os lances com um minuto de antecedência. Quando o próximo minuto tem gol, pênalti, cartão ou lesão, o painel segura o relógio da partida enquanto a jogada acontece no campo e só deixa o minuto virar no clímax (bola na rede, apito, falta no pênalti). Assim, placar e campo mudam juntos.
- **Depois do gol.** O relógio continua parado enquanto os jogadores voltam às posições e dão a saída de bola. No início de cada tempo vale o mesmo para a entrada em campo.
- **O minuto nunca fica mais curto.** Ao soltar o relógio, o painel executa o próprio passo de minuto do Brasfoot, nunca antes do horário em que o jogo o executaria. Fora dessas pausas, a partida corre na velocidade escolhida pelo jogador, e substituições e lances de estatística não pausam o jogo.
- **Quanto tempo a mais.** Cerca de 3 a 8 segundos por gol (jogada e saída de bola) e até 2,5 segundos por cartão; numa partida típica, de 15 a 30 segundos a mais. A proporção pesa mais nas velocidades rápidas, em que a partida inteira dura menos.

| Velocidade do jogo | Intervalo por minuto | Lances de estatística encenados |
|---|---|---|
| Lento | 2000 ms | até 2 por minuto |
| Normal | 1200 ms | 1 por minuto; experiência ideal |
| Rápido, Bem rápido, Super rápido, Ultra rápido | 700 a 100 ms | não encenados; gols com jogadas mais curtas |

- **Troca de lado.** No segundo tempo os times invertem o campo de ataque.

## Garantias de execução

- **Nunca travar o jogo:** qualquer erro no quadro do painel zera as animações e devolve o relógio ao Brasfoot; cada fase tem prazo máximo, e uma pausa de lance dura no máximo 9 segundos (14 segundos na jogada de um gol).
- **Nenhum gol perdido:** lances do jogo ficam na fila durante paralisações, na virada de tempo e depois de uma proteção contra travamento; a antecipação do minuto só acontece depois que o painel registra a troca de tempo; um gol pendente do 1º tempo é mostrado antes da entrada para o 2º tempo, e um gol interrompido é refeito uma vez.
- **Faltas no lugar certo:** faltas comuns e com cartão nunca são marcadas dentro da área de quem comete; a falta que gera pênalti é marcada dentro da área.
- **Diálogos e pausa:** com diálogos do jogo abertos o painel não segura o relógio, e um pedido de pausa ou substituição libera o relógio na hora.
- **Bola sempre ancorada:** a posse só muda por contato (passe, domínio, desarme ou cobrança), e cada fase termina em um estado explícito.
- **Diagnóstico:** eventos de integração são registrados em `%LOCALAPPDATA%\BrassfootPatch2026\live-match-debug.log`.

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
  - a linha defensiva fica alinhada, numa profundidade que acompanha a distância da bola ao gol, a marcação e o estilo;
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
- Quando a proporção de posse pede a troca, a bola é perdida para quem pressiona ou num passe interceptado pelo adversário mais próximo da linha.

**Laterais e escanteios.**

- Surgem de afastamentos, de desarmes que terminam em chutão e de bolas perdidas perto da lateral.
- O cobrador vai até a bola (no escanteio, conduz até a bandeira), os companheiros se aproximam e o adversário se organiza na área; no escanteio, o cruzamento termina em corte ou na mão do goleiro.
- Só começam com o jogo corrido livre: nenhum lance do jogo na fila nem iminente, nenhuma antecipação de minuto, nenhuma falta, gol ou pênalti em curso.
- Lateral exige 700 ms ou mais por minuto e escanteio 1200 ms ou mais.
- Um lance do jogo que chegue durante a cobrança a interrompe na hora; a bola fica onde está, com quem estiver em contato com ela.

**Velocidades.** A tela de partida usa os intervalos de `best/aq.rz` (2000, 1200, 700, 450, 220 e 100 ms por minuto), os de `best/aq.rA` (1200, 700, 300, 100, 70 e 30 ms) e 1 ms no modo instantâneo. Jogadores e bola sempre se movem no ritmo normal; nas velocidades rápidas, laterais e escanteios não são encenados.

### Simulação sem o jogo

[`tools/live_match_simulation.py`](../tools/live_match_simulation.py) roda o painel quadro a quadro sobre uma tela de partida falsa e mede o jogo corrido, cenários táticos e lances injetados:

```bash
python tools/live_match_simulation.py --output <saída.json>
python tools/live_match_simulation.py --ref <commit> --output <base.json>
python tools/live_match_simulation.py --events 12 --speeds 2000,1200,700,220,30 --output <lances.json>
```

A simulação prova propriedades da apresentação (linhas de passe, impedimento, bola sempre ancorada, lances chegando ao clímax). Ela não executa o motor do Brasfoot e não substitui partida real.

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

Ao mexer na movimentação ou nos eventos, preserve as regras de sincronização: transições de posse por contato, eventos durante paralisações enfileirados, placar do painel atualizado somente quando a bola entra e toda fase nova com condição de saída e prazo de segurança.
