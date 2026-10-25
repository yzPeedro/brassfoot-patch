# Auditoria de escudos e uniformes — temporada 2026

**Estado: ainda não há assets da expansão aprovados para redistribuição.**

O arquivo `assets_audit.py` permite inventariar em modo exclusivamente de leitura os diretórios existentes da instalação autorizada do Brasfoot, registrando arquivos, tamanhos, SHA-256 e cabeçalhos/dimensões PNG quando possíveis.

Exemplo:
```powershell
py -3 .\assets_audit.py --game "C:\Brasfoot22-23" --out ".\output\assets-audit.json"
```

| Categoria | Clubes auditados com origem/temporada/direitos | Assets autorizados a publicar nesta expansão |
|---|---:|---:|
| Escudos | 0 | 0 |
| Uniforme principal | 0 | 0 |
| Uniforme reserva | 0 | 0 |
| Terceiro uniforme | 0 | 0 |
| Uniforme de goleiro | 0 | 0 |

Esses zeros significam **auditoria ainda não efetuada**, não ausência de imagens no jogo. O script não distribui os arquivos encontrados nem presume que um PNG válido possa ser republicado. A relação clube↔arquivo só pode ser aprovada após investigação dos nomes e identificadores reais do jogo. Até lá `clubId`, `sourceUrl` e `season` permanecem nulos; `distributionAllowed=false`.

**Bloqueios:** inventário completo da pasta `C:\Brasfoot22-23`, confirmação de dimensões/formatos suportados, fontes oficiais das camisas de 2026, licenças e testes visuais.
