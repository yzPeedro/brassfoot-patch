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
