# Clubes e divisões nacionais — 2026

**Estado: catálogo de participantes verificado; instalação das novas divisões NÃO validada.**

Fonte de dados: `data/competitions/2026-brazil.json`. O arquivo distingue clube por ID persistente (`br-{nome-normalizado}-{UF}`), nome, UF, divisão e grupo da Série D. A UF evita confundir Botafogo-RJ, Botafogo-SP e Botafogo-PB, por exemplo.

| Série | Participantes em 2026 | Presença no instalador v2026.0.2 |
|---|---:|---|
| A | 20 | Elencos experimentais dos 20 clubes |
| B | 20 | **Não incluída** |
| C | 20 | **Não incluída** |
| D | 96 | **Não incluída** |
| Total | **156 clubes distintos** | **20 com elenco na release** |

## Fontes oficiais da CBF

- Série A: https://www.cbf.com.br/futebol-brasileiro/times/campeonato-brasileiro/serie-a/2026
- Série B (regulamento, Anexo A): https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/REC_Brasileiro_Serie_B_2026_85d55b9f72.pdf
- Série C (regulamento, Anexo A e B): https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/REC_Brasileiro_Serie_C_2026_f894bdfed3.pdf
- Série D (grupos A1–A16, seis por grupo): https://www.cbf.com.br/futebol-brasileiro/noticias/selecao-masculina/selecao-escalada-para-pegar-os-eua/cbf-divulga-grupos-da-serie-d-de-2026

Os 156 clubes pertencem à temporada 2026 e **não** são propagados automaticamente para 2027. A Série C terá 24 clubes em 2027 e 28 em 2028 conforme comunicado da CBF.

## Limites técnicos pendentes

1. Investigar em uma instalação real quais arquivos definem ligas, divisões e participação; os `.ban` analisados descrevem equipes, não provam que quatro divisões possam ser disputadas.
2. Resolver os identificadores Brasfoot dos 136 clubes fora da Série A por evidência independente, não por similaridade fuzzy.
3. Obter elencos e atributos verificáveis, convertê-los ao formato do jogo e testar sem alterar saves.
4. Validar escudos e uniformes atuais, formatos exatos de imagem, origens e direitos antes de distribuição.
5. Preservar a release v2026.0.2 enquanto a ampliação não tiver validação funcional.

**Não publicar um patch chamado "156 clubes instalados" com base apenas neste catálogo.**

## Prova binária de configuração de quatro divisões — 25/10/2026

Os **27 arquivos de configuração fornecidos privadamente** foram reconstruídos por um codec Java (UIDs compatíveis). O arquivo nacional `conf_ligas_nacionais/BRA.cfg` contém quatro instâncias de `est.ConfigLigaType` (UID 16), chamadas Série A/B/C/D, com `nTimes=20/20/20/64` e `nGrupos=0/0/0/8`. Os 25 `conf_estadual/*.ces` contêm quatro divisões estaduais cada, em `est.ConfigEstadualType` (UID 1).

O teste offline fez **27 round-trips idênticos byte a byte**. Uma cópia isolada de `BRA.cfg` aceitou na serialização `nTimes=96` e `nGrupos=16`, com só dois bytes distintos do original. Isso **não comprova** que o jogo possa simular o novo calendário nem que os 96 participantes estejam vinculados à liga: a composição das equipes **não consta desses objetos de configuração**.

A implementação está em `tools/competition-codec/`. Os binários proprietários do jogo permanecem privados. A v2026.0.2 pública não foi alterada.
