# Política de fontes dos elencos — 2026

## Objetivo
Usar **365Scores como fonte preferencial de conferência** dos jogadores/posições dos 60 clubes A/B/C. Usar páginas oficiais e CBF em divergências de inscrição, transferências e datas. API-Football como fallback **desativado por padrão**; não consumir requisições desnecessárias.

Não assumir que jogadores mostrados em outubro eram titulares ou inscritos em toda a temporada. Registrar URL, data da consulta e posição conferida por clube. A existência de um nome no 365Scores não valida automaticamente contrato atual.

## Condições de uso
- Referenciar URLs públicas por links.
- **Não raspar automaticamente em massa** nem espelhar bases, imagens ou marcas de terceiros sem permissão/licença; preferir consulta editorial e dados cuja reutilização esteja autorizada.
- O instalador deverá operar **offline**, com receitas verificadas do projeto. Nada de depender da conexão do usuário à fonte externa.
- Idades, nacionalidades e atributos estimados devem ser assinalados no relatório. Nenhum campo inventado poderá ser promovido a "verificado" por padrão.

## Conversão de posições da fonte para o Brasfoot
| Posição observada | Código Brasfoot |
| --- | --- |
| Goleiro | 0 |
| Lateral direito/esquerdo, ala direito/esquerdo | 1 |
| Zagueiro central, zagueiro, defensor central | 2 |
| Volante, meia central, meia, meia atacante | 3 |
| Centroavante, ponta direita/esquerda, atacante | 4 |

Não inferir a posição de um jogador rotulado somente como "defensor"; conferir se é lateral ou zagueiro.

## Referências públicas conferidas em 26/10/2026
- Cruzeiro: https://www.365scores.com/pt-br/football/team/cruzeiro-1213/squad
- Maranhão-MA: https://www.365scores.com/pt-br/football/team/maranhao-ma-12748/squad
- Maringá: https://www.365scores.com/pt-br/football/team/maringa-18884/squad

Estes 3 exemplos **não significam revisão de 60 clubes**. O Maranhão ainda não tem um arquivo-base entre os 703 originais enviados.

## Requisitos da release corretiva v2026.3.5
1. Gerar 60 arquivos reais de equipe usando os originais, com IDs e clube corretamente reconciliados; preservar os arquivos da Série D.
2. Conferir a lista final de atletas e posições em cada arquivo, separar estimativas e indicar divergências de fonte.
3. Embutir as mudanças de todos os clubes A/B/C no **mesmo instalador V4**, com backup integral antes de alterar, preservação de saves/configurações e rollback.
4. Não declarar "atualizado" sem verificar os SHA-256 dos .ban e contar jogadores após instalar.
5. Testar em Windows, criar carreira em cada divisão e testar restauração e preservação dos saves.
6. **Bloquear release** se não houver validação dos 60 clubes; não alterar o download no site para um pacote parcial.

As 40 planilhas TSV B/C já presentes no projeto permitem uma geração **experimental de 39 deltas** pelo editor Java; ainda há atributos não validados e Maranhão sem arquivo-base. O relatório de laboratório deve manter o marcador de distribuição não autorizada até revisão real.
