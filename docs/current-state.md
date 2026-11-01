# Estado do Brasfoot Mega Patch — 01/11/2026

> Registro do estado **publicado**. Frentes em andamento, prévias privadas e protocolo de retomada: [context/CONTINUIDADE-E-PENDENCIAS.md](context/CONTINUIDADE-E-PENDENCIAS.md). Decisões vigentes e substituídas: [context/HISTORICO-E-DECISOES.md](context/HISTORICO-E-DECISOES.md).

## Campo animado ao vivo — versão 2026.5.0

A tela da partida ganhou o campo animado ao vivo, desenvolvido como prévia privada (2026.4.8 a 2026.4.41) e publicado por instrução do proprietário em 01/11/2026. O campo ocupa um espaço próprio entre o cabeçalho e a tabela de outros jogos, mostra jogadores, bola e árbitro e anima gols, cartões, faltas com barreira, pênaltis, lesões, substituições e as estatísticas oficiais no momento em que o Brasfoot os registra. Os resultados continuam sendo os do motor; para sincronizar, o passo de simulação do minuto seguinte da partida assistida é executado antes, com os mesmos dados, e o minuto avança no clímax do lance. Uma proteção reinicia a animação e devolve o relógio ao jogo em qualquer falha.

Os elencos são os mesmos da 2026.4.7. O bundle estável herda a 2026.4.7 e aceita o original, as versões anteriores e as prévias do campo animado; todos os 398 arquivos da instalação de referência foram reconhecidos pelo manifesto.

Publicação confirmada:

- PR: https://github.com/yzPeedro/brassfoot-patch/pull/16, mergeado na `main` (merge `c38c05205f30db60af6668afe121b875f5dd91cb`).
- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.5.0; `prerelease=false`, `draft=false`; 13 assets.
- Windows: 10.576.384 bytes; SHA-256 `5b6b96540bdb1024fdb6cbd7e7a295c16ac31d661218f289b79d0cf7a4affc34`. O alias `releases/latest/download/Brasfoot-Mega-Patch-windows-x64.exe` serve esse arquivo.
- Executável do jogo após o patch: SHA-256 `bcdc27a44985ca01a37fab50e73d587d78b171814f53f045cb51dfc6c0647f6c`.
- Manifestos: `e631ee9`. Site em `gh-pages`: `c52ee046962b9e290b885503550d28c01c161242`; Pages confirmou `built`, sem erro, e o endereço público serve a 2026.5.0.
- Nenhum teste funcional, suíte, navegador ou gameplay foi executado; foram realizadas compilação produtiva, verificação de bytecode na JVM 1.8, conferência do manifesto contra a instalação de referência e conferência de integridade e publicação.

## Manutenção diária e auditoria de estrelas — versão 2026.4.7

A consulta de 31/10/2026 renovou as fontes públicas sem falhas nem fallback antigo e comparou o conteúdo normalizado com a 2026.4.6. Foram consultados 342 clubes com 8.709 atletas; o catálogo completo de 704 clubes registra 288 fontes completas, 54 respostas parciais preservadas e 362 identidades ainda pendentes de fonte completa. O catálogo complementar fez oito requisições sem falhas e permaneceu sem mudança material.

A compilação produtiva alterou 40 arquivos: Augustine Chima entrou no Apollon Limassol, Eryk Śledziński no Lech Poznań, Fernando Costa saiu do RB Bragantino, Corsin Konietzke foi transferido do St. Gallen para o Vaduz e 25 idades foram recalculadas. A auditoria individual baseada no Top 10 masculino oficial do Ballon d'Or 2026 incluiu oito novas estrelas, removeu sete flags herdadas, manteve Kylian Mbappé e marcou o vencedor Harry Kane como Top Mundial. Lionel Messi não foi inventado em outro clube porque o Inter Miami não existe no catálogo.

Publicação confirmada:

- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.7; `prerelease=false`, `draft=false`.
- Commit-fonte: `2d61dc557eb0a3988c20e2cc141fb263d46198ea`.
- Windows: 5.470.720 bytes; SHA-256 `6c0ebbaf082b95e651b40a6091666e764d7b672a4c8bf11496e87074dcb009f7`.
- Cinco artefatos versionados, cinco aliases permanentes, catálogo, manifesto e checksums foram carregados com digest confirmado pelo GitHub.
- Site em `gh-pages`: `fd0ca2c6bbd2090f22d53735612583c33d8ae5f9`; Pages confirmou `built`, sem erro, e o endereço público serve a 2026.4.7.
- Nenhum teste funcional, suíte, navegador ou gameplay foi executado; foram realizadas coleta, compilação produtiva e conferência de integridade e publicação.

## Manutenção diária de plantéis — versão 2026.4.6

A consulta de 30/10/2026 renovou as fontes públicas sem falhas e comparou o conteúdo normalizado com a última base publicada. Foram consultados 342 clubes com 8.708 atletas; o catálogo completo de 704 clubes registra 288 fontes completas, 54 respostas parciais preservadas e 362 identidades ainda pendentes de fonte completa. O catálogo complementar fez oito requisições sem falhas e permaneceu sem mudança material.

A compilação produtiva alterou 23 arquivos de clubes. Foram confirmadas duas entradas (Fernando Costa no RB Bragantino e Yoann Prigent no Derry City), três saídas (Stavros Panagi, Savvas Sofokleous e Eren Kaya), quinze correções de posição e dezessete atualizações de idade na data de referência. Respostas parciais não apagaram plantéis. O executável da 2026.4.5, a Copa do Mundo de 2026 e as listas de copas continentais foram preservados.

Publicação confirmada:

- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.6; `prerelease=false`, `draft=false`.
- Commit-fonte: `4c92c1909123947656d5e0715e341c08cd8254b6`.
- Windows: 5.363.712 bytes; SHA-256 `062517a674f54c7c97e6aa70634af23b41223e3cad29ceaf65758872e8923d26`.
- Cinco artefatos versionados, cinco aliases permanentes, catálogo, manifesto e checksums foram carregados com digest confirmado pelo GitHub.
- Site em `gh-pages`: `8ae1af02e08a1d5293560b8988a2366f8b239485`; Pages confirmou `built`, sem erro, e o endereço público serve a 2026.4.6.
- Nenhum teste funcional, suíte, navegador ou gameplay foi executado; foram realizadas coleta, compilação produtiva e conferência de integridade e publicação.

## Copas continentais de 2026 — versão 2026.4.5

A primeira temporada passa a priorizar os participantes oficiais disponíveis no catálogo do Brasfoot para Libertadores, Sul-Americana, Champions League, Europa League, Conference League e Champions Cup da Concacaf. Foram mapeadas 241 entradas oficiais existentes nos 704 arquivos de clubes do patch. Nas temporadas seguintes, a qualificação dinâmica original permanece ativa.

Os formatos internos antigos foram preservados. Quando um participante oficial não existe no catálogo ou quando a quantidade de vagas de 2026 difere da estrutura da engine, as vagas restantes continuam sendo preenchidas pela lógica original do jogo. A lista reproduzível, as ausências e as fontes oficiais estão registradas em `config/continental-cups-2026.json`.

Publicação confirmada:

- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.5; `prerelease=false`, `draft=false`.
- Commit-fonte: `63a6245680614e7134b60f0072e06b884c3fcbfb`.
- Windows: 5.323.776 bytes; SHA-256 `1423ccafdf798a3c22fa313d59919844ecf0fd587e56bb0bcc13e2fc731e21a3`.
- Cinco artefatos versionados, cinco aliases permanentes, catálogo, manifesto e checksums foram carregados com digest confirmado pelo GitHub.
- Site em `gh-pages`: `05fc18f7ce9b0304052d0f058f128d7967e7dfc1`; Pages confirmou `built`, sem erro, e o endereço público serve a 2026.4.5.
- Nenhum teste funcional, suíte, navegador ou gameplay foi executado; foram realizadas compilação produtiva, inspeção do código compilado e conferência de integridade.

## Correção emergencial da nova carreira — versão 2026.4.4

A versão 2026.4.3 foi substituída porque a alteração que mantinha a opção da Copa marcada acrescentou bytes inválidos após o retorno do método `best.f.isUsarGruposReaisCopa`. A JVM recusava a classe com `VerifyError: Expecting a stack map frame`, interrompendo a criação da carreira antes da tela de configurações.

Na 2026.4.4, o método inteiro é transplantado a partir de um molde Java compilado válido e contém somente `iconst_1; ireturn`. A inspeção estrutural também confirmou a preservação dos 48 participantes, 12 grupos, melhores terceiros, texto de 2026 e seleção obrigatória. A instalação existente não foi modificada durante a produção.

Publicação confirmada:

- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.4; `prerelease=false`, `draft=false`.
- Commit-fonte: `d17cda9d04fc7bd752077d5343fc6222e6951d92`.
- Windows: 5.081.088 bytes; SHA-256 `ece1c0d0cb482f08d1e10031133c970502ac775b86732012cd3e828508f47f0c`.
- Cinco artefatos versionados, cinco aliases permanentes, catálogo, manifesto e checksums foram carregados com digest confirmado pelo GitHub.
- Site em `gh-pages`: `d988714e2122200999abe96b30f8c83f4678091c`; Pages confirmou `built`, sem erro.
- Nenhum teste funcional, suíte, navegador ou gameplay foi executado; foram realizadas compilação produtiva, inspeção do código compilado e conferência de integridade.

## Correção da Copa do Mundo 2026 — versão 2026.4.3

Esta versão foi substituída pela 2026.4.4 por impedir a abertura da tela de nova carreira.

A tela inicial agora escreve `Usar grupos da Copa do Mundo 2026` e mantém a escolha ativada. A primeira Copa da carreira iniciada em 2026 substitui a lista fixa de 32 participantes de 2022 pelas 48 seleções da edição concluída de 2026, distribuídas nos 12 grupos oficiais de quatro equipes. Avançam os dois primeiros de cada grupo e os oito melhores terceiros para a fase de 32.

Os identificadores internos e a composição A–L estão em `config/world-cup-2026.json`, com fonte oficial da FIFA. A adaptação do executável é reproduzível, exige o SHA-256 exato da versão 2026.4.2 e modifica somente quatro classes Java; saves, licenças e a instalação de origem não foram alterados durante a produção.

Publicação confirmada:

- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.3; `prerelease=false`, `draft=false`.
- Commit-fonte: `ed2b2bbac3b4c6787b932bf80c04aefb3fd280c2`.
- Windows: 4.954.112 bytes; SHA-256 `8ec902aa2b7ffe6a3f8d0770fc7021e581ac195f05035ce4b5b25c042c40bd9a`.
- Cinco artefatos versionados, cinco aliases permanentes, catálogo, manifesto e checksums foram carregados com digest confirmado pelo GitHub.
- Site em `gh-pages`: `91fadf213b3826eb8aef5295a11b21e0168de507`; Pages confirmou `built`, sem erro.
- Nenhum teste funcional, suíte, navegador ou gameplay foi executado. Foram realizadas compilação produtiva, leitura do código compilado e conferência de integridade e hashes.

## Manutenção 2026.4.2

Release final publicada após consulta nova dos plantéis em 29/10/2026. O catálogo completo registra 704 clubes: 288 retornos completos do coletor ao vivo, 54 fontes parciais e 362 identidades ainda sem fonte completa; suplementos datados elevam o resultado compilado a 300 elencos substituídos, 54 parciais preservados e 350 preservados.

A comparação normalizada eliminou alterações apenas de ordem e consulta. O pacote final altera materialmente 28 clubes frente à 2026.4.1: quatro entradas, cinco saídas e 19 registros corrigidos, além de diferenças com nomes duplicados. Respostas parciais ou ausentes não apagaram atletas; Barcelona foi preservado quando não apareceu na coleta atual.

O cache de plantéis passou a aceitar renovação explícita com validade padrão de 18 horas e fallback para o último dado confiável. A compilação usa a data corrente de São Paulo, preserva idade da última release quando não há nascimento e evita reserialização por simples ordem. O gerador aceita múltiplas bases anteriores e encadeia receitas 2026.4.1 para manter os hashes reconhecidos de original, V4, 2026.3.5/4.0 e 2026.4.1.

Publicação confirmada:

- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.2; `prerelease=false`, `draft=false`.
- Commit-fonte: `0f44dd3716dcf772ba20cb192fe4a2fc3189ddf5`.
- Windows: 4.752.384 bytes; SHA-256 `598c8b750b8674ede7ad39b1633a2fa98eba6a7bf4008cd78cef115a0d3964fc`.
- Cinco artefatos versionados, cinco aliases permanentes, catálogo, manifesto e checksums carregados com digest confirmado pelo GitHub.
- `release.json` e `distribution.json` identificam 2026.4.2 e o download continua em `releases/latest/download`.
- Site em `gh-pages`: `945b0f2d8dfea8d7c945e746dd889cc6fee3c5ff`; Pages confirmou `built`, sem erro.
- Nenhum teste funcional, suíte, navegador ou gameplay foi executado. Coleta, compilação produtiva, geração e integridade/publicação foram realizadas.

## Entrega corretiva 2026.4.1

Release final. Instalador único com 398 receitas (397 equipes e executável), bases original/V4/3.5/4.0 identificadas por SHA-256, menu inicial 2026 e seletor 2026. Nenhum arquivo de `C:/Brasfoot22-23` foi alterado durante a produção.

Coleta de plantéis em `tools/collect_live_rosters.py`, snapshots rastreados em `config/rosters-2026.4.1.json` e `config/live-rosters-supplement.json`. Compilador batch em `tools/compile_live_rosters.py`, codificação original Java em `src/app/Main.java`. Mapa de países extraído do enum original e registrado em `config/brasfoot-country-names.json`.

301 plantéis completos substituídos (60 Brasil, 241 Europa), 8.672 jogadores importados, 1.320 laterais, 1.221 pontas como atacantes, 2.584 lados observados. 54 fontes parciais preservaram o plantel anterior e produziram 82 correções pontuais. A regra de nomes com até duas palavras alcança os 704 clubes, incluindo a lista secundária.

O campo `i` é lado, não há pé dominante separado no formato. 5.388 atletas novos usam pares de características derivados da função; não afirmar verificação individual de atributos. O relatório público identifica os clubes preservados. Não afirmar que todos os clubes europeus foram atualizados.

Site interativo com animações, iluminação seguindo o mouse e botão Baixar com seta. `release.json` e `distribution.json` passam a apontar para a mesma release final. Os cinco aliases `releases/latest/download/Brasfoot-Mega-Patch-*` impedem que a página encaminhe o usuário para a base antiga.

Nenhum teste foi executado. Foram realizadas leitura de código, coleta produtiva, geração de arquivos, compilação e conferência de integridade de pacotes. A publicação final foi solicitada explicitamente pelo proprietário, independentemente de homologação de gameplay. Histórico preservado em `docs/audit/state-before-mega-2026.4.1.md`.

## Operação

`tools/build_release_bundle.py` constrói receitas de múltiplas bases; `tools/build_distribution.py` compila cinco plataformas; `tools/publish_distribution.py` publica final/latest com aliases e metadados; `tools/publish_pages.py` publica o site após os assets.

A tarefa local diária de dados existente permanece ativa e coleta o catálogo. Ela não substitui a manutenção integral de plantéis e publicações.

Em 28/10/2026 foi criada no aplicativo Codex a rotina ativa `atualizar-brasfoot-e-site`: todos os dias às 18:00, America/Sao_Paulo, modelo `gpt-5.6-sol`, esforço `medium`, execução local. O proprietário autorizou pesquisa de todos os clubes, implementação, compilação, commit/push, release final, publicação do site, atualização anual e patch notes sem aprovação recorrente. Processo e limitações conhecidas: `docs/scheduled-maintenance.md`.

A rotina usa o projeto local do aplicativo em `C:/Users/Pedro/Documents/ChatGPT/brassfoot patch`, cujo `AGENTS.md` aponta para este checkout real. Há configuração de execução sem confirmações somente nessa pasta do projeto; os padrões globais não foram modificados. A máquina deve estar ligada e o aplicativo aberto para a execução local. A criação da agenda não representa uma nova coleta, release ou teste executado; cada execução registra seu resultado real e retoma falhas parciais.

A especificação integral ainda tem requisitos de expansão da engine e cobertura mundial pendentes; esta entrega trata os dez pontos da correção solicitada.

## Publicação confirmada

- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.1 ; `prerelease=false`, `draft=false`.
- Fonte dos cinco binários: `264365d91686814ba50353f276175993f6d52766`.
- Windows: 4.730.880 bytes; SHA-256 `e3bd5c13b29e2f7c5230338c0964894f457413e6ecb96aeaee4f4372f0566897`.
- Cinco nomes versionados, cinco aliases permanentes, catálogo, manifesto e checksums carregados com digest confirmado pelo GitHub.
- Site em `gh-pages`: `8cad7bce8800ed4e8b6077b532a2776e3f2cf00d`; Pages confirmou `built`, sem erro.
- A antiga 2026.4.0 também perdeu o marcador de pré-release, mantendo seus arquivos; somente 2026.4.1 é latest.
- Suítes de testes não executadas. O único workflow de release anterior foi ignorado por sua condição de tag; Pages concluiu a implantação.
