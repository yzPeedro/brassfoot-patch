# Brasfoot 22-23 — interface: telas, navegação, componentes, opções e atalhos

**Resumo.** A interface é Swing puro, com uma única janela (`JFrame` sem bordas e maximizado) criada por `best.S`, cujo conteúdo é trocado inteiro por `best.S.aY(código)` entre poucas telas de página cheia (configuração inicial, técnicos, tela do clube, partida, fim de rodada, fim de temporada, leilão, torneio amistoso). Todo o resto (cerca de 70 telas) são painéis do pacote `a` colocados em `JDialog` modais, sem moldura, centralizados e abertos diretamente por quem precisa deles, sem pilha de navegação. A tela do clube (`a.eg`) é o centro do jogo: botões de barra com menus suspensos, teclas de função F2–F11 e o botão "Escalar Time", que leva à escalação (`a.bz`) e, por "Jogar >>", ao avanço do calendário (`best.f.ap`). As opções ficam em `est.Options`, gravadas em `options.bcf` e espelhadas na carreira atual (`c.a.SR`); sons são sete `.wav` opcionais em `sons/`. Quase todos os textos estão fixos no código em português; `arquivos/default_lang.xml` traz apenas nomes de países, competições e textos do registro.

Fonte: decompilação Vineflower 1.11.1 do executável original (SHA-256 `2fa65476…bb1c`), em `data/private/re/src/`. Os arquivos decompilados têm `_` antes de cada maiúscula (`a/d_V.java` = `a.dV`); este documento usa os nomes originais. Os *listeners* são classes de topo separadas (por exemplo `a.eh`…`a.fv` para `a.eg`) e chamam a tela por acessores sintéticos (`eg.a(eg)`, `eg.h(eg)`) que o Vineflower não mostra; esses acessores foram resolvidos com `javap -c -p` sobre as classes do jar, o que vale para `a.gq`, `a.eg`, `a.dV`, `a.hk`, `a.cR`, `a.bV` e os diálogos citados com teclas. O que não foi lido diretamente vem marcado como **(inferido)**. Nada foi executado no jogo.

Documentos relacionados: [01 — arquitetura e arquivos](01-arquitetura-e-arquivos.md), [03 — motor de partida](03-motor-de-partida.md), [05 — gestão e economia](05-gestao-e-economia.md) e [campo animado](../live-match.md).

---

## 1. Pacotes de interface

| Pacote | Classes | Papel na interface | Origem |
|---|---:|---|---|
| `a` | 565 | 80 subclasses de `JPanel`/`JFrame` (as telas) e seus *listeners* (398 `ActionListener`, 64 `MouseAdapter`, 36 `AbstractAction`, 17 `ListSelectionListener`) | cabeçalhos de classe em `a/*.java` |
| `components` | 85 | Peças reutilizáveis: layout absoluto, fundo da janela, grade tática, marcadores de jogador, painéis de tabela e chave, filtros, formatação de dinheiro, tratador de exceções; também algumas classes `Serializable` que entram no save | seção 11 |
| `b` | 101 | Modelos de tabela (`AbstractTableModel`) e renderizadores de célula (`DefaultTableCellRenderer`) usados pelas telas | por exemplo `b.Q` (elenco), `b.M` (jogos da rodada), `b.aH`, `b.aG` |
| `h` | 42 | Somente comparadores (`Comparator`) para ordenar listas, expostos como campos estáticos de `h.a` (`h.a.abe`, `h.a.abg` etc.) | `h/a.java` |
| `d` | 82 | Editor de times separado (`d.n`, "Editor Brasfoot") e seus diálogos | seção 5.14 |
| `forms` | 26 | Não são telas do jogo: `forms.h` é um lançador de testes ("Passa Dia", "Torneio Teste") usado só por `best.h.main`; `forms.Randoms`, `forms.x`, `forms.u`, `forms.f` são distribuições e métodos numéricos usados pela simulação | `best/h.java`, `best/af.java`, `best/aq.java` |

Os nomes `components.a` e `components.b` são, respectivamente, as **restrições** (`x`, `y`, `width`, `height`) e o **gerenciador de layout absoluto** (`LayoutManager2`), equivalentes ao `AbsoluteConstraints`/`AbsoluteLayout` do NetBeans. A hipótese inicial de que `components.a` era o layout está corrigida: o layout é `components.b` (`components/a.java`, `components/b.java`, uso em `a.gq.mJ`). Muitas telas usam `GroupLayout` gerado pelo NetBeans (`a.dV`, `a.dN`), o que explica os textos de exemplo que aparecem nos fontes ("Red Bull Bragantino", "Moisés Lucarelli", "jLabel2").

## 2. Arranque e janela principal

1. `best.h2.main` (classe principal do manifesto) instala `components.ar` como tratador global de exceções, aplica o *look and feel* Nimbus, verifica o registro (mecanismo fora do escopo), carrega os textos (`new best.M(true)`), monta a lista de países (`best.n.cU`) e abre a **tela inicial** `a.gq` (532 × 300). Em seguida pré-carrega os sons (`c.a.vH`). `best.h.main` é um segundo ponto de entrada, com *look and feel* Metal e o lançador de testes `forms.h`.
2. A tela inicial `a.gq` é um `JFrame` sem bordas cujo fundo é a imagem `aiconsj/tela_inicial.jpg`; as "opções" são rótulos invisíveis posicionados sobre a imagem (`a.gq.mJ`). Os cliques foram resolvidos pelos acessores sintéticos:

| Rótulo (posição) | Listener | Método | Efeito |
|---|---|---|---|
| `aft` (30, 110) | `a.gr` | `gq.mi` | Novo jogo: cria `c.a` (nova carreira), `best.p.dd`, troca o *look and feel* para Metal e cria a janela principal (`new best.S(true)`) com a configuração inicial `a.hU`, ou chama `S.aY(0)` se ela já existe |
| `afx` (210, 110) | `a.gu` | `gq.pW` | Carregar jogo: `best.S.cX` abre `a.dN` |
| `afs` (370, 110) | `a.gs` | `gq.rN` | Editor: `best.n.cV` e `best.n.cW` abrem `d.n` e escondem a tela inicial |
| `afu` "REGISTRAR JOGO" | `a.gt` | `gq.rP` | Tela de registro (`S.aY(7)`, `a.da`); oculta quando o jogo já está registrado |
| `afw` (420, 260) | `a.gv` | — | `System.exit(0)` |

3. `best.S` (construtor) cria o `JFrame` estático `S.cC`, título "Brasfoot", ícone `aicons/ball.png`, **sem decoração e maximizado** dentro da área útil da tela. Se a área útil tiver largura ≤ 1020 ou altura ≤ 700, liga `S.gJ` e passa a envolver todo o conteúdo num `JScrollPane` (`S.aZ`, `S.iI`). O conteúdo é sempre um `components.E` com `BorderLayout` e fundo verde (36, 91, 45); `components.E` pinta `img/f01.jpg` da pasta do jogo a cada repintura (modo 0).

## 3. Navegação

### 3.1 Troca de tela cheia: `best.S.aY(int)`

`aY` descarta o conteúdo da janela, cria uma nova instância da tela e a coloca no centro (`S.aZ`); não há pilha nem "voltar" genérico. Para 1, 2 e 5 chama `on()` da tela para dar foco à tabela principal.

| Código | Tela | Tamanho preferido | Quem chama |
|---|---|---|---|
| 0 | `a.hU` Configurações iniciais | — | `a.gq.mi` |
| 1 | `a.bV` Técnicos humanos | — | `a.hU.oq` ("Iniciar Jogo >>") |
| 2 | `a.eg` Tela do clube | tela inteira | `best.f.ap` |
| 3 | `a.hU` (igual a 0) | — | sem chamador encontrado |
| 4 | `a.dV` Partida | 1024 × altura útil | `best.s.dx` (só se `SR.bs`, ver 3.3) |
| 5 | `a.hk` Fim de rodada | 1024 × 748 | `best.f.at` |
| 6 | `a.cR` Fim da temporada | 1024 × 718 | `best.f` (≈ linha 1525, ao fim do ano) |
| 7 | `a.da` Registro | 941 × 718 | `a.gq.rP`, `forms.s` |
| 8 | `a.dz` Leilão de jogadores | 941 × 718 | `a.hk.nx` (quando há leilão) |
| 10 | `a.jH` Torneio amistoso | 742 × 577 | `a.bV`, `a.cR`, `best.f.iX` |

`aY(4)` devolve a instância de `a.dV` (guardada por `best.s` em `cR`) e `aY(5)` a de `a.hk`; os demais devolvem `null`.

### 3.2 Diálogos

O padrão, repetido em `best.S` e nas telas, é: `new JDialog(S.cC)`, `add(painel)`, tamanho fixo, `setModal(true)`, `setResizable(false)`, `setLocationRelativeTo(null)`, `setUndecorated(true)`, `setVisible(true)`. Por ser modal, a chamada bloqueia até o painel fechar o próprio diálogo (cada painel recebe o `JDialog` no construtor e chama `dispose`). Depois do retorno, a tela chamadora costuma reler o modelo (por exemplo `a.eg.qI`/`qJ`/`qH`, que refazem a tabela do elenco).

`best.S` concentra os diálogos abertos de vários lugares:

| Método | Tela | Tamanho | Chamadores |
|---|---|---|---|
| `S.a(ah, at, int)` | `a.dJ` "É campeão!" | 306 × 413 | `best.i` (≈ l. 63) |
| `S.a(ArrayList, al, int)` | `a.gO` Convites para ser técnico | 774 × 724 | `a.eg.AI`, `best.a` |
| `S.l(al)` | `a.gE` Central de Empregos | — | `a.eg.AI` |
| `S.K(ArrayList)` | `a.bl` Demissões na Rodada | — | `best.f` (≈ l. 1620) |
| `S.a(al, al, ah, int)` | `a.dm` Demitido! | — | `a.eg.rr`/`rs`, `a.hk.rr`, `best.ay`, `best.f`, `f.s` |
| `S.cX()` | `a.dN` Carregar jogo salvo | — | `a.gq.pW`, `a.eg.rd`, `best.n.cX` |
| `S.a(String, boolean)` | `a.hz` Salvando/Carregando | — | `a.eg.ru` |
| `S.iG()` | `a.hF` (depuração) | — | sem chamador |
| `S.a(ah, boolean)` | `a.aP` Convocação da seleção | — | `a.eg.rc`, `best.a` |
| `S.a(F, JDialog)` | `a.dk` Histórico do jogador | — | `a.eg.qC`, `components.H`, `a.iH` |
| `S.v(ah)` | `a.di` Galeria de Troféus | 886 × 219–762 | `a.eg.rw`, `a.hc`, `a.iA`, `a.jv` |
| `S.a(int, at)` | `a.ay` Tabelas | 833 × 735 | `a.eg.qV`, `a.hk.qV`, `a.gE`, `a.gO` |
| `S.b(int, at)` | `a.al` Classificação e jogos | 883 × ≤ 800 | sem chamador |
| `S.e(al)` | `a.dg` Troféus do técnico | 971 × 646 | `a.eg.rx`, `a.gX` |
| `S.a(f.B, Z, int)` | `a.iu` Time da Rodada / do Ano | 372 × 657 | `a.eg.do`, `a.hk` (via `a.hm`), `a.cR.pm` |
| `S.a(JTable)` | `a.fB` Opções | 867 × 620 | `a.eg.rv`, `a.eZ` (F3), `a.hU.rv`, `a.hv` |
| `S.w(ah)` | `a.h` Marcar amistoso (clube) | 565 × 575 | `a.eg.re`, `a.cR` |
| `S.x(ah)` | `a.d` Marcar amistosos (seleção) | 565 × 575 | `a.eg.rf`, `a.cR` |
| `S.a(ah, ah, boolean)` | `a.iA` Informações do time | 1024 × 718 (1200 × 740 em telas grandes) | `a.eg.G`, `a.gx` |

### 3.3 Ciclo de jogo visto pela interface

Pseudocódigo do caminho normal com um técnico humano (os métodos de `best.f` e `best.s` são de outro domínio; a descrição deles aqui é **(inferido)** pelo que chamam):

```
gq (tela inicial) -> hU (configuração) -> bV (técnicos humanos) -> [jH torneio amistoso] -> f.ap
f.ap: se há decisão do humano no dia -> S.aY(2) tela do clube (eg)
eg "Escalar Time" -> bz (escalação) -> "Jogar >>" -> bz.oi grava escalação -> SR.ap
f.ap (dia de jogo): best.s.dx -> S.aY(4) partida (dV)
dV ao fim de todos os jogos -> best.s.dJ -> f.at -> S.aY(5) fim de rodada (hk)
hk "Continuar >>" -> [S.aY(8) leilão dz] -> SR.ax -> ... -> S.aY(2) eg
fim do ano -> S.aY(6) fim da temporada (cR) -> "Iniciar novo ano >>" -> f.V ...
```

`a.bz.oi` copia as casas 1–25 da grade para titulares e jogadores em campo da partida (`best.I.hl`/`hp` para o mandante, `hm`/`hq` para o visitante) e as casas 26–36 para o banco (`hn`/`ho`), salva automaticamente se `getAutoSalvar() > 0` (`S.iF().rt()`), fecha o diálogo e chama `c.a.SR.ap()`.

## 4. Tela do clube (`a.eg`)

Criada por `S.aY(2)`; lê `best.f.B()` (time do humano da vez, campo `zu`), `best.f.bl()` (próxima partida, campo `bv`) e o adversário (`bv.hc()`/`hd()`, campo `Hv`). Mostra nome do técnico, data, confiança da diretoria e da torcida (barras), dinheiro em caixa, colocação, próximo jogo, contador de mensagens, o cartão do jogador selecionado (`components.m`: contrato, empréstimo, contusão, suspensão) e a tabela do elenco (`Iy`, modelo `b.Q` com as colunas "P", "Nome", "L", "F", "Energia", "Salário", "Passe", "G", "Car.", "Idade", "GC", "A", "NM"; renderizador `b.aH`; seleção amarela). Quando o humano dirige uma seleção (`yp`), várias ações passam a usar a seleção (`zu.ka().jo()` ou `fg()`). Não há barra de menus: os botões da barra superior abrem `JPopupMenu`.

### 4.1 Botões e rótulos clicáveis

| Controle | Listener → método | Abre |
|---|---|---|
| "Escalar Time" (`HU`) | `a.eC` → `qZ` | `a.bz` Escalação, 1024 × 748 |
| "Agenda" (`HR`) | `a.ex` | menu `Hx` |
| "Seleção" (`afl`, visível só com seleção) | `a.ey` | menu `afi` |
| "Técnicos" (`Ia`) | `a.ez` | menu `Hz` |
| "História" (`HZ`) | `a.eA` | menu `HA` |
| "Opções" (`HX`) | `a.ew` | menu `Hy` |
| "Tabelas" (`HS`) | `a.eG` → `qV` | `S.a(tR, bv.hy())` → `a.ay` |
| "Estádio" (`HV`) | `a.eB` → `ra` | `a.cl` (estádio), que abre `a.cq` (expansão) |
| "Juniores" (`HW`) | `a.eE` → `qY` | `a.ds` Academia de Juniores |
| "Times" (`Ib`) | `a.eF` → `G(null)` | `a.iA` do próprio time (ou da seleção) |
| "Treino" (`Id`) | `a.eI` → `qU` | `a.iQ` Treino |
| "Procura" (`yY`) | `a.eH` → `dn(1 ou 2)` | `a.gx` busca de jogadores (modo 2, maior, com `isHabilidadeIndividual`) |
| Ícone "Cores da tela" (`HT`) | `a.eP` → `qQ` | `a.bb` Cores do Time |
| Ícone "Galeria de troféus" (`Ie`) | `a.eQ` → `rw` | `S.v` → `a.di` |
| Ícone "Retrospecto do time" (`HY`) | `a.eR` → `qP` | `a.hw` |
| Ícone "Jogadores emprestados" (`Ic`) | `a.eS` → `qO` | `a.bs` |
| Dinheiro (`Iw`) | `a.eJ` → `qT` | `a.cW` Finanças |
| Mensagens (`ze`) | `a.eK` → `rm` | `a.bn` Central de Mensagens (lista `zu.ka().lQ()`) |
| `zb` | `a.eL` → `rh` | `a.aL` histórico de confrontos com o próximo adversário |
| Nomes dos times (`vw`, `yt`) | `a.eM`/`a.eN` → `G(Hv)` | `a.iA` do próximo adversário |
| Tabela do elenco | `a.em` → `qC` | `S.a(F, null)` → `a.dk` Histórico do jogador |

`a.js` (em "Agenda") e `a.jt` (em "Escalar Time") são *listeners* vazios gerados pelo editor visual.

### 4.2 Menus suspensos

| Menu (botão) | Itens (texto → método → tela) | Origem |
|---|---|---|
| `Hx` (Agenda) | "Jogos do seu time" [F4] → `ad(false)` → `a.L` Calendário; "Jogos Amistosos" [F9] → `re` → `S.w` → `a.h`; "Central de Empregos" → `AI` → `S.l` → `a.gE` (desabilitado quando já recebeu convites) | `a.eg.AL` |
| `afi` (Seleção) | "Jogos Amistosos Seleção" → `rf` → `S.x` → `a.d`; "Calendário da seleção" → `ad(true)` → `a.L`; "Convocar Seleção" → `rc` → `S.a(ah,false)` → `a.aP`; "Pedir demissão da seleção" → `rs` (confirmação e `S.a(al,al,ah,0)` → `a.dm`) | `a.eg.AM` |
| `Hy` (Opções) | "Salvar jogo" [F2] → `ru`; "Preferências" [F3] → `rv` → `a.fB`; "Pedir demissão" → `rr`; "Sair do jogo" → `rq` (`System.exit`); "Sobre o Brasfoot" → `rp` → `a.jp` | `a.eg.rb` |
| `Hz` (Técnicos) | "Ranking de técnicos" → `ro` → `a.gX`; "Adicionar/remover técnicos" → `rn` → `a.ip`; "Últimas trocas de técnicos" → `dp(0)` → `a.hC`; "Troféus do Técnico" → `rx` → `S.e` → `a.dg` | `a.eg.rb` |
| `HA` (História) | "Campeões" [F10] → `rl` → `a.R`; "Ranking Clubes" → `ri` → `a.hc`; "Ranking Seleções" (só com seleções ligadas) → `AN` → `a.jv`; "Artilheiros" [F11] → `rk` → `a.o`; "Líderes de Assistências" → `rj` → `a.y`; "Galeria de Troféus" → `rw` → `a.di`; "Time da Rodada" → `do(0)` → `a.iu`; "Time do Ano" → `do(1)` → `a.iu`; "Bola de Ouro" → `rg` → `a.H`; "Transferências de Jogadores" → `dp(1)` → `a.hC`; "Histórico de confrontos" → `rh` → `a.aL`. Os itens de galeria, time da rodada/ano, bola de ouro e transferências somem no modo seleção (`yp`) | `a.eg.rb` |
| `HB` (botão direito no elenco) | "Propor contrato" → `qS` → `a.fy`; "Vender Jogador" → `qX` → `a.jc`; "Aposentar Jogador" → `qW` → `a.ji`; "Escolher número" → `qM` → `a.ce`; "Histórico do jogador" → `qC` → `a.dk`; "Cancelar empréstimo" → `qG`; "Comprar jogador" → `qF` (confirmação; compra jogador emprestado); "Pôr/Não pôr para empréstimo" → `qE` (limite de 10 emprestáveis) | `a.eg.qD` |

"Salvar jogo" (`ru`): se a carreira ainda não tem nome (`SR.br() == null`), abre `a.fw` para escolher o nome; depois abre `a.hz` ("Salvando jogo… isso pode demorar um pouco…"), cuja *thread* `a.hB` chama `c.a.ae(nome)` e fecha. "Pedir demissão" (`rr`) confirma, pede um substituto (`zu.kE()`; sem ele, "A diretoria ainda não achou um técnico a sua altura…") e abre `a.dm`.

### 4.3 Propostas espontâneas

`a.eg.ac(boolean)` sorteia um jogador do elenco e abre `a.jm` ("Proposta de empréstimo" ou "Oferta de compra", com "Aceitar/Vender" e "Recusar proposta"). É chamado por `best.f` com sorteios (`nextInt(100) == 1`, `nextInt(2) == 1`) **(inferido: frequência real depende do contexto em `best.f`)**.

## 5. Mapa de telas por assunto

### 5.1 Início e nova carreira

| Classe | Tela | Aberta por | Conteúdo e ações |
|---|---|---|---|
| `a.gq` | Tela inicial | `best.h2.main`, `a.hU.sp` ("<< Voltar ao início"), `a.da.pb` | Seção 2 |
| `a.hU` | Configurações iniciais | `S.aY(0)` | Ligas nacionais (tabela de países, "configurar" → `a.cw`), estaduais ("configurar" → `a.dG`), regionais ("configurar" → `a.fZ`), botão de marcar todas as ligas (`Mf`, ícone `iconsellall`, → `best.f.bi`), "Competições internacionais" (seleções, taças de clubes, "Usar grupos da Copa do Mundo 2022"), botão "Preferências" (`a.ih` → `hU.rv` → `S.a(null)` → `a.fB`), "<< Voltar ao início" (`a.jG` → `sp`: reabre `a.gq` e esconde a janela), sistema de salários (Mensal/Semanal), força dos jogadores (Modo clássico/Individual), temporada de início (2022/2023). "Iniciar Jogo >>" (`oq`) grava no `SR` (`I(ano)`, `setJogaEstadual`, `setJogaIntClubes`, `setJogaSelecoesAll`), guarda o ano em preferências (`aq.f("anoinicio", …)`) e vai para `S.aY(1)`; sem liga escolhida: "Selecione pelo menos uma liga" |
| `a.cw` | Configurar Ligas – país (até 4 divisões) | `a.hU.ss` | Times por divisão, "Salvar", "Resetar tudo", "Usar grupos reais se possível"; sistema de mata-mata em `a.cu` (quartas, semifinal, final em 1 ou 2 jogos, pênaltis) |
| `a.dG` / `a.dK` | Configurar estaduais | `a.hU.st` / `a.dG` | Formato por divisão: grupos, turnos, mata-mata, sobem/descem, playoff, "Usar novo formato na Copa BRA" |
| `a.do` | Preferências de competições internacionais | só `a.hU.AS`, que nenhum *listener* chama (seção 5.13) | Grupos reais, primeira temporada, "Sem times humanos ver jogos" por competição (Libertadores, Liga dos Campeões etc.; lê `SR.getVerJint`) |
| `a.fZ` | Regionais | `a.hU.sr` | Rio-São Paulo, Sul-Minas, Copa do Nordeste, Copa Verde; "Sempre ser convidado…" |
| `a.bV` | Técnicos humanos | `S.aY(1)` | Nome, nacionalidade, país, time por divisão ou "Escolher um time aleatório"; "Adicionar e incluir outro" (só registrado: "Somente na versão registrada é possível jogar com mais de um técnico humano"); "Iniciar Jogo >>" (`a.cc` → `oq`) pergunta pelo torneio amistoso (`S.aY(10)`) ou começa a temporada (`f.az`, `f.V`) |
| `a.jH` | Torneio Amistoso | `S.aY(10)` | Nome, sede, participantes, fórmula (2 grupos de 4 + semi e final; 1 grupo de 4 + final; 1 grupo de 6), "Sortear grupos", "Iniciar", "Cancelar torneio" |
| `a.da` | Registro | `S.aY(7)` | Lista de vantagens da versão registrada, nome e código, link ao site. Textos vêm de `default_lang.xml` (`fix_*`). O esquema de licença fica fora do escopo deste documento |
| `a.jp` | Sobre | `a.eg.rp` | Créditos e estado do registro |

### 5.2 Salvar e carregar

| Classe | Tela | Detalhes |
|---|---|---|
| `a.dN` | Carregar Jogo Salvo | Lista `sav/*.s22` (filtro `a.dS`); ao selecionar, mostra técnico e próximo jogo lidos do `.info` (`c.a.af`). "Carregar" agenda um `Timer` de 10 ms (`a.dR`) que chama `c.a.c(nome, false)`; ao terminar a leitura, `c.a.c` cria a janela (`new S(false)`) e chama `SR.ap()`. "Deletar" pede confirmação ("Deseja excluir o arquivo?") e apaga o `.s22`. Ícones `loadt`, `home`, `icondel` |
| `a.fw` | Nome do save | "Escolha um nome de arquivo para salvar o jogo:"; valida nome, avisa se já existe |
| `a.hz` | Progresso | "Salvando jogo…" ou "Carregando…"; Esc mapeado (`a.hA`) |

### 5.3 Elenco e jogador

| Classe | Tela | Aberta por | Ações principais |
|---|---|---|---|
| `a.dk` | Histórico do jogador | `S.a(F, JDialog)` | Jogos na temporada e histórico da carreira (`components.x`) |
| `a.fy` | Novo contrato | `a.eg.qS` | Duração (6 meses a 3 anos), salário; recusa com salário pedido |
| `a.jc` | Vender jogador | `a.eg.qX` | Leilão (preço inicial) ou preço fixo; mostra multa rescisória; o leilão do próprio jogador segue em `a.iX` (aberto por `components.an.vb`) |
| `a.ji` | Aposentar jogador | `a.eg.qW` | Nome do substituto (ou automático) e posição; vai para os juniores ou para o time principal |
| `a.ce` | Numeração do elenco | `a.eg.qM` | Número de 1 a 99, escolha automática, limpar |
| `a.bs` | Jogadores emprestados | `a.eg.qO` | Emprestados a outros times e recebidos (linhas `components.H`; limite 10, vagas 4) |
| `a.cz` | Proposta de compra | `a.ds.pL`, `a.iA.sA` | Valor do passe, salário pedido, envio |
| `a.jm` | Proposta recebida | `a.eg.ac` | Aceitar/vender ou recusar |
| `a.l` | Apelido de júnior | `a.ds.pP` | Define apelido |

### 5.4 Escalação e tática

`a.bz` (aberta por `a.eg.qZ`; recebe time, partida `best.f.bl()` e modo seleção) desenha o campo com 36 casas (`components.ao`), arrasta jogadores entre "Jogadores disponíveis", campo e "Banco de reservas", e oferece estilo de jogo, marcação, "Concentrar ataques", "Seleção Automática", "escalação padrão", "táticas salvas" (→ `a.il`, que guarda `components.ag` por nome), "ver juniores", adversário e "Condição do gramado". Menu de contexto do jogador: "Batedor de faltas", "Capitão", "Batedor de escanteios" e "Falso 9" (só casas ≥ 14, exceto 17). "Jogar >>" (`a.bC` → `oh`/`oi`, também Espaço) valida 11 jogadores ("Selecione 11 jogadores") e avança o jogo; "<< Voltar ao time" fecha.

Grade tática (`components.ao.RJ`, canto superior esquerdo de cada casa de 60 × 60 px; o campo é desenhado na vertical, com o próprio gol embaixo):

| Casas | Linha | y (px) |
|---|---|---|
| 1 | Goleiro | 565 |
| 2–9 | Defesa (2 e 9 nas pontas, mais altas) | 405–485 |
| 10–17 | Meio (10 e 17 nas pontas) | 205–315 |
| 18–25 | Ataque (18 e 25 nas pontas) | 30–115 |
| 26–36 | Banco, em duas linhas à direita do campo | 30 e 105 (x 470–950) |

`components.ao.S(x, y)` devolve a casa sob o ponteiro; `V(x, y)` testa se o ponto está no campo ou no banco. Os marcadores de jogador são `components.K` (escalação), `components.M` (substituição na partida) e `components.L`, `JLayeredPane` com camisa, nome e dica de "Improvisado como…" (posição e lado originais).

### 5.5 Clube

| Classe | Tela | Aberta por | Conteúdo |
|---|---|---|---|
| `a.cW` | Finanças | `a.eg.qT` (Ctrl+F, clique no dinheiro) | Caixa, salários por mês/semana, receitas, empréstimo bancário ("Pegar 500 mil", "Pagar 500 mil", juros) |
| `a.cl` / `a.cq` | Estádio / Expansão | `a.eg.ra` / `a.cl.oG` | Lugares por setor (geral, arquibancada, cadeira, camarote), preços ("Usar sempre os preços sugeridos"), obra em andamento; orçamento e construção. Não abre no modo seleção |
| `a.ds` | Academia de Juniores | `a.eg.qY` (F6), `a.iA` | Promover, dispensar, propor compra, definir apelido; vagas |
| `a.iQ` | Treino | `a.eg.qU` | Foco semanal (principais gol/des/arm/fin ou secundárias vel/tec/pas) ou "Deixar auxiliar técnico decidir" |
| `a.bb` | Cores do Time | `a.eg.qQ` | Cor de fundo e de texto do time (`ah.kB`/`kC`), usadas na própria tela do clube e nos placares |
| `a.hw` | Retrospecto | `a.eg.qP`, `a.gE`, `a.gO`, `a.iA`, `a.jv` | Tabela por ano (`components.ay`) |
| `a.aL` | Histórico de confrontos | `a.eg.rh` | Jogos, vitórias, empates, maior vitória entre o time e o próximo adversário |
| `a.iA` | Informações do time | `S.a(ah, ah, boolean)` | Elenco e dados do time; abas/botões "Calendário" (`a.L`), "Academia de Juniores", "Galeria de troféus", "Retrospecto", "Transferências", "Ranking" (`a.gX`), "Info", "Carreira"; compra, empréstimo e "Fazer oferta" (oferta por jogador fora da lista só na versão registrada); Esc fecha |
| `a.gx` | Procura de jogadores | `a.eg.dn` (F7) | Filtros (`components.O`: posição, faixas de preço, idade, características, com *range slider*), "Procurar", "Resetar filtros"; Enter abre o time do jogador (`S.a` → `a.iA`), Esc fecha |
| `a.L` | Calendário | `a.eg.ad` (F4), `a.gE`, `a.gO`, `a.iA`, `a.jv` | Jogos do time ou da seleção, "Mostrar todos"; abre a ficha do jogo `a.dq` (estádio, posse de bola) em `L.mZ`; Esc fecha |

### 5.6 Competições, estatísticas e história

| Classe | Tela | Observações |
|---|---|---|
| `a.ay` | Tabelas | Rodadas, classificação e chaves (`components.au`, `av`, `aw`, `ax`), artilheiros, melhores notas médias, "Estatísticas e história" (média de gols, maior vencedor, atual e último campeão, maior goleada) |
| `a.al` | Classificação e jogos | Variante antiga de `a.ay` (fases, grupos, rodadas); só `S.b`, que não tem chamador |
| `a.R` | Campeões | Por competição |
| `a.o` | Artilheiros | "Melhores de sempre de todas competições", "mostrar todos >>" |
| `a.y` | Líderes de assistências | — |
| `a.hc` | Ranking Clubes | Por reputação, pontos corridos ou colocação; nacional e internacional |
| `a.jv` | Ranking de Seleções | Por continente |
| `a.gX` | Ranking de Técnicos | Por pontos ou reputação |
| `a.H` | Bola de Ouro | Seleção por posição |
| `a.iu` | Time da Rodada / Time do Ano | Parâmetro `int` (0 rodada, 1 ano **(inferido pelos itens de menu)**) |
| `a.hC` | Últimas trocas de técnicos / transferências | Parâmetro 0 ou 1; filtro "Todos os times" |
| `a.di` | Galeria de Troféus do time | Altura conforme o número de troféus (`pG`); imagens em `trofeus/*.png` (`best.aq.w`, `aq.x`) |
| `a.dg` | Galeria de Troféus do técnico | `components.aC` |
| `a.de` | Galeria de Troféus (variante) | Sem chamador |

### 5.7 Partida (`a.dV`) e diálogos de jogo

`a.dV` é criada por `S.aY(4)` com a altura útil da tela. Mostra o tempo ("N' – Nº tempo", "Acréscimos", "Intervalo", "Fim de jogo") e uma barra de progresso, um painel de placar da partida acompanhada (`Hr`: nomes com as cores dos times, placar, último evento com ícone, posse de bola, informação da rodada) e a tabela de todos os jogos do dia (`Hs`, modelo `b.M`, renderizador `b.aG`; cada linha é um `components.v` que embrulha um `best.I`). A partida acompanhada (`GW`) é a do humano; a tabela rola até ela quando passa da 20ª linha. O relógio é um `javax.swing.Timer` sem repetição (`GO`) cujo intervalo vem de `best.aq.rz[velocidade]` = 2000, 1200, 700, 450, 220, 100 ms; a velocidade inicial é `SR.getVelocidade()`, ou `getVelocidadeNH()` quando nenhum jogo tem humano (`a.dV` ≈ l. 216). O funcionamento do minuto, da pausa e do pênalti está detalhado em [03 — motor de partida](03-motor-de-partida.md) e em [campo animado](../live-match.md).

Pedidos de pausa: Enter/Espaço (`a.dW` → `qh`, `GV = Hc`), clique nos rótulos do placar (`a.dX`, `GV = GW`) ou numa linha da tabela (`a.ef`, `GV = linha`). No fim do minuto o jogo abre `a.cD` para a partida pedida.

| Classe | Tela | Quando |
|---|---|---|
| `a.cD` | Substituições / tática durante o jogo ("Substituições restantes", estilo, marcação, ataques, cobradores, falso 9, "Voltar ao jogo") | Pausa pedida (`dV.e(i, false)`); intervalo, para cada partida humana, se `getVerJanelaSubs() == 1` (`dV.qg`); expulsão (tipos 3 e 4) ou lesão (tipo 5) de time humano (`dV.a(v, I, A, int)`). Esc, Enter e Espaço voltam ao jogo (`a.cJ`/`a.cK` → `pb`) |
| `a.gh` | Penalty – escolha do batedor | Pênalti a favor de time humano, antes de `a.gb` |
| `a.gb` | Cobrança de pênalti (narração "prepara para bater…", decide o resultado) | Todo pênalti em jogo com humano (`dV.b(v, A)`) |
| `a.C` | Disputa de pênaltis – ordem dos batedores ("subir", "descer", "Jogar") | Decisão por pênaltis do time humano |
| `a.bg` | Disputa de pênaltis ("vai pra bola…", "Gol!!!", "Perdeu!", "continuar") | Fim de jogo com decisão por pênaltis; jogos só de computador entram se `getVerDecisaoPenNaoHumano() == 1` (`dV.qd`) |

Não há tela própria de intervalo nem de pós-jogo dentro de `a.dV`: o intervalo é tratado em `dV.qg` (som, texto e janela de substituição) e o fim em `dV.qc` (som, disputas de pênaltis, `best.s.dJ`). O resumo da rodada é a tela seguinte, `a.hk`.

### 5.8 Fim de rodada, fim de temporada e carreira

| Classe | Tela | Conteúdo e ações |
|---|---|---|
| `a.hk` | Fim de rodada (`S.aY(5)`) | Resultados por competição e estatísticas do jogo selecionado (finalizações, no gol, erros de passe, posse, desarmes; `components.V`, `components.i`, `components.u`, `components.z`); "Continuar >>" (`a.ht` e Enter → `nx`), ↑/↓ mudam a linha, "Tabelas" (`a.hu`), "Opções" (`a.hv` → `a.fB`), "Time da Rodada" (`a.hm` → `a.iu`), pedido de demissão (`a.hn` → `rr`). `nx` sorteia de 0 a 3 leilões (`best.N`) quando `isVerLeiloes` e o campo `hk.w` vale 1, 3 ou 10 (tipo da rodada exibida **(inferido)**), e abre `S.aY(8)` se houver algum e `SR.cd()`; senão chama `SR.ax()` |
| `a.dz` | Venda de jogador em leilão (`S.aY(8)`) | Lance mínimo, oferta, "Ver próximo leilão", "Continuar Jogo >>" (Enter → `SR.ax`) |
| `a.cR` | Fim da temporada (`S.aY(6)`) | Campeões nacionais, internacionais e regionais; "Time do Ano" (`pm` → `a.iu`); "Marcar amistosos" (`S.w`/`S.x`); "Iniciar novo ano >>" (`pn`: autossalvamento, `f.j`, `f.V`); oferta de torneio amistoso (`S.aY(10)`) |
| `a.bl` | Demissões na Rodada | Lista de técnicos demitidos (`components.h`) |
| `a.dm` | Demitido! | Motivo e substituto; "Agora, espere por propostas de outros times" |
| `a.gO` | Convites para ser técnico | Times e seleções que convidam; "Assumir time", "Assumir seleção", "Rejeitar todos" |
| `a.gE` | Central de Empregos | Times e seleções sem técnico; candidatar-se |
| `a.dJ` | É campeão! | Técnico campeão |
| `a.bn` | Central de Mensagens | Mensagens da diretoria (`components.as`); ação "Multar" (10% do salário) |

### 5.9 Seleção e amistosos

| Classe | Tela | Observações |
|---|---|---|
| `a.aP` | Convocar jogadores para seleção | 2 goleiros e 15 de linha no mínimo; "Convocação automática", "Desconvocar todos", filtros `components.O` |
| `a.h` | Marcar amistoso (clube) | Casa/fora, data livre, adversário |
| `a.d` | Marcar amistosos (seleção) | Mesma estrutura de `a.h` |

### 5.10 Técnicos humanos durante a carreira

`a.ip` ("Técnicos humanos": adicionar, remover/aposentar; limite) abre `a.a` ("Adicionar técnico humano": nome e nacionalidade).

### 5.11 Opções (`a.fB`)

Aberta por F3, pelo menu "Preferências", pelo botão "Preferências" de `a.hU` e por `a.hk`. Duas partes:

- Combos (`II`): "Salvar automaticamente" (Não usar auto-save, A cada 3 jogos, A cada jogo, Início do ano); "Velocidade do Jogo" e "Velocidade sem jogos humanos" (Lento, Normal, Rápido, Bem rápido, Super rápido, Ultra rápido; até o índice `IJ`/`IK` = 4 na listagem lida); "Disputas de pênaltis sem humanos", "Mudanças de técnicos", "Janela de substituição no intervalo" (Não/Sim); "Aviso de término de contrato" (Não, Após término, Faltando 1 mês). Cada mudança grava por `fB.c(Object)` pelo nome `comb0`…`comb6`.
- Caixas e escolhas: atualizar contratos automaticamente, cor nos placares humanos (`cor0s`, `cor2s`, `cor3s`), sons, destaque do time da casa, cores na lista de jogadores (→ `a.aX`, cor por posição), tema de cores das janelas (5 temas), ver leilões, ver estaduais agrupados, não mostrar ligas/estaduais/regionais sem humanos, e a tabela "Competições sem times humanos: Ver só resultados / Ver partidas" (`verJint`, modelo de linhas `components.aE`).

### 5.12 Editor de times (`d.n`)

Janela separada "Editor Brasfoot" (`JFrame`, aberta da tela inicial por `best.n.cW`), que lista e grava `teams/*.ban` (`d.av`, `d.ap` para jogadores, `d.ay` para times). Diálogos: `d.ac` (adicionar time: nome, técnico, estádio de 1 mil a 120 mil lugares, arquivo), `d.f` (adicionar/editar jogador, com limites de elenco e reputação), `d.ai` (transferir jogador). `d.b` contém um importador de formatos antigos (`.b16`, `.b18`) com caminho de desenvolvimento fixo **(inferido: não usado pelo jogador)**.

### 5.13 Telas sem chamador encontrado

Busca textual por `new <Classe>(` em todos os pacotes não encontrou quem abra: `a.hF` (depuração de simulação: "set 1", "r1000", "campo neutro"), `a.aa`/`a.bu` (classificação e jogos antiga), `a.gl`, `a.de`, `a.al` (só via `S.b`, sem chamador), `a.do` (só via `a.hU.AS`, sem chamador) e os painéis `components.B`, `components.F`, `components.L`, `components.N`, `components.c`. Provavelmente são restos de versões anteriores **(inferido)**.

## 6. Tabela classe → tela

| Classe | Tela | Classe | Tela |
|---|---|---|---|
| `a.C` | Disputa de pênaltis – ordem dos batedores | `a.dz` | Venda de jogador em leilão (rodada) |
| `a.H` | Bola de Ouro | `a.eg` | Tela do clube |
| `a.L` | Calendário | `a.fB` | Opções |
| `a.R` | Campeões | `a.fZ` | Regionais (configuração inicial) |
| `a.a` | Adicionar técnico humano | `a.fw` | Nome do arquivo para salvar |
| `a.aL` | Histórico de confrontos | `a.fy` | Novo contrato |
| `a.aP` | Convocação da seleção | `a.gE` | Central de Empregos |
| `a.aX` | Cores por posição na lista | `a.gO` | Convites para ser técnico |
| `a.aa` | Classificação e jogos (antiga, sem uso) | `a.gX` | Ranking de técnicos |
| `a.al` | Classificação e jogos (sem uso) | `a.gb` | Cobrança de pênalti |
| `a.ay` | Tabelas | `a.gh` | Escolha do batedor de pênalti |
| `a.bV` | Técnicos humanos | `a.gl` | Sem uso |
| `a.bb` | Cores do time | `a.gq` | Tela inicial |
| `a.bg` | Disputa de pênaltis | `a.gx` | Procura de jogadores |
| `a.bl` | Demissões na rodada | `a.h` | Marcar amistoso (clube) |
| `a.bn` | Central de Mensagens | `a.hC` | Trocas de técnicos / transferências |
| `a.bs` | Jogadores emprestados | `a.hF` | Depuração de simulação (sem uso) |
| `a.bu` | Contêiner de `a.aa` (sem uso) | `a.hU` | Configurações iniciais |
| `a.bz` | Escalação | `a.hc` | Ranking de clubes |
| `a.cD` | Substituições durante a partida | `a.hk` | Fim de rodada |
| `a.cR` | Fim da temporada | `a.hw` | Retrospecto |
| `a.cW` | Finanças | `a.hz` | Salvando / carregando |
| `a.ce` | Numeração do elenco | `a.iA` | Informações do time |
| `a.cl` | Estádio | `a.iQ` | Treino |
| `a.cq` | Expansão do estádio | `a.iX` | Leilão do próprio jogador |
| `a.cu` | Sistema de mata-mata da liga | `a.il` | Táticas salvas |
| `a.cw` | Configurar ligas nacionais | `a.ip` | Técnicos humanos (carreira) |
| `a.cz` | Proposta de compra | `a.iu` | Time da Rodada / do Ano |
| `a.d` | Marcar amistosos (seleção) | `a.jH` | Torneio amistoso |
| `a.dG` | Configurar estaduais | `a.jc` | Vender jogador |
| `a.dJ` | É campeão! | `a.ji` | Aposentar jogador |
| `a.dK` | Formato de divisão estadual | `a.jm` | Proposta recebida (empréstimo/compra) |
| `a.dN` | Carregar jogo salvo | `a.jp` | Sobre o Brasfoot |
| `a.dV` | Partida | `a.jv` | Ranking de seleções |
| `a.da` | Registro | `a.l` | Apelido de júnior |
| `a.de` | Galeria de troféus (variante, sem uso) | `a.o` | Artilheiros |
| `a.dg` | Galeria de troféus do técnico | `a.y` | Líderes de assistências |
| `a.di` | Galeria de troféus do time | `d.n` | Editor Brasfoot |
| `a.dk` | Histórico do jogador | `d.ac` | Editor: adicionar time |
| `a.dm` | Demitido | `d.f` | Editor: adicionar/editar jogador |
| `a.do` | Preferências de competições internacionais | `d.ai` | Editor: transferir jogador |
| `a.dq` | Ficha da partida | `a.ds` | Academia de juniores |

## 7. Atalhos de teclado

Os mapas são registrados com `getInputMap()` (condição "com foco") nos componentes indicados, embora o código também obtenha o mapa de "ancestral do foco" sem usá-lo; por isso os atalhos dependem de o componente certo ter o foco **(inferido)**.

**Tela do clube** (`a.eg.a(JComponent)`, aplicado ao painel, à tabela do elenco, ao botão "Escalar Time" e à barra `ve`):

| Tecla | Ação | Tela |
|---|---|---|
| Enter, Espaço | `a.eh` → `qZ` | Escalação (`a.bz`) |
| F2 | `a.es` → `ru` | Salvar jogo |
| F3 | `a.eZ` → `S.a(Iy)` | Opções (`a.fB`) |
| F4 | `a.fk` → `ad(false)` | Calendário (`a.L`) |
| F5, Ctrl+T | `a.eD` → `qV` | Tabelas (`a.ay`) |
| Ctrl+F | `a.eO` → `qT` | Finanças (`a.cW`) |
| F6 | `a.ft` → `qY` | Juniores (`a.ds`) |
| F7 | `a.fu` → `dn` | Procura (`a.gx`) |
| F8 | `a.fv` → `G(null)` | Times (`a.iA`) |
| F9 | `a.ei` → `re` | Jogos amistosos (`a.h`) |
| F10 | `a.ej` → `rk` | Artilheiros (`a.o`) |
| F11 | `a.ek` → `rl` | Campeões (`a.R`) |

Os itens do menu "História" exibem aceleradores trocados em relação ao mapa: "Campeões" mostra F10 e "Artilheiros" mostra F11 (`a.eg.rb`). Como aceleradores de `JPopupMenu` fechado não costumam disparar, vale o mapa acima **(inferido)**.

**Partida** (`a.dV.a(JComponent)`): F1–F4 escolhem as velocidades 0–3 (2000, 1200, 700, 450 ms por minuto); F5 escolhe a velocidade 4 (220 ms) ou, com o jogo registrado, é remapeada para a velocidade 5 (100 ms); Enter e Espaço pedem pausa (`qh`).

**Outros diálogos:**

| Tela | Teclas |
|---|---|
| `a.bz` Escalação | Espaço e Alt+F4 → "Jogar >>" |
| `a.cD` Substituições | Enter, Espaço e Esc → voltar ao jogo |
| `a.hk` Fim de rodada | Enter → "Continuar >>"; ↑/↓ → linha anterior/seguinte (`dz(1)`/`dz(0)`) |
| `a.dz` Leilão | Enter → continuar |
| `a.gx` Procura | Enter → abrir time do jogador; Esc → fechar |
| `a.iA`, `a.L`, `a.hz` | Esc |
| `a.C`, `a.bg`, `a.gb` | Alt+F4 mapeado para ação vazia, o que impede fechar esses diálogos pelo atalho **(inferido)** |

## 8. Sons

`c.a.dj(i)` resolve `sons/<nome>.wav` na pasta do jogo (não há sons dentro do jar); `c.a.vH` pré-carrega os existentes no arranque e `a.dV.qf` abre os fluxos. Tocam só com `SR.isUsaSons()`, por `a.dV.dk(i)` (um `Clip` por som, reiniciado a cada uso). `a.dV.qb` fecha os *clips* (chamado por `a.hk.nx`).

| Índice | Arquivo | Quando toca (`a.dV`) |
|---|---|---|
| 0 | `intervalo.wav` | Intervalo, só com janela de substituição ligada (`qg`) |
| 1 | `fimjogo.wav` | Fim de jogo (`qc`) |
| 2 | `gol1.wav` | Gol do time humano (`A.cu().jZ()` verdadeiro) em partida com humano |
| 3 | `goladv.wav` | Gol do adversário em partida com humano |
| 4 | `penalty.wav` | Pênalti (lance tipo 1 com `el() == 3`) |
| 5 | `expulsao.wav` | Lances tipo 3 e 4 **(inferido: cartão vermelho)** |
| 6 | `contusao.wav` | Lance tipo 5 (lesão) |

`dV.dl` e `dV.dm` tocam um som avulso abrindo o arquivo de novo; não foi encontrado uso que os diferencie de `dk`.

## 9. Opções e onde ficam gravadas

| Onde | Formato | Conteúdo | Origem |
|---|---|---|---|
| `options.bcf` na pasta do jogo | Serialização Java de `est.Options` | Todas as opções do jogo (tabela abaixo) | `c.a.vI` (leitura), `c.a.vJ` (gravação), `c.a.vM` (acesso) |
| Carreira (`best.f`, dentro do `.s22`) | Kryo, junto com o save | Cópia das mesmas opções | `best.f.<init>` copia de `vM()`; cada *setter* de `est.Options` também chama o *setter* de `c.a.SR` |
| `Preferences` do usuário, nó `bfoptions` | API `java.util.prefs` | `anoinicio` (0 = 2022, 1 = 2023), lido por `a.hU` para preselecionar a temporada | `best.aq.f`, `best.aq.am` |
| Preferências do usuário | API `java.util.prefs` | Dados do registro (licença) | não documentado aqui |

A tela `a.fB` lê os valores da carreira (`c.a.SR.get…`) e grava em `c.a.vM().set…` seguido de `c.a.vJ()`; como os *setters* de `est.Options` repassam a `c.a.SR`, a mudança vale para a carreira aberta e para as próximas.

Campos de `est.Options` (valores iniciais):

| Campo | Padrão | Uso na interface |
|---|---|---|
| `autoSalvar` | 0 | `a.bz.oi`, `best.f.ap` |
| `velocidade`, `velocidadeNH` | 4, 4 | Velocidade inicial em `a.dV` |
| `verDecisaoPenNaoHumano` | 0 | `a.dV.qd` |
| `verMudancaTecnicos` | 1 | Exibição de `a.bl` **(inferido)** |
| `verJanelaSubs` | 1 | `a.dV.qg` |
| `avisoTerminoContrato` | 0 | Mensagens de contrato **(inferido)** |
| `autoRenovaContrato` | true | — |
| `usaCorPlacar`, `corPlacar` | true, 0 | Placar de jogos humanos |
| `usaSons` | true | Seção 8 |
| `negritoCasa` | true | Destaque do mandante nos eventos |
| `usaCoresLista` (+ cores) | false | Cores por posição (`a.aX`) |
| `verEstaduaisAgrupados` | false | — |
| `ignoraLigas`, `ignoraEstadual` | true, true | `best.f` decide se mostra rodadas sem humanos |
| `regionaisSemHumanos` | 0 | `best.f` |
| `verLeiloes` | false | `a.hk.nx` |
| `corTema` | 0 | Tema das janelas |
| `verJint[]` | — | Ver resultados ou partidas por competição sem humano (`best.s`) |
| `jogaEstadual`, `jogaRegionais`, `jogaIntClubes`, `jogaSelecoesAll`, `salarioMensal`, `habilidadeIndividual`, `gruposIntPadrao`, `UsarGruposReaisCopa`, `conviteRegionais`, `novoFormatoCopa`, `verMundias`, `verSuperCopas` | ver `est/_Options.java` | Configurações de nova carreira (`a.hU`, `a.do`, `a.fZ`) |

## 10. Aparência: *look and feel*, tema, fontes e cores

- *Look and feel*: Nimbus no arranque (`best.h2.main`); ao sair da tela inicial para o jogo, para o editor ou para carregar, `best.n.g("Metal")` troca para Metal (`a.gq.mi`, `pW`, `rN`). As telas do jogo, portanto, usam Metal.
- Tema das janelas: `best.aq.E(tema, variante)` devolve a cor de fundo; tema 0–4 (azul `#004469`, cinza-esverdeado `#687864`, preto, vinho `#6E0000`, roxo `#990099`), variantes 1 (fundo), 2 (mais escuro) e 3 (mais claro). 43 classes de `a` e `components` pintam o fundo com `E(corTema, 1)`, 20 usam a variante 2. Ícones de escolha em `aiconsc/corTema0…4(s).png`.
- Cores do time: `best.ah.kB()` (fundo) e `kC()` (texto) pintam placares e o painel do clube; a cor do texto também é aplicada globalmente a `ProgressBar.selectionForeground` (`a.eg`, via `UIManager.put`).
- Fontes: quase só Tahoma e Arial; as mais usadas são Arial negrito 12, Tahoma 12, Tahoma negrito 14 e 12 (contagem de `new Font` em `a` e `components`). Não há fonte embutida.
- Imagens: ícones e bandeiras vêm do jar (`aicons`, `aiconsb`, `aiconsc`, `aiconsj`, `aeicons`, `aesticons`, `aflags`, `aflagslarge`, `acamisas`); fundos (`img/f01.jpg`…`f04.png`), escudos, camisas e troféus vêm da pasta do jogo (ver [01](01-arquitetura-e-arquivos.md)). O gramado da escalação usa `aicons/campo*.png` e `aiconsj/campo_diminuido*.jpg` conforme a condição do campo **(inferido pelos nomes)**.
- Cursores: as telas trocam para cursor de espera (`Cursor(3)`) antes de abrir diálogos pesados e voltam para a mão (`Cursor(12)`).

## 11. Idioma

Só há português do Brasil. `best.M` carrega `arquivos/default_lang.xml` (264 chaves) em `Properties` e expõe `M.getString(chave)`. As chaves cobrem nomes de países (`P0`…), posições (`gk`, `lat`, `zag`, `meia`, `ata`), nomes de competições (`lib`, `ligaC`, `ncm`, `eliEU`…) e os textos do registro (`fix_*`, `mw_btnoreg*`). São usadas por `a.da`, `best.ac`, `best.aq`, `best.f`, `best.p` e por classes de competição em `f`. Todos os demais textos de tela são literais no código. `arquivos/names/` e `arquivos/surnames/` (221 países cada) servem à geração de nomes (`best.M.s`), não à interface. Não existe seleção de idioma.

## 12. Componentes reutilizáveis (`components`)

| Classe | Papel | Usada em |
|---|---|---|
| `components.a`, `components.b` | Restrições e layout absoluto | Quase todas as telas |
| `components.E` | Painel de fundo com imagem de `img/` (modo 0: `f01.jpg`; 8: `f02.jpg`; 3: `f03.png`; 1: degradê) | `best.S` |
| `components.ao` | Casa da grade tática (seção 5.4) e desenho da camisa do jogador | `a.bz`, `b.L`, `b.O`, `b.P` |
| `components.K`, `L`, `M` | Marcadores de jogador no campo tático (`JLayeredPane`) com dica de improvisação | `a.bz`, `a.cD` |
| `components.m` | Cartão do jogador (contrato, empréstimo, contusão, suspensão) | `a.eg` |
| `components.O` | Painel de filtros de busca (posição, preço, idade, características; *range slider* `RangeSliderUI`, `aa`, `ac`) | `a.gx`, `a.aP` |
| `components.v` | Linha da tabela de jogos da partida (envolve `best.I`, placar visível, último lance) | `a.dV`, `a.cD`, `a.dq` |
| `components.V` | Widget de placar | `a.hk` |
| `components.au`, `av`, `aw`, `ax` | Classificação, chave de mata-mata e grupos | `a.ay` |
| `components.d`, `e`, `w`, `y` | Montagem de chaves, grupos e rodadas para as tabelas | `a.ay`, `a.al`, `a.aa` |
| `components.ay` | Tabela de retrospecto por ano | `a.hw` |
| `components.k`, `l`, `aC`, `aj` | Cartões de troféu | `a.di`, `a.dg`, `a.de` |
| `components.H` | Linha de jogador emprestado (cancelar empréstimo) | `a.bs` |
| `components.at` | `JScrollPane` especializado | `components.H` |
| `components.NumberFormat` | Formatação de valores ("5 milhões 200 mil", negativos em vermelho) | várias |
| `components.f` | `Icon` composto | — |
| `components.ar` | Tratador global de exceções: acrescenta a pilha (formatada como HTML) a `erros.log` na pasta do jogo e a imprime no console; não mostra nada na tela | `best.h2.main` |
| `components.t` | Registro de empréstimo (jogador, time de origem, prazo) | `a.bs`, `a.eg`, `best.ah`, `best.f` |
| `components.an` | Leilão de jogador (abre `a.iX`) | `a.jc`, `best.f` |
| `components.as` | Mensagem da diretoria | `a.bn`, `a.eg`, `best.ah`, `best.al` |
| `components.ag` | Tática salva (nome + listas) | `a.bz`, `a.il`, `best.ah` |
| `components.aE` | Linha da tabela "competições sem humanos" | `a.fB` |

`components.t`, `as`, `ag`, `ah`, `am`, `aD` e `a` implementam `Serializable` e quatro deles (`t`, `as`, `ag`, `ah`) são referenciados por `best.ah`/`best.f`/`best.al`, isto é, entram no save. Pela regra de compatibilidade de saves do projeto, os campos dessas classes também não podem mudar **(inferido: a lista completa de classes do grafo do save está em [01](01-arquitetura-e-arquivos.md))**.

## 13. Pontos de interesse para o patch

- O campo animado injeta-se em `a.dV.<init>(JFrame, int)`, troca a chamada `best.I.q(II)V` dentro de `a.dV.aa(Z)V` e intercepta `a.dV.b(components.v, best.A)` (pênalti), como descrito em [campo animado](../live-match.md) e conferido em `tools/live-match-view-src/LiveMatchTransformer.java`. Esses nomes batem com o fonte decompilado.
- A partida abre `a.cD` dentro do passo de minuto (pausa, intervalo, lesão, expulsão), de forma modal; qualquer painel sobreposto precisa conviver com esse bloqueio.
- A janela é única e o conteúdo é trocado por `S.aY`; não há eventos de "tela fechada" para as telas de página cheia, apenas a nova instância.
- Busca de telas por texto: como os rótulos são literais, `grep` pelo texto visível em `a/*.java` localiza a classe diretamente.

## Lacunas

- O mapeamento botão → método foi resolvido por bytecode para `a.gq`, `a.eg`, `a.dV`, `a.hk`, `a.cR`, `a.bV` e para as teclas dos diálogos listados; nas demais telas, ações e conteúdo foram descritos pelos textos e pelos construtores, sem seguir cada *listener*.
- O significado dos métodos ofuscados do modelo (`best.ah.kc`, `best.F.fk`, `best.I.hy` etc.) foi tomado pelo uso na interface e pelos outros documentos; não foi revalidado aqui.
- Os códigos de lance 3, 4 e 5 em `a.dV` (sons de expulsão e lesão) não foram cruzados com o gerador de lances.
- Não foi verificado qual atalho vale para F10/F11 quando o menu "História" mostra aceleradores diferentes, nem se as teclas funcionam sem foco no componente certo.
- As condições exatas em que `best.f.ap`, `at` e `ax` escolhem a próxima tela (por exemplo `f.ay()`, `bH`, `bk`) pertencem ao domínio de calendário e não foram detalhadas.
- O papel de `f.B` (usado em Time da Rodada e Bola de Ouro, devolvido por `best.ah.kF`) não foi confirmado.
- Telas sem chamador (seção 5.13) podem ser alcançadas por caminhos não textuais (reflexão); isso não foi descartado por análise de bytecode completa.
- As abas e colunas de `a.iA`, `a.ay`, `a.hk` e `a.cD` não foram listadas uma a uma.
- O esquema de registro e licença foi deixado de fora de propósito.
