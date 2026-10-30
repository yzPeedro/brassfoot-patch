# Brasfoot Mega Patch 2026.4.3

> **Versão substituída:** a 2026.4.3 impede a abertura da nova carreira. Instale a correção 2026.4.4.

Esta correção troca a referência fixa da Copa de 2022 pela última Copa masculina concluída, a edição de 2026.

## Alterações

- A tela inicial passa a escrever `Usar grupos da Copa do Mundo 2026`.
- A opção permanece marcada e a primeira Copa de uma carreira iniciada em 2026 usa sempre os grupos oficiais.
- A lista antiga de 32 participantes foi substituída pelas 48 seleções de 2026, nos grupos A a L.
- O formato passa a usar 12 grupos de quatro, com os dois primeiros e os oito melhores terceiros na fase de 32.
- O arquivo `config/world-cup-2026.json` registra participantes, grupos, identificadores internos e fontes da FIFA.

## Fontes

- Grupos e participantes: FIFA, composição oficial da Copa do Mundo de 2026.
- Convocações da edição histórica: lista oficial de 48 seleções publicada pela FIFA. A lista é preservada como fonte histórica; esta correção de engine atualiza participantes e estrutura do torneio, sem afirmar substituição individual de todos os jogadores dentro dos clubes.

## Produção e limites

O executável é produzido por adaptação reproduzível e limitada a quatro classes Java identificadas por SHA-256. Originais, saves e licenças não são alterados durante a compilação. Nenhum teste funcional, suíte, navegador ou gameplay foi executado, conforme instrução do proprietário. A integridade do contêiner, os hashes e a leitura do código compilado foram conferidos como etapas de produção, sem alegação de validação em jogo.
