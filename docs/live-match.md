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
