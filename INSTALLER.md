# Instalador Windows — implementação do motor e da interface

`installer/engine.py` realiza preflight offline, validação SHA-256, checagem das assinaturas de origem aprovadas por **arquivo**, backup verificado, cópia atômica, rollback e instalação repetível. `installer/gui.py` exibe uma interface nativa Tk/Segoe UI, sem terminal, com seleção de pasta, verificação, progresso por operações concluídas e resultado. O instalador não acessa a API-Football ou a rede.

## Condições de segurança para um pacote real

O gerador experimental `build_preview.py` ainda produz `schemaVersion: 1`, `kind: UNVERIFIED_PREVIEW_NOT_FOR_PUBLIC_RELEASE` e `publicationAllowed: false`. O instalador **recusa** esse formato. Não renomeie ou altere os marcadores manualmente: o formato novo só pode ser gerado após validação independente no jogo, e cada `acceptedOriginalSha256` precisa vir de um `.ban` original da versão realmente suportada.

O manifesto de distribuição é `schemaVersion: 2`, `kind: BRASFOOT_VERIFIED_PATCH`, com campos `version: 2026.x.y`, `patchSeason: 2026`, `publicationAllowed: true`, `compatibilityTestedInGame: true` e `files` de `teams/*.ban`, cada qual com `size`, `sha256` e `acceptedOriginalSha256` (hashes originais autorizados). Flags não constituem evidência por si só.

### Desenvolvedor

- Testar sem rede: `py -3 -m unittest discover -s tests -p test_*.py -q`
- Requer Python 3 no **build**, e PyInstaller instalado no Python do build Windows. O **usuário final não precisa de Python**.
- Após validar no Brasfoot e certificar o payload, gerar o executável com `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\release.ps1 -PackagePath .\payload -GamePath "C:\caminho\Brasfoot"`.
- O comando falha intencionalmente quando não existe payload aprovado ou quando o jogo não foi fornecido. `-Publish` ainda falha fechado: compilação isolada não autoriza release.

### Validação executada / pendências

65 testes Python integrados à v5 (62 aprovados, 3 ignorados), incluindo testes automatizados do motor em Linux com fixtures sintéticas: integridade, caminho inválido, arquivo modificado, symlink, repetição, cancelamento, backup, preservação de saves, rollback e instalação parcial. A interface Tk passou na compilação sintática e em teste de abertura/navegação inicial no Linux usando Xvfb; a execução real no Windows segue pendente. **Pendente:** build PyInstaller em Windows, teste visual real, abertura dos arquivos `.ban` no Brasfoot, política de cancelamento sob bloqueio de arquivo e teste da limpeza do instalador. Não publicar `.exe` até resolver essas dependências.

Nenhum mecanismo de autoexclusão foi ativado sem teste no Windows. Os temporários usados pelo PyInstaller são responsabilidade do empacotador, e os backups são preservados.
