# Instruções para agentes

Regras para qualquer agente que trabalhe neste repositório. A documentação técnica está em [`docs/`](docs/README.md); este arquivo trata apenas de como operar.

## Contexto

- Projeto: atualizador gratuito e independente de uma instalação existente do Brasfoot 22-23. Repositório `yzPeedro/brassfoot-patch`; código em `main`, site em `gh-pages` (https://yzpeedro.github.io/brassfoot-patch/).
- Idioma de trabalho e de documentação: português do Brasil.
- Base de conhecimento operacional (histórico, decisões, continuidade e checkpoints): `data/private/knowledge/` no checkout de produção. É local e fica fora do Git; não copie seu conteúdo para o repositório.
- Referência do jogo original: `data/private/vanilla-22-23/` é uma instalação limpa do Brasfoot 22-23 (executável `2fa65476…bb1c`, 703 times). Use-a só para leitura, como base de engenharia reversa, comparação de hashes e `--original-game` de `build_component_bundle.py`; nunca a modifique nem a inclua em pacotes. Se ela faltar, peça ao proprietário uma cópia limpa.
- Saves: o patch não muda o formato dos saves e o hub nunca grava em `sav/`. Toda mudança no executável precisa manter iguais os campos das classes serializadas (`best/*`, `f/*`), para que a carreira abra com e sem o patch.
- Ao retomar trabalho, leia `data/private/knowledge/context/CONTINUIDADE-E-PENDENCIAS.md` e o checkpoint mais recente em `data/private/scheduled-maintenance/<data>/`.

## Precedência de fontes

1. Instrução mais recente e explícita do proprietário.
2. Estado verificado: código, Git (`main`, `origin/main`, `gh-pages`), releases do GitHub, `dist/` e `data/private/`.
3. Checkpoints e a base de conhecimento local.
4. Documentação em `docs/`.

## Antes de alterar o checkout

- `git status --short --branch`, `git fetch origin` e `git log --oneline -5 origin/main`. A rotina diária publica a partir de outro worktree, então este checkout pode estar atrás do remoto.
- Nunca descarte alterações locais: faça backup em `data/private/working-tree-backup-<data>/`, compare com o remoto e avance com `git merge --ff-only`. Nada de `reset --hard`, `clean` ou `stash pop` às cegas.

## Regras invioláveis

- Não modificar o jogo instalado, saves, ativação, licenças ou backups do usuário; trabalhar sempre em cópias em `data/private/`.
- Não redistribuir binários proprietários; distribuir apenas receitas delta reconhecidas por SHA-256.
- O motor de simulação do Brasfoot não é alterado; recursos visuais usam apenas informações expostas pelo jogo.
- Não inventar dados esportivos, transferências, testes, compatibilidade ou porcentagens.
- Segredos (tokens, `.env`, chaves) nunca entram em commits, logs ou documentos. Dados pessoais só com necessidade técnica.
- Código sem comentários explicativos.
- Commits saem no nome do proprietário (`yzPeedro`), sem linhas de coautoria de ferramentas.

## Verificações

- Por instrução do proprietário, testes, suítes, testes de navegador e gameplay não são executados, salvo pedido explícito. Conferência visual de páginas no navegador é permitida quando solicitada.
- Compilação, geração de hashes, leitura de código e conferência de publicação não são testes; não as descreva como tal.
- Vocabulário de estado, sem misturar: solicitada → planejada → parcialmente implementada → implementada → compilada → testada (dizer onde) → homologada pelo proprietário → publicada.

## Publicação

- Commits, push, releases e atualização do site estão autorizados dentro da manutenção diária descrita em [`docs/scheduled-maintenance.md`](docs/scheduled-maintenance.md), executada às 18h de Brasília.
- Fora desse ciclo, mudanças de produto (site, hub, campo animado) são entregues primeiro como prévia privada em `dist/` e só são publicadas quando o proprietário pedir.
- Publicar artefatos verificados antes de manifestos e site; vincular cada versão a commit e hashes; recuperar falhas parciais de forma idempotente.
- Releases seguintes partem do executável publicado mais recente, que contém o campo animado. Base atual (2026.6.3, com os executáveis da 2026.5.7; a 2026.6.1 e a 2026.6.2 mudaram só o hub): executável `data/private/live-match-release-2026.5.7/bf22-23.exe` (SHA-256 `fc670a5857d2a2f0eaf8960249ff1c5f2e15a55564d3cfc7ae87865ad1b76414`), executável só com o campo `data/private/live-match-release-2026.5.7/bf22-23-live-only.exe` (SHA-256 `05a90040fb10b6b0475490c9243dd7fe8fab86eb5b9b4ed0c7e452f471aa50b9`) e bundle `data/private/scheduled-maintenance/2026-11-03/release-bundle-2026.6.3-final` (Super Update da América do Sul preservado: `.cfg` de 10 países, 253 clubes novos, escudos e camisas; exige hub 1.4.0). `build_release_bundle` herda do pacote anterior as entradas que não processa (ligas de outros países e clubes acrescentados) e `build_crest_bundle --previous-bundle` herda escudos e camisas; nunca rode a release sem `--inherit-bundle` e `--previous-bundle`. O Super Update é recompilado com `python -m tools.world.compile_game` e empacotado com `python -m tools.world.build_preview_bundle --release`, fora da rotina diária. O hub aceita no máximo 64 origens por arquivo: não acumule executáveis de prévias privadas no bundle de release (`tools/prune_bundle_origins.py` remove; `build_distribution` e `build_component_bundle` recusam pacotes fora do limite). A versão do hub fica em `config/hub.json` e só muda quando o código do hub muda.
- Toda release precisa manter os componentes do hub: depois de `tools/build_release_bundle.py` (herdando o bundle anterior), rode `tools/build_component_bundle.py --release` com o original, o executável do patch sem campo, o completo e o só-campo e, por último, `python -m tools.build_crest_bundle bundle --previous-bundle <bundle-publicado-anterior>`, como descrito em [`docs/release.md`](docs/release.md). Pacote com escudos exige `requiresHub` 1.2.0.

## Campo animado

Toda mudança no campo animado precisa preservar a sincronização da bola: posse só por contato, bola nunca abandonada, eventos do jogo enfileirados durante paralisações, placar do painel atualizado somente quando a bola entra e toda fase nova com condição de saída e prazo de segurança. Detalhes em [`docs/live-match.md`](docs/live-match.md).

## Ao encerrar

Atualize a frente correspondente em `data/private/knowledge/context/CONTINUIDADE-E-PENDENCIAS.md` e registre decisões novas em `data/private/knowledge/context/HISTORICO-E-DECISOES.md`. Logs, planos e telemetria ficam em `data/private/`.
