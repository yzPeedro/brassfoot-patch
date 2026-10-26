# Patch in-place, Pix e SEO — implementação parcial e bloqueios

## Objetivo original
Um único `Brassfoot-Patch-2026-Setup.exe` que atualize **no mesmo diretório**
uma instalação legítima do Brasfoot 22–23; sem gerar outra cópia do jogo,
sem alterar saves ou atalhos e sem distribuir executáveis proprietários.

## O que está implementado nesta branch
- Motor Go preexistente ampliado para **manifesto v4** e receita diferencial
  de `bf22-23.exe` exclusivamente por caminho/hash autorizado.
- Pré-verificação e instalação in-place do executável com backup persistente,
  hash e rollback transacional juntamente com arquivos de equipes.
- Detecção do processo real `bf22-23.exe` em execução.
- Testes Go sintéticos de alteração/reversão de EXE, arquivo de equipe,
  preservação dos saves e rejeição de origem desconhecida.
- Interface nativa Go com opção Pix totalmente secundária.
- Pix EMV original sem valor fixo e CRC **82B0**, tanto no site quanto
  no instalador; QR gerado offline com **ECI UTF-8 explícito**, tamanho
  65×65 (inclui quiet zone); decodificado em teste local via ZBar,
  com bytes coincidentes com o payload UTF-8 original.
- Metadados SEO, canonical, OG/Twitter, JSON-LD, sitemap e páginas HTML
  estáticas para instalação, compatibilidade e versões.
- Coletor web-first/offline dos 40 TSVs B/C; nenhuma chamada da API é
  necessária para preparar candidatos. O Maranhão teve quatro saídas
  comprovadas removidas da lista de candidatos.
- Orquestrador PowerShell com ordem **teste/build → release → confirmação
  do hash do asset → atualização do site → gh-pages → verificação pública**.
  Sem solicitação de aprovação humana. O agendador Windows diário é
  configurável, mas **ainda não está instalado em computador algum**.

## Situação: ainda NÃO distribuir
O publicador não deve gerar o artefato novo enquanto faltarem
evidências; isso **não é aprovação manual**, e sim preservação do jogo
dos usuários.

Pendências objetivas:
1. O código-fonte da receita de correção do seletor do ano/divisões da
   **v2026.2.0 que cria cópia isolada** não está integrado ao instalador Go
   in-place no repositório, assim como os bytes originais privados do jogo.
   Não é lícito anexar um EXE completo de Brasfoot na release.
2. **40 plantéis B/C homologados não existem** no patch distribuído;
   existe pesquisa/TSV, e alguns dados não representam elenco atual.
   A construção diferencial de 40 .ban, inclusive a origem do Maranhão,
   deve ser comprovada antes da release.
3. Os testes de UI e carreira no Brasfoot real para Windows (inclusive
   calendário/progressão 2026→2027) ainda não podem ser reproduzidos no
   presente ambiente. Não afirmar homologação a partir de testes sintéticos.
4. Não há credenciais Windows `gh` nem máquina agendada acessíveis
   por este ambiente para ativar a execução diária.
5. A versão atual **v2026.2.0**, no GitHub e no site público, continua
   distribuída como ZIP de utilitário de **cópia isolada**, e assim permanece
   até o instalador in-place ter sido testado e uma nova release existir.
6. O SEO técnico fica **na branch**, não no website publicado, até
   validação e publicação. Ranking orgânico não pode ser garantido.

## Formato da nova release
Tag `v2026.n.n`; asset principal `Brassfoot-Patch-2026-Setup.exe`,
sem instalador ZIP de código como download principal. O manifesto do
site é atualizado somente depois que a API do GitHub confirmar nome,
URL, tamanho e SHA-256 do executável **realmente disponível**.

## Invariantes de segurança
- Arquivo executável sempre com nome/caminho conhecido
  `bf22-23.exe` e origem SHA aceita. Nenhuma substituição por bytes
  de versão desconhecida.
- Backups persistentes antes de modificar qualquer arquivo; no rollback
  não sobrescrever modificações desconhecidas feitas depois.
- `teams/*.ban` exclusivamente dos clubes A/B/C; Série D intocada;
  `BRA.cfg`, saves e `options.bcf` não editados no escopo.
- Não publicar versão declarando 60 elencos reais antes de existirem
  60 arquivos de equipe e dados públicos da própria release.
- A aprovação de release é **automática por gates**, nunca humana.

## Comandos dos gates (ambiente Windows do projeto)
```powershell
py -3 -m unittest discover -s tests -q
node site/tests/site.test.js
node site/tests/seo-pix.test.js
node site/tests/explorer-interaction.test.js
Push-Location windows-installer
go test ./...
go vet ./...
Pop-Location
```

Esses comandos precisam ser executados no checkout completo antes da
integração. O teste local de decodificação do QR via ZBar passou;
**o build/GUI Windows e suíte Go remota não foram executados aqui**.
