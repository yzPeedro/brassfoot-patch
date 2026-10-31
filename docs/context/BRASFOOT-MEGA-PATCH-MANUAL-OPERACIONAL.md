# CLAUDE.md — CONTEXTO MESTRE, MANUAL OPERACIONAL E HISTÓRICO DE CONTINUIDADE

> **Projeto: Brasfoot Mega Patch**  
> **Versão do contexto:** 2026-10-31, revisão consolidada a partir de conversas deste projeto, registros compartilhados do Work e inspeção do GitHub conectado.  
> **Destinatário:** Claude Code / Claude com acesso ao checkout Windows, ferramentas de terminal e, quando houver, conectores de GitHub.  
> **Finalidade:** permitir entender a missão, as decisões, a situação de cada domínio, a operação de cada subsistema, as entregas públicas, as prévias privadas, tudo que foi iniciado e interrompido, e como retomar com segurança.  
> **Idioma padrão de trabalho:** português brasileiro.  
> **ALERTA:** este documento é um snapshot. Em toda sessão, **as mensagens mais recentes do usuário, o estado real do checkout, os manifestos, a release efetivamente publicada e o histórico mais recente do Work prevalecem sobre qualquer afirmação antiga aqui**. Nunca inventar verificação.

---

## 0. ORDEM DE LEITURA E REGRAS DE PRECEDÊNCIA (OBRIGATÓRIO)

1. Leia **integralmente este arquivo**, em particular as seções `ESTADO ATUAL`, `WORK EM ANDAMENTO` e `PROTOCOLO DE RETOMADA`.
2. Consulte mensagens e conversas novas do usuário, incluindo sessões do Work/Codex acessíveis. Não substitua evidência recente por memória resumida.
3. Inspecione `git status`, HEAD, branch, diferenças locais, arquivos não rastreados e processos em execução. **Não descarte mudanças de trabalho que ainda não foram commitadas.**
4. Leia `AGENTS.md`, `docs/current-state.md`, `docs/mega-patch-specification.md`, `docs/scheduled-maintenance.md`, `config/backlog.json`, `config/specification-coverage.json`, `config/edition.json`, `site/data/release.json`, `site/data/distribution.json` e notas da última release. Esses documentos são os contratos e checkpoints originais; possuem prioridades diferentes e podem estar defasados.
5. Compare HEAD local, `origin/main`, `gh-pages`, `releases/latest`, conteúdo publicado do site, e o último bundle **privado**. Um ZIP/EXE local e uma release pública são coisas diferentes.
6. Se houver conflito entre duas fontes, explique o conflito e resolva por **data, evidência verificável e escopo**. A requisição do usuário mais recente é a autoridade de produto, dentro dos limites técnicos/legais. O código e os manifestos atuais são a autoridade do estado implementado; testes e demonstrações são a autoridade da compatibilidade comprovada.
7. Prossiga com implementação quando solicitada, não apenas planejamento; não faça modificações destrutivas no jogo/saves. O usuário prefere solução completa em uma rodada e checkpoints objetivos quando uma operação longa é interrompida.
8. Não afirme possuir acesso às mensagens privadas de outras sessões, ao desktop, a uma conexão de rede, ao Work ou a serviços que não estejam realmente disponíveis no ambiente do Claude. Este Markdown transfere **contexto e procedimentos**, não permissões, identidade, ferramentas nem capacidades exclusivas de outra IA.
9. **Segurança operacional:** nenhum histórico antigo autoriza burlar licenças/DRM, distribuir jogos proprietários, coletar dados sem permissão, ignorar controles de acesso, ultrapassar cotas ou publicar credenciais. O projeto distribui atualizações/deltas para uma instalação legítima do jogo.

**Critério de honestidade:** diferencie `pedido`, `implementado`, `compilado`, `publicado`, `testado em fixtures`, `testado em Windows`, `homologado por usuário`, `não comprovado` e `bloqueado`. *Compilou* não significa *funciona no gameplay*. *Release publicada* não significa *escopo inteiro concluído*.

---

## 1. O QUE É O PROJETO E O QUE NÃO É

**Nome oficial público:** Brasfoot Mega Patch. O repositório manteve o slug histórico `brassfoot-patch` para não quebrar links. O produto é um **atualizador gratuito de uma instalação existente e legítima do Brasfoot 22–23**, inicialmente voltado à atualização do futebol brasileiro de 2026 e evoluído para uma plataforma de atualização mundial com catálogo, elencos, competições, seleções, ajustes do executável, gráficos, instaladores, site, releases e rotinas diárias.

**Não é** um novo jogo reescrito, uma cópia separada que apaga o original, um repack que distribui o jogo comercial, um app que depende da API-Football em cada máquina de usuário, nem um simulador totalmente novo. Preservar a experiência original do Brasfoot é requisito central. Alterações na interface ou no motor só podem ampliar a experiência sem quebrar regras, saves e licenças.

### 1.1 Fluxo ideal de uso para o jogador

1. O jogador tem o Brasfoot 22–23 instalado, normalmente em `C:\Brasfoot22-23`.
2. Acessa o site e baixa o atualizador compatível. No Windows, abre um **único executável de instalador com GUI**.
3. O instalador localiza/solicita a pasta **da instalação já existente**, mostra a versão, verifica assinaturas e integridade dos arquivos esperados, explica incompatibilidades em vez de modificar às cegas.
4. O instalador cria backup dos arquivos que vai trocar, preserva saves, configurações, ativação/licenças, preferências e o restante do diretório, calcula diferenças, aplica alterações atomicamente e oferece rollback automático em falha.
5. A UI exibe progresso verdadeiro, estados claros e botão de fechamento/restauração. Não surge uma janela inesperada de PowerShell/CMD. Há botão **Jogar** quando aplicável.
6. O jogador abre o **mesmo Brasfoot**, agora com elencos, competições, ano e demais modificações reconhecidas e documentadas. A ação **Restaurar original** deve funcionar.
7. O PIX para doação é opcional, discreto, não bloqueante. O produto continua gratuito.

### 1.2 Visão maior e escopo de longo prazo

O objetivo mestre não se limita ao Brasil. Quer um catálogo para países, clubes, seleções, treinadores, atletas, campeonatos nacionais, continentais e internacionais, temporadas, atributos e históricos verificáveis; coleta diária com proveniência; reconhecimento de mudanças; sincronização de patch/site; aplicações multi-plataforma para atualizar instalações compatíveis; identidade gráfica azul/celeste; ganhos de UX no jogo; automação autônoma com limites de quota e recuperação. **Suportar uma entidade no catálogo não significa que o jogo já a simule**. Há três níveis distintos: `catalogado`, `gerado para patch` e `jogável na engine`.

### 1.3 Links e caminhos confiáveis

- Repositório: `https://github.com/yzPeedro/brassfoot-patch`
- Branch de código: `main`
- Branch de publicação estática: `gh-pages`
- Site: `https://yzpeedro.github.io/brassfoot-patch/`
- Releases: `https://github.com/yzPeedro/brassfoot-patch/releases`
- Última release (URL móvel): `https://github.com/yzPeedro/brassfoot-patch/releases/latest`
- Checkout Windows principal: `C:\Users\Pedro\projects\brassfoot-patch`
- Jogo local: `C:\Brasfoot22-23`
- Documentos de operações: `AGENTS.md`, `docs/current-state.md`, `docs/scheduled-maintenance.md`
- O projeto pode ter contextos da interface Work em `C:\Users\Pedro\Documents\ChatGPT\brassfoot patch`; **não confundir** com o checkout de produção.
- Diretórios históricos (`C:\Users\Pedro\brassfoot patch\...`) e arquivos ZIP experimentais podem existir, mas não são automaticamente a base atual.
- Locais de logs/estado: `data/private/continuity/`, `data/private/scheduled-maintenance/`, `data/private/daily/`, `dist/`; alguns são intencionalmente privados/ignorados pelo Git.

### 1.4 Ambiente e ferramentas

- Desenvolvimento principal em **Windows 11**, usando PowerShell, Python 3.12, Go 1.25, Java/JDK (`java`, `javac`, `javap`, `jar`), Git, `gh` autenticado, e ferramentas de análise de bytecode. Esses números de versão aparecem no README; confirme com `--version` no ambiente real.
- A arquitetura já possui Go (instaladores), Python (ETL, build, deltas, publicação, continuidade), Java/Java bytecode (jogo, serialização e modificações) e HTML/CSS/JavaScript (site).
- `gh auth status` e `git remote -v` verificam autenticação/remotos. **Nunca transcreva tokens, chaves, cookies ou conteúdos de `.env` para logs públicos**.
- Projetos não relacionados (Aimi, trabalho, Minecraft, máquina pessoal etc.) não são parte do Brasfoot Mega Patch. O pedido deste arquivo ocorre dentro do projeto Brasfoot e o contexto detalhado é deliberadamente restrito a ele.

---

## 2. ESTADO PÚBLICO CONFIRMADO EM 31/10/2026

A inspeção direta do GitHub conectado durante a elaboração deste documento encontrou:

- **Release pública final/latest: `v2026.4.7`**, publicada em **31/10/2026**, `draft=false`, `prerelease=false`.
- `config/edition.json`: `PATCH_YEAR=2026`, `version=2026.4.7`, `channel=stable`.
- `site/data/release.json`: `status=published`, versão `2026.4.7`, `compatibilityVerifiedInGame=false`, `gameplayVerified=false`.
- Executável de instalador Windows publicado: `Brasfoot-Mega-Patch-2026.4.7-windows-x64.exe`, **5.470.720 bytes**, SHA-256 `6c0ebbaf082b95e651b40a6091666e764d7b672a4c8bf11496e87074dcb009f7`.
- Cinco artefatos versionados: Windows x64, Linux x64, Linux ARM64, macOS x64 e macOS ARM64; cinco aliases de download, catálogo compactado, `distribution.json`, `SHA256SUMS.txt`. **Esses utilitários multi-plataforma não representam ports nativos do jogo e Linux/macOS não foram homologados em gameplay**.
- Commit-fonte da release `2026.4.7`: `2d61dc557eb0a3988c20e2cc141fb263d46198ea` (de acordo com `docs/current-state.md`). Commits posteriores na main incluíram manifestos e confirmação da publicação; ao consultar, HEAD de `main` era `61511cc4` (`docs: confirm 2026.4.7 publication [skip ci]`). Não tratar o commit de metadados como o mesmo commit do bundle sem ler o manifesto.
- O documento `docs/current-state.md` afirma deploy `gh-pages` no commit `fd0ca2c6bbd2090f22d53735612583c33d8ae5f9` e Pages `built` para a 2026.4.7. Houve workflow de Pages com conclusão `success`. Revalide ao operar.
- O README ainda começava referindo-se à `release final 2026.4.1`. **Documentação legada pode estar defasada**; use a versão efetiva no GitHub/manifestos e corrija referências enganadoras quando apropriado.

### 2.1 Conteúdo público declarado pela 2026.4.7

O estado documentado é: **704 clubes** no jogo/catálogo de equipes, **300 elencos substituídos por fontes atuais na compilação**, 60 brasileiros e 240 internacionais, **54 elencos parciais preservados**, **350 sem fonte completa preservados**, 16.972 jogadores no total compilado, 8.644 atletas com fontes compiladas (`config/roster-build-2026.4.7.json`). A coleta de consulta do dia cobriu **342 clubes, 8.709 atletas**, sendo 288 fontes completas, 54 parciais, e 362 identidades sem fonte completa no universo geral. Contagens de `fonte consultada`, `elenco substituído` e `clube total` são diferentes e não devem ser misturadas.

A manutenção alterou materialmente 40 arquivos de clubes em relação à edição anterior e reavaliou flags de estrela e Top Mundial. `config/player-status-2026.json` registra uma regra atual de estrelas baseada no Top 10 masculino da Bola de Ouro 2026 e Top Mundial atribuído ao vencedor; **isto é a política interna do patch registrada no repositório, não validação independente dos fatos externos aqui**. O estado declara nove atletas marcados estrela dentro do catálogo e Harry Kane como Top Mundial, com remoção de sete flags herdadas. O sistema preservou identidades não mapeadas, sem inventar um clube para Lionel Messi.

A engine pública acumulou Copa do Mundo 2026 com 48 seleções, 12 grupos e avanço de melhores terceiros (versões 4.3/4.4) e priorização de participantes de seis copas continentais para a primeira temporada com fallback do motor quando faltam clubes/vagas (4.5). A `2026.4.3` provocou erro `VerifyError` de bytecode e foi substituída pela 4.4. **Nenhum teste funcional do jogo foi declarado na produção dessas releases**.

### 2.2 Histórico recente público resumido (não confundir com prévias do Work)

| Versão | Conteúdo/destaque | Observação |
|---|---|---|
| 2026.4.0 | base da arquitetura mundial, site e distribuidores multiplataforma | infraestrutura/catalogação não equivalem a cobertura total jogável |
| 2026.4.1 | entrega corretiva de elencos, ano 2026, múltiplas bases e instalador; 301 elencos então atualizados | README pode mencionar esta versão defasada |
| 2026.4.2 | manutenção de plantéis, mudanças normalizadas, cache e fallback | preservação de elencos parciais |
| 2026.4.3 | Copa do Mundo 2026, 48 seleções | gerou regressão de verificação JVM |
| 2026.4.4 | correção de `VerifyError` | não confundir inspeção do bytecode com jogo testado |
| 2026.4.5 | copas continentais, participantes oficiais existentes no catálogo | motor original preenche vagas não suportadas |
| 2026.4.6 | atualização diária de elenco, idades, posições | mantém executável anterior |
| 2026.4.7 | coleta de 31/10, transferências, idades e flags estrela/Top Mundial | última release pública verificada neste snapshot |

### 2.3 Matriz de progresso público por domínio

**Documento autorizado de cobertura:** `config/specification-coverage.json` ainda traz `edition=2026.4.0`, `fullSpecificationComplete=false`, 42 seções, muitas parciais. Todos os seus status de validação eram `not-run-at-owner-request` na inspeção. A cobertura deve ser atualizada/triangulada por código, release e prova real; não afirmar “100%” apenas porque algumas seções estão `implemented`.

| Domínio | Estado verificável | O que não se pode presumir |
|---|---|---|
| Atualizador Windows | existe EXE final + receitas de delta + backup/restauração no código | homologação total em todas as instalações e saves |
| Linux/macOS | distribuidores/atualizadores de arquiteturas publicadas | versão nativa do Brasfoot, compatibilidade Wine/CrossOver testada |
| Elencos Brasil A/B/C | 60 elencos de fonte compilados, conforme relatório público | toda elegibilidade, todo atributo e gameplay conferidos manualmente |
| Outras equipes | 704 no universo, 300 atualizados, 54 parciais, 350 sem fonte completa | todas as ligas do mundo jogáveis |
| Posições | mapeador converte laterais, zagueiros, meias, atacantes; lado existe | campo específico de pé dominante na engine |
| Ano 2026 | menu e seletor adaptados, segundo docs | próxima temporada, calendário e saves homologados |
| Mundial 2026 | modificações compiladas e publicadas | cada cenário de chaveamento verificado no jogo |
| Copas continentais | participantes iniciais prioritários conforme catálogo | torneios completos em todos os formatos históricos |
| Estrelas/Top Mundial | auditoria e flags compiladas na 4.7 | critério universal definitivo para todas as temporadas |
| Catálogo mundial | SQLite, snapshots, ingestão, proveniência, dados parciais | cobertura mundial integral e todos os clubes jogáveis |
| Site/SEO | publicado, identidade azul, catálogo/filtros, informações de download | que todas as interações foram testadas em navegador |
| Gráficos | pipeline de assets com licenças/cache e identidade visual | acervo completo licenciado e compatível com todos os clubes |
| Continuidade/autonomia | scripts e agendadores documentados | que toda tarefa local esteja ligada ou saudável neste exato momento |
| Campo de partida animado | **linha privada do Work, versões de prévia até 4.27** | não publicado na 4.7; não homologado; não presente na main pública |

### 2.4 O que está comprovadamente pendente

- Expandir fontes confiáveis e cobertura atual dos clubes sem plantel completo; não apagar atletas quando a fonte está incompleta.
- Validar de fato o jogo em Windows, salvamentos, próxima temporada, equipes, competições, atualização sobre versões anteriores, rollback e componentes gráficos; compatibilidade deve ser descrita com verdade.
- Concluir investigação e engenharia reversa para cobertura mundial **jogável**, além do catálogo, inclusive regras do motor e suporte a competições.
- Manter coerência dos atributos (posição, lado do campo, características, idade, estrelas) sem inventar dados.
- Evitar que o site prometa mais do que o patch realmente instala; acompanhar links, filtros, patch notes e metadados.
- Concluir e testar a linha **privada de visualização de partidas** antes de decidir sua integração numa release pública.
- Manter progresso granular por domínio e atualizar `config/specification-coverage.json`, que ainda aponta edição anterior.

---
## 3. MAPA DO REPOSITÓRIO — SUBSISTEMAS, ARQUIVOS E RESPONSABILIDADES

> Sempre abra o arquivo antes de modificá-lo. Os nomes e contratos descritos são baseados nos arquivos presentes na `main` pública em 31/10/2026; alterações locais privadas podem adicionar módulos. `--help`, assinatura real do código e manifesto têm precedência sobre exemplos deste manual.

### 3.1 Núcleo, configuração e documentação

| Caminho | Propósito | Como trabalhar |
|---|---|---|
| `AGENTS.md` | regras existentes de continuidade, autonomia, publicação e validação | ler antes de executar; preservar regras legítimas e atualizar se decisão mais recente mudar |
| `README.md` | introdução pública, instalação, dependências e comandos | corrigir versões defasadas; nunca confundir manifesto com README |
| `docs/mega-patch-specification.md` | especificação integral com 42 seções | contrato de escopo de longo prazo; não apagar nem resumir a fonte |
| `docs/current-state.md` | registro cronológico de releases, correções e limitações | atualizar depois de mudanças reais verificadas |
| `docs/implementation-progress.md` | engenharia reversa, laboratórios, problemas históricos e provas | distinguir protótipos de resultados atuais; preservar evidências |
| `config/edition.json` | produto, `PATCH_YEAR`, versão, canal e plataformas | origem central da identidade da edição e do build |
| `config/specification-coverage.json` | cobertura das 42 áreas da especificação | separar implementação, validação e operação; atualizar estado obsoleto |
| `config/backlog.json` | tarefas da continuidade, dependências, checks e responsáveis | não marcar concluído sem artefato e evidência |
| `config/mega-patch-specification.json` | proveniência/hash da especificação mestre | não alterá-lo sem manter consistência |
| `config/sources.json` | feeds públicos, limites, agenda, descritores de competições | validar fontes, licenças, timestamps e intervalos |
| `data/private/**` | cópias proprietárias locais, caches, executáveis de referência, logs, estados | NÃO publicar no Git; nunca subir binários proprietários, saves ou segredos |
| `output/**`, `dist/**` | relatórios/artefatos gerados | distinguir protótipo e pacote autorizado; verificar hashes |
| `.github/workflows/**` | jobs de dados, distribuição, Pages, CI | conferir política de cotas e evitar CI não desejada quando instruído |

### 3.2 Código de coleta, banco e sincronização

| Arquivo | Entrada | Operação e saída |
|---|---|---|
| `tools/fetch_sources.py` | URLs/configuração/cache | transporte/cache e validação de fontes permitidas; salva último conteúdo confiável |
| `tools/daily_sources.py` | cache local estruturado | fronteira offline de ingestão e validação de proveniência, tamanho e limite |
| `tools/daily_update.py` | `config/sources.json`, feeds, tabelas locais | normaliza fixtures OpenFootball, catálogo SQLite, snapshots/diffs, relatório de cobertura; **não altera `.ban` ou EXE do jogo** |
| `tools/daily_maintenance.py` | estado diário e fonte/config | controla horário, lock, repetição, retry e status; chama `daily_update.run` |
| `tools/world_catalog.py` | países, associações, clubes, competições, temporadas, pessoas | SQLite, IDs estáveis, vínculos, `catalog/generated/playable` e proveniência |
| `tools/world_snapshot.py` | dados normalizados e snapshot anterior | snapshots determinísticos, diff por conteúdo, recuperação de fonte indisponível |
| `tools/collect_live_rosters.py` | catálogo original + mapa de times + páginas públicas/cache | coleta limitada de plantéis e posições observadas; saída versionada como JSON; `--refresh` e cache 18h |
| `tools/compile_live_rosters.py` | EXE/jogo de base, original, snapshot, suplementos, Java | serializa/atualiza plantéis numa **pasta de saída**, sem editar jogo instalado; gera relatório |
| `tools/roster_position_map.py` | posições observadas | mapeamento correto de goleiro/lateral/zagueiro/meia/atacante, lados e ambiguidades |
| `tools/audit_roster_readiness.py` / `tools/audit_official_roster_tsv.py` | elencos e mapeamentos | auditam completude, identidade e consistência; não promovem chute a fato |
| `tools/export_release_rosters.py` / `tools/export_patch_clubs.py` | arquivo compilado e snapshots | regeneram dados públicos do site e cobertura a partir dos dados realmente compilados |
| `api_football_sync.py`, `sync-api.ps1`, `quota_guard.py` | integração histórica API-Football | **API desativada por padrão**; não introduzir consumo de quota nem dependência de chave em ciclo diário |
| `catalog.py`, `collect_abc_rosters.py`, `roster_to_tsv.py` | utilitários históricos | validar se substituídos antes de usar; evitar dados obsoletos e fluxo paralelo divergente |

### 3.3 Engenharia reversa, compilação, competições e ano

| Arquivo/módulo | Função | Cuidado especial |
|---|---|---|
| `tools/patch_official_career_year.py` | adapta seletor de carreira em classe reconhecida | é/foi prova de conceito por SHA exato; não substituir binário desconhecido |
| `tools/build_official_year_candidate.py` | montagem de candidato de EXE do ano 2026 | escreve fora da instalação; verifica recursos/bytecode |
| `tools/inspect_career_years.py`, `tools/trace_career_controls.py` | análise dos seletores, datas e APIs internas | evidências antigas podem referir-se a variante diferente do jogo |
| `tools/trace_national_league_routing.py` | rastreia como a engine monta divisões | verificar dados efetivamente consumidos, não somente listas visuais |
| `tools/build_bra_delta.py`, `tools/build_abc_team_map.py` | mapeamento/alteração das equipes A/B/C | preservar identidades e Série D original, sem substituição por nome genérico |
| `tools/build_bc_lab_deltas.py`, `tools/build_v4_roster_deltas.py` | laboratórios de arquivos B/C e elencos | laboratório não é release sem dados e compatibilidade comprovados |
| `tools/build_team_delta.py`, `tools/build_inplace_bundle.py` | gerar operações diferenciais sobre arquivos reconhecidos | preservar byte a byte os trechos não modificados |
| `tools/build_release_bundle.py` | transformar originais/bases/versões anteriores em receitas reversíveis multi-variante | **não redistribuir EXE integral**, manter cadeia de hashes, aceitar versões anteriores corretas |
| `tools/patch_world_cup_2026.py` | reconstruir EXE com Mundial de 2026 em classes reconhecidas | fonte esperada ligada à 4.2; evitar `VerifyError` e alterar classes não previstas |
| `tools/patch_continental_cups_2026.py` | priorizar participantes iniciais de torneios continentais 2026 | fonte esperada ligada à 4.4; fallback para vagas/clubes não suportados |
| `tools/world-cup-2026-src/**`, `tools/continental-cups-2026-src/**` | fontes Java para transformações | conferir compatibilidade de bytecode, frames e constantes |
| `tools/competition-codec/**` | leitura/escrita de formatos de competições | fazer round-trip e preservar estruturas não relevantes |
| `src/app/Main.java`, `tools/team-roster-editor/**` | suporte Java para compilação de dados do jogo | conferir JDK/versão do classfile, preservar enums/serialization UID |
| `config/world-cup-2026.json` | seleções/grupos e identidades do Mundial | evidência de participantes, grupos e regras; não inventar dados |
| `config/continental-cups-2026.json` | participantes iniciais de seis copas | formatos e ausências devem ser documentados |
| `config/brasfoot-country-names.json` | códigos de país internos | índices do jogo não são livremente intercambiáveis |
| `config/player-status-2026.json` | estrelas e Top Mundial por atleta exato | processar **inclusão e remoção** de flags antigas; casar identidade e clube |
| `config/rosters-2026.4.7.json`, `config/roster-build-2026.4.7.json` | snapshot/report da release | carimbos/data, saídas e limitações da edição específica |
| `config/live-roster-team-map.json`, `config/live-rosters-supplement.json` | mapeamento estável e suplementação | evitar cruzar clubes homônimos e usar suplemento antigo como fonte atual |
| `config/transfer-windows-2026.json` | regras/janelas de transferências | separar rumor, negociação e inscrição confirmada |
| `tools/history_records.py` | histórico externo versus simulação | jamais misturar premiação real com campeonato simulado |

### 3.4 Instalador, distribuição e publicação

| Arquivo | Papel |
|---|---|
| `windows-installer/main_windows.go`, `main_other.go` | entrypoints da aplicação por plataforma |
| `windows-installer/engine.go` | motor de instalação e verificação de receitas |
| `windows-installer/bundle.go` | embed/leitura do manifesto e deltas |
| `windows-installer/restore.go`, `replace_windows.go`, `replace_nonwindows.go` | backup, restauração, substituição e rollback por sistema |
| `windows-installer/edition.go`, `diagnostic.go` | versão, erros/códigos de diagnóstico, informações da distribuição |
| `windows-installer/pix.go`, `pix_windows.go` | PIX discreto opcional |
| `windows-installer/assets/**` | ícone, visual e recursos da interface |
| `windows-installer/bundled_release/**` | pacote embutido usado no build legado/atual | 
| `installer/engine.py`, `installer/gui.py` | motor/UI históricos Python/Tk; **não assumir que são o atualizador final Go vigente** |
| `tools/build_distribution.py` | compila cinco pacotes a partir de bundle explícito e `config/edition.json`; agrega hashes, snapshot e source commit |
| `tools/publish_distribution.py` | publica com `gh`, verifica assets/digests, marca release final, atualiza manifestos do site |
| `tools/publish_pages.py` | publica `site/` via worktree temporário em `gh-pages` e solicita build Pages |
| `release.ps1` | orquestra coleta/build e opcionalmente publicação; recebe `-PackagePath`, `-OutputDirectory`, `-Publish`, `-PublishExisting` |
| `scripts/run-daily-data.ps1` | wrapper diário de `python -m tools.daily_maintenance`, log em `data/private/daily/` |
| `scripts/install-daily-data.ps1`, `scripts/configurar-ciclo-windows.ps1` | configuração do Task Scheduler, conforme variante local |
| `scripts/run-continuity.ps1`, `tools/continuity_service.py` | coordenação/orquestração local com estado, quota e workers |
| `tools/continuity.py`, `tools/codex_quota.py` | política de ondas, checkpoint, orçamento e quota |

### 3.5 Site

| Caminho | Responsabilidade |
|---|---|
| `site/index.html` | página principal, tabela e estrutura |
| `site/styles.css` | aparência azul/celeste, responsividade, campo de pesquisa, seleção, animações |
| `site/app.js` | interatividade, busca, filtros, ordenação, downloads, modais |
| `site/coverage.js`, `site/divisions.js` | visualização de cobertura e divisões |
| `site/pix.js` | fluxo e modal de contribuição opcional |
| `site/data/**` | catálogos JSON, elenco, equipes, competições, release, patch notes e cobertura |
| `site/como-instalar/**` | instruções de instalação e restauração |
| `site/compatibilidade/**` | limites e sistemas suportados |
| `site/versoes/**` | histórico público de versões |
| `site/robots.txt`, `site/sitemap.xml` | indexação/SEO |
| `site/tests/**` | testes de interface existentes, cuja execução estava dispensada em manutenção recente |

### 3.6 Recursos gráficos e extras

- `tools/graphics_pipeline.py`, `config/graphics.json`, `assets/`, `data/assets/`: conversão/cache de recursos autorizados, proporções, transparência, registro de origem/licença. Não raspar logotipos/imagens protegidos indiscriminadamente.
- `assets_audit.py`, `docs/assets-coverage.md`: auditoria de qualidade/cobertura de assets, não garantia de copyright.
- `scripts/inventory-competitions.ps1`, `scripts/collect-game-structure.ps1`, `scripts/collect-competition-configs.ps1`: inventários de estrutura e codecs históricos; usar cópias isoladas.
- `docs/architecture.md`, `docs/data-pipeline.md`, `docs/patch-format.md`, `docs/security.md`, `docs/troubleshooting.md`, `docs/platform-distribution.md`, `docs/graphics-pipeline.md`: manuais complementares; ler sempre que mexer no domínio correspondente.
- `tests/**`, `windows-installer/*_test.go`: suites e fixtures de legado/engenharia; scripts históricos documentam o funcionamento mesmo quando execução de testes foi dispensada. Nenhum `skip ci` deve ser confundido com verificação de qualidade.

---

## 4. TUTORIAL OPERACIONAL DETALHADO — COMO RETOMAR QUALQUER TRABALHO

### 4.1 Etapa zero: preflight, sem modificar nada

Abra PowerShell no Windows. **Os comandos abaixo são de diagnóstico no ambiente de desenvolvimento, não comandos para aparecer na tela do usuário final.**

```powershell
Set-Location 'C:\Users\Pedro\projects\brassfoot-patch'
Get-Location
Get-Date
Get-Command git, gh, python, go, java, javac, javap, jar -ErrorAction SilentlyContinue | Select-Object Name,Source
python --version
go version
java -version
git status --short --branch
git remote -v
git branch -vv
git log -8 --oneline --decorate
git diff --stat
git diff --check
gh auth status
gh release view --repo yzPeedro/brassfoot-patch --json tagName,isDraft,isPrerelease,isLatest,publishedAt,assets
Get-Content -Raw AGENTS.md
Get-Content -Raw docs\current-state.md
Get-Content -Raw config\edition.json
Get-Content -Raw site\data\release.json
Get-Content -Raw config\backlog.json
```

Se uma flag não for aceita pela versão atual do `gh`, veja `gh release view --help` e adapte a consulta, sem inventar resultado. Acesso ao GitHub pode estar indisponível. **Não rode `git reset --hard`, `git clean -fd`, `git checkout .`, `git stash pop` ou `git pull` sem conferir alterações existentes**. Se a branch tiver trabalho local do Work, registrar/continuar antes de atualizar a base.

Confirme o jogo/EXE em disco sem iniciá-lo:

```powershell
$game='C:\Brasfoot22-23'
if (Test-Path "$game\bf22-23.exe") {
  Get-Item "$game\bf22-23.exe" | Select-Object FullName,Length,LastWriteTime
  Get-FileHash -LiteralPath "$game\bf22-23.exe" -Algorithm SHA256
}
Get-CimInstance Win32_Process | Where-Object {
  $_.Name -match '^(java|javaw|bf22-23|brasfoot).*\.exe$'
} | Select-Object ProcessId,Name,CommandLine
```

NUNCA encerrar processos inesperadamente nem instalar prévias automaticamente. A pasta pode conter saves ou binários proprietários. O hash instalado deve ser comparado com o conjunto de variantes aceitas no **manifesto efetivo da build que se pretende instalar**.

### 4.2 Etapa 1: escolher exatamente o tipo de atualização

Determine o escopo antes de compilar:

1. **Dados públicos apenas**: `daily_update` atualiza catálogo/snapshot, não `.ban` do jogo. Sem mudança material, não criar nova release.
2. **Dados dos jogadores do jogo**: coleta e compila `.ban`, gera deltas e distribuição; exige fontes e identidade dos clubes.
3. **Engine/competição**: altera EXE Java em cópia isolada, gera bundle, instalador; exige matriz de hashes e proteção contra regressões.
4. **Site somente**: HTML/CSS/JS/dados públicos e deploy `gh-pages`, sem inventar atualização do EXE.
5. **Feature experimental do Work**: prévia privada para testes do usuário, sem release nem site, mesmo que exista autorização geral de publicar mudanças. **A restrição mais recente da feature de campo animado é explícita: não publicar.**
6. **Release final de produto**: commit de código, build rastreado, assets, release, manifestos e site, nesta ordem, após verificações exigidas para a mudança.

### 4.3 Etapa 2: ler a especificação de produto relevante

Para qualquer tarefa, faça uma trilha curta de evidência: intenção do usuário -> requisito da especificação -> arquivos existentes -> dados base -> saída esperada -> risco e rollback. Se o domínio tem documentação antiga contraditória, explique e atualize a documentação, não reutilize a receita cegamente. **Não reinicie auditorias antigas sem investigar resultados existentes**.

### 4.4 Etapa 3: editar em pequenos grupos isolados

- Faça uma alteração coerente por vez; diffs revisáveis; preserve todos os arquivos não relacionados.
- Se um trabalho é multiagente, cada worker deve receber apenas os arquivos que pode alterar, checks e meta; nenhum worker publica. O coordenador integra e publica depois.
- Evite mais de dois workers simultâneos no PC de 16 GB; preferência histórica por modelos econômicos, Alethe `savings`, perfil `economy` e escritor único. Nenhum modelo é obrigatório se não existir no ambiente.
- Não introduza chaves pagas, quotas novas ou serviços cobrados sem permissão.
- Mantenha logs textuais curtos e checkpoints persistentes em `data/private/**`; não polua o repositório com telemetria, dados temporários ou binários proprietários.
- Para commits de mudanças completas, revisar `git diff --check`, os arquivos afetados, o estado da build, os efeitos sobre versões anteriores e os manifestos. Histórico de commits costuma usar `feat(...)`, `fix(...)`, `docs(...)`, `release:` e `[skip ci]` onde apropriado.

### 4.5 Etapa 4: medir progresso sem enganar

Para cada pedido, criar checklist com colunas: `requisito`, `arquivo/commit`, `compilado`, `validado`, `publicado`, `homologação gameplay`, `bloqueio`, `próximo passo`. Medir percentuais pelo número de critérios de aceite ponderados **e declarar o método**, não chutar 95%. Separar `implementação`, `qualidade/validação` e `operação/publicação`.

---

## 5. COMO FAZER CADA TIPO DE UPDATE — PLAYBOOKS COMPLETOS

### 5.1 Manutenção diária do catálogo mundial (não altera o jogo)

**Objetivo:** renovar feeds públicos configurados, preservar dados confiáveis, atualizar SQLite/snapshot e cobertura, detectar mudanças sem gastar API paga.

1. Leia `config/sources.json`, `tools/fetch_sources.py`, `tools/daily_update.py`, `tools/daily_maintenance.py` e `docs/daily-update.md`.
2. Confira URLs, licenças e o relógio `America/Sao_Paulo`.
3. Leia `data/private/daily/maintenance.json`, `snapshot.json`, `world-status.json` quando existirem, e o cache; não apague cache de recuperação.
4. Faça execução produtiva autorizada (rede pública disponível) ou offline quando a fonte não puder ser acessada:

```powershell
Set-Location 'C:\Users\Pedro\projects\brassfoot-patch'
python -m tools.daily_update
# Ambiente sem rede, apenas se precisar reproduzir o cache existente:
python -m tools.daily_update --offline
# Wrapper diário com lock, janela e retry:
python -m tools.daily_maintenance
```

5. Examine status, erro por fonte, snapshot, hash de conteúdo, lacunas e alteração material; se erro, preservar último dado conhecido. `daily_update` **não substitui nem gera automaticamente elencos jogáveis**.
6. Se não houve mudança material, registre a consulta e termine **sem bump/release artificial**. Se mudou apenas o site, publique somente o site se apropriado.
7. O `daily_maintenance.py` usa lock, data local, horário de `config/sources.json`, `completedDate`, retry de 1h para fontes falhas e 30min para exceção. Isso é coleta, não motor autônomo de desenvolvimento de código.

### 5.2 Atualização real dos elencos do Brasfoot

**Objetivo:** identificar e efetivar transferências confirmadas, saídas, posições, lados, idades, treinadores e status no formato de arquivos que o jogo carrega. Não usar simples troca de texto em tabela web como se fosse atualização do jogo.

1. **Definir universo**: usar catálogo compilado do patch (704 no snapshot 4.7), não apenas clubes com fontes completas. Cada clube precisa de estado `fonte completa`, `parcial`, `indisponível`, `sem identidade`, `inalterado`, `alterado`.
2. **Fonte**: priorizar páginas oficiais/CBF/federações; usar 365Scores como preferência editorial de conferência de elencos/posições, se permitido pelas condições da fonte; evitar raspagem em massa não autorizada. API-Football desativada por padrão. Não afirmar transferências por rumores, não assumir ausência de elenco parcial como saída.
3. **Revisar mapeamento estável** entre ID da fonte, clube do jogo, nome, país e arquivo `.ban` em `config/live-roster-team-map.json` e `config/brasfoot-country-names.json`. Homônimos exigem identidade inequívoca.
4. **Coletar novo snapshot sem descartar fallback**:

```powershell
python tools/collect_live_rosters.py --help
# Exemplo estrutural, troque os caminhos por bases locais que EXISTEM:
python tools/collect_live_rosters.py `
  --original-catalog 'CAMINHO_PRIVADO_DO_CATALOGO_ORIGINAL.json' `
  --output 'config/rosters-2026.N.N.json' `
  --mappings 'config/live-roster-team-map.json' `
  --cache 'data/private/live-roster-cache' `
  --cache-max-age-hours 18 `
  --refresh
```

O script requer `--original-catalog`, recebe `--output`, `--cache`, `--mappings`, `--cache-max-age-hours`, `--refresh`; **não passar um caminho inventado como se houvesse arquivo**. Verifique parâmetros reais com `--help`.

5. **Comparar com última versão publicada**, por identidade normalizada, não por posição/ordem/timestamp; gerar diffs de entradas, saídas, trocas, nomes, idade e função. Se a informação é incompleta, preservar o elenco anterior.
6. **Compilar em cópia isolada** com base privada reconhecida, original reconhecido, fallback anterior, snapshot novo, suplementações e data de Brasília:

```powershell
python tools/compile_live_rosters.py --help
# Modelo de execução; substituir placeholders por caminhos verificados:
python tools/compile_live_rosters.py `
  --base-game 'BASE_PRIVADA_RECONHECIDA' `
  --original-game 'ORIGINAL_PRIVADO_RECONHECIDO' `
  --fallback-game 'ULTIMA_BASE_PRIVADA_PUBLICADA' `
  --output 'data/private/compiled-2026.N.N' `
  --snapshot 'config/rosters-2026.N.N.json' `
  --supplement 'config/live-rosters-supplement.json' `
  --version '2026.N.N'
```

7. **Posições Brasfoot** observadas/documentadas: `0=goleiro`, `1=lateral/ala`, `2=zagueiro`, `3=volante/meia`, `4=atacante/centroavante/ponta`. Diferenciar lateral de zagueiro quando fonte diz apenas defensor. `lado` direito/esquerdo do jogo **não é prova de pé dominante**. Preservar atributos existentes quando não há evidência; características derivadas por função são defaults, não fatos. Idade via nascimento quando disponível e data de referência, sem aumento arbitrário.
8. **Nomes**: na regra vigente, jogadores com três ou mais palavras são exibidos com as duas primeiras. Não mudar essa política por acidente.
9. **Flags estrela/Top Mundial**: ler `config/player-status-2026.json`, garantir correspondência única (jogador+clube+variante), adicionar e **remover marcações erradas** nos dois sentidos; registrar fonte e critério. Um critério anual de prêmio não necessariamente mede toda a qualidade de jogadores do mundo; se o usuário alterar a política, atualizar parser/testes/dados e explicar impactos.
10. **Validar artefatos**: contagem de jogadores, identidade da equipe, hashes das saídas e atributos modificados, cobertura e ausência de sobrescrita de saves/configuração. Se autorizado realizar testes, incluir roundtrip, fixture e gameplay; no histórico recente o usuário dispensou testes de manutenção, então documentar claramente o que não rodou.
11. **Gerar os dados públicos a partir do compilado**, não de planilha histórica: `tools/export_release_rosters.py`, `tools/export_patch_clubs.py`; ler as flags e argumentos reais antes. Atualizar `site/data/roster-coverage.json` e patch notes com números honestos.
12. **Gerar bundle, distribuição, publicação e site** se alteração material aprovada para release final, conforme seções 5.5–5.7.

### 5.3 Atualização de divisões do Brasil A/B/C/D

Requisito histórico inicial: **Séries A, B e C 2026 com 20 clubes cada e Série D preservada na forma original da instalação**, não sobrescrever os arquivos da Série D ao corrigir A/B/C. A organização oficial de 2026 e a capacidade do Brasfoot são fatos diferentes; histórias de 96 participantes oficiais da Série D e de 64/8 grupos no `BRA.cfg` original devem ser explicitamente distinguidas. **Nunca declarar que a Série D do jogo possui 96 se não for demonstrado**.

1. Consulte dados oficiais de federações e documentos `docs/divisions-2026.md`, `docs/team-mapping.md`, `docs/engine-acceptance.md`.
2. Identifique SHA de cada arquivo real antes de aplicar transformações. O Brasfoot 22–23 original analisado tinha 196 equipes brasileiras, 703 `.ban`; um Maranhão 2026 sem original conhecido exigiu laboratório e não pode ser confundido com origem oficial.
3. O campo serializado `e.t.c` foi identificado como relacionado à classificação da divisão: originais A `16..19`, B `12..15`, C `10..11`; as listas de clubes eram derivadas de objetos, não apenas combo fixo.
4. Use `tools/trace_national_league_routing.py`, `tools/build_abc_team_map.py`, `tools/build_bra_delta.py`, editor Java e mapeadores por ID/SHA. Reconfigure a participação real no motor, não apenas no seletor visual.
5. Gere candidatos em pasta temporária, preserve `BRA.cfg`/Série D e os saves, verifique equipe e classificação, crie bundle reversível. Verifique calendário, promovidos/rebaixados, próxima temporada, competições e a possibilidade de uma carreira passar de 2026 para 2027.
6. Releases antigas que mexeram na Série D ou inseriram times fictícios foram consideradas inadequadas. Não ressuscitar sem evidência.

### 5.4 Ano de carreira, Copa do Mundo e copas continentais

**Ano 2026 único na interface de nova carreira** foi pedido explicitamente. O ano inicial, calendários internos, selector e valores nos arquivos podem estar em classes diferentes; `year` de interface não garante temporadas corretas. Preservar anos históricos verdadeiros.

**Mundial 2026:** o módulo `tools/patch_world_cup_2026.py` usa `--source-exe` e `--output-exe`, além de `--java`, `--javac`. Segundo código, é travado por fingerprint da 4.2 e reconstrói quatro classes numa cópia de EXE. O `config/world-cup-2026.json` declara participantes e grupos. Na 4.3 uma classe obteve `VerifyError: Expecting a stack map frame`; a 4.4 corrigiu repondo método Java válido. Procedimento:

```powershell
python tools/patch_world_cup_2026.py --help
# SOMENTE com EXE de fonte cujo SHA foi reconhecido:
python tools/patch_world_cup_2026.py `
  --source-exe 'CAMINHO_VERIFICADO_EXE_BASE_4_2' `
  --output-exe 'CAMINHO_NOVO_CANDIDATO_EXE'
```

**Copas continentais 2026:** `tools/patch_continental_cups_2026.py` parte de EXE 4.4 reconhecido e compila classes auxiliares a partir de `config/continental-cups-2026.json`. Trata Libertadores, Sul-Americana, Champions League, Europa League, Conference League e Champions Cup da Concacaf; usa clubes oficiais encontrados no catálogo e o seletor antigo como fallback para ausentes e vagas restantes.

```powershell
python tools/patch_continental_cups_2026.py --help
python tools/patch_continental_cups_2026.py `
  --source-exe 'CAMINHO_VERIFICADO_EXE_BASE_4_4' `
  --output-exe 'CAMINHO_NOVO_CANDIDATO_EXE'
```

**Importante:** não pegar os dois comandos e executá-los sequencialmente em qualquer EXE novo; cada transformador checa SHA e versão de classe, deve ser adaptado explicitamente quando a base evolui. Confirmar compatibilidade de classfile Java e não replicar o bug da 4.3. A build 4.7 manteve o EXE da 4.5 enquanto atualizava `.ban`.

### 5.5 Construir bundle de delta reversível para versões anteriores

`tools/build_release_bundle.py` recebe diretórios de `original`, `base`, lista de `previous`, `teams`, executável compilado, `destination`, `version` e opcional `inherit_bundle`. A CLI contém `--previous` repetível. Gere output **novo** e em pasta privada, preservando o jogo proprietário fora da distribuição. O bundle deve conter `manifest.json`, `patches/`, variantes reconhecidas por SHA e operação de copiar/inserir; o gerador limita literais do EXE a 30% para evitar distribuir grande parte do jogo.

O formato atual de manifesto produzido por esse gerador é `schemaVersion=4`, `kind=BRASFOOT_RELEASE_PATCH`, `channel=stable`, `publicationAllowed=true`, `compatibilityTestedInGame=false`, `tests=not-run-at-owner-request`. **Marcadores no JSON não são prova independente de testes e não autorizam distribuir código proprietário**.

```powershell
python tools/build_release_bundle.py --help
# Exemplo conceitual; confirme cada caminho e a sintaxe de --help:
python tools/build_release_bundle.py `
  --original 'DIRETORIO_ORIGINAL' `
  --base 'DIRETORIO_BASE' `
  --previous 'DIRETORIO_PUBLICADO_ANTERIOR' `
  --teams 'DIRETORIO_TEAMS_COMPILADOS' `
  --executable 'EXE_DE_JOGO_COMPILADO_EM_COPIA' `
  --destination 'data/private/release-bundle-2026.N.N' `
  --version '2026.N.N'
```

**Cuidado:** nomes exatos dos argumentos devem vir do `--help` real; a fonte de 31/10 definia `--` + nome do campo de destino. Inclua o `--inherit-bundle` quando for necessário manter variantes legadas. Gere cadeia correta quando o target de uma etapa é origem da próxima; nunca construir `steps` aninhadas sem observar como o instalador Go executa cada variante. O trabalho privado de animação sofreu `BF-199` por encadeamento incorreto.

### 5.6 Compilar instaladores finais e manifestos

Com `config/edition.json` atualizado, bundle recém-gerado validado, source commit selecionado e Go disponível:

```powershell
python tools/build_distribution.py --help
python tools/build_distribution.py `
  --bundle 'data/private/release-bundle-2026.N.N' `
  --output 'dist/2026.N.N' `
  --edition 'config/edition.json' `
  --snapshot 'data/private/daily/snapshot.json'
# Build apenas Windows para prévia privada (NÃO para release final de cinco plataformas):
python tools/build_distribution.py `
  --bundle 'data/private/preview/bundle' `
  --output 'dist/preview-2026.N.N' `
  --edition 'config/edition-preview.json' `
  --target windows/amd64
```

O compilador aceita `--source-commit` e `--target` repetível. O próprio código exige versão `ANO.N.N`, compatível com `PATCH_YEAR`; customiza `GOOS`, `GOARCH`, `CGO_ENABLED=0`, `-trimpath` e em Windows `-H=windowsgui` para **não abrir console**. Adiciona `build-info.json`, checksums, pacote de catálogo quando fornecido e anexos. O jogo original **não** é colocado no instalador.

Os cinco targets no estado 4.7: `windows/amd64`, `linux/amd64`, `linux/arm64`, `darwin/amd64`, `darwin/arm64`. MacOS usa utilitário de console com seletor de pasta e não inclui Wine; builds cross-platform não são homologação de execução do jogo.

### 5.7 Publicar release completa e sincronizar site (quando autorizada)

**NÃO executar este playbook para a prévia privada da animação ao vivo.** Para mudanças públicas, há autorização permanente de publicação sem aprovação recorrente, concedida 28/10, exceto se a instrução específica pedir manter privado.

1. Confirmar mudança material, release anterior e versionamento novo, sem reutilizar tag. Atualizar edição, notas honestas, docs e dados públicos. **O `release.ps1` espera `docs/releases/v{versão}.md`, mas a nota pública 4.7 encontrada está em `docs/release-2026.4.7.md` e o caminho `docs/releases/v2026.4.7.md` não foi encontrado nesta inspeção.** Corrigir/verificar esse descompasso antes de usar `release.ps1`, sem sobrescrever notas existentes.
2. Revisar diffs, hashes, licença dos artefatos e ausência de segredos. Commit e push de **fonte** antes do build, usando `git add` limitado aos arquivos da mudança, depois `git commit` e `git push origin main`. Não abrir PR por padrão neste repositório pessoal; respeitar regras do repositório quando houver.
3. Gerar bundle e distribuição vinculada ao SHA completo da fonte, em pasta nova. Verificar nomes, bytes, SHA256 e variantes originais.
4. Publicar via GitHub CLI:

```powershell
python tools/publish_distribution.py `
  --directory 'dist/2026.N.N' `
  --notes 'docs/releases/v2026.N.N.md'
```

5. O publicador verifica digest de todos os assets, confirma que SHA de fonte existe remoto, cria tag e draft técnico, faz upload dos cinco binários versionados e seus cinco aliases permanentes, mais manifesto/checksums/anexos; recusa substituir asset conflitante; só depois marca release **final** e `latest`.
6. Só após assets finalizados, o código atualiza `site/data/distribution.json` e `site/data/release.json`. Confirmar versão, commit, hashes, download e declaração `compatibilityVerifiedInGame=false` quando não foi testado.
7. Atualizar `site/data/patch-notes.json`, páginas e documentação. Commitar metadados/patch notes e enviar `main`; em seguida:

```powershell
python tools/publish_pages.py
```

8. O publicador usa worktree temporário do `gh-pages`, copia `site/`, omite `site/tests`, cria commit e push, e solicita Pages build. Verificar `gh api repos/yzPeedro/brassfoot-patch/pages/builds` e **abrir o link do site quando tiver acesso a navegador**; se sem navegador, consultar conteúdo servido e estado do Pages, sem alegar teste visual.
9. A URL de download permanente do Windows é `https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/Brasfoot-Mega-Patch-windows-x64.exe`. NÃO deixar botão preso em `verificando download` nem apontar para versão incompleta.
10. Em falha parcial, não criar outra tag cegamente; recuperar draft/asset/site de maneira idempotente e manter a última release boa acessível.

**Wrapper alternativo** (cuidado com efeitos colaterais):

```powershell
.\release.ps1 -PackagePath '.\windows-installer\bundled_release' -OutputDirectory '.\dist\2026.N.N' -Publish
# Se o build já está pronto, após revisar os arquivos:
.\release.ps1 -OutputDirectory '.\dist\2026.N.N' -PublishExisting
```

O `release.ps1` tenta atualizar dados e criar build por padrão, e com `-Publish/-PublishExisting` faz publicação, commit/push de manifestos e Pages. Usar uma rota de release por execução, não chamar wrapper **e** scripts independentes sem avaliar duplicidade.

### 5.8 Atualizar SOMENTE o site

1. Leia `site/index.html`, `site/app.js`, `site/styles.css`, `site/data/*` relevante, `site/coverage.js`, `site/divisions.js`, `site/pix.js`.
2. Requisitos mais recentes do site (30/10/2026): mostrar **somente últimos cinco patch notes** na página para evitar scroll infinito; retirar outline de foco do campo de pesquisa da tabela conforme pedido, **sem perder acessibilidade de foco** (substituir por indicação visual apropriada se necessário); incluir **seleções** no explorador/busca; filtros de competições cobrindo copas (Copa do Mundo, Eurocopa, Sul-Americana, Libertadores e demais do catálogo) e distinguir item catalogado de item jogável.
3. Ordenar/agrupar por todas as colunas da tabela, com paginação, busca, modal do clube, rótulos e contagens consistentes. Os commits de 30/10 incluíram seleções/copas, informações por país e estilos que impedem seleção acidental.
4. Textos decorativos, títulos chamativos, animações e componentes visuais não devem ser selecionáveis por engano; **dados úteis devem continuar copiáveis** (nome de time, jogador, competição, informação técnica, links etc.). Não bloquear seleção global no `body`.
5. Visual celeste/azul profundo/ciano/branco, estética inspirada no Cruzeiro mas **sem afirmar afiliação oficial**, animações elegantes e desempenho. Animação do fundo não deve travar página.
6. PIX/QR code opcional discreto no site e instalador, sem obrigação de pagar. Evitar alterar dados de pagamento se não houver fonte atual confirmada ou pedido explícito.
7. Atualizar URLs e manifesto com conteúdo publicado real; não declarar seleção/copa jogável se estiver apenas no catálogo.
8. Revisar site localmente quando autorizado, conferir assets e conteúdo público, `git diff --check`; fazer commit/push e `python tools/publish_pages.py` para entrega web. Quando a tarefa também alterar o jogo, **release ANTES de atualizar o site**.

### 5.9 Como diagnosticar falhas de instalação e regressões

- **BF-106 (prévia do Work):** verifique esquema da versão. `2026.4.6-live-preview.1` foi rejeitado pois o instalador exige `ANO.N.N` numérico. A prévia precisa de sinalização coerente com a CLI/manifests e **não** pode mascarar produto privado como final.
- **BF-199:** localizar erro exato no fluxo de aplicação, hashes e variantes de receita. Houve falha devido a cadeia de deltas aninhada e receita que declarava hash original idêntico ao target. Verifique manifesto privado, ordem das operações, arquivos com mesmo target, listas de `acceptedOriginalSha256` e integridade. Nunca desabilitar check de hash para fazer passar.
- **Jogo bloqueia substituição do EXE:** conferir processos Java/launcher existentes e handles de arquivos. Pedir ao usuário para fechar o jogo quando necessário; não matar processos automaticamente nem trocar EXE aberto.
- **Painel de partida não aparece:** verificar se a build está realmente instalada, se não houve rollback, se classes Java são compatíveis com a JVM do jogo, se injeta na classe **verdadeira da tela de partida** e se a camada aparece no layout esperado. Em histórico do Work, o painel não aparecia porque primeira injeção era em classe errada e compilação Java incompatível.
- **Jogo congela no pós-jogo:** temporizadores/threads do painel precisam encerrar quando tela é destruída. Evitar bloquear EDT de Swing e listeners que sobrevivem depois da partida.
- **`VerifyError` da JVM:** modificar bytecode mantendo stack frames válidos, formato esperado e método completo, não inserir bytes inválidos após `return`.
- **Saves ou restauração:** jamais alterar/limpar saves, ativação e preferências; backup verificado, rollback e `Restaurar original` devem permanecer.

---
## 6. WORK/CODEX — DESENVOLVIMENTO PRIVADO DO CAMPO ANIMADO (PRIORIDADE ATUAL DE CONTINUIDADE)

### 6.1 Contexto essencial e restrição de publicação

Em uma sessão do Work/Codex de **31/10/2026**, o usuário propôs uma inovação na tela original de partida do Brasfoot: desenhar um campo 2D **dentro da tela existente**, abaixo do placar e acima da tabela de outros jogos, mostrando as duas equipes como marcadores/círculos com nomes, bola, movimentação, passes, desarmes, chutes, faltas, pênaltis, substituições e gols, tudo sincronizado com o log e com os dados internos do Brasfoot. O objetivo é deixar o jogo mais imersivo, **sem alterar o resultado calculado pela engine**. Uma montagem/imagem foi usada como referência, mas **o arquivo de imagem original pode não estar disponível na sessão atual**; se estiver, abrir e usar sua geometria. Evitar reconstruir a UI apenas de memória quando existe referência.

**Instrução explícita deste fluxo:** criar **instaladores privados para teste local**, **sem criar release, sem atualizar site, sem publicar a feature**. Isso tem prioridade sobre a regra geral de publicar todos os ajustes. Esta linha não está presente nos arquivos `tools/live-match-view-src/**` da `main` pública consultada em 31/10, mas foi relatada/gerada no checkout local do Work. **Primeiro verificar os arquivos locais não commitados e artefatos privados.** Não confundir `2026.4.27` privado com `2026.4.7` público e não promover um protótipo de animação à release estável.

### 6.2 Descoberta da engine e arquitetura da animação

- O Brasfoot original usa classes Java/Swing embutidas num executável Windows híbrido/JAR. O painel de partida foi identificado como layout fixo de cerca de **1024 × 750**.
- A engine tem eventos, jogadores, placar, log, marcadores e estatísticas, **mas não fornece trajetórias espaciais reais quadro a quadro**. Portanto a UI deve converter eventos discretos em representação visual plausível. Nunca dizer que microeventos (triangulação, roubo entre eventos, lateral visual) realmente aconteceram no motor se foram apenas reconstrução sintética.
- A UI `LiveMatchPanel.java` deve ficar embutida na tela, sem sobrepor placar nem ocultar a tabela de outras partidas. Integração Java requer injeção na **classe correta da tela de partida**, com bytecode **compatível com Java 7**, temporizadores encerrados na saída e janela pós-jogo preservada.
- A camada visual pode interceptar cliques de botões da tela original; torná-la **click-through**, preservando pausa, substituições e controles originais.
- As fontes de verdade são os objetos/eventos/estatísticas internos; visualização não pode modificar posse oficial, gol, placar, cartões ou consequências da simulação sem justificativa aprovada. Cuidado: pausa do motor durante animações foi necessária para sincronizar; isso altera o **tempo de avanço** de eventos e exige validação de ausência de deadlock.

### 6.3 Arquivos privados de feature relatados pelo Work

| Arquivo local | Função aparente pela sessão | Estado a verificar |
|---|---|---|
| `tools/live-match-view-src/LiveMatchPanel.java` | campo 2D, jogadores, física, fases, animações, estados de jogo, estatísticas, ações visuais | **principal fonte de código da feature; pode ter alterações não commitadas** |
| `tools/live-match-view-src/LiveMatchTransformer.java` | integração/transplante do painel para classes Java do EXE | confirmar assinatura e bytecode alvo |
| `tools/patch_live_match_view.py` | transformar EXE-fonte verificado e gerar EXE candidato em caminho isolado | conferir SHA da fonte, JDK e output |
| `tools/build_live_match_preview_bundle.py` | montar bundle de delta da prévia, herdando receitas e variantes prévias | verificar formato, cadeia e `acceptedOriginalSha256` |
| `config/edition-live-match-preview.json` | edição/versão da prévia isolada do `edition.json` público | não deixar canal stable/manifesto público por acidente |
| `tools/build_distribution.py` | teve ajustes locais para aceitar prévias | revisar diff antes de merge; não quebrar stable |
| `data/private/live-match-preview-20261031*/` | EXEs modificados e bundles das versões privadas | estado local, pode estar ignorado pelo Git |
| `dist/live-match-preview-2026.4.*` | instaladores locais gerados, privados | não representam release no GitHub |
| `data/private/continental-cups-2026.4.5-final/bf22-23.exe` | EXE-fonte em várias transformações da UI | é base privada de referência, não redistribuir |
| `data/private/release-bundle-2026.4.6-final/` | bundle de release herdado no primeiro protótipo | verificar se herança funciona para 4.7 e posteriores |

A referência do código **não** foi verificada diretamente neste chat, pois esses arquivos não estavam na branch pública do repositório. A evidência para sua existência e várias edições é o registro do Work anexado integralmente ao final. Se não existirem no checkout atual, **não diga que foram recuperados do GitHub**: busque em histórico do Work/local, backups e artefatos privados. O instalador `dist` não basta para reconstruir fonte editável.

### 6.4 Linha do tempo das prévias e aprendizados

O arquivo bruto do Work registra **muitas etapas em 31/10**, inclusive comandos, correções, tentativas e testes manuais relatados pelo usuário. Resumo do que importa:

| Sequência | Resultado/pedido | Risco ou aprendizado |
|---|---|---|
| Protótipo inicial | painel no jogo, nome/22 marcadores/bola/eventos, instalador local | o motor não gera posição real; reconstrução visual é necessária |
| Prévia 4.6 com sufixo | erro `BF-106` pela versão `2026.4.6-live-preview.1` | versão do instalador precisa ser `ANO.N.N` |
| Primeiras prévias | `BF-199` por cadeia de receitas aninhadas / hash igual | herança/ponte delta precisa seguir semântica exata do motor |
| 4.10 | instalador havia aplicado e depois foi restaurado pelo usuário | não presumir falha do patch só porque disco voltou ao original |
| 4.11 | compilação adaptada para Java 7 | se painel invisível, inspecionar ponto de injeção real |
| 4.12/4.13 | painel ainda não aparecia; diagnóstico; pós-jogo travava | classe de tela errada; temporizador sem encerramento |
| 4.14 | campo passou a aparecer; pós-jogo voltou a funcionar | depois precisou corrigir sobreposição da tabela de outros jogos |
| 4.15–4.17 | layout abaixo do placar, outras partidas embaixo, integração/sincronismo | não ocultar informações que já existiam no Brasfoot |
| 4.18 | modelo preditivo do log, passes antes do evento, posições por função, FPS 30–144 | jogadas ficavam óbvias e congelavam antes do evento; movimento rígido |
| 4.19 | movimento interpolado, jogo corrido sintético, passes/roubadas, laterais/escanteios | melhorou significativamente, mas jogadores se embolavam e gols eram de lugares irreais |
| 4.20/4.21 | física tática com aceleração, desaceleração, funções, marcação e distância mínima | inspecionar no código/artefatos, não afirmar gameplay sem prova |
| 4.22 | bloqueio de avanço para preparar goleador/finalização, recomposição e saída após gol | usuário confirmou geração de prévia; ainda havia desincronização |
| 4.23 | bola em voo, domínio real, intervalo de toque e condução; posse por contato | ajuda a evitar passes instantâneos entre jogadores |
| 4.24 | correções de pausas, pênaltis, lances sintéticos e reinícios | houve novas reclamações de eventos e cartões desconectados |
| 4.25 | janela modal, pênalti, falta, lesão, cartão, gols, estatísticas internas, reinício | instalador foi anunciado, mas usuário apontou bugs graves depois |
| 4.26 | correções de posse com contato, nome completo, gol/falta e travamento do relógio | não considerar homologada até testar |
| 4.27 | corrigido click-through na UI, comandos de compilação do bundle/EXE registrados | **execução terminou com interrupção por limite de uso; não houve confirmação final de instalação, resultado ou entrega do instalador** |

As versões 4.18–4.27 **são números de prévia local**, não tags públicas. Não supor que a numeração continuará monotônica se a base pública avançar; o conceito de preview e sua compatibilidade por SHA precisam ser preservados.

### 6.5 Últimos pedidos do usuário antes da interrupção (critérios ainda não homologados)

**Problemas visuais e técnicos relatados e ainda prioritários:**

1. **Gols e faltas muito longe da área.** Gol de falta deve sair de zona coerente próxima à entrada da área (não do outro campo); gol de bola rolando na maioria das vezes surge dentro da área ou em distância plausível. Cobrador e bola devem se tocar antes do chute.
2. **Bola fora de sincronia com quem passa e chuta.** Em muitos momentos jogador sem bola marcava gol; jogador longe do lance era escolhido por erro de nome abreviado. Manter identidade pelo **nome completo + equipe**, posse do passador até o receptor efetivamente tocar na bola; bola em voo não pertence magicamente ao receptor.
3. **Loops de passes entre equipes opostas.** O estado de posse não pode alternar dono a cada frame/evento sem contato real, produzindo espera infinita.
4. **Jogo continuava durante paralisação/recomposição.** Após gol, pênalti, cartão, falta, lesão ou janela de decisão, relógio interno e eventos devem permanecer bloqueados até **fim da recomposição e reinício de fato**, sem outro gol no meio. Mas pausa manual e substituições devem continuar possíveis e não deve haver deadlock.
5. **A camada interceptava cliques.** O controle de pausa/substituição precisa receber mouse mesmo quando campo desenha por cima, inclusive no pós-gol.
6. **Após gol, saída errada.** Quem sofreu o gol reinicia no centro com dois jogadores e toca para **companheiro do próprio time para trás**, não para adversário distante. Bola e marcador precisam estar alinhados.
7. **Jogadores embolados e movimentação artificial.** Um ou dois pressionam; resto mantém formação/setor, linha defensiva, amplitude, lateral pelo corredor, atacante com profundidade, um pouco de jogo no campo adversário. Velocidade com aceleração/frenagem, distância mínima e interpolação suave. Não movimentar todo mundo na mesma direção seguindo bola.
8. **Eventos sem causalidade.** Jogador que recebe cartão deve estar no lance; goleiro advertido fica na área e a disputa chega até ele; pênalti com batedor/goleiro/área posicionados corretamente; cartões visíveis no ícone do atleta; lesões e trocas com transição.
9. **Estatísticas desincronizadas.** Posse, finalização, faltas, desarmes, passes errados devem vir das mesmas estruturas internas do Brasfoot. Microanimações sintéticas não devem falsificar estatísticas oficiais.
10. **Segundo tempo**: saída central com dois jogadores, recomposição nos campos corretos. Fim da partida deve voltar à tela pós-jogo sem travar.
11. **Tooltip indevido**: remover texto que surgia ao passar mouse: `Visualização animada baseadas nos eventos da partida`.
12. **FPS/adaptação de monitor**: nas prévias houve tentativa de acompanhar 30–144 Hz, cache e performance. Não afirmar VSync real do monitor no Java 7 quando for apenas aproximação de cadência.
13. **Campo dentro do layout original**: posicionamento abaixo do placar; outras partidas embaixo do campo. Não deixar logs, colunas e outros jogos desaparecerem.
14. **Transições naturais**: nenhum jogador teleporta nem há preparação de evento denunciada por congelamento; progressão, passe, desarme, lateral, escanteio e tiro de meta podem ser reconstruídos visualmente, mas não alterar o resultado oficial nem ser apresentados como eventos reais observados.

**A ordem correta de decisão** ao animar eventos: evento oficial do motor > identidade e time corretos > restrições/estatísticas reais > estado de pausa > proximidade física de jogador e bola > encenação coerente entre eventos. Nunca priorizar uma animação vistosa a ponto de quebrar o jogo ou mentir sobre um evento.

### 6.6 Máquina de estados recomendada para compreender o código existente

Isso é uma **especificação de leitura e investigação**, não uma afirmação de que os nomes exatos existam no código privado. Localize os nomes reais antes de editar:

- `pre_kickoff`: ambas equipes em seus campos, bola no centro, dois jogadores de saída.
- `open_play`: portador real da bola, fases de ataque/defesa, passes em trânsito, contenção e cobertura por setor.
- `pass_in_flight`: posição contínua da bola, passador ainda associado, receptor alvo mas **sem posse até domínio confirmado**.
- `controlled_possession`: domínio e eventual condução; trocar receptor só quando bola se aproxima e é controlada.
- `upcoming_engine_event`: motor tem evento de gol/falta/cartão etc.; preparar espaço de forma natural, sem freeze denunciador.
- `goal_finalize`: autor confirmado na equipe certa, bola posicionada no pé ou em movimento plausível, distância válida de finalização, animação até gol, placar intacto.
- `recompose_after_goal`: tempo da engine congelado, jogadores voltam, bola ao centro, equipe que sofreu gol reinicia com passe recuado para companheiro.
- `free_kick` / `penalty`: pausa, barreira/área, batedor e goleiro, cobrança só com bola próxima, visual até conclusão.
- `modal_decision` / `injury` / `substitution`: relógio/visual respeitam diálogo e controle; mouse não é capturado pela overlay.
- `halftime` / `second_half_kickoff`: reconfigurar campo e dois atletas no centro, sem “teleporte” perceptível.
- `match_end`: interromper timers/listeners e liberar a transição para a tela pós-jogo.

**Separação entre realidade e encenação:** `event.source = engine` ou `visual_synthetic` no raciocínio/estado; sintéticos podem consumir animação, nunca gerar gol/cartão oficial, alterar estatísticas ou insistir em loop até acontecer evento. Reconciliar bola com jogador, inclusive em transição de estado. Verificar um invariante por frame: não permitir chute se a bola está longe; não permitir novo evento oficial durante parada; não permitir posse simultânea em times distintos; nenhum evento não-explicado com origem ambígua.

### 6.7 Procedimento detalhado para RETOMAR O WORK após quota estourada

**Passo 1 — NÃO gerar novo código ainda.** Localize o checkout Windows exato (`C:\Users\Pedro\projects\brassfoot-patch`), verifique `git status --short`, timestamps, `tools/live-match-view-src`, `tools/patch_live_match_view.py`, `tools/build_live_match_preview_bundle.py`, `config/edition-live-match-preview.json`, `dist/live-match-preview-2026.4.27` e bases `data/private/live-match-preview-20261031-*`. Não use `git pull --rebase` ou `clean` antes de registrar diffs locais.

**Passo 2 — Verifique se a 4.27 foi realmente construída**:

```powershell
Set-Location 'C:\Users\Pedro\projects\brassfoot-patch'
git status --short
Get-ChildItem 'tools/live-match-view-src' -ErrorAction SilentlyContinue
Get-ChildItem 'data/private' -Directory | Where-Object Name -like 'live-match-preview*' | Select-Object Name,LastWriteTime
Get-ChildItem 'dist' -Directory | Where-Object Name -like 'live-match-preview*' | Sort-Object Name | Select-Object Name,LastWriteTime
Get-ChildItem 'dist/live-match-preview-2026.4.27' -ErrorAction SilentlyContinue | Select-Object Name,Length
Get-Content -Raw 'config/edition-live-match-preview.json' -ErrorAction SilentlyContinue
```

**Passo 3 — Trace último comando e artefato real** em histórico Work (anexo). A última ação exibida tentou aplicar modificação `click-through` e executar:

```powershell
python tools/patch_live_match_view.py `
  --source data/private/continental-cups-2026.4.5-final/bf22-23.exe `
  --output data/private/live-match-preview-20261031-contact-synced-clickthrough/bf22-23.exe

python -m tools.build_live_match_preview_bundle `
  --inherit-bundle data/private/live-match-preview-20261031-fluid-natural/bundle-2026.4.19 `
  --published-executable data/private/live-match-preview-20261031-fluid-natural/bf22-23.exe `
  --preview-executable data/private/live-match-preview-20261031-contact-synced-clickthrough/bf22-23.exe `
  --previous-preview-executable data/private/live-match-preview-20261031-contact-synced/bf22-23.exe `
  --output data/private/live-match-preview-20261031-contact-synced-clickthrough/bundle-2026.4.27 `
  --version 2026.4.27

python tools/build_distribution.py `
  --bundle data/private/live-match-preview-20261031-contact-synced-clickthrough/bundle-2026.4.27 `
  --output dist/live-match-preview-2026.4.27 `
  --edition config/edition-live-match-preview.json `
  --target windows/amd64
```

**Atenção:** o comando real usou **vários** `--previous-preview-executable` adicionais 4.19–4.26. A versão acima está simplificada para compreensão e **não deve ser executada como reconstrução definitiva sem consultar o comando original completo e confirmar hashes**. O Work terminou por limite de uso após registrar a tentativa; **não existe confirmação final de retorno zero**.

**Passo 4 — Conferir o instalador gerado**: inspecione `distribution.json`, `manifest.json` e variante do EXE, `Get-FileHash`, tamanho, `publicationAllowed`/canal e `acceptedOriginalSha256` contra o **EXE instalado**. Não confundir versão do instalador, versão do jogo original e versão-base da herança. Evitar `BF-106`/`BF-199`.

**Passo 5 — Revisar o diff antes de testar manualmente**, especialmente threads Swing, tratamento de eventos, pause/substituição, botão/tabela original, alinhamento de bola e estados `recomposition`. O proprietário pediu em sessões anteriores para não sair clicando no app como parte de auditorias gerais; nesta feature de jogo, no entanto, **ele explicitamente solicitou EXE para testar localmente**. Não executar gameplay automático quando a instrução atual proíbe. Se não for possível testar no ambiente, entregue a prévia, explique precisamente a limitação e receba o resultado do usuário.

**Passo 6 — Manter privado**. Se a 4.27 foi gerada e íntegra, informar caminho/arquivo local efetivamente existente e checksums. Não publicar `gh release`, não alterar `gh-pages`, não afirmar que é release 4.27 pública.

**Passo 7 — Incorporar feedback** do usuário e completar bugs específicos. A última reclamação antes da interrupção envolve gols de longe, bola/cobrador desacoplados, troca infinita entre times, pausa durante recomposição, acesso a substituições e tooltip indevido. O código foi editado em resposta, mas sem homologação conclusiva.

### 6.8 Lista de verificações comportamentais para a animação (futuro, quando autorizado)

- Um gol de bola rolando: atacante correto, contato bola/pé, chute de zona plausível, sem teleporte, bola vai ao gol; jogador que fez gol aparece no lance.
- Gol de falta: falta na zona coerente, batedor se aproxima, barreira e gol conforme engine.
- Pênalti: seleção batedor, relógio parado, atleta e goleiro reposicionados, cobrança, defesa/trave/gol visual coerente, **sem avançar a simulação durante decisão**.
- Dois jogadores de mesmo sobrenome: gol vinculado a equipe e nome completo correto.
- Saída após gol e início do segundo tempo: dois atletas no centro, próprio time toca para trás, relógio só libera após saída.
- Cartão para goleiro: goleiro não sai da área, atacante adversário aproxima e ocasiona disputa.
- Marcadores de cartão: amarelo persistente, vermelho após expulsão, identidade não transfere para outro jogador.
- Chute ambiente/erro de passe: não muda estatísticas do motor; sem loop infinito de posse entre lados.
- Substituição/pausa em qualquer frame, inclusive pênalti e recomposição: mouse atravessa overlay, interface responde, sem deadlock.
- Tabuleiro de outros jogos segue visível abaixo do campo; placar fica no topo; janela pós-jogo abre quando termina.
- Desempenho com múltiplos FPS, sem timer vivo depois de sair da tela, sem memory leak/EDT bloqueada.
- Installer reconhece original, 4.18–4.26 e bases públicas **somente quando os hashes constam de fato nas receitas**; backup/rollback sem tocar saves.

---

## 7. SISTEMA DE AUTOMAÇÃO E CONTINUIDADE

### 7.1 Há **mais de uma** automação: não confundir

Historicamente foram configuradas tarefas Windows distintas:

- `Brasfoot Mega Patch - Continuity`: serviço de retomada multiagente (`scripts/run-continuity.ps1`, `tools/continuity_service.py`). Houve tentativa de rodar a cada ~11–15 minutos. Logs mostraram `checkout_dirty` e parada de quota. Ela foi **habilitada e posteriormente desabilitada** manualmente pelo usuário em 27/10; **verificar estado atual** antes de concluir se está ativa.
- `Brasfoot Mega Patch - Daily Data`: coleta diária/dados, com gatilho periódico de **15 minutos** e gatilho de **logon**, segundo inspeção do Task Scheduler de 30/10. A repetição faz o wrapper verificar horário/estado, não significa que todo ciclo cria release. Ao verificar, identificar se abre terminal visível.
- Manutenção diária de pesquisa + release + site: documento `docs/scheduled-maintenance.md`, com orientação de execução **18:00 Brasília** pelo Codex, fonte nova, comparação, build e publicação se houver mudança material. O documento distingue esse agendamento do coletor público mais cedo.
- `docs/daily-update.md`/README também mencionam coleta por volta de **06:00 Brasília** no Windows e 06:20 no GitHub Actions; não confundir com o fluxo completo das 18h.

**São cronogramas e responsabilidades distintas.** A consulta ao Task Scheduler e configurações locais é obrigatória para saber o estado atual. Não criar gatilhos duplicados automaticamente.

### 7.2 Consultar e gerenciar tarefas (somente quando solicitado/autorizado)

```powershell
Get-ScheduledTask | Where-Object TaskName -like '*Brasfoot*' | Select-Object TaskName,State,TaskPath
Get-ScheduledTask -TaskName 'Brasfoot Mega Patch - Continuity' -ErrorAction SilentlyContinue | Format-List *
Get-ScheduledTask -TaskName 'Brasfoot Mega Patch - Daily Data' -ErrorAction SilentlyContinue | Format-List *
Get-ScheduledTaskInfo -TaskName 'Brasfoot Mega Patch - Daily Data' -ErrorAction SilentlyContinue | Format-List *
```

Se o usuário quer **não ver janelas de CMD/PowerShell abrirem**, inspeção de `Actions`, `Principal`, `Settings` e argumentos é necessária. Usar execução escondida/serviço/task compatível sem UI visível, mas **sem mecanismos furtivos maliciosos**; o instalador Windows já compila `-H=windowsgui` para não exibir console. Não esconder erros críticos do usuário; registrá-los em arquivo.

### 7.3 Orquestração Alethe/Codex e cotas

O plano do projeto utilizou Alethe e workers em perfil `savings`, até dois simultâneos, um escritor/integrador por vez, worktrees/contratos pequenos, checkpoint persistente e limitação de gasto de tokens. Históricos mencionam Astra low, Codex com `9router` e provedores econômicos. **Não afirmar que determinado provider está configurado ou pago sem conferir ambiente real.** O `scripts/run-continuity.ps1` consulta variável de ambiente de usuário `NINEROUTER_API_KEY` e chama `tools/continuity_service.py`; **nunca incluir o valor da variável neste documento ou logs públicos**.

Se faltar quota: registrar tarefas adiadas, motivo, hash/branch/HEAD e próxima operação, não utilizar bypass nem múltiplas contas para contornar limites de serviço. `checkout_dirty` deve preservar alterações do usuário, não forçar reset. O agente não trabalha de forma permanente por existir uma instrução textual; precisa de scheduler/serviço autenticado real. Não prometer atividade em background se o processo/serviço não estiver configurado/rodando.

### 7.4 Regras de manutenção diária integral, definidas em 28/10

A cada execução autorizada de manutenção: ler estado, consultar TODOS os clubes do catálogo, fontes atuais, diferenciar fonte parcial, atualizar apenas mudança confirmada, compilar `.ban`/EXE quando necessário, gerar pacote, commit/push, release final/latest, patch notes, site. **Não exigir validação manual recorrente para a rotina pública que já foi autorizada.** Preservar cotas, licenças, caches, compatibilidade e a última release boa. Quando não houver diferença material, registrar consulta e **não gerar release**.

Para cada pedido de alteração pública dentro do projeto, a regra de 28/10 é **entrega de ponta a ponta**: patch/código, confirmação técnica disponível, commit/push, release e atualização do site. A exceção expressa é **prévia privada solicitada** (campo ao vivo), que não pode ser publicada sem mudança da instrução.

---

## 8. HISTÓRICO DE DECISÕES DE PRODUTO E DE REQUISITOS (PRIORIDADES RECENTES)

### 8.1 Evolução cronológica

- **24/10**: nasce patch 2026 para Brasfoot 22–23; atualização de divisões/clubes/elencos e site GitHub Pages; `C:\Brasfoot22-23` como instalação de referência. Preferência por comandos `git`/`gh` e deploy sem depender de Actions quando cota acabar.
- **25/10**: engenharia reversa de classes Java, `.ban`, `BRA.cfg`, seletores de ano e de ligas, hashes exatos, compatibilidade v4; pedido de tabelas com ordenação/agrupamento e modais. Clubes A/B/C 20/20/20, Série D original preservada. Corrigir 2023/2024 para 2026 e refletir na engine.
- **25–26/10**: correção do desvio do instalador: **não criar jogo novo**. O patch substitui somente o que precisa sobre a instalação já existente, faz backup/restauração e não altera saves. Inserir QR code PIX discreto no instalador/site, visualização de progresso real, sem abrir PowerShell/CMD, ícone próprio e encerramento sem travar.
- **26/10**: preferência por 365Scores (com validação oficial), API-Football desativada; implementar atualização real dos jogadores, não apenas colocar clube em divisão correta. Entregas locais v4 compatíveis e pedidos de release/site. Últimos builds experimentais exigiram atenção a hash, original, posição dos jogadores e data da temporada.
- **26–28/10**: identidade evolui oficialmente para **Brasfoot Mega Patch**, expansão global, ligas e seleções, premiações, gráficos e multi-plataforma. Automação com continuidade mesmo sem chat, Alethe/Codex econômicos, publicação a cada mudança material, site azul inspirado no Cruzeiro, documentação, checkpoints de porcentagens e auditorias. Quotas fizeram algumas ondas pararem; scheduler de continuidade foi discutido, desligado e investigado.
- **28/10**: regra explícita de entrega completa para **toda alteração pública**: implementar, validar até o nível possível/declarado, publicar no repositório, release e site. Pedidos posteriores de manutenção específica dispensaram suites de testes; documentação deve reconhecer ausência de testes.
- **29–30/10**: versões públicas 4.2–4.6; correção de Mundial/bytecode e participantes de copas; pesquisas atualizadas; pedir apenas 5 patch notes visíveis, busca sem outline padrão, seleções e copas no filtro, texto decorativo não selecionável, dados úteis copiáveis.
- **31/10, cedo/tarde**: release pública **4.7** com elencos e estrelas/Top Mundial, conferência da publicação; **em paralelo** campo de partida animado privado no Work, prévias 4.8–4.27, regressões e melhorias. O último fluxo foi **interrompido por limite de uso** antes de confirmar 4.27.
- **31/10, ESTA CONVERSA**: o usuário solicita `CLAUDE.md` supercompleto que explique projeto, andamento por área, código extra, updates, passo a passo, histórico de conversas e Work, inclusive tarefas começadas e paradas na metade, com precedência pelos chats mais recentes. Essa solicitação é documentação/contexto; **não é pedido para lançar uma release do patch**.

### 8.2 Regras UX site/instalador acumuladas

- Site deve ser rápido, responsivo, sem scroll infinito de patch notes, cores celestes, download sempre funcional e correto por sistema.
- Campo de busca na tabela, seletor de competições incluindo copas, clubes e seleções visíveis e pesquisáveis, filtros e ordenação reais.
- Seleção de texto deve privilegiar conteúdos copiáveis, não animações, ornamentos ou chamadas decorativas.
- Atualizador não pode assustar usuário com terminais; mostrar progressos reais e mensagens claras. Backup/restauração devem ser compreensíveis e confiáveis.
- Botão PIX discreto/opcional em site e instalador. Sem paywall.
- Jogador não deve fazer QA para corrigir procedimentos de build; quando o usuário pede prévia privada para jogar, entregar artefato e instruções objetivas, respeitando que essa é uma homologação manual pedida pelo próprio usuário.
- Não criar PRs desnecessárias; quando autorizado, commit e push incremental direto no repo pessoal, com cuidados com branch/regras.

---

## 9. PENDÊNCIAS, TRABALHOS INCOMPLETOS E RISCOS POR FRENTE

| Prioridade | Frente | Último sinal | Próxima ação verificável |
|---|---|---|---|
| **P0** | Work/visualização animada | 4.27 tentou build, sessão terminou por limite de uso; 4.26/4.25 tiveram problemas de bola, gol, pausa e UI | **inspecionar alterações locais sem perder diff**, conferir build 4.27, corrigir ou entregar prévia privada com SHA e ressalvas; não publicar |
| **P1** | Bugs de sincronia visual | usuário reportou gol de longe, passe infinito entre times, controle de substituição e tooltip | checar máquina de estados + física + identidade + click-through com critérios de §6 |
| **P1** | Compatibilidade funcional pública | `compatibilityVerifiedInGame=false`, `gameplayVerified=false` no manifesto 4.7 | manter afirmações honestas; se testes autorizados, validar Windows/carreiras/competições/saves/rollback |
| **P1** | Cobertura mundial de elencos | 704 clubes, 300 com fonte compilada, 54 parciais, 350 preservados | ampliar fontes e mapeamentos sem inventar atributos; distinguir cobertura por estado |
| **P1** | Continuidade/automações | Task Scheduler/Docs descrevem serviços diferentes; `Continuity` foi desabilitada historicamente | verificar estado real e ausência de terminais visíveis; sem duplicidade |
| **P2** | Especificação 42 seções | `fullSpecificationComplete=false`, coverage ainda indica edição 4.0 | atualizar matriz com evidências por área, percentuais separados e gaps reais |
| **P2** | Cobertura mundial jogável | catálogo global parcial não garante engine compatível com todos os países | aprofundar modelagem, divisões, temporadas e regras no motor de jogo |
| **P2** | Dados de estrelas/Top Mundial | correção bidirecional 4.7 documentada; política é restrita a premiação/clubes conhecidos | revisar critério com fontes atuais por ano, identidades e explicações transparentes |
| **P2** | Site recente | commits 30/10 mostram filtros de seleções/copas e seleção de texto; sem teste visual independente nesta sessão | conferir últimos 5 patchnotes, outline substituído por foco acessível, pesquisa, downloads, paginação, mobile |
| **P2** | Ano/competições | 2026, Mundial e copas publicados, mas testes funcionais dispensados | preservar versão, validar calendário e avanço de temporadas quando autorizado |
| **P3** | Gráficos/escudos/uniformes | pipeline existe, cobertura integral não demonstrada | licenças, fontes, tamanho/cache e fallback, sem usar assets de terceiros sem permissão |
| **P3** | macOS/Linux | atualizadores existem; jogo não portado | informar limites e confirmar camadas de compatibilidade antes de anunciar suporte |

**Pendência não é falha definitiva.** Pode já ter sido resolvida em um chat/commit posterior ao snapshot. Claude deve conferir a evidência mais recente antes de iniciar. Para cada item, registrar `evidência do pedido`, `implementação observada`, `validação disponível`, `requisitos ainda faltantes` e `ação mais próxima`.

---

## 10. COMO AGIR QUANDO O USUÁRIO PEDIR ALGO — REGRAS DE RESPOSTA E EXECUÇÃO

- Fale em **português do Brasil**, com clareza, frases diretas, linguagem técnica quando necessário, sem floreios.
- O usuário prefere **resultado final completo** e implementação real, não trocas repetidas de confirmação nem respostas só com plano.
- Se modificar código, fornecer/indicar **arquivos completos** quando solicitado; fornecer caminhos, comandos concretos que realmente funcionam e evidências de execução. Não prometer download quando não houver arquivo.
- Em perguntas de status, consultar o **último chat**, o Work e o repo antes de citar % ou versão. Diga explicitamente qual versão é **pública**, qual é **local/experimental** e qual **está só no planejamento**.
- Não perguntar o que já está decidido: repo, branch, objetivo principal, identidade do site, preservação de saves, PIX opcional, manutenção de A/B/C e regra de publicação são conhecidos. Perguntar somente detalhe bloqueador que não seja inferível com segurança.
- Não afirmar que Claude possui ferramentas, computador, navegador, automações, conectores, agentes, edição de imagem, busca de internet ou APIs que não foram disponibilizados; adapte plano à capacidade real e informe lacuna.
- Em solicitações de código, examinar o fonte atual, preservar arquivos do usuário, não executar comandos destrutivos. Se tiver acesso a Work/computer use real, usá-lo quando autorizado, caso contrário não simular ações.
- Quando não puder completar, entregar **parte comprovada** + bloqueio verificável + próximo passo exato, nunca declarar finalizado.
- Código-fonte/release são artefatos diferentes. A regra de publicar toda alteração tem **exceção específica** para a feature de partida ao vivo experimental.
- Não tentar ocultar que testes foram dispensados; o estado público reporta `tests=not-run-at-owner-request`. Se instrução atual voltar a exigir testes, executar os apropriados em ambiente autorizado e registrar resultados.
- Nunca inventar alterações de transferências, atletas, licenças, arquivos do usuário, resultados de partidas ou porcentagens.

---

## 11. PROTOCOLO DE ATUALIZAÇÃO DO PRÓPRIO CONTEXTO (ESSENCIAL PARA O CLAUDE)

**Este arquivo só é útil se for atualizado.** Ao fim de cada sessão com implementação ou descoberta importante, manter em paralelo um `docs/claude-context-changelog.md` (pode ser criado) ou uma seção de checkpoints no próprio contexto, com:

```text
Data/hora e fuso (America/Sao_Paulo):
Projeto/branch/HEAD local e remoto:
Versão pública final/latest e data:
Versão experimental local (se houver):
Pedido exato do usuário e alterações de escopo:
Arquivos alterados e o porquê:
Dados/fonte/consulta, cache e data de validade:
Comandos executados, códigos de retorno e resultados:
Testes funcionais executados / não executados e motivo:
Builds gerados, caminho e SHA-256:
Publicação: commit, push, tag, assets, Pages e links verificados:
Bugs relatados, bugs corrigidos, bugs pendentes:
Pendências começadas e interrompidas:
Alterações locais que não podem ser descartadas:
Próximo comando/ação concreta e riscos:
```

**No início de cada nova sessão:** ler último checkpoint, comparar com `git status`, logs e conversas recentes, conferir último release, e só então continuar. Não substituir o snapshot anterior por suposta conclusão. Se o usuário enviar link/ID de conversa do Work e não for acessível ao Claude, registrar limitação e usar o transcript exportado, sem fingir leitura.

### 11.1 Template rápido de resposta de status

```text
Estado conferido em DD/MM/AAAA HH:mm (Brasília).
Última release pública: vAAAA.N.N (link + evidência).
Última prévia local: AAAA.N.N (artefato verificado ou não verificado).
Concluído: [escopo comprovado por commit/artefato].
Compilado mas não homologado: [escopo].
Em andamento: [itens com arquivos e último passo].
Bloqueado: [causa precisa, não especulação].
Próxima ação: [ação concreta e segura].
```

---

## 12. AUDITORIA DAS AÇÕES DESTA CONVERSA (O QUE FOI FEITO AQUI)

Este arquivo foi solicitado em 31/10/2026 para transferir contexto do projeto, rotinas e procedimentos ao Claude. O usuário reforçou quatro vezes os pontos críticos: **(a)** explicar projeto/como funciona/andamento, **(b)** usar chats mais recentes, **(c)** incluir Work e tarefas interrompidas, **(d)** explicar cada código extra e atualizar tudo passo a passo.

Nesta sessão de consolidação foram feitas as seguintes verificações **somente de leitura**:

1. Leitura de histórico recente deste projeto e orientações passadas (instalador, divisões, site, elencos, continuidade, publicação).
2. Consulta via conexão GitHub ao repositório `yzPeedro/brassfoot-patch`: metadados de branch, raiz, diretórios, commits recentes, releases, runs de Pages, arquivos-chave, documentação, matriz de cobertura, configuração de edition, relatórios de elenco e status de estrelas.
3. Confirmação direta no GitHub de `v2026.4.7` como última release pública no momento da consulta, com artefatos e Pages publicados; diferenciação de metadados e ausência de testes funcionais.
4. Recuperação via arquivos disponíveis do projeto/biblioteca de um **transcript extenso do Work de 31/10/2026**, nome de origem `Texto colado(20261031-214447).txt`, com 2187 linhas indexadas. Foram extraídos e incorporados os trechos das prévias de animação ao vivo, inclusive final interrompido em 4.27.
5. Recuperação de três documentos históricos de prompts/missões de 25–26/10: missão definitiva, instalador/PIX/SEO e escopo dos clubes, apresentados como fontes históricas subordinadas às decisões mais recentes.
6. Um redirecionamento para Work foi proposto no início mas não foi aceito; **esta consolidação foi feita nesta conversa**. Não houve acesso direto ao computador local do usuário, nem inspeção do checkout privado no PC, nem alteração no jogo, builds, commits, push, release ou publicação do site.
7. O histórico do Work foi materializado como **texto extraído**, não como arquivo bruto original. Trechos ainda indisponíveis em outras sessões não podem ser considerados capturados. O manual não transfere as ferramentas do ChatGPT ao Claude; documenta como Claude pode realizar o trabalho se possuir ferramentas/acesso equivalentes.

**Conclusão correta desta sessão:** documentação/contexto produzido. **Não** afirmar que a feature animada foi finalizada nem que o patch foi alterado ou republicado em função deste pedido de documentação.

---

## 13. FONTES PRIMÁRIAS E LIMITAÇÕES DE COMPLETUDE

1. `AGENTS.md` do GitHub público.
2. `docs/mega-patch-specification.md` (contrato de 42 seções; **leitura integral obrigatória**).
3. `docs/current-state.md`, `docs/release-2026.4.7.md`, `config/roster-build-2026.4.7.json`, `config/player-status-2026.json`.
4. `docs/scheduled-maintenance.md`, `config/backlog.json`, `config/specification-coverage.json`, `config/edition.json`.
5. Código real Python/Go/Java/HTML/CSS/JS do repositório e manifestos de releases.
6. Histórico conversacional visível do projeto entre 24 e 31/10 e documentos históricos recuperados.
7. Transcript do Work exportado de 31/10/2026 no **Apêndice A** e documentos de instrução históricos nos Apêndices B–D.

**Alcance real:** documentos públicos e os trechos de conversas/Work que estavam acessíveis durante a consolidação. Não existe garantia de que sejam **absolutamente todas** as sessões de ChatGPT ou Work da conta. O conteúdo de pastas privadas locais, commits não enviados, downloads e imagens de screenshots referenciadas pelo Work **não** foi inspecionado nesta consolidação. Claude deve ampliar a informação ao entrar no ambiente real e nunca tratar esta limitação como inexistente.

---

## 14. CHECKLIST DE BOOTSTRAP PARA CLAUDE CODE

1. Abrir este arquivo como `CLAUDE.md` no root do checkout (sem destruir um `CLAUDE.md` existente, se houver; mesclar primeiro).
2. Ler `AGENTS.md` e a especificação integral, matriz/backlog/estado, depois `docs/scheduled-maintenance.md`.
3. Verificar `git status`, `git log`, `gh release`, `site/data/*`, diretórios privados e tarefas locais.
4. Se o usuário pedir **continuar o último trabalho**, buscar primeiro a linha privada de partida animada de 31/10; verificar versão 4.27 e alterações não commitadas, SEM publicar.
5. Se o usuário pedir **atualização diária pública**, executar playbook de fontes/dados/deltas/release/site, respeitando mudanças materiais e políticas de testes/autorização.
6. Ao final, gerar checkpoint completo, salvar/commitar somente arquivos autorizados e registrar o que NÃO foi validado.
7. Reexaminar mensagens do usuário mais recentes a cada sessão. Se novas decisões mudarem a prioridade, atualizar esta documentação.

**Diretriz definitiva:** não use um status “done” antigo para ignorar solicitação nova; não refaça atividade comprovadamente concluída; não abandone trabalho meio feito; não publique artefato privado; proteja o jogo original, saves e dados pessoais; escreva exatamente o que observou.

---
