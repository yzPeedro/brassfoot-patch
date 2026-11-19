# Competições brasileiras 2026

Parte do componente **Elencos + Competições 2026**. Altera o motor de competições do Brasfoot 22-23 por transformação de bytecode, com autorização do proprietário registrada no `AGENTS.md`. Nenhum campo de classe serializada é criado ou alterado, e o motor de partidas não muda.

## O que é implementado

| Competição | Formato oficial 2026 | No jogo |
|---|---|---|
| Série A | 20 clubes, 38 rodadas | composição oficial na carreira iniciada em 2026 |
| Série B | 20 clubes; 1º e 2º sobem; 3º x 6º e 4º x 5º em ida e volta, volta na casa do melhor, empate no agregado classifica o melhor colocado (sem pênaltis) | igual |
| Série C | 20 clubes em turno único; 8 melhores em dois quadrangulares; 4 sobem; 2 caem | igual; em 2027 tem 24 clubes e, a partir de 2028, 28, com 6 rebaixados |
| Série D | 96 clubes em 16 grupos de 6; 4 por grupo; mata-mata em ida e volta com chaveamento do Anexo B; quartas reordenadas pela campanha; 4 eliminados nas quartas em 2 playoffs (1º x 4º e 2º x 3º); 6 acessos; 610 jogos | igual |
| Copa do Brasil | 126 clubes; 9 fases; fases 1–4 e final em jogo único; 5ª a 8ª em ida e volta; 155 jogos | igual |

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

## Lacunas conhecidas

- **Clubes ausentes:** 37 clubes oficiais da Série D e 34 da Copa do Brasil (a maioria são os mesmos) não existem no jogo. As vagas são preenchidas por clubes do mesmo estado até os elencos reais serem criados.
- **Desempate na fase de grupos da Série D:** o jogo ordena por pontos, vitórias, saldo e gols pró. Confronto direto, cartões e sorteio não são aplicados.
- **Sorteios da Copa do Brasil:**
  - a 1ª fase segue o RNC (1º x 28º);
  - a 5ª fase é Bloco I x Bloco II pelo RNC;
  - as demais fases são sorteadas.
  - O sorteio real de 2026 e os mandos do Anexo B não são reproduzidos.
- **RNC e RNF:** ficam fixos nos valores de 2026 em todas as temporadas da carreira. O critério 3 da Série D (5º a 32º da Série D anterior) não é aplicado nas temporadas seguintes.
- **Formato da Série C de 2027 e 2028:** não há regulamento publicado. A carreira mantém o formato de 2026 com mais clubes.
- **Calendário:** as datas seguem os tipos de data do jogo, não a tabela oficial.
- **Interface:**
  - enquanto os playoffs da Série D existem, a tela principal da divisão mostra os playoffs;
  - o nome da rodada dos playoffs vem da tabela genérica do jogo.
