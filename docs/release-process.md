# Processo de release

## Estado em 25/10/2026

A **v2026.0.2 (experimental)** é pública:
https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.0.2

Instala elencos de **20 clubes da Série A** e preserva saves por escopo de escrita, com backup/rollback/desfazer. Limitações: 730 atletas incluídos, 713 com características estimadas, 15 não incluídos. Não declarar cobertura das Séries B, C ou D.

O repositório possui uma expansão de código em curso: catálogo oficial de 156 clubes e motor Go V3 capaz de adicionar arquivos de equipe e instalar lotes variáveis. A interface pública/instalador da v2026.0.2 **não muda automaticamente** com esses commits.

## Gates para uma nova release com 156 clubes

1. Resolver os vínculos de clubes e IDs do Brasfoot para todos os participantes que serão instalados; provar que as estruturas reais do jogo aceitam novos arquivos e as divisões alegadas.
2. Coletar e validar elencos, posições e atributos; não anunciar como oficiais valores estimados.
3. Validar assets: temporada, formato real, associação com a equipe, origem e autorização de redistribuição. Nunca incluir imagens apenas porque são públicas na internet.
4. Gerar manifestos e receitas com integridade SHA-256 e flags somente após evidências.
5. Testar pacote completo, backups, rollback, restauração, preservação de saves e instalação incremental.
6. Compilar e **executar** o instalador no Windows e testar em instalação isolada do Brasfoot, com carreira nova e verificação de clubes/divisões.
7. Publicar tag e Release separadas da v2026.0.2, conferir asset público/tamanho/hash e só então atualizar o site.
8. Preservar a release atual até a nova passar integralmente os gates.

GitHub Actions não é requisito para publicação manual com GitHub CLI (`gh`), mas nenhum fluxo deve contornar testes ou direitos de distribuição.
