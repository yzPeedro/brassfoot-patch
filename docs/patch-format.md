# Formato de equipes Brasfoot

- Extensão `.ban`, cabeçalho de Java Object Serialization `AC ED 00 05`.
- Classe principal ofuscada `e.t`; jogadores `e.g` em coleções serializadas.
- Codec Java com filtro de desserialização, tamanhos máximos e round-trip.
- A instalação do usuário comprovou 703/703 round-trips idênticos antes desta versão.
- `replace-roster` substitui exclusivamente a lista principal de jogadores e preserva dados do time e elenco secundário.
- Campos `g/h/hash/tid` exigem estudo adicional antes de considerar ratings reais em novos jogadores.
- `build_preview.py` preserva os campos de atletas correspondentes aos originais; jogadores novos usam template de atleta do mesmo clube/posição e isso é registrado em `inferredPlayers`.
- Não há prova de compatibilidade de patch modificado dentro do Brasfoot. Toda prévia tem `publicationAllowed=false`.
