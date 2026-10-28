# Manutenção automática do patch e do site

Autorização permanente do proprietário em 28/10/2026: realizar o processo completo de pesquisa, atualização, commit, push, release final e publicação do site, sem pedir aprovação a cada execução. A rotina do Codex deve executar todos os dias às 18:00, em America/Sao_Paulo, com `gpt-5.6-sol` e esforço `medium`. O agendamento é administrado pelo Codex; este documento não cria um agendador paralelo.

## Contexto e escopo

O checkout de produção está em `C:/Users/Pedro/projects/brassfoot-patch`, mesmo quando o projeto do aplicativo começa em `C:/Users/Pedro/Documents/ChatGPT/brassfoot patch`. O repositório é `yzPeedro/brassfoot-patch`, o branch de código é `main` e o site é `https://yzpeedro.github.io/brassfoot-patch/`, publicado em `gh-pages`.

Leia `AGENTS.md`, `docs/current-state.md`, `config/edition.json`, os manifestos públicos e a última release antes de operar. Use a versão efetivamente publicada, não uma versão fixa deste documento. Consulte os checkpoints locais de execuções anteriores. Preserve alterações alheias e evite execuções simultâneas que escrevam no mesmo checkout. Se outra publicação estiver em andamento, retome o estado registrado depois que ela terminar, sem duplicar release.

O escopo de pesquisa é a lista completa de clubes existente no patch, obtida do catálogo e dos arquivos compilados. Atualmente são 704 clubes; não limitar a pesquisa aos 301 plantéis já substituídos nem às ligas europeias cobertas pelo coletor inicial. Manter uma situação por clube: consultado com/sem mudanças, fonte parcial, fonte indisponível ou identificação pendente. Continuar ampliando fontes e mapeamentos confiáveis para os clubes sem cobertura.

## Pesquisa e comparação

Buscar transferências, entradas e saídas, elencos, posições, lados, características comprováveis, nomes, comissões, identidade dos clubes, competições, divisões e demais informações representadas no patch. Priorizar clubes, federações, ligas e outras fontes confiáveis; usar a coleta pública existente onde aplicável. Registrar URL, data de consulta, data da informação e proveniência dos campos. Rumores não são transferências confirmadas.

Consultar fontes novas em cada execução das 18h. O cache inicial de `tools/collect_live_rosters.py` dura 20 horas: adaptar o coletor para atualização explícita ou validade menor que 24 horas, preservando o último dado confiável para falhas. Não descartar o cache de recuperação. O coletor deve registrar quando usa dados antigos por indisponibilidade. Não driblar autenticação, limites de acesso ou cotas; usar fontes públicas alternativas quando necessário.

Comparar conteúdo normalizado com a última versão publicada. Mudanças somente em timestamps, ordenação ou metadados de consulta não justificam uma nova release do instalador. Uma pesquisa sem novidades não deve fabricar atualização, data de transferência ou patch note. Informações atuais relevantes podem justificar uma publicação só do site.

Conservar dados confiáveis quando a fonte está parcial ou indisponível. Um elenco maior não é necessariamente mais recente: o suplemento antigo não deve substituir um snapshot recente apenas por ter mais atletas. Não confundir ausência em uma resposta incompleta com saída do clube. A definição atual de completude por quantidade de jogadores/goleiros não comprova, sozinha, atualização integral.

## Aplicação e dependências

Executar as alterações, não apenas escrever um relatório ou abrir uma proposta. Ajustar também os coletores, compiladores e publicadores quando isso for necessário para concluir o ciclo. Ler as interfaces reais dos scripts antes de usá-los; nomes abaixo são pontos de entrada, não uma sequência cega de comandos.

- `tools/collect_live_rosters.py`, `config/live-roster-team-map.json` e os snapshots versionados: coleta e identificação dos clubes.
- `tools/compile_live_rosters.py`: geração produtiva dos arquivos das equipes. Usar a data corrente de Brasília, a versão da edição e a última release como base de preservação. Remover dependência de data/versão fixas de 2026.4.1 e do incremento fixo de idade quando afetarem a atualização.
- `tools/build_release_bundle.py`: receitas de delta com as bases originais e versões anteriores reconhecidas. A interface inicial aceita apenas um `previous`; ampliar a lista ou preservar as variantes anteriores ao adicionar a release mais recente, para não perder compatibilidade com original, V4, 3.5/4.0 e sucessoras.
- `tools/build_distribution.py`: compilação dos instaladores de cinco plataformas, com versão, ano, commit e hashes corretos.
- `tools/export_release_rosters.py` e `tools/export_patch_clubs.py`: regeneração dos dados públicos a partir do resultado realmente compilado, incluindo todos os clubes, cobertura, elencos e fontes. Atualizar caminhos de snapshots que estejam fixos em 2026.4.1.
- `tools/daily_update.py`: catálogo complementar de competições; não substitui a atualização dos plantéis instalados.
- `tools/publish_distribution.py`: arquivos versionados, aliases permanentes e release final/latest. Corrigir títulos e notas com ano fixo quando a edição mudar.
- `tools/publish_pages.py`: publicação da pasta `site` em `gh-pages` e solicitação de implantação.

Dados locais privados usados na entrega inicial: instalação original `C:/Brasfoot22-23`; bases em `data/private/v4-build-base`, `data/private/published-3-5-base` e `data/private/compiled-2026.4.1-final`; artefatos em `dist`. Esses diretórios históricos são referências de proveniência, não a escolha permanente de base. Não sobrescrever os originais, saves, licenças nem backups. Preservar as novas bases compiladas para permitir atualizações seguintes. Não publicar arquivos privados ou o executável proprietário completo; continuar distribuindo o mecanismo de delta autorizado.

Manter laterais como laterais e pontas como atacantes, preservar funções principais e evidências de lado/características. O campo `i` do formato atual é lado do campo, não pé dominante; não tratar um como prova do outro. Usar características observadas quando houver evidência, distinguir valores derivados de fatos verificados e preservar atributos confiáveis existentes. Nomes de jogadores com três ou mais palavras ficam com as duas primeiras, conforme solicitado pelo proprietário.

## Ano, site e notas

Obter o ano atual em America/Sao_Paulo em toda execução. Ao mudar o ano, atualizar `PATCH_YEAR`, versão da edição, instaladores, interface do jogo, imagens/menu, seletor de carreira, metadados, títulos, textos, nomes de assets atuais, SEO, copyright e demais referências da edição corrente no patch e no site. Atualizar idades usando nascimento e data de referência quando disponíveis.

Aplicar engenharia reversa e modificações no formato/recursos do jogo quando necessárias, usando as técnicas e evidências anteriores, identificação exata das bases e alterações reproduzíveis. Não realizar substituição global cega de números em binários. Não remover ativação. Anos históricos de temporadas, registros, fontes, nascimento, saves e patch notes antigas devem continuar verdadeiros; não reescrever a história para parecer atual.

Preservar a identidade azul/celeste inspirada no Cruzeiro, animações, interação e gratuidade. Atualizar tabelas, busca, contagens, datas reais de dados e de publicação, compatibilidade, instruções e `site/data/patch-notes.json`. Não anunciar 100% de clubes/atributos atualizados sem comprovação. Registrar separadamente última consulta e última mudança efetiva.

## Publicação e recuperação

Quando houver mudanças materiais no patch, incrementar a versão sem reutilizar uma tag já publicada. Preparar notas verdadeiras e atualizar todos os arquivos dependentes. Commitar e enviar o código de origem antes de compilar os artefatos vinculados àquele commit. Publicar e conferir existência, tamanho e hash dos arquivos das cinco plataformas e dos aliases antes de apontar os manifestos e o site para a nova versão.

A release pública deve ser final, `prerelease=false`, `draft=false` e `latest`; não exigir homologação humana. Um rascunho técnico transitório durante upload só pode ser considerado concluído depois da publicação final. Não deixar o site apontando para downloads incompletos. Manter `site/data/release.json` e `site/data/distribution.json` coerentes. O botão Baixar deve continuar usando `releases/latest/download` e seleção automática de sistema.

Commitar e enviar os metadados/patch notes e publicar o site. Consultar o resultado real da implantação e dos uploads; não declarar publicado quando apenas iniciado. Em falha parcial, preservar a release pública válida e retomar idempotentemente os uploads ou a implantação pendentes antes de produzir outra versão. Não anunciar sucesso nem trocar links para arquivos ausentes.

Por instrução explícita do proprietário, não executar testes, suítes, testes de navegador ou gameplay. Compilação produtiva, leitura de código, geração de dados, hashes e consulta ao estado de publicação não são testes funcionais; não descrevê-los como tal. Não disparar pipelines de testes incidentalmente; usar os mecanismos existentes de publicação direta e `[skip ci]` quando apropriado.

Registrar por execução, em `data/private/scheduled-maintenance/`, os clubes consultados, fontes, diferenças materiais, lacunas, versão/commit, etapas concluídas e publicação pendente, sem segredos. Atualizar `docs/current-state.md` quando mudar o estado publicado. Se não houver mudança, registrar a consulta e encerrar sem release artificial. Se houver bloqueio real, guardar um checkpoint e descrever o motivo sem inventar conclusão ou solicitar novamente uma aprovação já concedida.
