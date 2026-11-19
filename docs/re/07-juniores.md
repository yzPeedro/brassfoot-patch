# 07 — Juniores: auditoria do sistema original

Base: vanilla `2fa65476…bb1c` decompilado (`data/private/re/src/`). Complementa `02-modelo-de-dados.md` §3.13–3.14 e `05-gestao-e-economia.md` (Base e juniores).

## Onde os juniores vivem

| Item | Onde | Observação |
|---|---|---|
| Lista do clube | `best.ah.ne` (`ky()`) | `ArrayList<F>`; sem limite na estrutura |
| Lista global | `c.a.SR.Q()` | todos os juniores da carreira |
| Marca de júnior | `F.fb` (`fC()`) | `Boolean` |
| Maturação | `F.fd` (`fE()`), `F.fe` | barra verde; sobe toda semana em `F.fY` |
| Idade | `F.em` | inteiro; o setter aceita 16–20 para júnior (senão 18) |
| Potencial | `F.es` (1–10) e exibido `fZ` | no `.ban` é o campo `hash` de `e.g` |
| Arquivo `.ban` | `e.t.m` (`getJuniores`) | `ArrayList<e.g>`; o limite de 15 é só do editor embutido (`d.ac`) |

## Geração (o que cria jovens fictícios)

| Origem | Método | Regra |
|---|---|---|
| Criação da carreira | `best.f.c(false)` | clubes de liga com reputação ≥ 3 e menos de 12 juniores ganham 6; os demais, com menos de 5, ganham 5 |
| Virada de temporada | `best.f.c(true)` | clubes com menos de 15 ganham 1 a 5; teto efetivo de 18 a 20 |
| Júnior de 20 anos | `best.F.gf()` | promove (potencial e vaga na posição, elenco < 32) e repõe um júnior se o clube tiver menos de 20; sem promoção, em clube da IA, **regera o mesmo objeto com nome e idade novos** |
| Aposentadoria (IA) | `best.F` (§3.14 de `02`) | gera um júnior de reposição e pode promovê-lo na hora |
| Falta de jogador na IA | `best.l` (linha 717 do decompilado) | cria um jogador por `F.a(...)` e promove na hora (`K.a`) |

Todas passam por `F.a(ah, int, F, int, String, Boolean)`: nome por `au(país)`, idade 16–19, posição e potencial sorteados.

## Limites de quantidade

| Limite | Onde | Efeito |
|---|---|---|
| 5/6 na criação, 15/18–20 na virada | `best.f.c` | gerador |
| 20 juniores | `best.F.gf` | reposição depois da promoção |
| "Vagas: n/20" e compra de júnior bloqueada com 20 | `a.ds` (`pK`, `<init>`, `pL`) | só interface; a tabela (`JTable` em `JScrollPane`) não limita linhas |
| Profissionais < 35 para promover na tela | `a.ds.pN` | regra do elenco profissional |
| Profissionais < 32 para promover na virada | `best.F.gf` | idem |
| 15 juniores | editor `d.ac` | não afeta o jogo |

## Promoção e evolução

- `best.K.a(boolean, F, ah)`: move o **mesmo objeto** `F` para o profissional, sem criar jogador. A força nasce do potencial e da maturação (`02` §3.13).
- `F.fY` (semanal, idade ≤ 20): maturação. Não depende de limite de quantidade.

## Plano de implementação (modo de juniores reais)

1. **Dados:**
   - catálogo Sub-20 por clube, com proveniência, em `data/private/youth-sources/`;
   - compilação dos atletas de 18 a 20 anos (idade exata pela data de nascimento na data de referência) para `e.t.m` dos `.ban`, por `WorldBuild` com o modo de juniores `replace`;
   - potencial estimado documentado, nunca 0.
2. **Motor (classe auxiliar e transformações localizadas, só com o marcador do componente instalado):**
   - `best.f.c`: não gera juniores;
   - `best.F.gf`: idade +1; aos 21 o júnior sai da base (promoção se houver vaga; senão fica sem clube). Não regera e não repõe;
   - reposição por aposentadoria: não gera júnior;
   - `a.ds`: sem teto de 20 na exibição e na compra.
3. **Sem campos novos nos saves:** o estado continua nos objetos existentes.
4. **Testes:** harness com carreira em cópia isolada. Conferências:
   - quantidade de juniores igual ao arquivo;
   - nenhum júnior gerado;
   - promoção e saída aos 21;
   - várias temporadas;
   - save e recarga.
