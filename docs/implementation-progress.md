# Progresso atual — Brasfoot Patch 2026

## Novo requisito: seletores de clubes por divisão na carreira 2026

- Screenshot de criação de carreira recebido em 25/10/2026. Controles observados: **1ª divisão**, **2ª divisão**, **3ª divisão**, **Jogando estaduais**. Exemplos de escolha visíveis: América-MG, Bahia, ABC e ASA. Esses exemplos não provam sozinhos a composição das listas.
- **Objetivo obrigatório:** listas 2026 com **20 clubes corretos por divisão** nas Séries A/B/C. O controle de estaduais deve continuar válido; a Série D é preservada sem modificar grupos, clubes ou o BRA.cfg.
- **Não é só apresentação:** o jogo deverá montar competições, adversários, calendário, classificação, acesso/rebaixamento e temporadas subsequentes usando as mesmas divisões mostradas ao criar uma carreira.
- **Integrar ao seletor de ano:** única opção **2026**, e novo save e partidas efetivamente iniciando em 2026.
- **Status: enfileirado e não implementado.** O BRA.cfg inspecionado define regras/quantidades, mas não contém a lista dos clubes. A origem da filiação dos clubes às ligas e a rotina dos seletores no motor precisam ser identificadas no binário/JAR original.
- **Gate de release:** teste real em cópia isolada do Brasfoot em cada divisão, verificação de adversários, rodadas, acesso/rebaixamento, reabertura do save, nenhuma tela de carregamento infinito; hash da Série D e de saves antigos imutável, rollback do patch verificado.
- Critérios completos: docs/rosters-abc-2026.md, seção **Seletores de divisão na criação de carreira**.

## Requisito final: ano único 2026 ao iniciar carreira

Solicitação de 25/10/2026: depois de integrar e testar os 60 elencos A/B/C, substituir a escolha de anos **2023/2024** na criação de nova carreira por **somente 2026**, assegurando que o save e as partidas realmente iniciem em 2026. Os saves já existentes não podem ser modificados. A **Série D original deve continuar intacta**.

**Pendente de engenharia reversa e teste no jogo:** `.ban` e `BRA.cfg` conhecidos não codificam o seletor de ano; é necessário identificar os bytes ou métodos no executável/JAR exato da instalação do usuário e testar em cópia isolada. Não há executável original com hash homologado no repositório para uma modificação responsável. A distribuição deverá ser diferencial, condicionada ao SHA-256 original, com backup e rollback. Uma alteração visual isolada não satisfaz o requisito.

Aceite: só 2026 na interface; nova carreira criada sem travar; ano 2026 persistido e calendário válido; saves antigos iguais por hash; desinstalação restaura os anos antigos. Nenhuma release anuncia o recurso até prova real.


### Quatro elencos oficiais convertidos em laboratório

Foram adicionadas listas TSV de Criciúma (29), Londrina (29), Cuiabá (25) e Juventude (36), total de **119 jogadores com nomes e posições observados em páginas oficiais**. Nos quatro casos foram desserializados os originais privados, reconstruídos `.ban` experimentais e aplicadas receitas SHA-vinculadas à função Go `applyRecipe`, com **quatro resultados iguais byte a byte**. Essas cópias não foram instaladas no jogo, não modificam Série D e **ainda contêm estimativas de idade, nacionalidade e atributos para jogadores sem dados completos**. Portanto não são candidatos homologados à release. Fonte/código: `tools/team-roster-editor/`.

## Novo pipeline de elencos .ban, auditoria e fontes oficiais — 25/10/2026

- Trabalho executado com os **arquivos originais privados do Brasfoot** fornecidos previamente, sem publicar o conteúdo proprietário e sem modificar a instalação do usuário.
- **Formato Java real da equipe:** `e.t` com `e.g` (UID 16); arquivo original do Criciúma `criciuma_bra.ban` (ID 2226, SHA-256 `5eabaec785b1bffa23692dbd04718cf938cc8caecee02c94dcbaa40659b0ba94`) desserializado e reserializado de modo idêntico. Mapeamento de posições validado no conteúdo original: **0 goleiro, 1 lateral, 2 zagueiro, 3 meio-campo, 4 atacante**.
- **Criciúma:** 29 nomes e posições do próprio [elenco profissional oficial](https://mail.criciumaec.com.br/equipes/elenco-profissional), conforme consulta 25/10/2026. Em laboratório o `.ban` resultou em 29 atletas, 4 IDs/atributos históricos preservados, 25 novos com idades, nacionalidades e qualidades **estimadas**. Resultado de laboratório SHA-256 `334bb75defb31d1035f05d87b961d7a0cbfba2799546303c6ba05c4898e38e3e`; **não distribuído**.
- **Londrina:** 29 nomes e posições do [site oficial do clube](https://www.londrinaesporteclube.com.br/futebol/profissional/elenco). Original `londrina_pr.ban` (ID 2360, SHA `8ca8e53ba3e7bfd3c930f92ef52de0593fe71490b7bec4b93e50d3f25b02eb45`) reproduzido em laboratório com 29 jogadores. 0 IDs históricos reaproveitados, 29 posições identificadas, idades/nacionalidades/qualidades ainda estimadas. Destino privado SHA `2bd726cef710f9680cc28ba8694483d9e992d2890ed8709c414c8fa49963457f`; **não distribuído**.
- Implementado e publicado `tools/team-roster-editor/`: editor Java offline com bloqueio por SHA-256 e ID do clube, comparação de serialização original, entrada de jogadores/posição em TSV, bloqueio de arquivos dentro da instalação original, rejeição de IDs duplicados, tratamento explícito de atributos estimados apenas em modo de laboratório, teste sintético. **GitHub Actions aprovado**.
- Implementado `tools/build_team_delta.py`: gerador de receita diferencial de bytecode Java verificável por SHA-256, sem distribuir o original, com três testes sintéticos. Teste real privado do Criciúma: 48 operações e 1.636 bytes de dados adicionados, round-trip idêntico. O instalador **Go** reconstruíu esse alvo usando a própria função `applyRecipe` em teste privado local.
- Implementado `tools/audit_roster_readiness.py` + suíte: entre os **40** elencos B/C pesquisados na internet, há **1.302 registros nominais** de fonte, mas **nenhum tem dados completos de idade, posição/ID, vínculo de temporada e transferência já validados para release**. Caxias **51**, Confiança **43** e Floresta **46** excedem 40 atletas e exigem seleção com evidência de vínculo.
- **Importante:** pesquisa na internet, elenco de laboratório e elenco efetivamente instalado são estados separados. Não há release nova A/B/C com esses nomes. Nenhuma alteração feita em `BRA.cfg`, Série D ou saves. O requisito final de ano 2026 único e seletores coerentes com divisão permanece na fila para análise do binário original e teste em carreira real.

## Nova interface e retomada A/B/C — 25/10/2026

- O site público recebeu **paginação 10/20/50**, filtros por divisão e status, busca sem acentos e modal acessível com informações do clube.
- Os **730 nomes efetivamente instalados na v2026.0.2** foram extraídos de 20 arquivos `.ban` cujos SHA-256 conferem com o manifesto publicado; expostos em `site/data/published-rosters-2026-0-2.json`. **Não** foi usado o snapshot bruto de 745 jogadores para afirmar nomes que não entraram no patch.
- A pesquisa e o modal foram validados com testes simulando interação de usuário, incluindo páginas, divisão, estado, abertura/fechamento e retorno de foco. **Website regression: sucesso** no GitHub Actions. **GitHub Pages: deploy aprovado**.
- O novo pipeline `collect_abc_rosters.py` cobre **20 clubes B + 20 clubes C**. Rejeita colisões de identidade e jogadores incompletos, utiliza cache e não consulta a Série D. **Coletor regression: sucesso**, inclusive em fixture offline de 40 equipes e 800 atletas sintéticos (usados exclusivamente nos testes).
- **Bloqueador real:** nenhum dos 40 elencos B/C da temporada 2026 está disponível no cache desta sessão. Não foram consumidas requisições à API nesta tarefa. O endpoint `/players/squads` fornece uma foto atual, sem garantia de temporada; dados e elenco completo exigem verificação antes da inclusão no jogo.
- **Release futura A/B/C ainda não publicada.** A v2026.1.1 alterava Série D e é incompatível com o escopo desejado; v2026.0.2 é a prévia de elenco A que o site apresenta. Nenhuma configuração de Série D foi alterada pelo trabalho atual.
- Veja [`docs/rosters-abc-2026.md`](rosters-abc-2026.md).


## Pipeline diferencial BRA.cfg — execução local validada em 25/10/2026

- Implementado `tools/build_bra_delta.py`: transforma `BRA.cfg` original e candidato de laboratório em uma receita compatível com Go v3, sem copiar configurações completas ao repositório/distribuição. Exige SHA-256 explícito do original, tamanho igual, assinatura Java e **exatamente 2 bytes distintos**, além de recusar saída dentro do jogo.
- Experimento privado: original 1.089 bytes `76b7af89b81859ed8ee29f78de34ced3c48636ec0a27554c29d8d0da55bc2834`; candidato 96/16 `edda3712891e30fa212dddddbcbba9af8dd4c8a83c02d735e3b80f014a776dcd`; receita **5 operações, 2 bytes adicionados**, que reconstruiu o candidato byte a byte.
- O Go v3 foi executado localmente com a receita, em uma **cópia isolada com 703 equipes reais**: preflight, instalação da configuração, verificação SHA-256, estado já instalado, restauração do `BRA.cfg` original e preservação de `options.bcf` e `career.s22`. A regressão da v2026.0.2 também foi aprovada com os 20 originais privados.
- Python: **3 testes do gerador** passaram, incluindo hash original incorreto, operação corrompida e rejeição de mais de 2 bytes alterados. Go: `go test -race -count=1 ./...`, `go vet ./...` e build Windows amd64 passaram na árvore local. O binário dessa validação não foi distribuído.
- Gate não atendido: **o motor real do Brasfoot não foi executado**. Serialização, hashes e rollback não provam que Série D 96/16 possa gerar calendário nem que 96 clubes estejam nas divisões certas. **Release pública v2026.0.2 preservada**; não publicar o candidato experimental.

## Instalação transacional de BRA.cfg — validação 25/10/2026

- O motor oficial Go `windows-installer/` passou a aceitar **somente** `conf_ligas_nacionais/BRA.cfg` em manifesto **schema 3**, operação `replace`, com SHA-256 do original previamente homologado, cabeçalho Java Serialization, limites de tamanho e preflight de diretório.
- `BRA.cfg` agora participa do mesmo fluxo de **backup externo, instalação, idempotência, rollback e restauração** usado para arquivos de equipes. O schema 2 publicado em v2026.0.2 permanece restrito a `teams/*.ban`. Tentativas de adicionar `BRA.cfg`, modificar `ESP.cfg` ou usar path traversal são recusadas.
- **Testes locais realmente executados:** `go test -race -count=1 ./...` com originais privados, `go vet ./...` e build cruzado Windows amd64 passaram. Foram executados 24 testes de topo Go (incluindo caso sintético do `BRA.cfg`).
- **Teste com dados reais:** em pasta de teste isolada com os **703 arquivos .ban privados**, o Go substituiu o `BRA.cfg` original (**SHA-256 `76b7af89...`**) pelo candidato 96/16 (**SHA-256 `edda371...`**), inspecionou o estado instalado, restaurou o original byte a byte e confirmou preservação de `options.bcf` e `career.s22`. **Nenhum arquivo da instalação real do usuário foi modificado.**
- O teste real do pacote de elencos **v2026.0.2**, usando os **20 .ban originais**, também passou com backup/desfazer. Isso preserva a regressão da versão pública.
- O binário compilado Windows é um **artefato de laboratório**; embute os mesmos 20 arquivos da v2026.0.2, mas contém motor expandido. **Não foi executado na interface Windows e não foi publicado.** Seu hash SHA-256 local: `944078c0083637a2e95cd9405207546bb98dd4a548ea293f2b2a5821c4ab1ca9`.
- **Limitação factual:** o Brasfoot não está executável no ambiente Linux/container desta sessão, e nenhum executável legítimo completo foi fornecido. O teste de serialização e instalação **não demonstra jogabilidade** da Série D 96/16 nem distribuição das 96 equipes pelos grupos. O `BRA.cfg` não lista clubes individuais.
- Os 110 clubes com correspondência de arquivo ainda não possuem elencos 2026 homologados para B/C/D; 46 equipes requerem arquivos legítimos novos. Não habilitar flags de publicação, não inserir o `BRA.cfg` experimental no pacote público e não afirmar 156 jogáveis.
- **API-Football consultada nesta etapa: zero requisições.** A release pública v2026.0.2 e seu SHA-256 permanecem inalterados.

## Configurações binárias nacionais e estaduais decodificadas — 25/10/2026

- Usuário enviou ZIP **privado** com `conf_ligas_nacionais/BRA.cfg`, `ESP.cfg` e 25 arquivos de `conf_estadual/*.ces`. Foram conferidas assinaturas SHA-256, tamanhos e 27/27 objetos Java sem bytes extras.
- O `BRA.cfg` original possui `est.ArrayLigaType` (UID 1) contendo quatro objetos `est.ConfigLigaType` (UID 16), com divisões 1/2/3/4: **20, 20, 20 e 64 clubes**, respectivamente. A quarta se identifica como **Série D**, com `nGrupos=8`; países: `pais=29`, `versaoArquivo=22`.
- `ESP.cfg`: também quatro divisões com 20, 22, 10 e 30 equipes; fornece comparação de esquema, mas não prova formato jogável brasileiro de 96 clubes.
- Os 25 arquivos `.ces` usam `est.ArrayLigaEType` e `est.ConfigEstadualType` (UID 1), com quatro registros `divisao=1..4` em cada UF.
- Criado `tools/competition-codec/`: modelo tipado da serialização, leitura, round-trip byte-exato, filtro de classes permitidas, teste sintético e laboratório de Série D com 96 clubes/16 grupos **sem tocar no jogo**.
- **Teste real de serialização:** 27/27 round-trips Java JDK 21 reproduziram os bytes originais exatamente. Alterar exclusivamente `nTimes:64→96` e `nGrupos:8→16` em cópia privada do `BRA.cfg` alterou **apenas dois bytes**, sem mudar o tamanho de 1.089 bytes. A cópia resultante também foi desserializada com sucesso.
- **Limitação ainda aberta:** serialização aceita 96/16, mas não há prova de que a lógica de jogos/grupos, classificação, promoção/rebaixamento ou IDs das 96 equipes funcione no Brasfoot real. Não foi instalada configuração modificada nem iniciada carreira. A release v2026.0.2 continua inalterada.
- O arquivo `BRA.cfg` contém configurações de quantidade/formato das ligas e **não contém a lista dos times participantes**. O mapeamento dos 156 clubes às divisões jogáveis ainda depende de identificar o vínculo de equipe com competição.
- Nenhum arquivo proprietário de configurações foi adicionado ao GitHub. **API-Football consumida nesta etapa: 0 chamadas.**

## Implementação do motor Go v3 — 25/10/2026

- **Release existente:** v2026.0.2 publicada e aprovada pelo usuário em teste no Brasfoot; contém 20 clubes da Série A, 730 jogadores com limitações relatadas. Não foi substituída nesta execução.
- **Catálogo:** 156 clubes distintos nos dados oficiais (20 A, 20 B, 20 C, 96 D) e explorador de clubes publicado; 136 clubes adicionais ainda não estão no instalador.
- **Motor Go:** manifesto v3 com `operation: add` / `replace`; suporte a quantidades de 1 a 512; empacotador sem limite hardcoded de 20; validação de operações, caminhos, hashes, destinos existentes e duplicações. Mantido v2 para compatibilidade com a release atual.
- **Transações:** inclusão de novas equipes com criação exclusiva; backup para substituições; rollback de inclusões sem apagar arquivos modificados externamente; desfazer somente o que a transação instalou, preservando arquivos já modificados antes dela.
- **Testes reais executados localmente:** `go test -race -count=1 ./...` passou, incluindo 20 originais privados da release, testes sintéticos de 1 e 156 equipes, adição, restauração, colisões, idempotência, saves e rollback. O comando foi executado no motor Go reconstruído localmente a partir do código-fonte da release e evoluído nesta execução. **É necessária uma execução final dos testes após `git pull` na árvore atual do GitHub.**
- **Build:** compilação cruzada Go para Windows amd64 concluída; **não houve execução interativa em Windows nem prova de jogabilidade das novas 136 equipes**.
- **Quota:** ledger SQLite local ganhou proteção de janela móvel de 24h para evitar surtos no reset UTC; smoke tests locais de concorrência, persitência, teto 90 e transição de dia passaram. Não há prova de coordenação de múltiplos hosts externos.
- **Evidências e insumos:** o upload privado anterior possui apenas 20 `.ban`; criado `scripts/collect-game-structure.ps1` para coletar de forma privada arquivos de equipes e competições sem copiar saves/executáveis. Precisa ser executado em uma instalação real com os 703 clubes antes do mapeamento confiável de 156 IDs e competições.
- **Escudos/uniformes:** pipeline de inventário somente leitura já existe; não há aprovação de direitos/formato para redistribuição de novos assets.
- **Publicação:** código atualizado em `main`. **Nenhuma release de 156 clubes foi criada**, e não se alterou o arquivo publicado v2026.0.2 nem o hash do seu download.

## Inventário recursivo de competições — 25/10/2026

- O usuário executou o coletor corrigido do PowerShell 5.1 e enviou `Brasfoot-2026-competicoes-inventario-20261025-151642.json`; o inventário é **somente metadados** e não inclui conteúdos binários.
- **25 arquivos estaduais `.ces`** em `conf_estadual/`, cada um com **432 bytes**, nos estados AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PR, RJ, RN, RO, RR, RS, SC, SP e TO.
- **2 configurações nacionais `.cfg`** em `conf_ligas_nacionais/BRA.cfg` e `conf_ligas_nacionais/ESP.cfg`, **1.089 bytes** cada. São o principal candidato para descobrir a organização nacional.
- Os arquivos `.ces` estavam ausentes do ZIP anterior porque o coletor original só procurava na raiz. **A inexistência de `.ces` não era uma limitação confirmada do Brasfoot.**
- A existência desses arquivos **não comprova** o suporte jogável às Séries A, B, C e D, seus formatos, quantidade de clubes ou IDs. É preciso analisar o conteúdo e depois testar no Brasfoot instalado.
- Criado `scripts/collect-competition-configs.ps1`: coleta privada, exclusivamente de leitura, de `BRA.cfg`, `ESP.cfg` e `conf_estadual/*.ces`, com metadados SHA-256 e verificação de integridade do ZIP; **exclui `.ban`, saves, opções, imagens e executáveis**. O usuário ainda precisa executar o script no Windows e enviar o ZIP privado para a análise binária.
- Nenhum dado proprietário coletado foi publicado; nenhum arquivo do jogo ou release existente foi alterado.

## Coleta privada de 703 arquivos .ban — 25/10/2026

- O usuário forneceu um ZIP com **703 equipes** da instalação Brasfoot 22-23, todas com hash SHA-256 confirmado e round-trip Java exato (703/703). Dessas, 196 possuem o código de país do Brasil (29).
- Contra o catálogo oficial de 156 clubes, a reconciliação de nomes e aliases revisados encontrou **110 arquivos existentes** (20 A, 20 B, 19 C e 51 D), e **46 ausentes** (0 A, 0 B, 1 C e 45 D). Associações ainda precisam de validação de identidade interna; os dados não foram incorporados ao pacote público.
- **Os 20 arquivos de Série A enviados já estão com a v2026.0.2 aplicada**, comprovado pelo SHA-256 dos 20 arquivos no manifesto do instalador publicado. O upgrade deve reconhecer hashes da versão anterior instalada.
- A coleta incluiu metadados de **2.086 PNGs** (escudos 703, mini-escudos 702, camisas 336, camisas2 334, camisas3 11); **nenhum desses arquivos foi incluído** no ZIP, nem validado para temporada 2026/direitos de publicação.
- Foram observados vários IDs internos igual a zero e duplicação `internalId=2477` entre São Bernardo e São Paulo; essas referências precisam de investigação antes de adicionar clubes. `tid`/`sid` zero no cabeçalho das equipes não prova divisão.
- **Nenhum arquivo `.ces` no ZIP**: o coletor anterior verificou apenas a raiz do Brasfoot para essa extensão. Isso não demonstra ausência de mecanismos de competições ou suporte às quatro divisões.
- O relatório individual de 156 clubes foi mantido **privado** e nunca deve ser publicado ou transformado em pacote que distribua os 703 arquivos de equipes originais.
- Um teste Go local com `-race`, `vet` e compilação cruzada Windows amd64 passou no motor V3; **não é homologação no Brasfoot**.
- Próxima etapa factual: encontrar estruturas de competição e referências internas, confirmar os clubes ausentes, obter elencos 2026 e testar um build privado em cópia isolada do jogo; preservar a release pública v2026.0.2.

## Histórico anterior (mantido como registro; não representa o estado atual)


- Dados: sincronização real no Windows confirmou 20 clubes, 745 jogadores e zero falhas de API. Snapshot privado não foi commitado.
- Reconciliador: correção do Atlético-MG ID 1062 aprovada no Windows; testes completos do hotfix v5.0.4 executados (52 aprovados, 3 ignorados).
- Gerador `.ban`: serialização e roundtrip locais testados; atletas novos ainda herdam atributos estimados e IDs internos zerados. **Não adequado para publicação.**
- Instalador: motor offline com backup, SHA-256, restrições de caminho, idempotência, rollback e 11 testes sintéticos do motor aprovados; interface Tk implementada e smoke test Linux/Xvfb aprovado. Em 25/10/2026, usuário apresentou evidência visual de **outro executável experimental para Windows**, cujo teste offline reportou backup, cópia, hashes, rollback e localização da pasta do jogo aprovados. **Essa evidência não valida o instalador real do repositório, a compilação definitiva nem a instalação de elencos no Brasfoot.**
- Site: `main/site/` e raiz da branch `gh-pages` sincronizadas; em 25/10/2026 foram removidos o elemento `.ball` e seus estilos/animação, mantendo campo e varredura. Página informa resultado do protótipo offline. Release permanece em desenvolvimento com botão desabilitado. A propagação pública em GitHub Pages não foi confirmada por consulta HTTP nesta execução.
- GitHub: source `main` e branch `gh-pages` públicas. Workflows personalizados em `workflow_dispatch` para economizar cota; GitHub Pages usa mecanismo interno de publicação.
- Distribuição: **nenhum instalador .exe com patch real foi validado e nenhuma release foi criada**. `release.ps1` bloqueia builds sem pacote previamente marcado e evidenciado como validado no jogo; `-Publish` permanece bloqueado até testes independentes.
- Direitos: arquivos originais do Brasfoot e dados proprietários não são distribuídos pelo repositório.

**Validação conjunta:** 65 testes Python executados em ambiente isolado (62 aprovados, 3 ignorados), além dos testes estáticos do site. **Bloqueador da primeira release:** criar arquivos .ban com atributos e identificadores corretos, testar no Brasfoot real, construir e executar o instalador no Windows. Não marcar requisitos não testados como aprovados.


## Expansão 156 clubes — atualização em 25/10/2026

- Catálogo CBF: **156 clubes únicos**, Séries A/B/C/D = **20/20/20/96**, Série D em 16 grupos A1–A16. IDs estáveis com UF. Fontes em `docs/divisions-2026.md`.
- Site: filtro por Série A/B/C/D, pesquisa de clube ou UF e cards com totais extraídos do catálogo; texto diferencia catálogo oficial de instalação real. Alterações em `main/site/` e `gh-pages/`.
- API: **0 chamadas API-Football nesta execução**. Novo `quota_guard.py` com ledger SQLite local conservador, integrado às tentativas de rede de `api_football_sync.py`. Coordenação multi-host e saldo externo não comprovados.
- Assets: criado `assets_audit.py` para inspecionar escudos e camisas em modo leitura, sem redistribuir materiais de terceiros. Nenhuma imagem da expansão aprovada ou instalada ainda.
- Testes: arquivos novos `tests/test_competitions_2026.py`, `tests/test_quota_guard.py`, `tests/test_assets_audit.py` e verificações estáticas do site. **Execução das novas suítes pendente** neste ambiente.
- Instalação: **não modificada**. A v2026.0.2 permanece como única release jogável experimental, com elencos de 20 clubes. Divisões B/C/D, escudos e uniformes novos ainda não instalados nem verificados no jogo.
- Documentos: `docs/api-usage-report.md`, `docs/assets-coverage.md`, `docs/divisions-2026.md`, `docs/upgrade-2026-acceptance.md`.
- Gate: não publicar nova release até obter dados confiáveis, rights clearance, compatibilidade de arquivos e teste no Brasfoot Windows.

- Auditoria de publicação: HTML, CSS, JS e catálogo das branches `main`/`gh-pages` conferidos com equivalência exata; 156 IDs únicos, contagem 20/20/20/96 e 16 grupos Série D de seis equipes confirmados em inspeção estrutural. JavaScript do explorador, app e testes passou em validação sintática.
- Regressão do instalador legado: `go test ./...` passou no código-fonte da release v2026.0.2 extraído do kit anterior; compilação cruzada GOOS=windows/GOARCH=amd64 passou. **Não é teste da expansão e não substitui execução dos testes Python recém-adicionados.**

- Corrigida a geração de novos IDs de atletas: a base de 59 arquivos existentes A/B/C contém **seis times com ID 0** e colisão de ID **2477 entre São Paulo e São Bernardo**. Agora o namespace dos IDs adicionais deriva do SHA-256 único do arquivo original; os 59 namespaces foram comparados sem colisões no inventário privado. Ambos os diferenciais (Criciúma e Londrina) foram reconstruídos byte a byte por `applyRecipe` no Go, em ambiente isolado; nenhum arquivo proprietário foi publicado.
