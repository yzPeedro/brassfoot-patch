# Hub e instalador

O código fica em [`windows-installer/`](../windows-installer/) (módulo Go). O mesmo motor gera o hub gráfico do Windows e os atualizadores de linha de comando para Linux e macOS.

## Arquivos principais

| Arquivo | Função |
|---|---|
| `engine.go` | Validação da pasta do jogo, inspeção do manifesto, instalação transacional com backup, rollback e conferência por SHA-256 |
| `bundle.go` | Leitura do bundle embutido e aplicação das receitas delta (schemas 1, 2 e 3), inclusive por um executável intermediário |
| `components.go` | Detecção do que está instalado e montagem do manifesto para a seleção do usuário |
| `snapshots.go` | Backups completos em `.zip`, listagem e restauração de backups |
| `restore.go` | Restauração do backup criado pela instalação do patch completo |
| `hub_windows.go` | Janela sem moldura com WebView2, ligação entre a interface e o motor |
| `ui/hub.html` | Interface do hub (HTML, CSS e JavaScript em um único arquivo) |
| `main_windows.go` | Interface Win32 simples, usada quando o WebView2 não está disponível ou com `--classic` |
| `main_other.go` | Atualizador de linha de comando para Linux e macOS |
| `winres/` | Ícone, manifesto do aplicativo e informações de versão do executável |

## Hub (Windows)

O hub abre em uma janela própria, sem a barra do Windows, com botões de minimizar e fechar na barra superior (que também arrasta a janela). Ele tem três áreas:

- **Início:** pasta do Brasfoot (detectada automaticamente ou escolhida), situação de cada componente (instalado, atualização disponível ou não instalado) e os botões **Jogar**, **Instalar** e **Atualizar**.
- **Instalar:** oferece só o que ainda não está instalado. Componentes já instalados aparecem bloqueados.
- **Atualizar:** disponível apenas quando a versão instalada de algum componente é diferente da versão do pacote. Os componentes desatualizados são sempre incluídos, e os que faltam podem ser adicionados na mesma operação. A atualização segue as mesmas garantias da instalação: backup dos arquivos alterados, substituição atômica e conferência por SHA-256.
- **Backups:** lista de backups, criação de backup completo, restauração e abertura da pasta do backup.

O hub requer o Microsoft Edge WebView2 Runtime, presente no Windows 11 e na maioria das instalações do Windows 10. Sem ele, o hub oferece a página oficial de instalação e abre a interface Win32 simples, que tem as mesmas garantias de instalação.

```text
Brasfoot-Mega-Patch.exe            hub
Brasfoot-Mega-Patch.exe --classic  interface simples
```

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

Regras da restauração:

- Antes de restaurar, o hub cria automaticamente um backup completo do estado atual.
- Cada arquivo restaurado é escrito em um arquivo temporário, conferido por SHA-256 e então movido para o lugar.
- Em backups completos, arquivos que não existiam no backup são removidos apenas das pastas de dados (`teams/`, `conf_ligas_nacionais/`, `conf_estadual/`). Saves criados depois do backup são mantidos.
- Um backup de instalação só é restaurado na mesma pasta de jogo em que foi criado.

## Linux e macOS

```bash
./brasfoot-mega-patch --game /caminho/do/Brasfoot
./brasfoot-mega-patch --game /caminho/do/Brasfoot --only live
./brasfoot-mega-patch --game /caminho/do/Brasfoot --inspect
./brasfoot-mega-patch --game /caminho/do/Brasfoot --restore
```

| Opção | Efeito |
|---|---|
| `--game` | Pasta principal do Brasfoot; sem ela, o atualizador procura a instalação e abre um seletor de pasta |
| `--only patch\|live` | Instala somente um componente |
| `--inspect` | Mostra a compatibilidade em JSON sem alterar nada |
| `--restore` | Restaura o backup da instalação completa |
| `--yes` | Confirma sem pergunta interativa |
| `--version` | Mostra edição, plataforma e commit |

## Recursos do executável e assinatura

O build do Windows gera os recursos a partir de `winres/winres.json` com o [go-winres](https://github.com/tc-hib/go-winres): ícone da marca em vários tamanhos, manifesto com `asInvoker`, DPI por monitor, caminhos longos e controles comuns v6, e informações de versão preenchidas com a versão da edição.

A assinatura Authenticode é opcional e acontece logo após a compilação:

```powershell
$env:MEGA_PATCH_SIGN_THUMBPRINT = "<thumbprint SHA-1 do certificado>"
python tools/build_distribution.py --bundle <bundle> --output dist/<versao> --target windows/amd64
```

O build usa `signtool sign /fd SHA256 /tr <carimbo> /td SHA256` e confere com `signtool verify /pa`. Sem certificado, o executável é publicado sem assinatura e o SmartScreen pode exibir um aviso até que o arquivo ganhe reputação.

## Compilação local

```bash
cd windows-installer
go build ./...
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -ldflags "-H=windowsgui" -o Brasfoot-Mega-Patch.exe .
```

O build de distribuição oficial está descrito em [Release e publicação](release.md).
