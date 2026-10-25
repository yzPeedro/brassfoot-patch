# Adaptadores seguros do ano inicial de carreira (2026)

## O que foi implementado

`tools/patch_official_career_year.py` agora separa a transformação de bytecode
da identificação da versão. A função `patch_verified_variant(original,
expected_sha256=..., source_years=(inicio, fim))` exige SHA-256 **exato do
`a/hU.class` de origem**, assinatura estrutural dos dois valores de ano,
referências de `JComboBox.addItem`, índice de preferência e literais numéricos
da rotina que comunica o ano ao motor. Uma divergência aborta a transformação.

A função original `patch_official(original)` e a interface de linha de comando
**permanecem limitadas** ao fingerprint oficial já analisado, que oferece
2022/2023. Não é permitido usar a variante 2023/2024 em uma instalação real
antes de identificar seu hash e verificar o fluxo completo do motor.

## Teste regressivo

`tests/test_patch_official_career_year.py` possui dois cenários de laboratório
com classes Java sintetizadas: fonte 2022/2023 e fonte 2023/2024.
Cada cenário precisa comprovar que a classe transformada exibe somente 2026,
inicia o campo do motor em 2026 para a preferência antiga 0 **e** 1, conserva
o comprimento do classfile e recusa bytecode com fingerprint diferente.

Os testes sintéticos não homologam saves, calendário, divisão ou o Brasfoot
proprietário. O bytecode transformado do jogo não deve ser publicado no repo.

## O que ainda é obrigatório para distribuir

1. Identificar o SHA-256 da instalação 2023/2024 usada pelo consumidor e da
   classe original `a/hU.class`, sem alterá-la.
2. Confirmar que a classe, o `JComboBox`, o setter de motor e referências
   de 2023/2024 são de fato equivalentes à assinatura testada.
3. Registrar a variante na allowlist interna somente após revisão e manter
   o rejeite conservador para hashes desconhecidos.
4. Gerar patch diferencial, nunca publicar executável completo de terceiros.
5. Executar instalação/rollback e abrir carreiras reais A/B/C com o ano
   selecionado 2026, checando save, calendário, virada, divisões e
   preservação da Série D.

**Estado:** mecanismo de transformação parametrizado disponível para
investigação controlada. Compatibilidade da instalação 2023/2024 não homologada.
