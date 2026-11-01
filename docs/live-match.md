# Campo animado ao vivo

O campo animado desenha um campo 2D dentro da tela de partida original do Brasfoot, entre o placar e a tabela de outros jogos, com os 22 jogadores, a bola e o árbitro acompanhando os lances da partida assistida.

<p align="center"><img src="../site/assets/live/pitch-0.jpg" alt="Campo animado renderizado pelo código do painel" width="90%"></p>

## Princípio: o motor do Brasfoot não muda

- O motor de simulação, as regras, os sorteios e os resultados continuam sendo os do Brasfoot.
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

- **O relógio é do Brasfoot.** O painel não para, não reinicia e não adianta o temporizador da partida. A duração de cada minuto é sempre a da velocidade escolhida pelo jogador, e pausa e substituições acontecem no tempo original do jogo.
- **A animação se adapta à velocidade sem acelerar o movimento.** Jogadores e bola mantêm o ritmo natural até a velocidade Bem rápido. O que se ajusta são as decisões: esperas, pausas de bola parada e reinícios ficam mais curtos, e os gols saem de jogadas mais diretas, para que os lances caibam no tempo do minuto.

  | Velocidade do jogo | Intervalo por minuto | Comportamento do campo |
  |---|---|---|
  | Lento | 2000 ms | Jogadas completas; até 3 lances de estatística por minuto |
  | Normal | 1200 ms | Melhor experiência; até 2 lances de estatística por minuto |
  | Rápido | 700 ms | Jogadas mais diretas; 1 lance de estatística por minuto |
  | Bem rápido | 450 ms | Jogadas diretas, ainda fluidas e realistas |
  | Super rápido | 220 ms | Movimento levemente acelerado; jogadas podem ficar irreais; sem lances de estatística |
  | Ultra rápido | 100 ms | Movimento acelerado; jogadas irreais; sem lances de estatística |

  Em Rápido ou mais, cartões e lesões acumulados são aplicados direto no jogador (cartão ou saída de campo) para não atrasar o campo; gols são sempre encenados.
- **Troca de lado.** No segundo tempo os times invertem o campo de ataque.

## Garantias de execução

- **Nunca travar o jogo:** qualquer erro no quadro do painel zera as animações; cada fase tem prazo máximo e o painel nunca segura a partida.
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
