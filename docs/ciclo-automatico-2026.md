# Ciclo automatico do Brassfoot Patch — contrato de implementacao

**Situacao:** especificacao de implementacao; o agendador e a publicacao automatica
ainda nao estao ativados. **Nao anunciar release de elencos B/C ate existir
pacote realmente instalado e verificado no Brasfoot.**

## Ordem obrigatoria

1. Consolidar os 40 plantéis de 2026 das series B/C em dados versionaveis,
   reconciliar transferencias e dupla inscricao com fontes datadas.
2. Reconstruir os arquivos do jogo somente para A/B/C, incluindo a identidade
   interna do Maranhao. Preservar Serie D, BRA.cfg, saves e os hashes esperados.
3. Demonstrar uma geracao repetivel, idempotente e executavel no Windows.
4. Ativar um unico worker recorrente que colete, compare, teste, gere, publique
   e sincronize o site, **sem aprovacao humana por release**.

## Fontes e quota

- **Web primeiro:** preferir escala e paginas oficiais dos clubes, federacao,
  CBf e fontes esportivas com data/procedencia registrada. Uma lista de quem
  passou pelo clube em 2026 nao equivale a elenco atual.
- Os TSVs de tools/team-roster-editor/sources representam referencias iniciais,
  nao consultas vivas. O comando de preparacao abaixo funciona com zero API.
- **API-Football e complementar.** Usar apenas para lacunas nao resolvidas
  pela pesquisa, nunca sobrescrever uma fonte datada mais confiavel
  silenciosamente; se quota terminar, continuar com fontes web e cache,
  deixando lacunas explicitamente bloqueadas em vez de inventar dados.
- Todas as chamadas do provedor passam pelo QuotaLedger, incluindo retries:
  teto operacional 90 tentativas por dia UTC e por janela de 24 horas,
  no mesmo host/ledger. Nunca distribuir a chave no repositorio, site ou asset.

## Primeiro passo executavel: preparar os 40 candidatos sem API

Da raiz do repositorio:

~~~powershell
py -3 tools/prepare_bc_2026_source_snapshot.py
py -3 -m unittest discover -s tests -p test_prepare_bc_2026_source_snapshot.py -v
~~~

Saidas privadas, que nao sao o patch distribuivel:

- data/private/bc-web-candidates-2026.json
- data/private/bc-web-readiness-2026.json

Cada jogador tem nome, posicao e campos age/countryCode apenas quando
existirem na fonte. A origem HTTP(S), checksum do TSV, clube, divisao,
arquivo original candidato e discrepancias com a pesquisa anterior
ficam registrados. O status sempre e **candidate-only-not-for-release**:
nomes presentes numa fonte nao comprovam vinculo atual, atributos,
compatibilidade ou instalacao no jogo.

Auditoria inicial no GitHub (25/10/2026): 40 TSVs com 1.296 nomes e
posicoes, 98 idades informadas. A primeira correção retirou quatro jogadores
com saidas confirmadas do Maranhão em 29/09/2026: agora sao **1.292** nomes
candidatos nos 40 TSVs. Nenhum desses totais equivale a jogadores instalados.

## Versao e publicacao futura

Formato **<ano-da-temporada>.<minor>.<patch>**, por exemplo:

- 2026.2.0: release atual aprovada para seletor 2026 e A/B/C.
- 2026.3.0: primeira expansao efetivamente homologada dos elencos B/C.
- 2026.3.1: proxima atualizacao incremental de dados compativeis.

Uma mudanca de conteudo reprodutivel pode gerar release automaticamente
**sem revisao manual**. O worker deve executar testes objetivos automaticos:
coerencia dos 60 IDs de A/B/C, identificadores de jogadores, checksum do
executavel original e dos deltas, ausência de escritas fora de A/B/C,
preservacao dos saves, rollback, arquivo ZIP reproduzivel, manifest e
validacao de uma copia isolada do jogo. Falhou gate? Registrar alerta,
manter release anterior, e nao subir binario defeituoso.

Uma mera alteracao no site nao requer incrementar versao do instalador;
ela deve ser sincronizada ao Pages automaticamente. Um no-op sem alteracao
nao gera release artificial.

## Operacao prevista sem GitHub Actions

Um unico host Windows usando Agendador de Tarefas executa ciclo diario com
lock exclusivo e logs persistentes. O worker guarda checkpoint e cache,
reaproveita arquivos locais, testa, compila e assina metadados SHA-256,
publica pelo gh autenticado e atualiza main/site e gh-pages. Retry com
backoff e notificacao sobre falha. Nao depende dos minutos do Actions,
mas **depende de o computador estar ligado** ou de executar a tarefa
pendente quando ficar disponivel.

A publicacao e **duas fases**: (1) release e asset realmente disponiveis
com tamanho/digest confirmados; (2) somente entao atualizar
site/data/release.json, frontend e gh-pages. O site deve indicar a
versao efetivamente disponivel, escopo verdadeiro dos elencos e changelog,
sem texto estatico dizendo que B/C sao historicos apos a atualizacao.
Falha em fase (2) nao apaga release antiga nem troca para um link quebrado.

## Invariantes

- A/B/C: 20 clubes por divisao, identidade estavel e elencos 2026.
- Serie D: arquivo original, 64 clubes e 8 grupos no BRA.cfg preservados.
- Somente 2026 no seletor de carreira para instalacoes cujo hash seja aceito.
- Nenhuma atualizacao toca saves preexistentes.
- Nunca distribuir executavel ou imagem original do jogo sem direitos.
- Dados incompletos nao sao convertidos em afirmacoes de cobertura total.
