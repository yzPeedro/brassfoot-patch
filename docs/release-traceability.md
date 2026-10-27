# Rastreabilidade de release

`tools.release_traceability.validate_traceability` define a barreira offline
para vincular uma release a quatro identidades: versão, commit Git, snapshot e
SHA-256 do artefato. O contrato apenas valida metadados fornecidos; não busca
GitHub, não altera manifestos e não declara gameplay, calendário ou saves
validados.

Uma publicação só pode preencher esses campos depois que o commit, o snapshot
e o artefato forem realmente produzidos e conferidos. Valores de fixtures dos
testes não são evidência de uma release pública.
