# Instalador Windows — motor transacional e GUI no código-fonte

O instalador anterior `install_preview.py` permanece somente para testes experimentais. A nova implementação está em `installer/engine.py` (mecanismo offline de arquivos `.ban`) e `installer/gui.py` (interface Tk, seleção de pasta, verificação, instalação, progresso e conclusão). `installer-entry.py` serve de entrada para o empacotamento Windows via PyInstaller.

O motor suporta backups externos, hashes SHA-256, rejeição de path traversal, symlinks e instalações desconhecidas, restauração com verificação e detecção de patch já instalado. O manifesto de distribuição exige `schemaVersion: 2`, `kind: BRASFOOT_VERIFIED_PATCH`, `publicationAllowed: true` e `compatibilityTestedInGame: true`, além de hashes originais aprovados por arquivo. Esses metadados só poderão ser produzidos depois da validação real; flags sozinhas não comprovam compatibilidade.

**Evidência obtida:** 11 testes automatizados do motor com fixtures sintéticas em Linux, incluindo falha injetada após substituição, rollback, preservação de saves e idempotência. Compilação sintática da interface concluída.

**Não concluído:** produção/teste do .exe no Windows, validação dos .ban no jogo, uma release pública, teste gráfico, autoexclusão autorizada do executável e URL de download. Não publicar o preview como patch final. Consulte `INSTALLER.md` e `release.ps1` para os gates de build.
