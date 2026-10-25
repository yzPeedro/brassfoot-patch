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
py -3 collect_abc_rosters.py --max-requests 60
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
