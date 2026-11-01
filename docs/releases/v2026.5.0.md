# Brasfoot Mega Patch 2026.5.0

Esta versão traz o **campo animado ao vivo**. A tela original da partida ganha um espaço entre o cabeçalho e a tabela de outros jogos, onde aparecem os 22 jogadores, a bola e o árbitro em um campo 2D.

## O que aparece no campo

- Gols, cartões, faltas com barreira, pênaltis, lesões e substituições, sincronizados com o momento em que o Brasfoot os registra no cabeçalho.
- Finalizações, desarmes, erros de passe e faltas acompanham as estatísticas oficiais da partida.
- A formação segue as posições do elenco. Estilo de jogo, marcação e foco de ataque mudam a movimentação.
- O gramado é desenhado conforme a condição do jogo (Excelente, Muito Boa, Ruim ou Precária).
- No início de cada tempo, a bola fica no centro e os jogadores entram pela lateral até suas posições.
- Pênalti: a escolha do batedor continua sendo feita no Brasfoot. Depois dela, o batedor vai até a marca, para e bate, e a tela de cobrança do jogo decide o resultado.
- A tecla de espaço abre a pausa imediatamente.

## Como funciona

A animação é uma representação visual. Os resultados, autores, cartões, substituições e estatísticas continuam sendo os do Brasfoot. Para sincronizar o campo com o cabeçalho, o passo de simulação do minuto seguinte da partida assistida é executado um pouco antes, com os mesmos dados que o jogo usaria, e o minuto avança quando o lance animado chega ao seu momento principal. Se a animação encontrar qualquer problema, ela é reiniciada e o jogo segue normalmente.

## Compatibilidade

Os elencos são os mesmos da 2026.4.7. O instalador reconhece o jogo original, as versões anteriores do patch e as prévias do campo animado. Nenhum teste funcional, suíte, navegador ou gameplay foi executado nesta produção; foram realizadas compilação produtiva, verificação de bytecode e conferência de integridade e publicação.
