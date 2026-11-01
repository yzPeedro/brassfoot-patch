# Histórico e decisões — Brasfoot Mega Patch

Consolidação, em 31/10/2026, das decisões de produto e de engenharia registradas no [contexto mestre](BRASFOOT-MEGA-PATCH-CONTEXTO-MESTRE.md) (§8 e Apêndices B–D), em [AGENTS.md](../../AGENTS.md), [current-state.md](../current-state.md) e nos dados do repositório. Cada linha aponta a evidência. O que não está documentado aparece como "motivo não documentado"; nada aqui foi inferido como fato sem fonte.

Abreviações de evidência: **CM** = `BRASFOOT-MEGA-PATCH-CONTEXTO-MESTRE.md`, com número de linha; **CS** = `docs/current-state.md`.

## Como usar este documento

1. Antes de uma decisão de produto ou arquitetura, procure aqui a decisão vigente do domínio.
2. Se a nova instrução do proprietário mudar uma decisão, mova a decisão antiga para a tabela "Substituídas". Registre data, motivo (ou "não documentado") e evidência, e acrescente a nova em "Vigentes".
3. Decisões substituídas continuam como histórico, mas não se aplicam. Requisitos da [especificação integral](../mega-patch-specification.md) continuam formalmente pendentes mesmo quando a prática os flexibilizou: `config/specification-coverage.json` mantém `fullSpecificationComplete=false`.

## Linha do tempo resumida

| Data | Marco | Evidência |
|---|---|---|
| 24/10/2026 | Nasce o patch 2026 para Brasfoot 22-23: divisões, clubes, elencos e site no GitHub Pages; `C:\Brasfoot22-23` é a instalação de referência | CM §8.1 (l. 742) |
| 25/10 | Engenharia reversa de classes Java, `.ban` e `BRA.cfg`, seletores de ano e de liga; A/B/C com 20 clubes cada, Série D original; missão definitiva de entrega autônoma | CM l. 743; Apêndice B (l. 3086–4090); Apêndice D (l. 5099–6103) |
| 25–26/10 | Correção do desvio do instalador: patch in-place, não um jogo novo. Backup e restauração, PIX discreto, SEO, publicação sem aprovação manual | CM l. 744; Apêndice C (l. 4092–5097) |
| 26/10 | 365Scores como fonte preferencial, com validação oficial; API-Football desativada; atualização real de jogadores | CM l. 745; `docs/365scores-roster-policy.md` |
| 26–28/10 | Identidade "Brasfoot Mega Patch", expansão mundial, multiplataforma, automação com Alethe/Codex, visual celeste inspirado no Cruzeiro | CM l. 746; AGENTS.md |
| 28/10 | Autorização permanente: toda alteração pública vai até release e site, sem homologação recorrente; manutenção diária às 18h | CM l. 747; `docs/scheduled-maintenance.md` |
| 29–30/10 | Releases 4.2 a 4.6: Copa do Mundo 2026, `VerifyError` da 4.3 corrigido na 4.4, copas continentais (4.5), manutenção de plantéis (4.6); ajustes do site | CS; CM l. 748 |
| 31/10 (tarde) | Release pública 4.7 (plantéis, estrelas e Top Mundial pelo Ballon d'Or 2026) | CS; `docs/release-2026.4.7.md` |
| 31/10 (paralelo) | Linha **privada** do campo animado no Work: prévias 2026.4.8→4.27, interrompida por limite de uso | CM §6 e Apêndice A |
| 31/10 (noite) | Contexto mestre transferido ao Claude Code e organizado em `docs/context/` | este documento |

## Decisões vigentes

| Domínio | Decisão vigente | Evidência |
|---|---|---|
| Natureza do produto | Patch in-place sobre a instalação existente. Sem segunda cópia do jogo, sem launcher obrigatório, sem ZIP manual | Apêndice C §1 e §5 (CM l. 4121–4145, 4307–4339); CM §1 |
| Proteção do usuário | Backup verificado por SHA antes de alterar; transação com rollback; restauração pela interface; saves, ativação, licenças e preferências preservados | Apêndice C §3 e §6 (CM l. 4205–4245, 4343–4364); AGENTS.md |
| Executável | Pode ser substituído por versão reconstruída via delta a partir do original do usuário. Transformadores exigem SHA exato da base; o binário proprietário completo não é redistribuído; não há contorno de DRM | Apêndice C §4 (CM l. 4249–4303); CS 2026.4.3/4.4; `tools/build_release_bundle.py` |
| Identificação de versões | Por SHA-256 e estrutura; não tocar em bytes de versões desconhecidas; sem offsets estáticos | Apêndice B §5 (CM l. 3379–3413) |
| Compatibilidade de upgrade | Receitas aceitam original, V4, 2026.3.5/4.0, 2026.4.1 e as sucessoras encadeadas | AGENTS.md "Entrega corretiva"; CS 2026.4.2 |
| Divisões | Séries A, B e C 2026 com 20 clubes cada. **Série D com a configuração original preservada** (`BRA.cfg` original esperado: 64 equipes, 8 grupos) | `site/data/target-abc-2026.json` (`serieD.policy = configuration-preserved`); Apêndice B §8 (CM l. 3520–3550); CM §5.3 |
| Escopo de clubes | Os 704 clubes do catálogo do patch entram na pesquisa diária; não limitar aos plantéis já substituídos | `docs/scheduled-maintenance.md`; CS |
| Fontes de dados | Fontes públicas (365Scores e oficiais); **API-Football desativada por padrão**; a coleta não pode depender de chave de provider; preservar o último dado confiável quando a fonte falha | AGENTS.md; `docs/365scores-roster-policy.md` |
| Dados de jogadores | Sem jogadores ou transferências inventados. Atributos derivados ficam identificados como derivados; o campo `i` é lado, não pé dominante; nomes com 3+ palavras mostram as duas primeiras | CS 2026.4.1; `docs/scheduled-maintenance.md` |
| Estrelas e Top Mundial | Estrela = Top 10 masculino do Ballon d'Or 2026 com identidade única no catálogo; Top Mundial = vencedor. Flags herdadas fora do critério são removidas | `config/player-status-2026.json`; CS 2026.4.7 |
| Testes | **Não executar** testes, suítes, navegador ou gameplay nesta fase. Compilação, hashes e leitura de código não são testes | AGENTS.md "Verificações" |
| Publicação | Releases finais (`prerelease=false`, latest) sem homologação humana recorrente; artefatos antes do manifesto e do site; sem reutilizar tag; recuperação idempotente | AGENTS.md; Apêndice C §20–21 (CM l. 5008–5076) |
| Versionamento | `ANO.N.N` numérico; o instalador rejeita sufixos (BF-106) | Apêndice C §21; CM §5.9 |
| Distribuição | Cinco artefatos (Windows x64, Linux x64/ARM64, macOS x64/ARM64), aliases permanentes em `releases/latest/download`. Linux e macOS não homologados | AGENTS.md; CS |
| Instalador | Gráfico, sem janela de console (`-H=windowsgui`), offline; o usuário não precisa de Python, Go, Java nem PowerShell. O instalador vigente é o Go em `windows-installer/` | Apêndice B §10; Apêndice D §12; `tools/build_distribution.py` |
| Identidade visual | "Brasfoot Mega Patch", celeste, azul profundo, ciano, branco e constelações, inspirada no Cruzeiro, sem afirmar afiliação | AGENTS.md |
| PIX | Opcional, discreto, nunca bloqueia; patch 100% gratuito; sem PayPal. O código Pix fica no Apêndice C (CM l. 4451) e não é repetido aqui | AGENTS.md; Apêndice C §8–§11 |
| Site | Últimos 5 patch notes; busca sem outline padrão mas com foco acessível; seleções e copas no explorador; texto decorativo não selecionável, dados úteis copiáveis; catalogado ≠ jogável | CM §5.8 (l. 515–524); commits de 30/10 |
| Execução por agentes | Alethe em perfil `savings`, no máximo 2 workers, um escritor por vez; workers não fazem commit nem publicam; sem bypass de cota | AGENTS.md "Execução" |
| Campo animado | **Prévia privada** para teste local do proprietário. Sem release, tag, asset ou site; exceção explícita à autorização geral de publicação | CM §6.1 (l. 541–543), §7.4 (l. 734) |
| Retomada | Não recomeçar o projeto; não repetir auditorias concluídas; não substituir soluções por versões mais simples que percam funcionalidade | AGENTS.md; Apêndice B §3 |
| Live Match: sincronia com o motor | O passo de simulação do próximo minuto da partida assistida é executado antecipadamente com os mesmos argumentos e a mesma condição; o motor pula o passo já executado (gancho na classe de interface `a.dV`); o minuto do Brasfoot é disparado no clímax da animação. A ordem e a regra da simulação não mudam, só o instante em que o mesmo passo roda (01/11/2026, prévia privada 2026.4.31) | CONTINUIDADE F1; commit `5221614` no branch `live-match-preview` |

## Decisões substituídas ou flexibilizadas

| Decisão antiga | Onde | Decisão vigente | Evidência | Motivo |
|---|---|---|---|---|
| Testes completos obrigatórios (Python, Go, Java, frontend, Windows, jogo real em 17 passos) | Apêndice B §11 (CM l. 3657–3717); Apêndice D §10 (l. 5753–5836) | Não executar testes; declarar `tests=not-run-at-owner-request` | AGENTS.md "Verificações"; CS | Pedido explícito do proprietário; detalhe não documentado |
| "Dispensa de aprovação humana não significa desativar testes" | Apêndice C §20 (CM l. 5036–5054) | Proprietário dispensou testes e determinou releases finais | AGENTS.md | Pedido do proprietário |
| Publicar somente após validação/homologação | Apêndice B §2, §15, §17–18 (CM l. 3198, 3842, 3928–3958) | Releases finais sem homologação de gameplay, com declaração honesta | CS (2026.4.1: "independentemente de homologação de gameplay") | Pedido do proprietário |
| Liberar `publicationAllowed`/`compatibilityTestedInGame` só com testes | Apêndice D §11 (CM l. 5840–5863) | Manifesto traz `publicationAllowed=true` e `compatibilityTestedInGame=false`; essas flags não são prova | CM §5.5 (l. 438) | Não documentado |
| Não substituir a v2026.0.2 antes de alternativa validada | Apêndice D §15 (CM l. 5993) | Releases sucessivas até 2026.4.7 como latest | CS | Decorre da dispensa de testes; não documentado especificamente |
| API-Football como último recurso, com quota 90/100 e ledger global | Apêndice B §4.2–4.3; Apêndice D §2.3 e §9 | API-Football desativada por padrão | AGENTS.md | Não documentado |
| Escopo de 60 clubes (B) ou 156 clubes brasileiros com 96 da Série D (D) | Apêndice B §2; Apêndice D §2.1, §5, §7 | Catálogo de 704 clubes; Série D com a configuração original preservada | CS; `site/data/target-abc-2026.json` | Expansão mundial posterior; para a Série D, o requisito "não alterar o comportamento" do Apêndice B prevaleceu. Não há registro formal da revogação do D |
| Download único `Brasfoot-Patch-2026-Setup.exe` | Apêndice C §7 (CM l. 4397–4415) | Cinco artefatos `Brasfoot-Mega-Patch-*` com aliases permanentes | CS; AGENTS.md | Não documentado |
| Nome "Brasfoot Patch 2026" e identidade visual anterior | Apêndice B §16; Apêndice C §2 e §11 | "Brasfoot Mega Patch", estética celeste | AGENTS.md | Pedido do proprietário |
| "Não modifique o executável proprietário do jogo" | Apêndice D §4.2 (CM l. 5363) | Executável reconstruído por delta, travado por SHA | Apêndice C §4; CS 2026.4.3–4.5 | Contradição entre B/C e D; a prática seguiu o C. Sem registro formal |
| Upgrade a partir de v2026.0.2, 1.1 e 2.0 | Apêndice C §6 (CM l. 4379–4393) | Bases reconhecidas: original, V4, 3.5/4.0, 4.1 e sucessoras | AGENTS.md | Não documentado se os caminhos 0.2/1.1/2.0 continuam aceitos (verificar no manifesto do bundle) |
| Checkpoints em `implementation-progress.md`, `rosters-abc-2026.md`, `acceptance-matrix.md`, `release-process.md` | Apêndice B §13 | Retomada por `docs/current-state.md`, `config/backlog.json`, `data/private/scheduled-maintenance/` e [CONTINUIDADE-E-PENDENCIAS.md](CONTINUIDADE-E-PENDENCIAS.md) | AGENTS.md; esta reorganização | Não documentado |
| Execução contínua sem parar em checkpoints | Apêndice B §14 e §20 | Ondas Alethe limitadas por cota; adiar sem bypass | AGENTS.md | Controle de custo e cota (inferido do texto do AGENTS.md) |
| Agendamentos Windows ativos (`Continuity` a cada ~11–15 min; `Daily Data` a cada 15 min + logon) | CM §7.1 (l. 704–707) | Em 31/10/2026 ~19h, **as duas tarefas estão `Disabled`** no Task Scheduler. A rotina das 18h roda no app Codex | `Get-ScheduledTask` em 31/10/2026; CS "Operação" | Desabilitação da `Daily Data` não documentada |
| Diretório de estado `data/private/continuity/` | AGENTS.md; `docs/continuity.md` | Diretório **ausente** em 31/10/2026; os checkpoints reais estão em `data/private/scheduled-maintenance/<data>/` | listagem de `data/private/` | Não documentado |
| Prévia com versão `2026.4.6-live-preview.1` | Apêndice A | Prévias numeradas `2026.4.8…2026.4.27` com `channel=local-preview` | CM §5.9 (BF-106); `config/edition-live-match-preview.json` | Instalador exige `ANO.N.N` |

## Ambiguidades em aberto

1. **Série D:** o Apêndice D pedia integrar os 96 clubes "conforme suporte real". A política vigente nos dados é `configuration-preserved`. Não há registro de o proprietário ter abandonado formalmente a meta dos 96.
2. **Escudos e uniformes** (Apêndice D §8): existe o pipeline `tools/graphics_pipeline.py`, mas não há registro de cobertura atual.
3. **SEO** (Apêndice C §12–19): não há registro do que foi implementado nem de Search Console/Bing.
4. **Limite de 40 jogadores e caso Maranhão** (Apêndice B §4.4 e §4.6; Apêndice D §7.4): sem estado atual registrado.
5. **Instalador Python legado** (`installer/`): o Go é o vigente, mas a remoção ou arquivamento do protótipo Python não foi documentada.
6. **Seletores de divisão integrados ao motor** (Apêndice B §7): implementação citada em CS 2026.4.1 (seletor 2026), sem validação de gameplay.
7. **Truncamentos:** o Apêndice C termina no §22, "ETAPA 1" (CM l. 5096), e o D no §16, Exemplo D (CM l. 6102). Podem faltar requisitos.
8. **`docs/releases/`:** `release.ps1` exige `docs/releases/v{versão}.md`, mas a pasta só tem notas até `v2026.4.2`. As notas de 4.3–4.7 estão em `docs/release-2026.4.N.md`. As publicações recentes usaram `tools/publish_distribution.py --notes` diretamente (inferido da ausência dos arquivos; confirmar antes de usar o wrapper).
9. **`config/specification-coverage.json`** ainda declara `edition=2026.4.0` (42 seções: 9 `implemented`, 33 `partial`).
10. **README.md** ainda menciona a release 2026.4.1 como atual (CM l. 83).
