# Hub e instalador

O código fica em [`windows-installer/`](../windows-installer/) (módulo Go). O mesmo motor gera o hub gráfico do Windows e os atualizadores de linha de comando para Linux e macOS.

Desde o hub 1.0.0 existe **um único hub**. Ele não carrega o patch dentro do executável: a cada abertura, busca a release mais recente do GitHub, baixa o pacote da versão, confere o SHA-256 e só então instala. O usuário baixa o hub uma vez e recebe pelo próprio hub as atualizações do patch e do instalador.

## Arquivos principais

| Arquivo | Função |
|---|---|
| `engine.go` | Validação da pasta do jogo, inspeção do manifesto, instalação transacional com backup, rollback e conferência por SHA-256 |
| `feed.go` | Leitura do `release.json` da release mais recente, download e cache dos arquivos, conferência por SHA-256 e comparação de versões |
| `bundle.go` | Pacote da versão carregado em memória e aplicação das receitas delta (schemas 1, 2 e 3), inclusive por um executável intermediário |
| `components.go` | Detecção do que está instalado e montagem do manifesto para a seleção do usuário |
| `snapshots.go` | Backups completos em `.zip`, listagem e restauração de backups |
| `restore.go` | Restauração do backup criado pela instalação do patch completo |
| `hub_windows.go` | Janela sem moldura com WebView2, ligação entre a interface e o motor |
| `hub_setup_windows.go` | Instalação do próprio hub em pasta fixa, atalhos, registro em Aplicativos, remoção e autoatualização |
| `ui/hub.html` | Interface do hub (HTML, CSS e JavaScript em um único arquivo) |
| `main_windows.go` | Interface Win32 simples, usada quando o WebView2 não está disponível ou com `--classic` |
| `main_other.go` | Atualizador de linha de comando para Linux e macOS |
| `winres/` | Ícone, manifesto do aplicativo e informações de versão do executável |

## Versões

| O quê | Formato | Onde é definida | Quando muda |
|---|---|---|---|
| Patch | `AAAA.M.m` (ex.: `2026.5.3`) | `config/edition.json` | A cada release, inclusive as diárias |
| Hub | `M.m.p` (ex.: `1.0.0`) | `config/hub.json` | Só quando o código do hub muda |

`config/hub.json` também define `requiresHub`, a versão mínima do hub capaz de aplicar o pacote da release, e o arquivo de notas do hub (`docs/hub/v<versão>.md`). Prévias usam sufixo (`1.0.0-preview.1`), que é sempre anterior à versão final.

## Como o hub obtém a versão mais recente

Cada release publica, além dos executáveis, dois arquivos:

| Arquivo | Conteúdo |
|---|---|
| `Brasfoot-Mega-Patch-<versão>-bundle.zip` | Manifesto e receitas delta da versão (`bundled_release/manifest.json` e `bundled_release/patches/*.json`). Nunca contém arquivos do jogo |
| `release.json` | Versão do patch, tag, data, notas da versão em Markdown, `requiresHub`, nome, tamanho e SHA-256 do pacote, versão e notas do hub e nome, tamanho e SHA-256 do executável de cada plataforma |

O fluxo do hub:

1. Lê `https://github.com/yzPeedro/brassfoot-patch/releases/latest/download/release.json`. *Latest* é a release final mais recente; rascunhos e prereleases não entram. Fora de uma prévia local, o hub recusa feed ou pacote que não sejam do canal `stable`.
2. Baixa o pacote pelo endereço da tag (`releases/download/v<versão>/...`), confere tamanho e SHA-256 com o `release.json` e confere se o manifesto é da mesma versão e é uma release final.
3. Guarda o `release.json` e o pacote em `%LOCALAPPDATA%\BrassfootPatch2026\cache\`, com o SHA-256 como nome. Em uma nova abertura, o pacote já conferido não é baixado de novo.
4. Compara o jogo com o manifesto e mostra a situação de cada componente.

Sem internet, o hub usa a última versão guardada e avisa. Sem nenhuma versão guardada, ele permite jogar e restaurar backups, e a instalação fica bloqueada até a conexão voltar. Os erros de rede e de conferência aparecem como `BF-120` (sem conexão), `BF-121` (download não conferiu) e `BF-122` (nenhuma versão carregada ou hub antigo demais).

## Hub (Windows)

O hub abre em uma janela própria, sem a barra do Windows, com botões de minimizar e fechar na barra superior (que também arrasta a janela). A barra mostra a versão do hub. Ele tem três áreas:

- **Início:** pasta do Brasfoot (detectada automaticamente ou escolhida), situação de cada componente (instalado, atualização disponível ou não instalado), a versão mais recente com o link **Ver novidades** e os botões **Jogar**, **Instalar** e **Atualizar**.
- **Instalar:** oferece só o que ainda não está instalado. Componentes já instalados aparecem bloqueados.
- **Atualizar:** disponível apenas quando a versão instalada de algum componente é diferente da versão publicada. Os componentes desatualizados são sempre incluídos, e os que faltam podem ser adicionados na mesma operação. A atualização segue as mesmas garantias da instalação: backup dos arquivos alterados, substituição atômica e conferência por SHA-256.
- **Backups:** lista de backups, criação de backup completo, restauração e abertura da pasta do backup.

### Avisos

No topo de todas as telas:

| Aviso | Quando aparece | Botões |
|---|---|---|
| Buscando a versão mais recente | Enquanto o hub lê o `release.json` e baixa o pacote (com porcentagem) | — |
| Nova versão do instalador | A versão do hub no `release.json` é maior que a do hub aberto | **O que mudou** (modal com as notas do hub) e **Atualizar instalador** |
| Nova versão do patch | Algum componente instalado é de versão anterior à publicada | **Ver novidades** (modal com as notas da release) e **Atualizar** |
| Sem conexão | O GitHub não respondeu; o hub usa a versão guardada ou fica sem versão | **Tentar de novo** |

As notas aparecem em um modal com Markdown simples (títulos, listas, negrito, código e links para o repositório ou o site).

### Instalação do próprio hub

Na primeira execução, o hub se copia para `%LOCALAPPDATA%\Programs\Brasfoot Mega Patch\Brasfoot-Mega-Patch.exe`, grava `hub.json` com a versão, cria atalhos no Menu Iniciar e na área de trabalho, registra-se em **Configurações > Aplicativos** (chave `HKCU\...\Uninstall\BrasfootMegaPatchHub`, sem pedir administrador) e reabre a partir da pasta fixa. Se já houver um hub instalado mais novo, o executável baixado apenas abre o instalado. Se a pasta fixa estiver em uso, o hub roda de onde foi aberto.

A remoção (pelo Windows ou com `--uninstall-hub`) apaga o hub, os atalhos e o registro. Jogo, saves e backups ficam intactos.

### Autoatualização

Ao confirmar **Atualizar instalador**, o hub baixa o executável da plataforma indicado no `release.json`, confere tamanho e SHA-256, grava como `.new`, renomeia o executável em uso para `.old`, coloca o novo no lugar e reabre com `--updated`. O hub novo apaga o `.old`. Em falha, o executável anterior volta ao lugar.

### Opções de linha de comando

```text
Brasfoot-Mega-Patch.exe                     hub (instala-se na primeira vez)
Brasfoot-Mega-Patch.exe --classic           interface simples
Brasfoot-Mega-Patch.exe --portable          roda sem se instalar
Brasfoot-Mega-Patch.exe --feed <pasta>      usa release.json e pacote de uma pasta local (prévias)
Brasfoot-Mega-Patch.exe --uninstall-hub     remove o hub do computador
```

O hub requer o Microsoft Edge WebView2 Runtime, presente no Windows 11 e na maioria das instalações do Windows 10. Sem ele, o hub oferece a página oficial de instalação e abre a interface Win32 simples, que também busca a versão mais recente, oferece atualizar o instalador e tem as mesmas garantias de instalação.

## Instalação por componentes

1. O hub detecta o estado atual pelo SHA-256 do `bf22-23.exe` e dos arquivos de equipe do manifesto. Um componente está **atual** quando o executável e os arquivos são exatamente os do pacote, **desatualizado** quando é de uma versão anterior reconhecida e **ausente** quando não foi instalado.
2. A seleção é somada ao que já está instalado. O executável final é escolhido na seção `components` do manifesto (veja a tabela em [Arquitetura](architecture.md#componentes)).
3. O manifesto da seleção é preparado em uma pasta temporária; cada arquivo é gerado pela receita correspondente e conferido.
4. Se a versão de origem do executável não estiver na receita do componente, o hub aplica primeiro a receita completa e depois a do componente, conferindo o executável intermediário.
5. A instalação copia os arquivos que serão alterados para um backup, substitui cada arquivo de forma atômica e confere o resultado. Em qualquer falha, os originais são restaurados.

O jogo precisa estar fechado; o hub verifica os processos `bf22-23.exe`, `brasfoot.exe` e `brasfoot22-23.exe` antes de escrever.

## Backups

Os backups ficam em `%LOCALAPPDATA%\BrassfootPatch2026\`:

| Pasta | Tipo | Conteúdo |
|---|---|---|
| `backups\<id>\` | Antes da instalação | Somente os arquivos alterados por uma instalação, com `install-report.json` e os hashes originais |
| `snapshots\<id>.zip` e `<id>.json` | Completo | Toda a pasta do jogo, incluindo saves, com o SHA-256 de cada arquivo |
| `cache\` | Versões baixadas | `release.json` da última consulta e pacotes conferidos, nomeados pelo SHA-256 |

Regras da restauração:

- Antes de restaurar, o hub cria automaticamente um backup completo do estado atual.
- Cada arquivo restaurado é escrito em um arquivo temporário, conferido por SHA-256 e então movido para o lugar.
- Em backups completos, arquivos que não existiam no backup são removidos apenas das pastas de dados (`teams/`, `conf_ligas_nacionais/`, `conf_estadual/`). Saves criados depois do backup são mantidos.
- Um backup de instalação só é restaurado na mesma pasta de jogo em que foi criado.

## Linux e macOS

O atualizador de terminal usa o mesmo feed: a cada execução busca a release mais recente, confere o pacote e avisa se há um atualizador mais novo (o arquivo `.tar.gz` é baixado manualmente na página da release).

```bash
./brasfoot-mega-patch --game /caminho/do/Brasfoot
./brasfoot-mega-patch --game /caminho/do/Brasfoot --only live
./brasfoot-mega-patch --game /caminho/do/Brasfoot --inspect
./brasfoot-mega-patch --game /caminho/do/Brasfoot --restore
./brasfoot-mega-patch --game /caminho/do/Brasfoot --bundle Brasfoot-Mega-Patch-2026.5.3-bundle.zip
```

| Opção | Efeito |
|---|---|
| `--game` | Pasta principal do Brasfoot; sem ela, o atualizador procura a instalação e abre um seletor de pasta |
| `--only patch\|live` | Instala somente um componente |
| `--inspect` | Mostra a compatibilidade em JSON sem alterar nada |
| `--restore` | Restaura o backup da instalação completa |
| `--bundle <zip>` | Usa um pacote baixado da página da release, sem internet |
| `--feed <pasta>` | Usa `release.json` e pacote de uma pasta local |
| `--yes` | Confirma sem pergunta interativa |
| `--version` | Mostra a versão do atualizador, edição, plataforma e commit |

## Recursos do executável e assinatura

O build do Windows gera os recursos a partir de `winres/winres.json` com o [go-winres](https://github.com/tc-hib/go-winres): ícone da marca em vários tamanhos, manifesto com `asInvoker`, DPI por monitor, caminhos longos e controles comuns v6, e informações de versão preenchidas com a versão do hub.

A assinatura Authenticode é opcional e acontece logo após a compilação:

```powershell
$env:MEGA_PATCH_SIGN_THUMBPRINT = "<thumbprint SHA-1 do certificado>"
python tools/build_distribution.py --bundle <bundle> --output dist/<versao> --target windows/amd64
```

O build usa `signtool sign /fd SHA256 /tr <carimbo> /td SHA256` e confere com `signtool verify /pa`. Sem certificado, o executável é publicado sem assinatura e o SmartScreen pode exibir um aviso até que o arquivo ganhe reputação. Atualizações feitas pelo próprio hub não passam pelo navegador e são conferidas pelo SHA-256 da release.

## Prévias locais

Antes de publicar, o proprietário testa a prévia com um feed local, sem tocar no GitHub:

```bash
python tools/build_distribution.py --bundle <bundle> --output <pasta-do-feed> \
  --edition <edição-de-prévia> --target windows/amd64 --notes <notas.md> --hub-version 1.0.0-preview.N
```

A pasta gerada contém `release.json`, o pacote e o hub; o hub da prévia é aberto com `--feed <pasta-do-feed>`. Para testar a autoatualização, abra um hub de prévia anterior apontando para o feed de um hub com versão maior.

## Compilação local

```bash
cd windows-installer
go build ./...
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -ldflags "-H=windowsgui" -o Brasfoot-Mega-Patch.exe .
```

O build de distribuição oficial está descrito em [Release e publicação](release.md).
