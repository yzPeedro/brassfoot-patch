# Instalador Windows — implementação oficial Go

## Release pública

A versão **v2026.0.2** foi publicada no GitHub em 25/10/2026:
https://github.com/yzPeedro/brassfoot-patch/releases/tag/v2026.0.2

**Distribuição oficial atual:** `windows-installer/`, aplicativo nativo Win32 escrito em Go. A versão pública instala experimentalmente os elencos de 20 clubes da Série A e não modifica arquivos de save intencionalmente. Ela aplica diferenças sobre arquivos `.ban` preexistentes, com hashes SHA-256 originais homologados, backup externo, rollback e operação de desfazer. A aprovação no Brasfoot Windows foi comunicada pelo usuário em 25/10/2026. Atributos de 713 jogadores são estimados; 15 dos 745 atletas coletados não entraram.

`installer/` (Python/Tk) e `release.ps1` representam a arquitetura **legada/experimental**. Não são a cadeia oficial usada na release pública. Não remover sem primeiro avaliar migrações.

## Ampliação pós-v2026.0.2 — ainda não distribuída

- Motor Go agora suporta manifestos de 1 a 512 arquivos de equipes `.ban`, em vez de exigir exatamente 20.
- O manifesto `schemaVersion: 3` distingue `operation: replace` e `operation: add`. O schema 2 continua aceito, sem alteração retroativa na release anterior.
- Adições novas exigem ausência do caminho de destino (ou hash final idêntico), são criadas sem sobrescrever arquivos desconhecidos e podem ser removidas com segurança no rollback/desfazer.
- Patches de substituição só aceitam hashes originais listados e validados. Uma instalação mista v3 pula arquivos já aplicados; o desfazer atua somente nos modificados pela transação.
- O gerador embutido permite receitas diferenciais de adição em `bundled_release/patches/*.json`; a saída é verificada por SHA-256 antes de escrita.

**Limite confirmado:** o código permite armazenar ou substituir até 156 arquivos de equipe, mas não prova que o jogo ofereça quatro divisões jogáveis ou aceite novos IDs sem referências adicionais. O pacote publicado ainda contém apenas 20 equipes; não gerar novo instalador nem marcar flags de aprovação com base somente em testes sintéticos.

## Evidências de testes

Em ambiente local Linux, os testes Go da release usaram os 20 `.ban` privados enviados pelo usuário e foram aprovados. Os testes de extensão Go também passaram com corrida de dados habilitada (`go test -race`), incluindo 156 substituições sintéticas, inclusão de novas equipes, rollback, idempotência e preservação dos saves das fixtures. Um novo binário foi compilado para Windows amd64, mas **não foi executado no Windows real nem testado no Brasfoot**. Não substitui a v2026.0.2 pública.

Próximos gates: mapear IDs dos 136 clubes adicionais, testar clubes/competição no jogo, gerar elencos íntegros e resolver procedência das imagens.


## Configuração nacional BRA.cfg em schema v3 — etapa de laboratório

O motor agora aceita somente `conf_ligas_nacionais/BRA.cfg` como arquivo adicional de substituição (`operation=replace` em manifesto v3); caminhos estaduais, outras configurações, criação de `BRA.cfg` e path traversal continuam bloqueados. Preflight exige pasta `conf_ligas_nacionais` real e dentro do jogo, arquivo Java Serialization regular e um hash original conhecido. Criação de backup, substituição atômica, verificação SHA-256 e desfazer estão implementados.

Foi realizado teste com os **703 `.ban` privados fornecidos pelo usuário** em instalação temporária, juntamente com o `BRA.cfg` original real e o laboratório 96/16: instalação, idempotência e restauração passaram com arquivos pessoais intactos. Os **20 originais privados da v2026.0.2** também passaram na suíte de regressão Go. O código-fonte possui testes opcionais ativados por fixture privada, mas **não contém nem distribui os arquivos do Brasfoot**.

A compilação Windows foi feita por cross-build e não equivale à execução da GUI. A configuração 96/16 **não deve ser anunciada como jogável até confirmação com o motor do jogo real**. Nenhum binário dessa etapa foi publicado no GitHub Releases.
