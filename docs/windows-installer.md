# Instalação Windows — estágio experimental

`install_preview.py` é um instalador de teste via CLI, **não um GUI**. Requer consentimento explícito, instalação com `teams/` e `options.bcf`, arquivos `.ban` existentes, hashes válidos, backups fora do jogo e integridade após substituição. Em falha tenta rollback; logs de falha são gravados na pasta de backup. `sav/` não é tocado. O teste automatizado injeta erro após o primeiro arquivo e verifica recuperação.

Pendência: Windows WPF/.NET LTS self-contained, UI premium, barra de progresso real, fluxo em telas, verificação de jogo em uso, restauração manual por UI, verificação do instalador no Windows, política transparente de exclusão pós-instalação. **Não executar a prévia em instalações com saves importantes sem cópia de teste.**
