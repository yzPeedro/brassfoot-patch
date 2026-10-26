# Séries A, B e C — elencos reais de 2026

## Escopo confirmado

**A, B e C:** 20 equipes cada, com nomes verdadeiros de atletas verificados contra fontes relevantes para 2026. **Série D não será modificada**: nenhum arquivo `teams/*.ban` de seus clubes, nem `conf_ligas_nacionais/BRA.cfg`, nem seus grupos serão tocados pelo futuro pacote.

## O que já existe

- **Prévia pública v2026.0.2:** 20 clubes Série A, **730 jogadores realmente incluídos no instalador**, dos 745 inicialmente coletados; 713 com atributos estimados. Esses 730 nomes foram extraídos em ambiente isolado dos 20 `.ban` instaláveis, conferidos por SHA-256 contra o manifesto da release, e apresentados em `site/data/published-rosters-2026-0-2.json`.
- **Site:** tabela paginada com busca sem acentos, filtros de divisão e status; modais exibem os 730 nomes exatamente como aparecem no patch. Para B/C, ainda não existe elenco real de 2026 validado nem publicado.
- **40 equipes B/C:** todas catalogadas em `site/data/target-abc-2026.json`. Implementado `collect_abc_rosters.py` para coleta de até 40 elencos com reconciliação conservadora dos clubes, cache e limite de tentativas.
- **Testes:** website regression (incluindo interação simulada de paginação, filtros, modal e foco) e testes offline do coletor aprovados no GitHub Actions. Um teste de ponta a ponta simula 40 elencos com dados sintéticos **somente dentro das fixtures de teste**, sem publicar jogadores falsos.
- **Série D:** zero processamento e zero chamadas à API para clubes dessa divisão no novo pipeline.

## Dados ainda pendentes

**Os dados reais dos jogadores dos 40 clubes B/C não estão no cache disponível neste ambiente.** O novo coletor não executou consultas reais; **zero requisições à API-Football foram realizadas nesta etapa**. O endpoint `/players/squads` fornece um plantel observado na coleta e **não comprova sozinho** a temporada histórica de 2026. Será preciso revisar os elencos e datas da fonte antes de afirmar 100% da temporada.

A ausência de snapshots ou a identificação ambígua de um clube bloqueiam o processo. Cada elenco exige jogadores com IDs únicos, posição reconhecida e quantidade compatível com o formato do Brasfoot; uma equipe com mais de 40 jogadores exige decisão explícita e registro das exclusões, sem fingir cobertura integral.

## Como executar a coleta (em ambiente com cache ou chave legítima)

Na raiz do repositório:

```powershell
# Só reaproveita arquivos do cache local; não usa rede e não exige chave.
py -3 collect_abc_rosters.py --offline

# Para coleta controlada e com API_FOOTBALL_KEY configurada apenas no ambiente:
py -3 collect_abc_rosters.py --allow-network --max-requests 60
```

O coletor salva o snapshot em `data/private/bc-rosters-2026-review.json`, ignorado pelo Git. Nunca versionar credenciais ou arquivos binários originais do jogo. O teto persistente de consumo da API depende de executar todos os consumidores no mesmo ledger local; não presume limite global entre máquinas.

## Critérios para uma release A/B/C

1. 20 A + 20 B + 20 C, todos com **jogadores reais verificados para 2026**, sem placeholders.
2. Conferir identidade e arquivo de destino de cada clube, impedindo troca de homônimos.
3. Comparar os jogadores esperados com os realmente gravados nos `.ban`; documentar eventuais limites do jogo.
4. Manifesto contendo **somente arquivos de A/B/C**, sem `BRA.cfg` e sem arquivos da Série D.
5. Testar aplicação, backup, desfazer, preservação de saves e início de uma carreira nova no Brasfoot Windows.
6. Atualizar site e release **somente depois** que houver os artefatos verificáveis.

A release **v2026.1.1, que modificava a Série D**, não corresponde ao escopo definitivo. O site mantém a v2026.0.2 como referência para a prévia de elencos da Série A.

## Requisito final de início de carreira — solicitado em 25/10/2026

Ao criar **uma carreira nova no Brasfoot 22–23**, o campo de temporada deve permitir **exclusivamente 2026**, ocultando/removendo os atuais valores 2023 e 2024. Não basta alterar textos exibidos: o ano efetivamente persistido no novo save e utilizado nas partidas também deve ser 2026. Carreiras existentes devem permanecer intactas.

Este requisito **não deve modificar a Série D** (equipes, formato, `BRA.cfg` e calendário). É um ajuste separado do patch de elencos A/B/C.

**Estado: pendente de identificação e homologação.** A lista de anos parece fazer parte do código do jogo, e não dos `.ban` ou `BRA.cfg` já decodificados; ainda não há evidência binária suficiente para localizar o controle no executável/JAR do usuário. Não reescrever bytes da aplicação nem distribuir um mod de executável sem verificar o hash da versão-alvo. Existe precedente público de mods que alteram os anos iniciais, mas isso não prova compatibilidade com esta cópia particular.

**Gate de aceitação:** após executar em cópia isolada, a interface mostra só 2026; é possível selecionar clube e iniciar uma nova carreira sem carregamento infinito; o save registra 2026; calendário e virada de temporada funcionam; backup/desfazer restaura a lista original 2023/2024; saves anteriores permanecem iguais por SHA-256. Não liberar release anunciando esse recurso até passar nessa sequência.

## Pesquisa web por elencos da Série B/C — 25/10/2026

- `site/data/researched-rosters-2026.json`: **40 clubes**, **1.302 nomes pesquisados**, com URL da fonte, tipo de fonte, data de consulta e observações; nenhum desses atletas foi instalado no Brasfoot pelas releases existentes.
- Algumas fontes refletem uma **lista de jogadores que passaram pelo clube durante 2026**, uma lista do início da temporada ou um retrato esportivo sem garantia de vínculo em outubro. Ex.: notícia do Maranhão de 29/09/2026 relata seis saídas de titulares e já prepara elenco 2027; não é correto somar todos os nomes e declarar um plantel atual de 2026. A fonte de fevereiro/2026 da Ferroviária usa nomes abreviados e repete a grafia de Denilson, o que requer desambiguação.
- A interface separa explicitamente **elenco publicado na v2026.0.2 (Série A)** de **jogadores pesquisados em fonte externa, ainda NÃO incluídos no patch (Séries B/C)**, com link no modal e filtros específicos.
- Para gerar o futuro pacote 60 A/B/C, faltam validar individualmente todas as 40 fontes/nomes e transferências, identificar idade/posição e resolver os vínculos de arquivos `.ban`, reproduzir o patch diferencial, testar backups e homologar início de carreira. **Não anunciar "elencos 100% reais e atualizados" com base apenas na existência de nomes em páginas da web.**
- Ordenação crescente/decrescente e agrupamento nas **quatro colunas** (clube, UF, série, situação do elenco) são feitos antes da paginação e funcionam com busca e filtros. Regressões do site executadas no GitHub Actions.

## Seletores de divisão na criação de carreira — requisito enfileirado (25/10/2026)

A captura de tela da criação de carreira mostra os controles **1ª divisão**, **2ª divisão**, **3ª divisão** e **Jogando estaduais**, com escolhas exibidas América-MG, Bahia, ABC e ASA. **Essas podem ser apenas as escolhas atuais: a imagem não comprova quais clubes integram cada lista nem o vínculo interno com as ligas.**

### Comportamento exigido

- **1ª divisão (Série A):** exatamente os 20 participantes oficiais de 2026.
- **2ª divisão (Série B):** exatamente os 20 participantes oficiais de 2026.
- **3ª divisão (Série C):** exatamente os 20 participantes oficiais de 2026.
- **Jogando estaduais:** permitir a escolha apropriada e compatível com a divisão/UF, sem realocar ou apagar clubes e sem mudar a Série D. É necessário apurar no jogo a função exata desse quarto controle.
- **Ano de início:** apenas **2026** selecionável, removendo as opções 2023/2024; partidas e save também devem começar realmente em 2026.
- **Vínculo com o motor:** divisão apresentada = divisão usada na criação da carreira, calendário, adversários, resultados, classificação, acesso/rebaixamento e temporadas seguintes. **Alterar só os textos/ordem na UI não satisfaz o pedido.**
- **Preservação:** Série D original intacta, inclusive clubes, jogadores, grupos e configuração BRA.cfg; saves anteriores intactos. Toda alteração real requer backup/desfazer.

### Critérios de aceite para teste no Brasfoot Windows

1. Identificar no executável/JAR ou no formato dos times o código que popula os quatro seletores e atribui a divisão aos clubes. O BRA.cfg decodificado contém regras e quantidades, **não a lista nominal de clubes**; a vinculação ainda não foi demonstrada.
2. Conferir os 60 participantes A/B/C da temporada 2026, 20 por divisão, sem duplicações ou nomes na divisão errada. Os estaduais devem continuar coerentes.
3. Iniciar uma carreira para cada divisão com **2026** selecionado; conferir clube, divisão, rivais, campeonato estadual quando aplicável e calendário realmente criado.
4. Avançar rodadas, classificação, acessos e rebaixamentos, virada para a próxima temporada e reabertura dos novos saves.
5. Comparar hashes de BRA.cfg, arquivos da Série D e saves preexistentes antes/depois; todos devem ficar idênticos.
6. Testar o instalador e o rollback, com verificação de SHA-256 da versão original. Se o jogo carregar infinitamente, o aceite **falha**.

**Estado:** enfileirado para engenharia reversa e teste na instalação real, **não implementado nem publicado**. O print mostra os seletores, mas não revela a lógica interna de divisão.

## Engenharia reversa do seletor de ano — executável oficial inspecionado (25/10/2026)

Foi baixado **somente para inspeção read-only em GitHub Actions** o instalador diretamente de `https://www.brasfoot.com/download22/brasfoot22-23.exe`, SHA-256 `8e3c7a77768d551a1f3c722ef2447c3e451af830613e8a65de33f35bc0e2b33d`, tamanho 18.113.849 bytes. O setup NSIS foi descompactado na pasta temporária do runner, sem execução e sem publicar arquivos proprietários.

- Executável oficial interno: `bf22-23.exe`, 7.320.384 bytes, ZIP anexado com **2.193 entradas e 1.038 classes Java**.
- Classe `a/hU.class`, SHA-256 `37fb17d876aab1263756bca97c3f9488007b7afe59f8c68494cf711a0f61a234` (14.933 bytes): **identificada como rotina do JComboBox de seleção de ano**. Seu método `mQ()` insere os anos **2022 e 2023**, chama `best/aq.am("anoinicio")` e seleciona índice 0 ou 1. A ação de iniciar usa `getSelectedIndex()` e grava ano 2022/2023 em `best/f.I(int)` e a preferência `anoinicio`.
- Classe principal de estado `best/f.class`, SHA-256 `dbd5bd8633e3a1c2f211e8bd6c322db8f7401c5ccf7cc622cc4050f0624df71b`. `best/p.class`, SHA-256 `466327e6cedae77503021dd222a33bf9163e453b639ebc29a399d9d851f4c256`, possui uma comparação de ano igual a 2023 que requer revisão caso passe a 2026.
- **Diferença de versão:** a instalação descrita pelo usuário mostra **2023 e 2024**, diferente dos **2022 e 2023** do executável baixado do site oficial. Portanto, não aplicar um patch estático dos bytes/classe oficiais na instalação sem confirmar a versão exata e sua assinatura.
- **Correção exigida:** não basta trocar o texto do JComboBox. A lista deve ter somente 2026; o evento do botão precisa configurar o motor para 2026 e gravar corretamente `anoinicio`, mesmo com preferências antigas; todas as referências internas que pressupõem 2022/2023 devem ser inspecionadas. Verificar save, calendário e telas reais em Windows.
- A mesma classe contém referências à interface de seleção inicial, mas **a relação efetiva entre clubes e divisões ainda não foi mapeada**; `BRA.cfg` define formatos/quantidades, não a composição de A/B/C.
- **Estado atual:** análise de bytecode concluída nessa parte; patch de ano e agrupamento interno **ainda não implementado, nem homologado, nem distribuído**. O workflow `inspect-official-game.yml` é reprodutível, apaga todos os arquivos privados ao final e registra apenas metadados/hashes nos logs de CI.


## Descoberta: tabelas de clubes embutidas no executável, além dos arquivos .ban

A inspeção do executável oficial `bf22-23.exe` revelou referências nominais a clubes em bytecode Java obfuscado `best/aq.class`. Por exemplo, a inicialização de um array fixo de **16 strings** inclui `corinthians_bra`, `santoandre_sp`, `interlimeirasp_bra`, `botafogosp_bra`, `pontepreta_bra`, `saobento_bra`, `bragantino_bra`, `palmeiras`, `ituano_sp` e `novorinzontino_sp`, entre outros. O trecho parece corresponder a uma lista estadual paulista; **não é prova de que defina a Série A, B ou C**. Em outras rotinas foram observadas referências a `bahia`, `abcrn_bra` e `avai_bra`.

**Implicação importante:** as listas podem estar embutidas no código do jogo, e não somente nos arquivos `.ban` e `BRA.cfg`. Antes de mexer nos seletores de 1ª/2ª/3ª divisão, identificar a função de cada array por análise de chamadas e testar o mapeamento da divisão **na lógica de calendário real**. É inadmissível substituir um array de clubes estaduais por uma lista nacional, ou mudar a interface sem atualizar os fluxos de simulação. O jogo do usuário usa ainda outro binário que mostra 2023/2024, não 2022/2023; aplicar patches só com SHA-256 exato da versão instalada.

Evidência reprodutível no workflow de CI `.github/workflows/inspect-official-game.yml`, execução `40240909477`; nenhum executável ou bytecode proprietário foi commitado nem distribuído.

