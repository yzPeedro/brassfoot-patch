# Editor seguro de elencos brasileiros do Brasfoot 22–23

Este módulo reconstrói **um arquivo `.ban` fornecido pelo proprietário da instalação**, com jogadores reais organizados em uma planilha TSV. Não distribui cópias dos arquivos originais do jogo. O código conserva os campos `e.t`/`e.g` cuja serialização foi verificada anteriormente.

## Progresso real

- **Criciúma:** 29 nomes e posições retirados do [elenco profissional oficial](https://mail.criciumaec.com.br/equipes/elenco-profissional), consulta de 25/10/2026.
- O arquivo original privado `criciuma_bra.ban` tem SHA-256 `5eabaec785b1bffa23692dbd04718cf938cc8caecee02c94dcbaa40659b0ba94`, ID `2226` e 22 atletas históricos.
- Em laboratório local, o editor recriou um time com **29 atletas** e produziu serialização Java válida com round-trip exato. Preservou IDs/atributos históricos dos quatro jogadores correspondentes; os outros **25** ainda precisaram de estimativas de idade, nacionalidade e atributos. **Não é um elenco homologado para release.**
- A receita diferencial de laboratório reconstruiu o mesmo resultado com 48 operações, 1.636 bytes de dados alterados, sem redistribuir o original. SHA-256 experimental do destino: `334bb75defb31d1035f05d87b961d7a0cbfba2799546303c6ba05c4898e38e3e`.
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

## Identificadores seguros e testes adicionais

Na base original, **Athletic, Amazonas, Anápolis, Barra, Inter de Limeira e Itabaiana têm ID interno 0**; **São Paulo e São Bernardo compartilham ID 2477**. Portanto, o editor não usa mais `team.id` como namespace para IDs de jogadores adicionados: deriva o namespace do SHA-256 específico do arquivo original. Os namespaces resultantes dos **59 arquivos existentes das Séries A/B/C** foram comparados localmente e são diferentes entre si. O Maranhão ainda precisa de arquivo legítimo novo.

Foram gerados dois patches diferenciais privados e os dois foram reconstruídos byte a byte pelo **motor Go do instalador** em teste local. O laboratório não publica os arquivos resultantes; seus metadados acima foram atualizados após a correção do namespace de IDs.


## Mais elencos oficiais reproduzidos em laboratório — 25/10/2026

Além de Criciúma e Londrina, foram confirmados diretamente nos sites dos clubes:

- [Cuiabá](https://www.cuiabaesporteclube.com.br/futebol/5/time-profissional/): **25 atletas** com posição, original `cuiaba_bra.ban` (ID 2232; SHA-256 `a13007e58a381fd45f393c4f03e41f09bd4ec859a274f15dbb0484ce4030d722`). Laboratório: 3 históricos reaproveitados, 22 novos com atributos estimados; alvo SHA-256 `3babfdee3410f62fa528795e4e8fd1d746ea735d5e299ccbd8b140caa74aae57`. Receita diferencial: 72 operações, 1.249 bytes adicionados.
- [Juventude](https://www.juventude.com.br/plantel/profissional): **36 atletas** com posição, original `juventude.ban` (ID 2335; SHA-256 `8aa0d733f9e776ca1954728211004dcd7f6313017d10c2f9a505445fb9610cd0`). Laboratório: 0 históricos reaproveitados, 36 com atributos estimados; alvo SHA-256 `380708953471d0f23c8cf8ceba44ba25e3ec1673531d17fe21c2bf29d9f55ae2`. Receita diferencial: 24 operações, 2.289 bytes adicionados.
- **Total neste laboratório:** quatro clubes da Série B, **119 nomes e posições publicados em fontes oficiais**, com quatro arquivos de equipe reserializados e **quatro reconstruções diferenciais byte-idênticas aprovadas no motor Go** em teste local.

Todos os arquivos de saída do laboratório ficaram **fora da instalação e do GitHub**; sem dados de identidade completos ou teste em carreira, nenhum deles foi anunciado como pronto para o usuário instalar.
