# Estado do Brasfoot Mega Patch — 30/10/2026

## Copas continentais de 2026 — versão 2026.4.5

A primeira temporada passa a priorizar os participantes oficiais disponíveis no catálogo do Brasfoot para Libertadores, Sul-Americana, Champions League, Europa League, Conference League e Champions Cup da Concacaf. Foram mapeadas 241 entradas oficiais existentes nos 704 arquivos de clubes do patch. Nas temporadas seguintes, a qualificação dinâmica original permanece ativa.

Os formatos internos antigos foram preservados. Quando um participante oficial não existe no catálogo ou quando a quantidade de vagas de 2026 difere da estrutura da engine, as vagas restantes continuam sendo preenchidas pela lógica original do jogo. A lista reproduzível, as ausências e as fontes oficiais estão registradas em `config/continental-cups-2026.json`.

Publicação confirmada:

- Release final/latest: https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.4.5; `prerelease=false`, `draft=false`.
- Commit-fonte: `63a6245680614e7134b60f0072e06b884c3fcbfb`.
- Windows: 5.323.776 bytes; SHA-256 `1423ccafdf798a3c22fa313d59919844ecf0fd587e56bb0bcc13e2fc731e21a3`.
- Cinco artefatos versionados, cinco aliases permanentes, catálogo, manifesto e checksums foram carregados com digest confirmado pelo GitHub.
- O site aguarda a implantação dos metadados desta release.
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
