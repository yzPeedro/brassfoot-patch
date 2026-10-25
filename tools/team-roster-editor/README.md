# Editor seguro de elencos brasileiros do Brasfoot 22–23

Este módulo reconstrói **um arquivo `.ban` fornecido pelo proprietário da instalação**, com jogadores reais organizados em uma planilha TSV. Não distribui cópias dos arquivos originais do jogo. O código conserva os campos `e.t`/`e.g` cuja serialização foi verificada anteriormente.

## Progresso real

- **Criciúma:** 29 nomes e posições retirados do [elenco profissional oficial](https://mail.criciumaec.com.br/equipes/elenco-profissional), consulta de 25/10/2026.
- O arquivo original privado `criciuma_bra.ban` tem SHA-256 `5eabaec785b1bffa23692dbd04718cf938cc8caecee02c94dcbaa40659b0ba94`, ID `2226` e 22 atletas históricos.
- Em laboratório local, o editor recriou um time com **29 atletas** e produziu serialização Java válida com round-trip exato. Preservou IDs/atributos históricos dos quatro jogadores correspondentes; os outros **25** ainda precisaram de estimativas de idade, nacionalidade e atributos. **Não é um elenco homologado para release.**
- A receita diferencial de laboratório reconstruiu o mesmo resultado com 40 operações, 1.716 bytes de dados alterados, sem redistribuir o original. SHA-256 experimental do destino: `840fd3e85f8bd6f384ff96b16ba15b77aaac7c83c525547580e3e5a8da92477b`.
- A ferramenta não altera nem precisa consultar `conf_ligas_nacionais/BRA.cfg`, saves ou a Série D.

## Compilar e testar

JDK 21 (Windows/Linux), a partir da raiz do projeto:

```bash
javac -encoding UTF-8 -d tools/team-roster-editor/classes tools/team-roster-editor/src/e/*.java tools/team-roster-editor/src/app/*.java
java -cp tools/team-roster-editor/classes app.RosterEditorSelfTest
python -m unittest discover -s tests -p 'test_team_delta.py' -v
```

Exemplo de **laboratório** com arquivos legítimos locais do usuário, sempre com saída fora do diretório de instalação:

```bash
java -cp tools/team-roster-editor/classes app.UpdateTeamRoster "/copia-privada/teams/criciuma_bra.ban" "tools/team-roster-editor/sources/criciuma-2026-official.tsv" "/laboratorio/resultado.ban" "5eabaec785b1bffa23692dbd04718cf938cc8caecee02c94dcbaa40659b0ba94" 2226 --lab-estimates
python tools/build_team_delta.py --original "/copia-privada/teams/criciuma_bra.ban" --candidate "/laboratorio/resultado.ban" --original-sha256 "5eabaec785b1bffa23692dbd04718cf938cc8caecee02c94dcbaa40659b0ba94" --filename "criciuma_bra.ban" --output "/laboratorio/resultado-delta.json"
```

Sem `--lab-estimates`, o editor recusa atributos estimados em jogadores novos. A revisão **não pode ser omitida** simplesmente por existir um nome em um site. Idade, nacionalidade e condições de inscrição na temporada devem ser verificadas com fontes confiáveis; as notas do site não equivalem a aprovação.

**Mapeamento de posições observado no arquivo original:** `0 = goleiro`, `1 = lateral`, `2 = zagueiro`, `3 = meio-campo`, `4 = atacante`. O conversor anterior de clubes fictícios usava uma convenção diferente; esta codificação foi extraída e conferida de um arquivo real do jogo, não presumida.

## Pendências

Para os outros 39 elencos B/C e a versão final A/B/C, ainda são necessários revisão dos vínculos atuais de cada atleta, atributos compatíveis, reconciliação dos arquivos de origem e testes reais de criação de carreira. **A atualização dos 60 clubes não foi publicada nem testada no jogo.** A Série D original e saves antigos permanecem intocados.
