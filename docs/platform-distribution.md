# Distribuição atual — 2026.4.1

Release final para Windows x64, Linux x64/ARM64 e macOS x64/ARM64. Instala diretamente sobre o Brasfoot 22–23 original ou bases V4/2026.3.5/2026.4.0 com hashes reconhecidos.

O Windows usa a interface gráfica. Linux/macOS usam o utilitário e seletor de pasta; o jogo requer Wine/CrossOver ou outra camada de compatibilidade configurada pelo usuário. As builds não incluem o jogo.

`tools/build_distribution.py` compila a edição e vincula artefatos ao commit, bundle e snapshot. `tools/publish_distribution.py` publica uma release final/latest, envia os aliases permanentes e só depois grava os dois manifestos do site. O botão Baixar usa `/releases/latest/download/Brasfoot-Mega-Patch-*`, inclusive quando os metadados estão em cache.

A publicação solicitada dispensa testes; compilação e hashes não são prova de execução do jogo nas plataformas. A cobertura real e os atributos derivados estão documentados nas notas da release.

