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

- Na manutenção diária, a regressão é obrigatória antes de publicar: suítes do repositório (os mesmos comandos dos workflows de verificação), integridade de todos os `.ban`, limites do pacote, instalação e remoção simuladas pelo hub em cópias descartáveis do jogo, compatibilidade de saves, campo animado renderizado sem o jogo e dados do site. O roteiro completo está em `data/private/codex/rotina-diaria-prompt.md` (local). Falha em etapa obrigatória bloqueia a publicação.
- Fora da manutenção diária, testes, suítes e testes de navegador só são executados com pedido explícito do proprietário. Conferência visual de páginas no navegador é permitida quando solicitada.
- Gameplay não é executado por agentes: nenhuma regressão substitui partida real, e os manifestos mantêm `compatibilityVerifiedInGame=false` e `gameplayVerified=false`.
- Compilação, geração de hashes, leitura de código e conferência de publicação não são testes; não as descreva como tal.
- Vocabulário de estado, sem misturar: solicitada → planejada → parcialmente implementada → implementada → compilada → testada (dizer onde) → homologada pelo proprietário → publicada.

## Publicação

- Commits, push, releases e atualização do site estão autorizados dentro da manutenção diária descrita em [`docs/scheduled-maintenance.md`](docs/scheduled-maintenance.md), executada às 18h de Brasília.
- Fora desse ciclo, mudanças de produto (site, hub, campo animado) são entregues primeiro como prévia privada em `dist/` e só são publicadas quando o proprietário pedir.
- Publicar artefatos verificados antes de manifestos e site; vincular cada versão a commit e hashes; recuperar falhas parciais de forma idempotente.
- Releases seguintes partem do executável publicado mais recente, que contém o campo animado. Base atual (2026.6.10, com os executáveis do campo animado novo da 2026.6.10): executável `data/private/live-match-release-2026.6.10/bf22-23.exe` (SHA-256 `3237e2ceaf56f81b14614109128a5133ee69db0fe954f738cd642806da09c7d0`), executável só com o campo `data/private/live-match-release-2026.6.10/bf22-23-live-only.exe` (SHA-256 `d330a79a396ce24b509dec508a224b12e237eeb8e6c049040f8fa8f6be656955`), executável do patch sem campo `data/private/live-match-release-2026.6.10/bf22-23-patch-only.exe` (SHA-256 `8193758a822282588548b263c5e29772bbb25e8d905fa882b21e2e5ce38ca119`) e bundle `data/private/scheduled-maintenance/2026-11-14/release-bundle-2026.6.10-final` (Super Update da América do Sul preservado: `.cfg` de 10 países, 253 clubes novos, escudos e camisas; exige hub 1.4.0). `build_release_bundle` herda do pacote anterior as entradas que não processa (ligas de outros países e clubes acrescentados) e `build_crest_bundle --previous-bundle` herda escudos e camisas; nunca rode a release sem `--inherit-bundle` e `--previous-bundle`. O Super Update é recompilado com `python -m tools.world.compile_game` e empacotado com `python -m tools.world.build_preview_bundle --release`; a rotina diária só o recompila quando a fonte tem diferença material e a ordem de herança entre esse pacote e `build_release_bundle` está comprovada no código e no checkpoint em que foi publicado. Sem essa comprovação, a recompilação fica para o dia seguinte e a lacuna é registrada. O hub aceita no máximo 64 origens por arquivo: não acumule executáveis de prévias privadas no bundle de release (`tools/prune_bundle_origins.py` remove; `build_distribution` e `build_component_bundle` recusam pacotes fora do limite). A versão do hub fica em `config/hub.json` e só muda quando o código do hub muda.
- Toda release precisa manter os componentes do hub: depois de `tools/build_release_bundle.py` (herdando o bundle anterior), rode `tools/build_component_bundle.py --release` com o original, o executável do patch sem campo, o completo e o só-campo e, por último, `python -m tools.build_crest_bundle bundle --previous-bundle <bundle-publicado-anterior>`, como descrito em [`docs/release.md`](docs/release.md). Pacote com escudos exige `requiresHub` 1.2.0.

## Campo animado

Toda mudança no campo animado precisa preservar a sincronização da bola: posse só por contato, bola nunca abandonada, eventos do jogo enfileirados durante paralisações, placar do painel atualizado somente quando a bola entra e toda fase nova com condição de saída e prazo de segurança. Detalhes em [`docs/live-match.md`](docs/live-match.md).

## Ao encerrar

Atualize a frente correspondente em `data/private/knowledge/context/CONTINUIDADE-E-PENDENCIAS.md` e registre decisões novas em `data/private/knowledge/context/HISTORICO-E-DECISOES.md`. Logs, planos e telemetria ficam em `data/private/`.
