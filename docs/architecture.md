# Arquitetura atual

- `api_football_sync.py`: fonte e reconciliador API-Football, orçamento/cache, snapshot de elencos.
- `output/serie-a-2026-coverage.json`: clubes obrigatórios e IDs Brasfoot observados nos arquivos locais.
- `src/app/Main.java` e `src/e/*.java`: leitura, escrita e verificação de serialização Java dos `.ban`.
- `build_preview.py`: conversão determinística a partir dos snapshots, com marcação de atributos estimados e hashes.
- `install_preview.py`: aplicação opt-in de previews com backup e rollback de arquivos `teams/*.ban` existentes.
- `transfer_windows.py`: gate conservador que identifica datas sem fazer chamadas à API.
- `site/`: site estático responsivo com estado de release; nenhuma credencial ou chamada autenticada do navegador.
- `.github/workflows/`: testes offline e verificação do calendário; **não publicam releases**.

**Gates planejados para produção:** cobertura de todos os clubes → consistência completa dos jogadores → atributos confiáveis → compatibilidade no jogo → documentação de licenças → executável gráfico assinado quando disponível → release pública → atualização de metadados do site.


## Atualização pós-release v2026.0.2

**Arquitetura de distribuição oficial:** `windows-installer/` (Go / Win32, manifesto v2/v3). O sistema Python em `installer/` é protótipo/legado e não compõe o executável público da v2026.0.2. O empacotamento Go aplica receitas diferenciais sobre arquivos da instalação do usuário, valida assinaturas/hashes e preserva saves; o schema v3 agora permite operações explícitas `add` e `replace`, com backup e restauração transacionais.

O pipeline de catálogo e divisões (156 IDs verificados) é um **subsistema informativo separado** do pacote jogável v2026.0.2 (20 equipes). A expansão de 136 arquivos ainda depende de dados do jogo, elencos e validação Windows; nenhum código atual comprova quatro divisões jogáveis.

## Migração Mega Patch 2026.4.0

A fonte de edição é `config/edition.json`. Os módulos produtivos agora incluem `fetch_sources` → `daily_update` → `world_snapshot`/`world_catalog`, separados de conversão gráfica e construção/publicação. O catálogo possui fontes e observações independentes da capacidade do jogo.

A distribuição segue `build_distribution` → assets em draft → digest do GitHub → pré-release → manifesto público → `publish_pages`. Windows, Linux e macOS usam o motor Go de atualização de arquivos; somente o frontend e a substituição atômica dependem do sistema. Isso não constitui port da engine do Brasfoot.

Os requisitos ainda não implementados estão em `config/specification-coverage.json`. O histórico de protótipos e os contratos anteriores foram preservados. A entrega atual omitiu testes a pedido do mantenedor.
