# Instruções para agentes

Regras para qualquer agente que trabalhe neste repositório. A documentação técnica está em [`docs/`](docs/README.md); este arquivo trata apenas de como operar.

## Contexto

- Projeto: atualizador gratuito e independente de uma instalação existente do Brasfoot 22-23. Repositório `yzPeedro/brassfoot-patch`; código em `main`, site em `gh-pages` (https://yzpeedro.github.io/brassfoot-patch/).
- Idioma de trabalho e de documentação: português do Brasil.
- Base de conhecimento operacional (histórico, decisões, continuidade e checkpoints): `data/private/knowledge/` no checkout de produção. É local e fica fora do Git; não copie seu conteúdo para o repositório.
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
- Releases seguintes partem do executável publicado mais recente, que contém o campo animado. Base atual (2026.5.2): executável inalterado em `data/private/live-match-release-2026.5.1/bf22-23.exe` (SHA-256 `d2e69ca3154ea998b7b6d4ae62ab4baef1d56beb68768cf82e46044c90fc32f3`), executável só com o campo em `data/private/live-match-release-2026.5.1/bf22-23-live-only.exe` e bundle `data/private/release-bundle-2026.5.2-final`.
- Toda release precisa manter os componentes do hub: depois de `tools/build_release_bundle.py` (herdando o bundle anterior), rode `tools/build_component_bundle.py --release` com o original, o executável do patch sem campo, o completo e o só-campo, como descrito em [`docs/release.md`](docs/release.md).

## Campo animado

Toda mudança no campo animado precisa preservar a sincronização da bola: posse só por contato, bola nunca abandonada, eventos do jogo enfileirados durante paralisações, placar do painel atualizado somente quando a bola entra e toda fase nova com condição de saída e prazo de segurança. Detalhes em [`docs/live-match.md`](docs/live-match.md).

## Ao encerrar

Atualize a frente correspondente em `data/private/knowledge/context/CONTINUIDADE-E-PENDENCIAS.md` e registre decisões novas em `data/private/knowledge/context/HISTORICO-E-DECISOES.md`. Logs, planos e telemetria ficam em `data/private/`.
