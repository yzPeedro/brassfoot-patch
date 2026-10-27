# Distribuição do Brasfoot Mega Patch

`config/edition.json` define nome, versão, `PATCH_YEAR` e destinos. O gerador
`tools/build_distribution.py` lê esse arquivo e injeta os metadados na compilação.
Os valores de desenvolvimento em `windows-installer/edition.go` permitem abrir
o código sem um gerador obrigatório; as builds de release usam a configuração.

A edição 2026.4.0 é um **atualizador experimental**. Os deltas de elencos exigem
uma instalação legítima do Brasfoot já preparada pela V4. O instalador anterior
2026.3.5 continua sendo a referência para a preparação inicial. O atualizador
não inclui nem redistribui o executável original do jogo.

| Artefato | Interface | Execução do jogo |
|---|---|---|
| Windows x64 `.exe` | Win32 com navegação por teclado, escala e backup | Brasfoot Windows instalado |
| Linux x64 `.tar.gz` | Terminal; Zenity/KDialog se disponível | Wine configurado pelo usuário |
| Linux ARM64 `.tar.gz` | Terminal; Zenity/KDialog se disponível | Camada externa compatível com o jogo x86 |
| macOS Intel `.tar.gz` | Terminal e seletor de pastas do macOS | Wine/CrossOver configurado |
| macOS Apple Silicon `.tar.gz` | Terminal e seletor de pastas do macOS | Camada externa compatível com o jogo x86 |

O programa de atualização é compilado para cada sistema; **o jogo não é um port
nativo**. Uma compilação cruzada não demonstra compatibilidade funcional. Nenhuma
destas builds declara gameplay verificado, assinatura Apple ou notarização.
Rosetta, Wine e CrossOver não são instalados silenciosamente ou distribuídos.

## Construir os arquivos de release

```powershell
python tools/build_distribution.py --bundle windows-installer/bundled_release --output dist/2026.4.0
```

O bundle deve ser escolhido explicitamente. O gerador copia os fontes para uma
pasta temporária, preserva os marcadores de compatibilidade e as receitas, muda
somente a versão do manifesto e compila os destinos declarados. O código não
executa testes. A opção `--target linux/amd64` limita a construção a um destino;
`--source-commit` permite indicar o SHA completo correspondente ao conteúdo.

`distribution.json` registra versão, plataforma, arquitetura, commit, hash dos
fontes usados, hash do bundle, tamanho, SHA-256 e o estado não verificado. O
arquivo `SHA256SUMS.txt` acompanha os downloads. Arquivos existentes não são
sobrescritos. As receitas diferenciais exigem os hashes originais conhecidos;
nenhuma flag ignora incompatibilidades de arquivos.

## Utilizar no Linux ou macOS

Extraia o pacote e abra `Abrir.command` no macOS ou `abrir.sh` no Linux. O
atualizador procura instalações Wine/CrossOver/Bottles conhecidas; se não houver
uma, oferece o seletor de pastas disponível. Em uma sessão sem interface:

```sh
./brasfoot-mega-patch --game /caminho/do/Brasfoot
./brasfoot-mega-patch --game /caminho/do/Brasfoot --restore
./brasfoot-mega-patch --game /caminho/do/Brasfoot --inspect
```

`--yes` confirma a operação explicitamente para uso automatizado; as verificações
de integridade continuam obrigatórias. `--inspect` não aplica arquivos. Antes
de modificar, o processo do jogo deve estar fechado. Backup, hashes, aplicação
transacional e restauração usam o mesmo motor do instalador Windows.

Os backups continuam no diretório histórico `BrassfootPatch2026/backups` dentro
de `%LOCALAPPDATA%` (Windows), `$XDG_CONFIG_HOME` ou `~/.config` (Linux), ou
`~/Library/Application Support` (macOS). Esse caminho foi preservado para não
perder backups de versões anteriores. Saves não fazem parte das operações.

## Estado desta implementação

Identidade azul e nome Brasfoot Mega Patch, ação Jogar e textos simplificados
foram implementados no Windows. As entradas Linux/macOS substituem o stub
anterior por operações reais sobre a instalação existente. Testes não foram
executados, por instrução expressa do proprietário nesta entrega. A confirmação
de instalação no host e de execução do jogo continua separada da compilação.
