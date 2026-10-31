# Brasfoot Mega Patch — continuidade

## Fonte e retomada
- Missão integral: `docs/mega-patch-specification.md`, cópia byte a byte de `PROMPT.md`; hash em `config/mega-patch-specification.json`. Não remover requisitos.
- Leia `docs/current-state.md`, `config/backlog.json`, `docs/context/CONTINUIDADE-E-PENDENCIAS.md` e o checkpoint local mais recente em `data/private/scheduled-maintenance/<data>/` antes de trabalhar. `data/private/continuity/` é usado apenas pelo serviço de continuidade, quando ativo.
- Base de conhecimento: `docs/context/` (índice em `CLAUDE.md`). Contexto mestre `docs/context/BRASFOOT-MEGA-PATCH-CONTEXTO-MESTRE.md` (manual operacional + histórico do Work e missões de 25–26/10), manual `docs/context/BRASFOOT-MEGA-PATCH-MANUAL-OPERACIONAL.md`, módulos `docs/context/GUIA-DE-MODULOS.md`, decisões `docs/context/HISTORICO-E-DECISOES.md`. Precedência: instrução recente do proprietário > estado verificado (código/Git/releases) > `current-state` e checkpoints > Work não publicado > contexto mestre > especificação e histórico, sem descartar requisitos.
- Prévia do campo animado (`tools/live-match-view-src/`, `dist/live-match-preview-*`) é privada: nunca publicar como release, asset ou site sem nova instrução explícita do proprietário.
- Manutenção recorrente autorizada: seguir `docs/scheduled-maintenance.md` na execução diária das 18h de Brasília; pesquisa de todos os clubes, publicação automática, datas/ano e patch notes fazem parte do mesmo ciclo.
- Evidências anteriores: `docs/implementation-progress.md`, `docs/release-2026.3.5.md`, `docs/365scores-roster-policy.md`. Não repetir auditorias concluídas. Documentos antigos podem descrever releases anteriores; consultar manifesto e GitHub para situação publicada.

## Execução
- Alethe local é o mecanismo de delegação; perfil savings, ondas economy, no máximo dois workers e preferencialmente um escritor por vez. Planos/telemetria fora do Git.
- Workers recebem objetivo delimitado, caminhos de propriedade e checks. Não delegam novamente nem fazem commits/publicações.
- Coordenador integra somente após revisão de diff e validações. Preserve mudanças preexistentes do usuário.
- Cota ausente, desatualizada ou acima do limite operacional adia novas ondas. Nunca usar bypass de cota, trocar para cobrança API ou contratar serviços.
- Checkpoints devem registrar implementação, validação e operação separadamente. Não inventar testes, fontes, compatibilidade ou cobertura.

## Publicação autorizada
- Commits, push, releases e atualização do site estão autorizados pelo proprietário dentro desta missão; não criar homologação humana recorrente.
- Nesta entrega o proprietário dispensou todos os testes e determinou releases finais. Compilar e publicar artefatos com integridade e proveniência, sem alegar testes ou compatibilidade funcional não observados.
- Não substituir saves, remover ativação ou redistribuir binários proprietários sem autorização aplicável.
- Publicar artefatos verificados antes do manifesto/site. Vincular versão a commit, snapshot e hashes; recuperar falhas parciais de forma idempotente.
- API-Football desativada por padrão. Não inventar dados esportivos; conservar último dado confiável se uma fonte falhar.
- Identidade visual atual solicitada: Brasfoot Mega Patch com estética celeste inspirada no Cruzeiro, azul profundo, ciano, branco e constelações; projeto independente. PIX existente opcional, sem PayPal.

## Verificações
- Por solicitação explícita do proprietário, não executar testes nesta manutenção, incluindo suítes Python/JavaScript/Go, testes de navegador e gameplay.
- Realizar apenas compilação produtiva, geração de dados, leitura de código, integridade/proveniência dos artefatos e conferência do estado de publicação. Não descrever essas atividades como testes funcionais.
- Não afirmar validação de gameplay, temporadas, macOS ou Linux sem evidência real.

## Entrega corretiva 2026.4.1
- Estado atual por seção: `config/specification-coverage.json`; conclusão integral explicitamente falsa.
- O mantenedor dispensou execução de testes nesta entrega. Não descrever compilação, hashes ou inspeção de código como testes executados.
- Build: `tools/build_distribution.py`; publicação: `tools/publish_distribution.py` e `tools/publish_pages.py`, ou `release.ps1`.
- `site/data/release.json` e `site/data/distribution.json` identificam a mesma release final mais recente. Downloads usam aliases permanentes em `releases/latest/download`.
- Receitas 2026.4.1 aceitam originais, V4 e 2026.3.5/4.0 reconhecidos por SHA. Fonte: `tools/build_release_bundle.py`. Os dados atuais vêm do coletor e compilador de elencos; cobertura e campos derivados ficam registrados no relatório.
- Coleta: `python -m tools.daily_update`; agendamento local usa `--report-output data/private/daily/world-status.json` para não sujar o checkout. O código de continuidade não deve depender de uma chave de provider para executar coleta pública.
