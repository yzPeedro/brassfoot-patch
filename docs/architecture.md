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
