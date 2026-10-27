# Conversão local de gráficos

`tools/graphics_pipeline.py` converte originais locais autorizados em PNG e
mantém cache por SHA-256 do original e das opções de conversão. Não faz
downloads nem instala arquivos no jogo. O cadastro `config/graphics.json`
começa vazio: nenhum escudo oficial ou uniforme foi inventado ou copiado.

Coloque os originais em `data/private/graphics/originals/`. Cada item de
`assets` deve declarar `id`, `path` relativo a essa pasta, `origin_url` HTTPS,
`license` e `authorized` booleano. A licença deve identificar a licença real
ou a referência da permissão; preencher o campo não comprova direitos.
`authorized: false` mantém o item no relatório sem ler ou converter o arquivo.
`sizes` pode sobrescrever as caixas delimitadoras padrão de 32, 64 e 128 pixels.
Somente cadastre imagens próprias ou cuja reutilização esteja autorizada.

Execute na raiz do projeto:

```powershell
python -m tools.graphics_pipeline
```

O cadastro vazio funciona sem dependências adicionais. Para converter imagens,
instale Pillow no ambiente Python normal usado pelo projeto, se necessário:

```powershell
python -m pip install Pillow
```

Os resultados ficam exclusivamente em `data/private/graphics/generated/`.
O manifesto registra origem, licença, autorização, SHA-256 do original, tamanho
em bytes, dimensões originais/orientadas, opções e dimensões/SHA-256 de cada
PNG. Os caminhos de PNG são relativos a `cache_root` no manifesto.

A conversão aceita PNG, JPEG e WebP estáticos, aplica orientação EXIF, preserva
proporção e transparência em RGBA e nunca amplia imagens pequenas. As caixas
representam dimensões máximas, sem recorte ou bordas acrescentadas. Originais
permanecem intactos. Metadados de câmera e perfis de cor não são copiados para
os PNGs; não há promessa de fidelidade de cor para perfis especiais.

Há limites de 256 imagens, 10 MB por original, 24 milhões de pixels, oito
tamanhos por imagem e 2048 pixels por lado de saída. Caminhos absolutos,
travessia de diretórios, links simbólicos e junctions são recusados. A saída
não aceita um diretório arbitrário de instalação. O cache inclui versões do
Pillow e zlib: mesmas entradas e opções no mesmo ambiente geram a mesma
chave. Uma mudança de versão pode gerar outro PNG e outra chave.

Cada arquivo é escrito em temporário e substituído atomicamente. O cache só
fica reutilizável depois de gravados seus metadados, e sua reutilização confere
os hashes dos PNGs. Uma falha preserva o manifesto anterior; pode deixar
arquivos de cache completos, reutilizáveis na próxima execução. Não existe
expurgo automático do cache. Não execute gravações concorrentes de originais
ou alterações de links enquanto a conversão estiver rodando.

Também foi corrigida a ingestão offline em `tools/daily_sources.py`: cada
registro herda URL, SHA-256 e, se informada, data efetiva da fonte; metadados
específicos do registro podem informar outra URL HTTPS/data efetiva. JSON,
codificação, arquivos ou registros inválidos geram falha somente daquela
fonte identificada, permitindo processar as demais e conservar os dados
anteriores pelo mecanismo de snapshots. Nomes ausentes/duplicados continuam
sendo erros do cadastro inteiro. `world_snapshot` conserva URL/data por campo;
o SHA do arquivo também permanece no resultado de coleta.

Esta entrega contém implementação e documentação. Não foram executados
testes, validadores, conversão de imagens ou builds nesta etapa.
