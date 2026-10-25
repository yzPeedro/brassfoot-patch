# Pipeline de dados

`/teams?country=Brazil` → reconciliação por ID/nome exato/alias → fallback pontual `teams?search=...` → `/players/squads?team={id}` → validação dos elencos → snapshot `data/.../YYYY-MM-DD/snapshot.json`.

O snapshot registra fonte e data; representa *elenco atual* na data da coleta, não uma foto histórica garantida da janela. Cada elenco exige pelo menos 11 atletas, IDs positivos e únicos, nomes preenchidos e posições da API reconhecidas. `build_preview.py` exige 16–40 jogadores e idade real 16–55. Provas de cobertura completa, nacionalidades, detalhamento das posições e ratings não estão disponíveis no endpoint gratuito; valores inferidos são auditados no manifesto da prévia. Não existe pipeline de publicação automática ainda.
