# Brasfoot Mega Patch — ponto de entrada do Claude Code

Atualizador gratuito e independente de uma instalação **existente e legítima** do Brasfoot 22-23: elencos, competições, ano 2026, ajustes do executável por delta reversível, instaladores para cinco plataformas, site no GitHub Pages e manutenção diária. Não é um jogo novo, não é um repack e não redistribui o executável proprietário.

- Repositório: `yzPeedro/brassfoot-patch`; código em `main`, site em `gh-pages` → https://yzpeedro.github.io/brassfoot-patch/
- Checkout de produção: `C:\Users\Pedro\projects\brassfoot-patch`. Jogo local de referência: `C:\Brasfoot22-23` (nunca modificar durante a produção).
- Idioma de trabalho: português do Brasil.

As regras operacionais do repositório (continuidade, publicação, verificações) estão em `AGENTS.md`, importado abaixo, e valem integralmente para o Claude:

@AGENTS.md

O estado das frentes ativas e o protocolo de retomada são carregados a cada sessão:

@docs/context/CONTINUIDADE-E-PENDENCIAS.md

## Mapa da base de conhecimento

| Documento | Uso | Carregamento |
|---|---|---|
| [docs/context/CONTINUIDADE-E-PENDENCIAS.md](docs/context/CONTINUIDADE-E-PENDENCIAS.md) | frentes ativas, último estado verificado, próxima ação, protocolo de checkpoint | automático |
| [AGENTS.md](AGENTS.md) | regras de continuidade, publicação e verificações para qualquer agente | automático |
| [docs/current-state.md](docs/current-state.md) | registro cronológico das releases públicas e da operação | ler antes de agir |
| [docs/context/BRASFOOT-MEGA-PATCH-MANUAL-OPERACIONAL.md](docs/context/BRASFOOT-MEGA-PATCH-MANUAL-OPERACIONAL.md) | manual: mapa do repositório, playbooks por tipo de update, diagnóstico, campo animado, automações | ler a seção do domínio |
| [docs/context/GUIA-DE-MODULOS.md](docs/context/GUIA-DE-MODULOS.md) | módulos com interfaces de CLI conferidas no código, entradas/saídas, riscos | ler a seção do domínio |
| [docs/context/HISTORICO-E-DECISOES.md](docs/context/HISTORICO-E-DECISOES.md) | decisões vigentes, decisões substituídas e motivo | antes de decisões de produto/arquitetura |
| [docs/context/BRASFOOT-MEGA-PATCH-CONTEXTO-MESTRE.md](docs/context/BRASFOOT-MEGA-PATCH-CONTEXTO-MESTRE.md) | contexto mestre integral (= manual + apêndices A–D: transcript do Work de 31/10 e missões de 25–26/10) | sob demanda, por seção |
| [docs/mega-patch-specification.md](docs/mega-patch-specification.md) | especificação integral de 42 seções (contrato de longo prazo, hash em `config/mega-patch-specification.json`) | antes de mudar escopo |
| [docs/scheduled-maintenance.md](docs/scheduled-maintenance.md) | ciclo diário das 18h: pesquisa, compilação, release e site | antes de manutenção pública |

O contexto mestre tem ~390 KB e não deve ser carregado inteiro sem necessidade. Use os títulos (`grep -n '^#'`) e leia a seção pertinente. O manual operacional é cópia byte a byte das linhas 1–884 do contexto mestre.

## Leitura obrigatória por tipo de tarefa

| Tarefa | Ler antes |
|---|---|
| Qualquer retomada ("continue", "onde paramos") | CONTINUIDADE-E-PENDENCIAS → `git status`/`git log`/`gh release view` → checkpoint mais recente em `data/private/scheduled-maintenance/` |
| Elencos, fontes, estrelas, idades | Manual §5.2, GUIA-DE-MODULOS (coleta/compilação), `docs/365scores-roster-policy.md` |
| Divisões A/B/C/D | Manual §5.3, `docs/divisions-2026.md`, `docs/team-mapping.md`, HISTORICO (Série D) |
| Executável, ano, Copa, copas continentais | Manual §5.4 e §5.9, `docs/implementation-progress.md` |
| Bundle, instalador, distribuição | Manual §5.5–5.6, GUIA-DE-MODULOS (bundle/distribuição/instalador) |
| Release e site | `docs/scheduled-maintenance.md`, Manual §5.7–5.8 |
| Campo animado (prévia privada) | CONTINUIDADE (frente F1), Manual §6, Apêndice A do contexto mestre |
| Decisão de produto ou arquitetura | HISTORICO-E-DECISOES, especificação integral |

## Precedência de fontes

1. Instruções mais recentes e explícitas do proprietário.
2. Estado real verificado: código, Git (`main`, `origin/main`, `gh-pages`), releases do GitHub, `dist/` e `data/private/`.
3. `docs/current-state.md` e checkpoints operacionais recentes (`data/private/scheduled-maintenance/<data>/checkpoint.md`).
4. Histórico recente do Work e desenvolvimento ainda não publicado (Apêndice A, arquivos locais não commitados).
5. Contexto mestre e manual operacional.
6. Especificação original e documentação histórica (`docs/release-*.md`, `docs/audit/`, Apêndices B–D).

A hierarquia resolve contradições entre registros de épocas diferentes; não autoriza descartar requisitos da especificação. Ao encontrar conflito, registre-o em HISTORICO-E-DECISOES com a evidência.

## Vocabulário de estado (nunca misturar)

`solicitada` → `planejada` → `parcialmente implementada` → `implementada` → `compilada` → `testada` (dizer onde: fixture, Windows, gameplay) → `homologada pelo proprietário` → `publicada`.

Compilação, geração de hashes, leitura de código e conferência de publicação **não** são testes. Release publicada não significa escopo concluído. Os manifestos públicos registram `tests=not-run-at-owner-request`, `compatibilityVerifiedInGame=false` e `gameplayVerified=false`.

## Regras que não podem ser violadas

- Não modificar o jogo instalado, saves, ativação, licenças ou backups; trabalhar sempre em cópias isoladas.
- Não redistribuir binários proprietários; distribuir somente receitas de delta reconhecidas por SHA-256.
- Não inventar dados esportivos, transferências, testes, compatibilidade ou porcentagens.
- Não descartar alterações locais não commitadas; antes de `pull`/`reset`/`clean`, fazer backup e comparar com o remoto.
- **Campo animado:** publicado na 2026.5.0. Prévias de novas mudanças continuam privadas até o proprietário pedir release. Releases seguintes devem partir do executável com o campo animado.
- Segredos (tokens, `NINEROUTER_API_KEY`, `.env`) nunca entram em logs, docs ou commits. Dados pessoais só com necessidade técnica (LGPD).
- Não executar testes, suítes, navegador ou gameplay enquanto vigorar a dispensa do proprietário registrada em `AGENTS.md`.
- Código sem comentários explicativos (preferência do proprietário); documentação em Markdown é livre.
- Live Match: em toda alteração, seguir a regra de ressincronização da bola (frente F1 de CONTINUIDADE) antes de gerar prévia.
- Commits deste projeto saem no nome do proprietário (yzPeedro), sem linha de coautoria do Claude.

## Ao encerrar uma sessão

Atualize a frente correspondente em [docs/context/CONTINUIDADE-E-PENDENCIAS.md](docs/context/CONTINUIDADE-E-PENDENCIAS.md) com o modelo de checkpoint dela. Registre decisões novas ou substituídas em [docs/context/HISTORICO-E-DECISOES.md](docs/context/HISTORICO-E-DECISOES.md). Atualize `docs/current-state.md` somente quando mudar o estado publicado. Logs, planos e telemetria ficam em `data/private/`, fora do Git.
