# Solução de problemas

- `not digitally signed` no PowerShell: execute o script do projeto com `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\sync-api.ps1"` em processo isolado.
- `UnsupportedClassVersionError 61.0 vs 52.0`: configure Java e javac 17+ no PATH da sessão.
- `Free plans do not have access to this season`: não use `/teams?league=71&season=2026` no plano Free.
- `Search field may only contain alpha-numeric characters and spaces`: a v5 remove pontuação/acento das pesquisas fallback.
- `Catalog reconciliation failed`: examine `data/api-football/2026/YYYY-MM-DD/mapping-report.json`; não apague clubes nem adivinhe IDs; verifique também `data/api-football/2026/_shared/teams-brazil.json` (o relatório não contém a chave).
- `API budget exhausted`: aguarde reinício da quota ou retome reutilizando cache, sem `-Refresh`.
- `Corrupt cache`: preserve evidência e renomeie/remova apenas o cache afetado após entender o erro.
- `Cannot overwrite prior build`: use novo diretório `--out` para preservar artefatos anteriores.
- `invalid .ban header`: interrompa instalação e confirme integridade/fonte dos dados.
- Site sem download: comportamento esperado enquanto não houver release validada.
