# Segurança

- `API_FOOTBALL_KEY` é segredo de execução; nunca no site nem no instalador. DPAPI local herdada pode ser usada no Windows. `.env` e cache são ignorados no Git.
- Não existe indício de chave literal nos arquivos analisados; histórico do Git remoto não disponível para inspeção.
- API com limites, timeouts e retry apenas transitório; relatórios sem valores de credenciais.
- Leitor Java aplica allowlist de classes e tamanho máximo; ainda requer avaliação adicional de dados corrompidos.
- Instalador local aceita apenas `teams/*.ban` pré-existentes, rejeita path traversal/symlinks, exige SHA-256 e backup externo.
- Site não possui chave, não chama API-Football e mantém download desabilitado em estado não publicado.
- Verificar licenças de logos, uniformes, API-Football, marca Brasfoot e dados antes de qualquer redistribuição.
- SHA-256 verifica integridade mas não substitui assinatura digital de autenticidade.
- A automação de release permanece bloqueada.
