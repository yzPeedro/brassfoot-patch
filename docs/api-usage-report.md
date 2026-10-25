# Economia da API-Football — execução de 25/10/2026

| Métrica | Resultado comprovável |
|---|---|
| Clubes catalogados com informação pública da CBF | **156** |
| Série A/B/C/D | **20/20/20/96** |
| API-Football consultada **nesta execução** | **0 requisições** |
| Resolução de identidades do catálogo via API-Football | **0** |
| Resolução do catálogo sem API | **156/156 (100%)** |
| Saldo real da chave da API | **não consultado/não conhecido** |
| Chamadas economizadas em relação a consulta por clube | **não mensuradas** |
| Dados obtidos do cache no processo atual | **não mensurados** |
| Endpoints API-Football acionados | **nenhum** |
| Retries API-Football | **0** |
| Pendências | elencos B/C/D, ativos visuais, vínculos com arquivos do Brasfoot |

A taxa de resolução sem API refere-se **somente à composição oficial dos clubes e divisões**; ela não mede elencos nem assets.

## Proteção implementada

`quota_guard.py` cria um ledger SQLite durável com teto local conservador de **90 tentativas por dia UTC**, reservando 10 para margem. `api_football_sync.py` passa a reservar um slot antes de **cada tentativa de rede, incluindo retries**. Respostas podem reduzir o saldo permitido com o cabeçalho oficial `x-ratelimit-requests-remaining`, nunca ampliá-lo. O ledger grava apenas o SHA-256 da chave, nunca a credencial.

**Limitação essencial:** SQLite coordena processos que apontam para **o mesmo banco**. Execuções em hosts diferentes, GitHub Actions e aplicativos alheios ao projeto não são coordenados globalmente por esse arquivo. A quota do provedor é compartilhada; para garantir orçamento global entre ambientes, é obrigatório um ponto único de passagem/ledger compartilhado confiável e reconciliar o saldo com o provedor. **Não considerar CAN22 totalmente aprovado ainda.**

`API_QUOTA_DB` permite especificar o caminho do ledger. Nenhuma requisição foi necessária para construir o catálogo.
