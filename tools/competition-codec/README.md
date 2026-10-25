# Codec de configurações nacionais e estaduais do Brasfoot 22–23

Ferramenta de leitura e serialização Java baseada em campos e `serialVersionUID` observados em **27 arquivos legítimos fornecidos privadamente pelo usuário**. Nenhum arquivo binário do jogo é versionado ou redistribuído neste diretório. Compatível com JDK 21.

## Classes identificadas

- `est.ArrayLigaType` (UID 1) contém `ArrayList<ConfigLigaType>`.
- `est.ConfigLigaType` (UID 16) contém `divisao`, `nTimes`, `nGrupos`, `pais`, `nomeDivisao`, regras de promoção e rebaixamento, além de arrays booleanos.
- `est.ArrayLigaEType` (UID 1) contém `ArrayList<ConfigEstadualType>`.
- `est.ConfigEstadualType` (UID 1) contém `divisao`, `id`, `formula`, `nRebaixados` e `finaisIdaVolta`.

## Compilar e testar

Na raiz do repositório, com um JDK 21 instalado:

```bash
javac -encoding UTF-8 -d tools/competition-codec/classes tools/competition-codec/src/est/*.java tools/competition-codec/src/app/*.java
java -cp tools/competition-codec/classes app.CodecSelfTest
```

O teste sintético não requer o jogo, Internet ou API-Football.

Ler as configurações originais, sem modificar nada:

```bash
java -cp tools/competition-codec/classes app.CompetitionCodec inspect "/caminho/conf_ligas_nacionais/BRA.cfg"
```

Fazer prova de round-trip (destino **fora da instalação**):

```bash
java -cp tools/competition-codec/classes app.CompetitionCodec roundtrip "/caminho/conf_ligas_nacionais/BRA.cfg" "/diretorio-de-laboratorio/BRA-copia.cfg"
```

Gerar **somente uma simulação isolada** da Série D com 96 clubes e 16 grupos:

```bash
java -cp tools/competition-codec/classes app.CompetitionCodec trial-serie-d-96 "/caminho/conf_ligas_nacionais/BRA.cfg" "/diretorio-de-laboratorio/BRA.cfg"
```

O modo `trial-serie-d-96` verifica as quatro divisões e os valores originais, modifica apenas `nTimes: 64 → 96` e `nGrupos: 8 → 16`, reserializa, confirma a leitura e rejeita alterações além dos dois bytes esperados. **Não modifica o Brasfoot, não altera saves e não prova que a implementação interna do jogo suporte 16 grupos ou 96 participantes. Não distribuí-lo como patch pronto.**

## Evidência da análise privada em 25/10/2026

- `BRA.cfg`: quatro divisões nacionais com `nTimes` 20, 20, 20, 64 e `nGrupos` 0, 0, 0, 8.
- `ESP.cfg`: quatro divisões, com formatos próprios: 20, 22, 10, 30 equipes.
- `conf_estadual/*.ces`: 25 arquivos; todos contêm quatro divisões estaduais.
- **27/27 round-trips Java 21 idênticos byte a byte.**
- Cópia experimental `BRA.cfg`: **somente dois bytes diferentes**, mantendo tamanho de 1.089 bytes. Esta é evidência de **serialização válida**, não de jogabilidade.
- Novos elencos, novos clubes, divisão dos grupos, participação e promoção/rebaixamento **ainda não foram testados** com o Brasfoot em execução.

**A release pública v2026.0.2 não é alterada por este trabalho.**
