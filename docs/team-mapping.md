# Resolução de clubes

1. Se existir mapeamento persistente **completo, válido e único** de 20 IDs brasileiros, usá-lo sem nova consulta ao catálogo.
2. Senão, consultar catálogo por país uma vez; aceitar apenas equivalência exata normalizada entre o nome do Brasfoot e aliases explícitos.
3. Se um clube não aparecer, usar no máximo uma pesquisa adicional sanitizada por clube não resolvido; aceitar somente um clube com país `Brazil` e nome equivalente.
4. Se aparecerem IDs diferentes ou dados conflitantes, bloquear a coleta de elencos e gerar relatório.
5. Nunca promover sugestões aproximadas do relatório a correspondências finais automaticamente.
6. Persistir os 20 IDs após reconciliação completa; qualquer mudança posterior de ID é motivo para bloqueio e verificação externa.

Regressões automatizadas: Atlético-MG versus Atlético-GO; Chapecoense-SC e Chapecoense AF; país incorreto; duas coincidências; nomes acentuados/hifenizados; cache corrompido; mudança suspeita de ID.

**Não confirmado:** quais eram os nomes exatos do Atlético-MG e da Chapecoense no catálogo real do usuário que falhou.
