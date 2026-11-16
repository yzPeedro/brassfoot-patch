# Brasfoot 22-23 — arquitetura, inicialização, persistência e formatos de arquivo

**Resumo.** O jogo é uma aplicação Swing de janela única, empacotada como jar dentro de um executável Launch4j, que sobe por `best.h2.main` e funciona por eventos, sem laço de jogo próprio. Todo o estado de uma carreira fica num único objeto raiz, `best.f`, acessível globalmente em `c.a.SR`. O save grava esse objeto e um auxiliar (`best.ay`) com a biblioteca Kryo 4, sem compressão, criptografia ou cabeçalho de versão, em `sav/<nome>.s22`, além de uma cópia `.sbck` e de metadados `.info`. Os arquivos de dados (`teams/*.ban`, `conf_ligas_nacionais/*.cfg`, `conf_estadual/*.ces` e `options.bcf`) são **serialização Java padrão** (`ObjectOutputStream`) de classes simples dos pacotes `e` e `est`. Imagens e sons são lidos do disco relativos a `user.dir`, com alternativas embutidas no jar quando o arquivo falta.

Fonte: decompilação Vineflower 1.11.1 do executável original (SHA-256 `2fa65476…bb1c`, idêntico byte a byte ao jar analisado). Os nomes de arquivo no material decompilado têm `_` antes de cada maiúscula (`best/_F.java` = `best.F`), mas o texto abaixo usa os nomes originais das classes. O que não foi lido diretamente vem marcado como **(inferido)**.

---

## 1. Empacotamento e dependências

| Item | Valor | Origem |
|---|---|---|
| Executável | Launch4j; o jar está anexado ao `.exe` (o mesmo arquivo abre como zip, com 125.440 bytes de prefixo) | cadeias `Launch4j`, `Bundled JRE`, mensagens sobre Java ausente no `.exe` |
| Opções de JVM embutidas | `-Xss4m -Xms512m` | cadeias do `.exe` |
| Versão mínima de Java | `1.7.0_71` aparece como cadeia no cabeçalho Launch4j **(inferido)** | cadeias do `.exe` |
| `Main-Class` | `org.eclipse.jdt.internal.jarinjarloader.JarRsrcLoader` (carregador "jar-in-jar" do Eclipse, em `org/eclipse/jdt/internal/jarinjarloader/`) | `META-INF/MANIFEST.MF` |
| `Rsrc-Main-Class` | `best.h2` | manifesto |
| Bibliotecas internas | `kryo-4.0.2.jar`, `minlog-1.3.0.jar`, `objenesis-2.1.jar`, `reflectasm-1.10.1-shaded.jar` (jars aninhados, no `Rsrc-Class-Path`) | manifesto e listagem do jar |
| Classes | 1.038 classes do jogo | `INDEX.tsv` |
| Recursos no jar | `acamisas/` (6), `aeicons/` (18), `aesticons/` (27), `aflags/` (224), `aflagslarge/` (224), `aicons/` (138), `aiconsb/` (19), `aiconsc/` (31), `aiconsj/` (19), `arquivos/` (444: idioma, nomes e sobrenomes) | listagem do jar |
| Outras APIs | Swing/AWT, `javax.imageio`, `javax.sound.sampled` (sons), `java.util.prefs` (registro e uma preferência), `javax.xml.parsers` (importadores XML legados) | imports em `a.dV`, `best.ah`, `best.h2`, `best.P`, `best.w` |
| Rede | Nenhum acesso de rede, exceto `Desktop.browse` para o site oficial na tela de versão registrada | `a.da` (única ocorrência de `java.net`/`Desktop`) |

Todos os caminhos de disco partem de `System.getProperty("user.dir")`, também guardado em `best.n.cK`. O jogo precisa, portanto, ser iniciado com o diretório de trabalho na pasta da instalação.

## 2. Estrutura de pacotes

| Pacote | Classes | Linhas | Conteúdo |
|---|---:|---:|---|
| `a` | 565 | 39.109 | Telas, painéis e diálogos Swing e seus *listeners* (classes internas anônimas viraram classes de topo, como `a.gr`–`a.gv` para `a.gq`) |
| `b` | 101 | 4.978 | 43 `AbstractTableModel`, 44 `DefaultTableCellRenderer`, 7 comparadores e rótulos |
| `best` | 78 | 25.938 | Núcleo: modelo (carreira, país, time, jogador, técnico, partida, campeonato, calendário), constantes, carga de dados e troca de telas |
| `c` | 2 | 1.419 | `c.a`: estado global e persistência; `c.b`: gerador de lances (hipótese anterior; fora deste domínio) |
| `components` | 85 | 7.504 | Componentes Swing próprios: `components.b` é um `LayoutManager2` de posição absoluta e `components.a` a sua restrição (x, y, largura, altura), no estilo do *AbsoluteLayout* do NetBeans (inferido); `components.E` é o painel com fundo; `components.ar` trata exceções não capturadas; há também `NumberFormat` e `RangeSliderUI` |
| `d` | 82 | 4.769 | Editor de times embutido (`d.n` é a janela; grava `.ban`) |
| `e` | 2 | 440 | Formato dos `.ban`: `e.t` (time) e `e.g` (jogador) |
| `est` | 7 | 825 | Tipos serializáveis de configuração: `Options`, `InfoArquivoSalvoType`, `ConfigLigaType`, `ArrayLigaType`, `ConfigEstadualType`, `ArrayLigaEType` e `LoadLigaOptions` (este último não é serializável) |
| `f` | 40 | 11.411 | 35 subclasses de `best.at` (campeonatos concretos: Libertadores, Liga dos Campeões, Conference League etc.) |
| `forms` | 26 | 2.100 | Ferramentas internas do desenvolvedor (`forms.h`, janela "Passa Dia", "Processa teste", "save", "load") e utilitários numéricos e aleatórios (`forms.Randoms extends Random`, integração numérica) |
| `g` | 2 | 118 | `g.b`: preparação antes de salvar e religação depois de carregar; `g.a`: lista serializável auxiliar |
| `h` | 42 | 793 | 41 `Comparator` (ordenações de listas e tabelas) |
| `org.eclipse…` | 6 | 218 | Carregador jar-in-jar |

## 3. Inicialização

### 3.1 `best.h2.main`

1. Registra `components.ar` como `Thread.setDefaultUncaughtExceptionHandler` (ver §9).
2. Ativa o *look and feel* Nimbus, se existir. Falhas vão para `java.util.logging`.
3. `best.h2.mg()` verifica o registro da cópia (ver §10). Também lê das **Preferences** do usuário uma preferência inteira para `c.a.SU`, cujo padrão é o modelo de dados da JVM (32/64); `c.a.SU` não é lido em nenhum outro lugar. Ver §10.
4. `new best.M(true)` carrega o idioma (§4).
5. `best.n.cU()` monta a lista ordenada de países (`best.n.cF`, objetos `best.ad`) a partir do enum `best.ac`, com o nome sem acentos (`best.n.f`) e a ordenação de `best.n.cL`.
6. Cria a tela inicial `a.gq` (JFrame sem moldura, 532 × 300, imagem `/aiconsj/tela_inicial.jpg`).
7. `c.a.vH()` localiza os sons (§8).
8. `best.h2.ml()` inicia uma `Thread` com `best.as`, cujo `run` chama `best.C.ey()`, um método **vazio**. A thread não faz nada.

A thread `main` termina em seguida. A interface é criada na thread `main`, fora da EDT (inferido de `main`), e a partir daí tudo acontece por eventos Swing.

`best.h` tem um segundo `main`, não referenciado pelo manifesto. É um *harness* de desenvolvedor: carrega o idioma, cria `c.a`, põe `c.a.SR.bs = false` (modo sem interface), abre `forms.h` e chama `best.p.dd()`.

### 3.2 Tela inicial `a.gq`

A associação entre rótulos e ações foi conferida nos acessores sintéticos do bytecode (`javap` de `a/gq.class`):

| Rótulo (posição) | Listener | Método | Efeito |
|---|---|---|---|
| `aft` (30, 110) | `a.gr` | `gq.mi` | Novo jogo: `new c.a()`, `best.p.dd()`, Metal L&F e `new best.S(true)` (tela 0) |
| `afx` (210, 110) | `a.gu` | `gq.pW` | Carregar jogo: `best.S.cX()` abre o diálogo `a.dN` |
| `afs` (370, 110) | `a.gs` | `gq.rN` | Editor de times: `best.n.cV()` lê todos os `.ban` e `best.n.cW()` abre `d.n` |
| `afu` "REGISTRAR JOGO" | `a.gt` | `gq.rP` | Tela 7 (`a.da`, vantagens da versão registrada) |
| `afw` (420, 260) | `a.gv` | — | `System.exit(0)` |

Na versão registrada, `gq.rO` esconde o rótulo de registro e o texto "versão não registrada".

### 3.3 Janela principal e troca de telas (`best.S`)

`new best.S(boolean)` cria um único `JFrame` sem moldura, maximizado na área útil da tela (`SunGraphicsEnvironment.getUsableBounds`). O fundo é o painel `components.E` (imagem `img/f01.jpg`, cor de reserva RGB 36, 91, 45). Se a área útil for ≤ 1020 × 700, o conteúdo vai dentro de um `JScrollPane` (`best.S.gJ`). O frame fica registrado em `best.n.a(JFrame)`.

`best.S.aY(int)` troca o painel central:

| Código | Classe | Papel (pelos textos da tela) |
|---:|---|---|
| 0 / 3 | `a.hU` | Configurações iniciais do novo jogo (ligas, estaduais, internacionais, seleções, ano inicial) |
| 1 | `a.bV` | Escolha de times e técnicos humanos |
| 2 | `a.eg` | Tela principal da carreira (menus Jogo, Técnico etc.) |
| 4 | `a.dV` | Tela de partida |
| 5 | `a.hk` | Tela pós-rodada (resultados) |
| 6 | `a.cR` | Fim de temporada ("Iniciar novo ano") |
| 7 | `a.da` | Vantagens da versão registrada |
| 8 | `a.dz` | Leilão de jogador |
| 10 | `a.jH` | Criação de torneio ("Nome do Torneio", "Fórmula") |

Diálogos modais auxiliares abertos por `best.S`: `a.dN` (carregar jogo, `cX`), `a.hz` (salvando/carregando, `a(String, boolean)`), `a.dJ`, `a.gO`, `a.gE`, `a.bl`, `a.dm`, `a.hF`, `a.ay`, `a.al`, `a.h` e `a.d`.

### 3.4 Criação da carreira

1. `c.a()` (construtor) lê `options.bcf` (§6), cria `best.f` em `c.a.SR` (o construtor copia as opções de `est.Options`) e `best.ay` em `c.a.afQ`.
2. `best.p.dd()`:
   - cria os 224 `best.Z` (países) em `SR.aG()` se a lista estiver vazia (`best.p.de`);
   - `best.U.w(false)` lê todos os `teams/*.ban` para `SR.bC` (só `vid == 185` e `valid == true`), contando times por país (`SR.bD`) e, no Brasil (país 29), por estado (`SR.bE`);
   - ordena `SR.bC` por `nivel` decrescente (`best.q`);
   - cria em `SR.bF` uma entrada `best.O` (liga jogável) para cada país com pelo menos 10 times, ou 16 para Alemanha (3), Argentina (11), França (72), Inglaterra (97) e Itália (104);
   - `best.p.ds()` lê todos os `conf_ligas_nacionais/*.cfg` para `SR.bG`.
3. Na tela 0 (`a.hU.oq`): o ano inicial (2022 ou 2023) vai para `SR.rM` (`best.f.I`) e para a preferência `anoinicio` (nó `bfoptions`, `best.aq.f`). Depois vêm `best.p.dg()` e a tela 1.
4. `best.p.dg()`:
   - `best.p.x` instancia um `best.ah` para cada `e.t`; nos países não escolhidos como liga jogável, só os 15 primeiros por nível;
   - em seguida monta ligas, copas internacionais (`f.r`, `f.v`, `f.u`, `f.w`, `f.y`, `f.t`, `f.H`, `f.x`, `f.J`) e seleções, e chama `best.F.fh()` e `best.al.fh()` para gravar os índices de time (§5.4).
5. A tela 1 (`a.bV`) chama `best.p.dh()` para os torneios regionais. Cada região precisa de pelo menos 16 times. Grupos de estados por índice de `best.aq.rX`:
   - {RJ, SP};
   - {MG, PR, RS, SC};
   - {AL, BA, CE, MA, PB, PE, PI, RN, SE};
   - os demais.
   Os estaduais (`best.w.dZ`) só existem nos estados com pelo menos 6 times.

## 4. Idioma e textos

- Um único arquivo de idioma: `/arquivos/default_lang.xml` dentro do jar, em formato XML de `java.util.Properties`, com 264 entradas. `best.M(true)` lê esse arquivo com `loadFromXML` para o `Properties` estático `best.M.gC`, e `best.M.getString(chave)` faz a consulta. Chaves observadas: `P0`…`P223` (nomes de países), `gk`/`lat`/`zag`/`meia`/`ata` (posições), `lib`, `ligaC`, `fix_*`.
- A maior parte dos textos da interface está fixa em português nas chamadas `setText` das telas do pacote `a`. Não há seleção de idioma (inferido: não existe outro arquivo de idioma, e `best.M.iw()` só percorre as chaves).
- Nomes gerados:
  - `/arquivos/names/<SIGLA>.txt` e `/arquivos/surnames/<SIGLA>.txt` (221 de cada) são lidos sob demanda por `best.M.a(String, int, int)`, que ignora linhas com ponto ou dígito e guarda o resultado em cache nas listas estáticas `gy`/`gz`;
  - `best.M.au(int)` e `best.M.k(int, boolean)` sorteiam nome e, às vezes, sobrenome;
  - o índice do país é a posição na lista ordenada de `best.n.cF` (`best.n.G`), com os desvios 221→85, 222→72 e 223→85.
- `/arquivos/ok_bra.txt` (37.219 nomes) é carregado por `best.M(false)` em `SR.bx` (campo **transient** de `best.f`, exposto por `aX()`), na criação e em cada carga de carreira. `best.F.av(int)` sorteia dele nomes de jogadores gerados, em faixas de índice que dependem da região do país (`best.ac.gg`).
- `best.M.iv()` contém um caminho absoluto da máquina do autor (`E:/Dropbox/...`) e não é chamado; o mesmo vale para `d.b`, com `E:/java/Brasfoot2017_editor/teams`. É código morto.

## 5. Saves

### 5.1 Arquivos

| Arquivo | Conteúdo | Escrito por | Lido por |
|---|---|---|---|
| `sav/<nome>.s22` | Kryo: `writeClassAndObject(best.f)` seguido de `writeClassAndObject(best.ay)` | `c.a.ae(String)` | `c.a.c(String, false)` |
| `sav/<nome>.sbck` | Cópia byte a byte do `.s22` recém-gravado (`Files.copy`, `REPLACE_EXISTING`) | `c.a.ae` | `c.a.c(String, true)`, só como reserva |
| `sav/<nome>.info` | Serialização Java de `est.InfoArquivoSalvoType` | `c.a.ae` (e `c.a.ad`, sem chamadores) | `c.a.af(String)`, para a pré-visualização no diálogo de carga |
| `sav/<nome>.sb19` | Mesmo tipo, formato antigo | — | `c.a.ag(String)` (sem chamadores; legado) |
| `sav/info.txt` | Texto "pasta de saves" | instalador | — |

`est.InfoArquivoSalvoType` (UID 1) é preenchido por `a.eg.qy` e `forms.h`:

| Campo | Conteúdo |
|---|---|
| `n` | Nome do time |
| `tc` | Nome do técnico (`ah.ka().dS()`) |
| `a` | Ano corrente: `SR.H()` (temporada, começa em 1) + `SR.iU()` (`rM − 1`) |
| `i` | Próximo jogo, como "C - " (casa) ou "F - " (fora) + adversário + rótulo |

### 5.2 Gravação (`c.a.ae`)

```
ae(nome):
  g.b.Ag()   # numera campeonatos e converte referências em índices
  g.b.Ai()   # numera jogadores e converte referências em índices
  grava .info (ObjectOutputStream)
  k = new Kryo(); k.setRegistrationRequired(false)
  grava .s22: writeClassAndObject(SR); writeClassAndObject(afQ)
  se deu certo: copia .s22 → .sbck
```

- **Sem compressão, sem criptografia, sem checksum e sem cabeçalho de versão.** O fluxo é um `com.esotericsoftware.kryo.io.Output` direto sobre `FileOutputStream`.
- Configuração Kryo efetiva (padrões da Kryo 4.0.2, conferidos por `javap` no jar embutido):
  - referências habilitadas (`Kryo.references = true`);
  - `FieldSerializer` padrão, com campos `transient` ignorados (`FieldSerializerConfig.serializeTransient = false`);
  - campos ordenados por nome (`FieldSerializer.compare` compara `getCachedFieldName`);
  - sem registro, então o nome qualificado de cada classe é escrito por extenso.
- Consequência: qualquer mudança no **conjunto, nome ou tipo** dos campos não transientes das classes alcançáveis a partir de `best.f` e `best.ay` (pacotes `best`, `f`, `est`, `g` e as coleções Java) torna o save ilegível. `serialVersionUID` não importa para a Kryo.
- Antes de gravar, as referências que ficariam `transient` são convertidas em índices:
  - `g.b.Ag`: dá a cada campeonato `best.at` dos dias do calendário um índice (`at.az`) e grava em cada `best.H` (estatística do jogador por campeonato, com `at Y` transient) o índice em `ft` (`H.gY`);
  - `g.b.Ai`: numera em sequência os jogadores profissionais (`SR.O()`, lista 1) e os juniores (`SR.Q()`, lista 2) com `F.az` e `F.aC`, e cada `best.ap` grava o índice e a lista do seu jogador (`ap.mb`);
  - o time de um jogador fica em `F.bW` (índice); a referência `F.eo` é transient. `best.al` (técnico) guarda o time do mesmo jeito.
- Gravação manual: no menu "Jogo → Salvar jogo" (atalho F2) de `a.eg`, `a.eg.ru()` pede um nome se `SR.bj` for nulo (diálogo `a.fw`) e abre `a.hz`. Esse diálogo inicia a thread `a.hB`, que chama `c.a.ae(SR.br())` fora da EDT com o diálogo modal aberto.
- Regras do nome (`a.fw.nH`):
  - de 1 a 15 caracteres, sem filtro de caracteres;
  - se `sav/<nome>.s22` já existe, pede confirmação para sobrescrever.

### 5.3 Autosave

Opção `autoSalvar` em `best.f`, com cópia em `est.Options` e rótulos em `a.fB.II[0]`:

| Valor | Rótulo | Regra (`best.f.ap`, ao voltar à tela principal com `bs` verdadeiro e `bL` falso) |
|---:|---|---|
| 0 | Não usar auto-save | — |
| 1 | A cada 3 jogos | Contador transient `bJ`: salva quando já está em 3 e então zera; senão incrementa. Na prática, salva a cada 4 retornos (inferido da lógica) |
| 2 | A cada jogo | Salva sempre |
| 3 | Início do ano | Salva quando o flag transient `bM` está ligado; `a.cR.pn` (fim de temporada) liga o flag |

O autosave usa o mesmo nome do save corrente (`a.eg.ru`). Se ainda não houver nome, `a.bz` (confirmação da escalação) chama `a.eg.rt()` para pedi-lo antes.

### 5.4 Carga (`c.a.c(nome, backup)`)

1. Relê `options.bcf` (`c.a.vI`).
2. Lê `.s22` (ou `.sbck`) com Kryo: o primeiro objeto vai para `c.a.SR`, o segundo para `c.a.afQ`.
3. Em caso de exceção:
   - se era o `.s22`, tenta o `.sbck`;
   - se o `.sbck` também falhar, `c.a.vK()` mostra "Arquivo inválido: save corrompido ou é de uma versão/build anterior.";
   - a chamada original devolve `false`.
4. Se ainda não existe janela principal (`best.n.db() == null`), religa o estado:
   - `g.b.Ah()`: `F.fg()` em profissionais, juniores e técnicos, que recupera o time pelo índice (`SR.x(bW)`);
   - `g.b.Af()`: renumera os campeonatos e liga cada `H` ao seu `at` pelo índice;
   - `g.b.Aj()`: `ap.me()` recupera os jogadores pelo índice e pela lista;
   - `SR.bs = true`, `SR.G()`, `new best.M(false)` (nomes), `SR.i(true)`, `new best.S(false)`, `SR.cb()` e `SR.ap()` (tela principal);
   - por fim fecha a tela inicial.
5. O diálogo `a.dN`:
   - lista os arquivos `sav/*.s22` (filtro `a.dS`);
   - mostra os dados do `.info`;
   - carrega depois de um `javax.swing.Timer` de 10 ms (`a.dR`);
   - "Deletar" apaga **só** o `.s22`, deixando `.sbck` e `.info`.

O caminho de carga com a janela já aberta (`a.eg.rd()` → `best.S.cX()`) não tem chamador encontrado (inferido: inacessível pela interface).

### 5.5 Objeto raiz `best.f` (o que vai para o save)

`best.f` (Serializable, UID 1) contém, entre outros:
- `ad` (InfoArquivoSalvoType);
- `ae` (temporada, começando em 1);
- `rM` (ano inicial, 2022 por padrão);
- `af` (índice do dia corrente no calendário);
- listas de jogadores profissionais (`ag`, `O()`), juniores (`ah`, `Q()`), times (`aj`, `P()`), técnicos (`al`, `L()`), técnicos humanos (`am`, `M()`), times humanos (`ak`, `aN()`), países em jogo (`ao`, `N()`), todos os países (`ap`, `aG()`), estaduais (`aq`, `aE()`), dias do calendário (`as`, `R()`, objetos `best.a`) e objetos `best.ap` (`au`, `bo()`);
- referências às competições internacionais (`f.r`, `f.v`, `f.u` etc.);
- cópia das opções (`jogaEstadual`, `autoSalvar`, `velocidade`, `verJint[21]` etc.);
- o nome do save (`bj`, `br()`).

Ficam fora do save por serem transient:
- `bx` (nomes de `ok_bra.txt`);
- `bC`–`bG` (dados da criação: `.ban` lidos, contagens, ligas candidatas, `.cfg`);
- `coresLista`;
- os contadores do autosave.

`best.ay` (UID 1, segundo objeto do save) guarda as listas da **Central de Empregos**: índices de times e países que alimentam ofertas a técnicos humanos (`ay.a`, `ay.b`, `ay.zj`, `ay.Ap`, `ay.Aq`; tela `a.gE`).

## 6. `options.bcf` (preferências globais)

- Serialização Java de `est.Options` (UID 1, 37 campos), na raiz da instalação. O `options.bcf` original (1.058 bytes) tem o mesmo descritor de 37 campos da classe.
- Lido por `c.a.vI()` no construtor de `c.a` e em cada carga. Se não existir, vale `new Options()`.
- Gravado por `c.a.vJ()` a cada mudança nas telas de preferências (`a.fB` e *listeners* como `a.fJ`–`a.fR`, `a.hW`–`a.ik`, `a.ju`, `a.aX`, `a.cx`, `a.do`, `a.dG`, `a.fZ`).
- Os *setters* de `Options` repassam o valor também a `c.a.SR`; por exemplo, `Options.setAutoSalvar` chama `SR.setAutoSalvar`. Uma preferência muda, portanto, o padrão das próximas carreiras e a carreira aberta.
- Campos:
  - competições: `jogaEstadual`, `jogaRegionais`, `jogaRegionaisTodos[4]`, `usaGrupoPadraoEstadual`, `jogaIntClubes`, `jogaIntano1`, `gruposIntPadrao`, `jogaSelecoesAll`, `jogaSelecoes[7]`, `UsarGruposReaisCopa`, `novoFormatoCopa`, `conviteRegionais` e `regionaisSemHumanos`;
  - exibição: `verJint[21]`, `verDecisaoPenNaoHumano`, `verMudancaTecnicos`, `verJanelaSubs`, `verEstaduaisAgrupados`, `verMundias`, `verSuperCopas`, `verLeiloes`, `ignoraLigas` e `ignoraEstadual`;
  - jogo: `salarioMensal`, `habilidadeIndividual`, `autoSalvar`, `velocidade`, `velocidadeNH` (6 níveis, de "Lento" a "Ultra rápido"), `avisoTerminoContrato` e `autoRenovaContrato`;
  - visual e som: `usaCorPlacar`, `corPlacar`, `usaSons`, `negritoCasa`, `usaCoresLista`, `coresLista` (`Color[]`) e `corTema` (0–4, ícones `/aiconsc/corTemaNs.png`).

Preferências fora de arquivo (`java.util.prefs`, no Windows sob `HKCU\Software\JavaSoft\Prefs`; inferido do comportamento padrão da JVM):
- nó `bfoptions`, chave `anoinicio` (0 = 2022, 1 = 2023), lida e gravada por `best.aq.am` e `best.aq.f`;
- dados de registro (§10).

## 7. Formatos dos arquivos de dados

Todos são fluxos `ObjectOutputStream` padrão (`AC ED 00 05`), com um objeto raiz. Na serialização Java, os campos aparecem no descritor e nos dados primeiro os **primitivos em ordem alfabética**, depois os **objetos em ordem alfabética**. Campos `transient` não são gravados.

### 7.1 `teams/<arquivo>.ban` — classe `e.t` (time), UID 16

Leitores:
- `best.U.a`: carreira, só `vid == 185` e `valid`;
- `d.av.e`: editor, só `vid == 185`;
- o nome do arquivo sem extensão sobrescreve `d` (`setFileRef`).

Escritores: `d.n.wo` e `d.n.c`, no editor, que fixa `vid = 185` e calcula `valid` (§7.3).

| Ordem | Campo | Tipo | Acesso | Significado |
|---:|---|---|---|---|
| 1 | `a` | int | `getPais` | País (índice do enum `best.ac`, 0–223; Brasil = 29) |
| 2 | `aid` | int | `getAid` | Identificador auxiliar (sempre 0 nos 703 originais; uso não encontrado) |
| 3 | `b` | int | `getEstado` | Estado brasileiro, índice de `best.aq.rX` (AC…TO, 27 siglas); só faz sentido com país 29 |
| 4 | `c` | int | `getNivel` | Nível de 1 a 25 no editor (padrão 15); nos originais vai de 6 a 20. Ordena a carga (`best.q`) |
| 5 | `g` | int | `getCapacidade` | Capacidade do estádio (o editor exige de 1.000 a 120.000) |
| 6 | `i` | int | `getTecNac` | Nacionalidade do técnico (país) |
| 7 | `id` | int | `getId` | ID do time (`ah.mY`); 0 em 282 dos 703 originais; o editor cria com 0 |
| 8 | `n` | int | `getReputacao` | 0–5: Municipal, Estadual, Regional, Nacional, Continental, Mundial (`best.aq.pZ`) |
| 9 | `o` | int | `getCorBase` | Cor de base (`ah.nl`); nos originais vai de 0 a 18 |
| 10 | `sid` | int | — | Sempre 0 nos originais; uso não encontrado |
| 11 | `tid` | int | — | Sempre 0 nos originais (no time); uso não encontrado |
| 12 | `valid` | boolean | `isValid` | Elenco válido: pelo menos 1 goleiro e 11 jogadores de linha |
| 13 | `vid` | int | `getVid` | Versão do formato; **185** é o único valor aceito |
| 14 | `cor1` | String | `getCor1` | Cor principal `#rrggbb` (convertida por `getCorF` com `substring`; outro formato gera exceção) |
| 15 | `cor2` | String | `getCor2` | Cor secundária `#rrggbb` |
| 16 | `d` | String | `getFileRef` | Nome-base dos arquivos (escudo, camisas); recalculado pelo nome do arquivo |
| 17 | `e` | String | `getNome` | Nome do time |
| 18 | `f` | String | `getEstadio` | Nome do estádio |
| 19 | `h` | String | `getTecnico` | Nome do técnico |
| 20 | `l` | ArrayList<e.g> | `getJogadores` | Elenco profissional (no editor, até 30) |
| 21 | `m` | ArrayList<e.g> | `getJuniores` | Juniores (no editor, até 15) |

Os campos `j` e `k` (`Color` em cache), `nomep` e `mark` são transient.

**Layout fixo.** Os 703 `.ban` originais têm os primeiros 202 bytes idênticos: o cabeçalho e o descritor de `e.t`, de `0x00` a `0xC9`. Os 11 inteiros `a`…`tid` ficam em `0xCA`–`0xF5` (big-endian), `valid` em `0xF6` e `vid` em `0xF7`–`0xFA`. Em seguida vêm as cadeias (`TC_STRING`, UTF modificado) e as listas. As listas são `java.util.ArrayList` padrão: o campo `size`, um bloco de dados de 4 bytes que repete o tamanho e, depois, os elementos. O primeiro `e.g` traz o descritor completo; os seguintes usam referência ao descritor (`TC_REFERENCE`). Tamanho dos originais: de 1.559 a 3.184 bytes.

### 7.2 Jogador — classe `e.g`, UID 16

| Ordem | Campo | Tipo | Acesso | Significado |
|---:|---|---|---|---|
| 1 | `aid` | int | — | Sempre 0 nos originais |
| 2 | `b` | boolean | `isEstrela` | Craque (16 jogadores nos originais) |
| 3 | `c` | int | `getPais` | Nacionalidade |
| 4 | `d` | int | `getIdade` | Idade (originais: 15–56, com dois registros em 0) |
| 5 | `e` | int | `getPosicao` | 0 goleiro, 1 lateral, 2 zagueiro, 3 meia, 4 atacante (`best.aq.rH`/`rI`) |
| 6 | `f` | int | `getStatus` | 0/1; o editor alterna e limita o valor 1 a 15 jogadores (`d.ap.Z`); `e.t.getNumeroTitulares` conta os 1. Semântica exata em Lacunas |
| 7 | `g` | int | `getCr1` | Característica 1 (índice de `best.aq.qN`) |
| 8 | `h` | int | `getCr2` | Característica 2 |
| 9 | `hash` | int | `getHash` | Escala de 0 a 10 (originais: 0–10, quase uniforme de 1 a 10). Vira `best.F.es` (`F.aq`), com valor forçado a 10 se for craque e > 8. Pesa em evolução e valor (`best.F`, `best.K`); inferido como "potencial" |
| 10 | `i` | int | `getLado` | 0 direito, 1 esquerdo (`best.aq.rK`/`rL`) |
| 11 | `j` | boolean | `isTopMundial` | "Top mundial" (0 nos originais) |
| 12 | `sid` | int | — | Sempre 0 nos originais |
| 13 | `tid` | int | — | Diferente de zero em 12.949 dos 14.672 profissionais; identificador do jogador (inferido) |
| 14 | `a` | String | `getNome` | Nome |

Características (`best.aq.qN`):

| Índice | Sigla | Uso |
|---:|---|---|
| 0 | Col | Colocação (goleiro) |
| 1 | DPe | Defesa de pênalti (goleiro) |
| 2 | Ref | Reflexo (goleiro) |
| 3 | SGo | Saída do gol (goleiro) |
| 4 | Arm | Armação |
| 5 | Cab | Cabeceio |
| 6 | Cru | Cruzamento |
| 7 | Des | Desarme |
| 8 | Dri | Drible |
| 9 | Fin | Finalização |
| 10 | Mar | Marcação |
| 11 | Pas | Passe |
| 12 | Res | Resistência |
| 13 | Vel | Velocidade |

O editor restringe goleiros aos índices 0–3 e jogadores de linha aos índices 4–13 (`d.f`).

Números dos originais (703 times):
- 14.672 profissionais e 1.175 juniores;
- de 17 a 28 profissionais por time;
- no máximo 15 juniores.

Conversão para o modelo (`best.ah(e.t)` e `best.F(e.g, boolean, ah)`):
- o time vira `best.ah`, e o técnico vira um `best.al` criado com nome e nacionalidade;
- cada jogador vira `best.F`, registrado em `SR.O()` (profissional) ou `SR.Q()` (júnior);
- o capitão inicial é o primeiro do elenco ordenado por `ah.nJ` (`ah.kz`).

### 7.3 Regras do editor embutido (pacote `d`)

- **Validação** (`d.n.b(e.t)`): `valid` exige pelo menos 1 goleiro e 11 jogadores de linha; `vid` é sempre 185.
- **Limites do formulário do time** (`d.ac.xd`):

  | Campo | Limite |
  |---|---|
  | Nome do time | 2–25 caracteres |
  | Técnico | 2–30 caracteres |
  | Estádio | 2–30 caracteres |
  | Nome do arquivo | 2–30 caracteres |

- **Criação de time** (`d.ac`):
  - novos times recebem `id = 0`;
  - a checagem de duplicidade procura `<nome>.b18`, que é a extensão antiga, enquanto a gravação usa `.ban`.
- **Jogador aleatório** (`d.n`):
  - `hash` de 7 a 10;
  - idade de 18 a 37 (profissional) ou de 16 a 19 (júnior);
  - nome por `best.M.k`.
- **Jogador manual** (`d.f`): `hash` de 1 a 10.
- **Importadores legados**, sem chamada a partir da interface do jogo:
  - `d.b.wj`: reserializa `.b16`/`.b18` de um diretório fixo do autor;
  - `best.P.iD`: lê XML de `teams2/` com as tags `n`, `p`, `nv`, `e`, `ec`, `t`, `es`, `r`, `cb`, `id`, `cf`, `ct` e, por jogador `jog`, `no`, `i`, `t`, `s`, `p`, `pa`, `l`, `c1`, `c2`, `ju`, `tl`.

### 7.4 `conf_ligas_nacionais/<SIGLA>.cfg`

- **Formato:** `est.ArrayLigaType` (UID 1), com um único campo `ArrayList a` de `est.ConfigLigaType` (UID 16, 23 campos).
- **Leitura:** `best.p.ds()` acumula, na criação, todas as `ConfigLigaType` de todos os `.cfg` em `SR.bG`.
- **Escrita:** `best.p.a(ConfigLigaType[], int pais)`, chamado pelo editor de liga `a.dG`.
  - Grava `<SIGLA do país>.cfg` com as divisões 1..n (ignora o índice 0 do vetor).
  - Substitui em `SR.bG` as entradas daquele país.
- **Campos, na ordem de serialização:**
  - primitivos:
    - `classificaPeloGeral`, `desempate`, `divisao`, `doisTurnos`, `formula`, `jogosDentroGrupo`, `melhoresTerceiros`;
    - `nGrupos`, `nRebaixados` (padrão 2), `nTimes`, `numeroTimesMataMata`, `pais`;
    - `playoffRebaixamento`, `rebaixadoPeloGrupo`, `rebaixadosDireto` (padrão 2), `vagasSobemPeloMataMata`, `valido`, `versaoArquivo`;
  - objetos: `duasVoltasMataMata` (boolean[7]), `duasVoltasMataMataSobe` (boolean[3]), `duasVoltasplayoffReb` (boolean[3]), `nome` e `nomeDivisao`.
- **Originais:** `BRA.cfg` e `ESP.cfg`, com 4 divisões cada (detalhes em `tools/competition-codec/README.md`).
- **Valores padrão:** `best.p.c` cria configurações de reserva, com `nTimes` 10 ou 20 e `nRebaixados` 2 ou 4.
- **Conversão:** `est.LoadLigaOptions` não é serializável. É a forma intermediária que o montador de liga usa ao converter a configuração.

### 7.5 `conf_estadual/<UF>.ces`

- **Formato:** `est.ArrayLigaEType` (UID 1), com `ArrayList a` de `est.ConfigEstadualType` (UID 1).
- **Campos de `ConfigEstadualType`:** `desempate`, `divisao`, `formula`, `id` (estado, índice de `best.aq.rX`), `nRebaixados` (padrão 2) e `finaisIdaVolta` (int[3], padrão {2, 2, 2}).
- **Leitura:** `best.w.ef()` lê todos os `.ces` para a lista estática `best.w.dv`.
- **Escrita:** `best.w.P(int estado)` grava `<UF>.ces`; o editor de estaduais é `a.cw`.
- **Uso da configuração:** cada estadual (`best.w`) consulta `best.w.g(estado, divisão)` para as divisões 1 a 4. Sem configuração, ou com uma fórmula que exige mais times do que o estado tem (`best.aq.sL[formula][0]`), usa o padrão.
- **Originais:** 25 arquivos, 432 bytes cada, sem PI e SE.
- **Importador XML legado:** `best.w.ds()` lê `conf_estadual/*.xml` com 8 inteiros separados por vírgula por elemento (`id`, `divisao`, `formula`, `nRebaixados`, `desempate` e as 3 finais). Não tem chamador.

### 7.6 Seleções

Não existe arquivo de elenco de seleção. A seleção é um `best.ah` criado sob demanda por `best.Z.jo()`, com `fileRef` nulo, as cores RGB do enum (`best.ac.jB`/`jC`) e nível e reputação do país. A pasta `selecoes/` guarda só imagens (§8).

## 8. Imagens, escudos, camisas, troféus e sons

| Recurso | Caminho | Reserva | Origem |
|---|---|---|---|
| Fundo principal | `img/f01.jpg`, relido a **cada** `paintComponent` | sem imagem (exceção ignorada) | `components.E` (modo 0) |
| Outros fundos | `img/f02.jpg` (leilão, `a.dz`; `a.cD`; `components.N`), `img/f03.png`, `img/f04.png` (`components.E`/`F`) | sem imagem; f03 e f04 não existem na instalação original | idem |
| Escudo do clube | `teams/escudos/<fileRef>.png` | seleção ou time sem `fileRef`: ver linha seguinte | `best.ah.L` |
| Escudo de seleção | `selecoes/escudos/<SIGLA>.png` | bandeira `/aflags/<id>.png` ou `/aflagslarge/flag_<id>.png` (jar) | `best.ah.L` |
| Escudo pequeno | `teams/escudosMini/<fileRef>.png` | escudo reduzido para 18 × 18 (`ah.kR`) | `best.ah.kQ` |
| Camisas 1/2/3 do clube | `teams/camisas/`, `camisas2/`, `camisas3/` + `<fileRef>.png` (`best.aq.tw`) | para camisas 1 e 2, camisa genérica do jar (`/acamisas/{preto,branco,vermelho,verde,azul,amarelo}.png`) pela cor dominante (`ah.bT`, com luminância 0,2126R + 0,7152G + 0,0722B e matiz HSB) | `best.ah.bU` |
| Camisas de seleção | `selecoes/camisas{,2,3}/<SIGLA>.png` (`best.aq.ty`) | idem | `best.ah.bU` |
| Troféus | `trofeus/<nome>.png` | `/aicons/trgen.png` | `best.aq.x`, `a.de` |
| Sons | `sons/{intervalo,fimjogo,gol1,goladv,penalty,expulsao,contusao}.wav` (índices 0–6) | sem som | `c.a.vH`/`c.a.dj`, tocados em `a.dV` por `javax.sound.sampled.Clip` |

Nomes de troféu (`a.de.a(best.ao)`), pelo tipo de campeonato:

| Tipo | Nome do arquivo |
|---:|---|
| 1 | `tr_nacional_<SIGLA>` (cai em `tr_nacional`) ou `tr_nacionalgenerico` |
| 2 | `tr_copa_<SIGLA>` (cai em `tr_copa`) |
| 3 | `tr_estadualgenerico` |
| 4 | `tr_ligacampeoes`, `tr_libertadores`, `tr_ligacaf`, `tr_ligaafc`, `tr_ligaconcacaf`, `tr_ligaofc` |
| 5 | `tr_mundial` |
| 6 | `tr_ligaeuropa`, `tr_sulamericana` |
| 8 / 9 | `tr_recopaeuropa`, `tr_recopasulamaericana` (grafia do jogo) |
| 10 | `tr_riosaopaulo`, `tr_sulminas`, `tr_copanordeste`, `tr_copaverde`, `tr_nacionalgenerico` |
| 11 | `tr_supercopa` |

Contagens na instalação original:
- 703 escudos e 702 escudos pequenos;
- 336, 334 e 11 camisas (1, 2 e 3);
- 62 e 61 camisas de seleção;
- nenhum escudo de seleção;
- 72 troféus e 7 sons.

Os índices de `aflags` são os do enum `best.ac` (224 países). Nesse enum, as constantes têm nomes ofuscados, mas o código as resolve por `valueOf("P" + id)`, o que indica que o nome lógico interno continua `P0`…`P223` (inferido). Cada país traz nome (chave de idioma), sigla de 3 letras (`jA`), id, código regional (`gg`), nível (`getNivel`) e duas cores RGB.

## 9. Threads, temporizadores e registro de erros

- **Threads explícitas:**
  - `main`;
  - a thread vazia de `best.as`;
  - `a.hB` (gravação do save).
- **Temporizadores:**
  - `javax.swing.Timer` em `a.dV.GO`, o relógio da partida: sem repetição, reagendado a cada minuto (ver `docs/live-match.md`);
  - `javax.swing.Timer` em `a.dN.GO`, o atraso de 10 ms da carga;
  - `java.util.Timer` em `a.bg`, `a.cD`, `a.cR`, `a.gb` (tela do pênalti), `a.gh` (escolha do batedor) e `a.hk`.
- **Laço principal:** não existe. O avanço do jogo segue a cadeia de eventos de interface:
  1. a tela principal (`a.eg`);
  2. o processamento do dia (`best.s.dx` abre a tela de partida com `S.aY(4)` quando há jogos e `SR.bs`);
  3. o fim da rodada (`best.f.at` → tela 5);
  4. o retorno à tela principal (`best.f.ap` → tela 2, com autosave);
  5. o fim de temporada (`best.f.ax` → tela 6).
- **Erros:**
  - `components.ar.uncaughtException` acrescenta (modo *append*) o *stack trace* em `erros.log`, no diretório de trabalho, cercado por `<html>` e com `<br>` antes de cada "at ", e também o imprime no `stderr`;
  - `components.ar.ao` cria um `File` `infoerro.txt` sem gravar nada (sem efeito);
  - o restante do código usa `printStackTrace()` (perdido sob `javaw`) e, nas falhas de *look and feel*, `java.util.logging`;
  - a carga de cada `.ban` ignora qualquer exceção em silêncio (`best.U.a`);
  - `System.out` imprime o tamanho da tela (`best.S`).
- **`System.exit`:** botão de sair da tela inicial (`a.gv`), "Sair do jogo" (`a.eg.rq`), editor (`d.r`), *harness* (`forms.j`) e a verificação de registro.

## 10. Licença e registro

O jogo tem uma versão não registrada e uma registrada. A registrada libera recursos listados pelo próprio jogo na tela de vantagens (`a.da`): estaduais e regionais, seleções, Copa Sul-Americana, fórmula do nacional, mais de um técnico humano, propostas por qualquer jogador e a velocidade mais rápida da partida. O registro é verificado na inicialização, fica guardado no perfil do usuário e não usa rede nem arquivo da instalação.

O mecanismo de verificação e os pontos do código que consultam o registro **não são documentados aqui de propósito**. O projeto não altera nem contorna o registro do jogo.

## 11. Tabela de classes do domínio

| Classe | Papel |
|---|---|
| `best.h2` | Ponto de entrada (`main`), verificação de registro, thread vazia |
| `best.h` | `main` alternativo de desenvolvedor (`forms.h`) |
| `best.as` | `Runnable` da thread iniciada no `main` (chama `best.C.ey`, vazio) |
| `best.C` | Balanço financeiro (receitas e despesas); `ey()` vazio |
| `best.M` | Idioma (`getString`), geração de nomes, carga de `ok_bra.txt` |
| `best.n` | Utilidades globais: lista de países ordenada, remoção de acentos, janelas raiz, *look and feel*, entrada do editor |
| `best.S` | Janela principal e troca de telas (`aY`), diálogos modais |
| `best.p` | Montagem da carreira: leitura de `.ban` e `.cfg`, ligas jogáveis, copas, regionais; grava `.cfg` |
| `best.U` / `best.V` | Leitor de `teams/*.ban` para a carreira / filtro `.ban` |
| `best.P` / `best.Q` | Importador XML legado `teams2/` / filtro `.xml` |
| `best.q` | Comparador de `e.t` por nível decrescente |
| `best.r`, `best.y`, `best.z` | Filtros `.cfg`, `.xml`, `.ces` |
| `best.w` | Campeonato estadual; leitura e gravação de `.ces` |
| `best.f` | **Objeto raiz da carreira** (`c.a.SR`), serializado pela Kryo; inclui cópia das opções |
| `best.ay` | Central de Empregos; segundo objeto do save (`c.a.afQ`) |
| `best.ap` | Registro que referencia um jogador, convertido em índice no save |
| `best.H` | Estatística do jogador num campeonato; referência ao campeonato convertida em índice |
| `best.Z` | País em jogo (ligas, seleção `jo()`) |
| `best.O` | Liga candidata a jogável na criação |
| `best.ac` | Enum dos 224 países (nome, sigla, região, nível, cores) |
| `best.ad` | Entrada da lista ordenada de países (`best.n.cF`) |
| `best.aq` | Constantes (posições, características, estados, reputações, gramado, caminhos de imagem) e utilidades de imagem/preferência |
| `c.a` | Estado global (`SR`, `afQ`, opções) e persistência: save, carga, `.info`, `options.bcf`, sons |
| `g.b` | Conversão de referências em índices antes de salvar e religação depois de carregar |
| `g.a` | `ArrayList` serializável auxiliar |
| `e.t` | Time no formato `.ban` |
| `e.g` | Jogador no formato `.ban` |
| `est.Options` | Preferências globais (`options.bcf`) |
| `est.InfoArquivoSalvoType` | Metadados do save (`.info`) |
| `est.ArrayLigaType` / `est.ConfigLigaType` | Arquivo `.cfg` / divisão nacional |
| `est.ArrayLigaEType` / `est.ConfigEstadualType` | Arquivo `.ces` / divisão estadual |
| `est.LoadLigaOptions` | Parâmetros intermediários de montagem de liga (não persistido) |
| `components.ar` | Tratador de exceções não capturadas (`erros.log`) |
| `components.E` | Painel de fundo com imagem de `img/` |
| `components.a` / `components.b` | Restrição e gerenciador de layout absoluto |
| `a.gq` (+ `a.gr`–`a.gv`) | Tela inicial e botões |
| `a.dN` (+ `a.dO`–`a.dU`) | Diálogo "Carregar Jogo Salvo" |
| `a.hz` / `a.hB` | Diálogo "Salvando/Carregando" / thread de gravação |
| `a.fw` | Diálogo do nome do save |
| `a.fB` | Tela de preferências (autosave, velocidades etc.) |
| `a.aa` | Diálogo de registro |
| `a.da` | Tela de vantagens da versão registrada |
| `a.de` | Sala de troféus (nomes de arquivo de troféu) |
| `d.n` | Editor de times (janela; grava `.ban`) |
| `d.ac` | Formulário de dados do time no editor |
| `d.f` | Formulário de jogador no editor |
| `d.ap` | Modelo da tabela de jogadores do editor |
| `d.av` / `d.aw` | Leitor de `.ban` para o editor / filtro |
| `d.b` | Conversor legado `.b16`/`.b18` (caminho fixo do autor) |
| `forms.h` | Janela de testes do desenvolvedor |
| `org.eclipse.jdt.internal.jarinjarloader.*` | Carregador dos jars aninhados |

## Lacunas

- **Semântica de campos do `.ban`:**
  - `e.g.f` (`status`): o editor o limita a 15 jogadores com valor 1, mas não ficou claro o efeito no jogo;
  - `e.g.hash`: o papel exato em `best.F.es` e `best.K` (potencial?) não foi confirmado;
  - `e.g.tid` e `e.t.tid`/`sid`/`aid`: não se achou leitura no jogo;
  - `e.t.c` (nível) e `e.t.o` (cor base): a influência na simulação não foi seguida.
- **Kryo:** o layout byte a byte de um `.s22` não foi descrito porque não há save de referência na instalação limpa. A descrição se baseia no código e nos padrões da Kryo 4.0.2.
- **Chamadores:** não foram achados para `c.a.ad`, `c.a.ag` (`.sb19`), `best.P.iD`, `best.w.ds()` e `a.eg.rd()`. Podem ser chamados por reflexão ou ser código morto (inferido: código morto).
- **`c.a.SU`:** a finalidade da preferência que o preenche é desconhecida; o valor não é lido.
- **Launch4j:** a versão mínima de Java e a configuração do diretório de trabalho não foram extraídas de forma estruturada (só por cadeias).
- **Autosave "A cada 3 jogos":** a frequência real (a cada 4 retornos) foi deduzida da lógica de `best.f.ap`, sem execução.
- **Filtro de jogos sem humano:** a regra que decide se um dia de jogos abre a tela de partida (`best.s.dx`) aparece aqui só no nível do fluxo; o detalhe pertence ao domínio de partida e calendário.
