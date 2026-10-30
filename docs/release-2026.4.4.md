# Brasfoot Mega Patch 2026.4.4

Correção emergencial da versão 2026.4.3. Ela elimina o carregamento infinito ao criar uma nova carreira e mantém integralmente a atualização da Copa do Mundo de 2026.

## Correção

- Corrigido o `VerifyError` da JVM no método `best.f.isUsarGruposReaisCopa`, que interrompia a inicialização antes da tela de configurações.
- O método que mantém a Copa de 2026 ativada foi recompilado e transplantado como bytecode Java válido, sem instruções residuais.
- A opção continua a escrever `Usar grupos da Copa do Mundo 2026` e permanece marcada.
- Foram preservados os 48 participantes, os 12 grupos oficiais de quatro seleções e a classificação dos oito melhores terceiros.
- A 2026.4.4 substitui integralmente a 2026.4.3 com defeito.

## Produção e limites

O executável foi reconstruído a partir da versão 2026.4.2 publicada, identificada por SHA-256. A integridade do contêiner, os hashes e o código compilado foram conferidos. Nenhum teste funcional, suíte, navegador ou gameplay foi executado, conforme instrução do proprietário. Saves, licenças, originais e a instalação existente não foram alterados durante a produção.
