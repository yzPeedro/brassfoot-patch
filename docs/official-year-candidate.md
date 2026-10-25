# Montagem isolada de executável experimental (somente seletor 2026)

O instalador oficial do desenvolvedor está em
https://www.brasfoot.com/download22/brasfoot22-23.exe. O setup NÃO é o
executável do jogo: dentro dele há um bf22-23.exe (PE com JAR anexado).
O projeto não versiona ou redistribui nenhum desses binários.

## Evidências verificadas para a versão oficial

- Setup oficial: SHA-256 8e3c7a77768d551a1f3c722ef2447c3e451af830613e8a65de33f35bc0e2b33d.
- bf22-23.exe interno: 7.320.384 bytes, com 2.193 arquivos e 1.038 classes Java no JAR anexado.
- Classe seletora a/hU.class, SHA-256 original: 37fb17d876aab1263756bca97c3f9488007b7afe59f8c68494cf711a0f61a234.
- tools/patch_official_career_year.py gera em laboratório a classe modificada de SHA-256: 9cb4b93ff5bc52bfe364c545128ecc69c7d5615d1c09d6ba01ca34d4c35dc591.
- As classes best/f.class e best/p.class também possuem fingerprints estritos. A referência 2023 dentro de best/p.class ainda NÃO foi corrigida porque sua finalidade no calendário não foi comprovada.

## O que faz o gerador de laboratório

tools/build_official_year_candidate.py valida o perfil conhecido do jogo,
preserva o prefixo PE, reconstrói o ZIP/JAR com apenas a/hU.class alterada e
confere os dados descompactados de todos os outros recursos. Gera um novo EXE
fora da pasta do Brasfoot. Nunca executa o setup, instala, altera saves ou
substitui arquivos do usuário. Rejeita hashes desconhecidos, arquivos ZIP
ambíguos, destino já existente e saída dentro da pasta original.

Exemplo EXCLUSIVAMENTE experimental:

    python tools/build_official_year_candidate.py --original-exe CAMINHO_ORIGINAL/bf22-23.exe --output-exe CAMINHO_FORA_DO_JOGO/brasfoot-2026-candidate.exe --experimental

## Limitações que impedem distribuir esta versão

Este protótipo NÃO é o patch definitivo. Reempacotar um JAR dentro de um
launcher Windows pode afetar sua execução. A ferramenta não substitui o
executável instalado, não assegura a carreira real em 2026 e NÃO altera a
composição das Séries A/B/C. Série D, BRA.cfg e saves permanecem intocados.

Os testes sintéticos em tests/test_build_official_year_candidate.py verificam
as condições de isolamento e integridade, não o funcionamento do Brasfoot.

Ainda é necessário validar best/p.class, calendário 2026/2027, clubes e ligas
A/B/C, iniciar uma carreira no Windows real e só então integrar um patch
diferencial com backup/rollback ao instalador Go.
