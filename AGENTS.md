# Brasfoot Mega Patch — continuidade

## Fonte e retomada
- Missão integral: `docs/mega-patch-specification.md`, cópia byte a byte de `PROMPT.md`; hash em `config/mega-patch-specification.json`. Não remover requisitos.
- Leia `docs/current-state.md`, `config/backlog.json` e o estado local em `data/private/continuity/` antes de trabalhar.
- Evidências anteriores: `docs/implementation-progress.md`, `docs/release-2026.3.5.md`, `docs/365scores-roster-policy.md`. Não repetir auditorias concluídas. Documentos antigos podem descrever releases anteriores; consultar manifesto e GitHub para situação publicada.

## Execução
- Alethe local é o mecanismo de delegação; perfil savings, ondas economy, no máximo dois workers e preferencialmente um escritor por vez. Planos/telemetria fora do Git.
- Workers recebem objetivo delimitado, caminhos de propriedade e checks. Não delegam novamente nem fazem commits/publicações.
- Coordenador integra somente após revisão de diff e validações. Preserve mudanças preexistentes do usuário.
- Cota ausente, desatualizada ou acima do limite operacional adia novas ondas. Nunca usar bypass de cota, trocar para cobrança API ou contratar serviços.
- Checkpoints devem registrar implementação, validação e operação separadamente. Não inventar testes, fontes, compatibilidade ou cobertura.

## Publicação autorizada
- Commits, push, releases e atualização do site estão autorizados pelo proprietário dentro desta missão; não criar homologação humana recorrente.
- Testes obrigatórios proporcionais à alteração; preservar release anterior diante de falha. Não publicar builds experimentais como estáveis.
- Não substituir saves, remover ativação ou redistribuir binários proprietários sem autorização aplicável.
- Publicar artefatos verificados antes do manifesto/site. Vincular versão a commit, snapshot e hashes; recuperar falhas parciais de forma idempotente.
- API-Football desativada por padrão. Não inventar dados esportivos; conservar último dado confiável se uma fonte falhar.
- Identidade futura: Brasfoot Mega Patch, azul neutro sem marca de clube; PIX existente opcional, sem PayPal.

## Verificações
- Python: `python -m unittest discover -s tests -q`.
- Site: `node site/tests/site.test.js`, `node site/tests/seo-pix.test.js`, `node site/tests/explorer-interaction.test.js`.
- Instalador: `go test ./...` e `go vet ./...` em `windows-installer` quando afetado.
- Testes unitários não comprovam gameplay, temporadas, macOS ou Linux. Manter esses gates pendentes até evidência real.

## Entrega 2026.4.0
- Estado atual por seção: `config/specification-coverage.json`; conclusão integral explicitamente falsa.
- O mantenedor dispensou execução de testes nesta entrega. Não descrever compilação, hashes ou inspeção de código como testes executados.
- Build: `tools/build_distribution.py`; publicação: `tools/publish_distribution.py` e `tools/publish_pages.py`, ou `release.ps1`.
- `site/data/release.json` é a base V4 anterior. `site/data/distribution.json` é o manifesto dos novos atualizadores, gerado somente após os assets públicos.
- Receitas atuais: 60 clubes, mesmos elencos da 2026.3.5, com proveniência em `config/payload-provenance.json`. Base histórica de 20 clubes preservada em `tools/baselines/2026.0.2`.
- Coleta: `python -m tools.daily_update`; agendamento local usa `--report-output data/private/daily/world-status.json` para não sujar o checkout. O código de continuidade não deve depender de uma chave de provider para executar coleta pública.
