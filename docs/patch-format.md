# Formatos de patch — situação atual

A versão pública **v2026.0.2** utiliza Go e receitas de atualização diferencial: `schemaVersion:2`, arquivos `teams/*.ban` preexistentes, hashes originais aceitos e digest do arquivo resultante.

A expansão em desenvolvimento adicionou `schemaVersion:3` com `operation: replace` ou `operation: add`. `replace` exige original conhecido. `add` aceita arquivo inexistente ou já instalado com digest idêntico, bloqueia colisões, integra rollback/restauração e exige receita de bytes finais verificada por SHA-256. O código Go antigo permanece compatível com schema 2. **Os testes estruturais de adição não comprovam que o Brasfoot reconheça um novo ID de equipe nem o suporte a quatro divisões.**

## Histórico técnico pré-v2026.0.2

# Formato de equipes Brasfoot

- Extensão `.ban`, cabeçalho de Java Object Serialization `AC ED 00 05`.
- Classe principal ofuscada `e.t`; jogadores `e.g` em coleções serializadas.
- Codec Java com filtro de desserialização, tamanhos máximos e round-trip.
- A instalação do usuário comprovou 703/703 round-trips idênticos antes desta versão.
- `replace-roster` substitui exclusivamente a lista principal de jogadores e preserva dados do time e elenco secundário.
- Campos `g/h/hash/tid` exigem estudo adicional antes de considerar ratings reais em novos jogadores.
- `build_preview.py` preserva os campos de atletas correspondentes aos originais; jogadores novos usam template de atleta do mesmo clube/posição e isso é registrado em `inferredPlayers`.
- Não há prova de compatibilidade de patch modificado dentro do Brasfoot. Toda prévia tem `publicationAllowed=false`.
