# Histórico real e simulação

`tools/history_records.py` define um ledger offline e fail-closed para separar fatos históricos concluídos, estado corrente e resultados gerados por uma carreira simulada.

Registros `historical` exigem data ISO, fonte HTTPS e confiança explícita (`high`, `medium` ou `low`). Registros `current` e `simulated` não recebem automaticamente status histórico nem podem ser usados como prova de uma competição concluída. IDs são estáveis dentro do ledger, duplicatas são rejeitadas e a exportação JSON é determinística.

O contrato usa apenas dados fornecidos localmente. Os testes usam fontes HTTPS sintéticas e não comprovam nenhum resultado esportivo real, atualização diária, gameplay, calendário ou licenciamento.
