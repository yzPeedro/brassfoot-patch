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
| `targets.go` | Estado-alvo por componente (instalar, atualizar, remover), variantes do executável, cofre de originais |
| `hub_setup_windows.go` | Instalação do próprio hub em pasta fixa, atalhos, registro em Aplicativos, remoção e autoatualização |
| `ui/hub.html` | Interface do hub (HTML, CSS e JavaScript em um único arquivo) |
| `ui/live-pitch.js` | Campo animado em movimento, cópia idêntica de `site/live-pitch.js`, embutida na página por `{{LIVEPITCH}}` |
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

- **Início:** pasta do Brasfoot (detectada automaticamente ou escolhida), situação de cada componente (instalado, atualização disponível ou não instalado), a versão mais recente com o link **Ver novidades** e os botões **Jogar**, **Instalar** e **Atualizar**. Clicar no campo animado abre um painel grande com o campo em movimento e as quatro condições de gramado (demonstração; fecha com o X, Esc ou clique fora).
- **Instalar:** mostra os componentes para marcar; os já instalados aparecem bloqueados. O switch **Escolha automática** (desde o hub 1.3.0) marca a recomendação e mostra o motivo em cada componente.
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

### Configurações

A tela **Configurações** reúne o que não precisa estar no caminho principal:

| Opção | Efeito |
|---|---|
| Pasta do jogo | Troca a instalação do Brasfoot usada pelo hub |
| Instalação original | Mostra quantas cópias originais o hub guarda (necessárias para remover os elencos) e permite indicar uma pasta do Brasfoot sem patch |
| Tema | Sistema (acompanha o Windows), claro ou escuro |
| Avisar quando sair uma versão nova | Liga a conferência com o hub fechado: valor `BrasfootMegaPatchNovidades` em `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (ao entrar no Windows) e tarefa agendada `Brasfoot Mega Patch\Novidades` (todo dia às 19h, depois da publicação diária). As duas executam o hub com `--notify-check`, que lê o `release.json` e mostra uma notificação do Windows quando há patch ou instalador ainda não visto; clicar na notificação abre o hub pelo protocolo `brasfootmegapatch:` |
| Procurar novidades agora | Repete a consulta à release mais recente |
| Remover o hub | Mesmo efeito de `--uninstall-hub` |

As preferências ficam em `%LOCALAPPDATA%\BrassfootPatch2026\hub-settings.json`, junto das últimas versões vistas e avisadas.

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
Brasfoot-Mega-Patch.exe --notify-check      confere a versão mais recente e notifica, sem abrir janela
```

O hub requer o Microsoft Edge WebView2 Runtime, presente no Windows 11 e na maioria das instalações do Windows 10. Sem ele, o hub oferece a página oficial de instalação e abre a interface Win32 simples, que também busca a versão mais recente, oferece atualizar o instalador e tem as mesmas garantias de instalação.

## Instalação e remoção por componentes

O hub trabalha com os componentes **Elencos 2026**, **Temporada 2026**, **Campo animado** e, desde o hub 1.2.0, **Escudos atualizados** (veja [Arquitetura](architecture.md#componentes)). O cartão dos escudos só aparece quando o pacote traz escudos.

- **Instalar:** os componentes aparecem para marcar, sem nada pré-marcado. Com o switch **Escolha automática** ligado, o hub marca a recomendação e mostra o motivo em cada cartão; o usuário pode mudar qualquer cartão, o que desliga o switch. A escolha do switch fica em `hub-settings.json` (`autoInstall`).
  - **Campo animado:** fica de fora com menos de 4 GB de memória instalada (`GetPhysicallyInstalledSystemMemory`), até 2 processadores lógicos ou com a velocidade padrão de partida em Super ou Ultra rápido. A velocidade vem de `options.bcf` (`est.Options.velocidade`, índice 0 Lento a 5 Ultra rápido), que o jogo copia para cada carreira nova.
  - **Elencos, Temporada 2026 e escudos:** sempre recomendados. Os motivos citam as carreiras salvas (`sav/*.s22`), que continuam abrindo, e os escudos trocados pelo usuário, que não são alterados.
- **Atualizar:** os componentes desatualizados são sempre incluídos; os ausentes podem ser adicionados.
- **Remover:** marque o que tirar ou use **Remover tudo**. O resto continua como está. As carreiras salvas não mudam.

Toda operação calcula um estado-alvo (o que deve ficar instalado) e aplica só a diferença:

1. O hub detecta o estado atual pelo SHA-256 do `bf22-23.exe` e dos arquivos do manifesto. Um componente está **atual** quando os arquivos são exatamente os do pacote, **desatualizado** quando são de uma versão anterior reconhecida e **ausente** quando estão como no jogo original.
2. O executável final é a variante que corresponde a Temporada e Campo animado no alvo. Os arquivos de equipe recebem a receita do pacote (Elencos no alvo) ou voltam à cópia original (Elencos removidos).
3. O manifesto da seleção é preparado em uma pasta temporária; cada arquivo é gerado pela receita correspondente e conferido.
4. Se a versão de origem do executável não estiver na receita do componente, o hub aplica primeiro a receita completa e depois a do componente, conferindo o executável intermediário.
5. A instalação copia os arquivos que serão alterados para um backup, substitui cada arquivo de forma atômica e confere o resultado. Em qualquer falha, os originais são restaurados.

Cada escudo é uma receita sobre o PNG original do clube. Um escudo cujo SHA-256 não é o original, nem o do pacote, nem o de uma versão anterior do pacote, foi trocado pelo usuário: o hub não o instala nem o remove, e ele não impede o resto da operação.

O jogo precisa estar fechado; o hub verifica os processos `bf22-23.exe`, `brasfoot.exe` e `brasfoot22-23.exe` antes de escrever.

### Cofre de originais

Para devolver os elencos e os escudos originais, o hub guarda em `%LOCALAPPDATA%\BrassfootPatch2026\originals\` uma cópia de cada arquivo do jogo cujo SHA-256 é o do jogo original (`vanillaSha256` no manifesto), nomeada pelo próprio hash. As cópias vêm do jogo antes da primeira instalação, dos backups de instalação e dos backups completos já existentes. Se faltar alguma, a remoção dos elencos fica indisponível e a tela Remover leva a **Configurações > Instalação original**, onde o usuário escolhe uma pasta do Brasfoot sem patch e o hub copia apenas os arquivos idênticos aos originais. O projeto nunca distribui arquivos originais.

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
- Em backups completos, arquivos que não existiam no backup são removidos apenas das pastas de dados (`teams/`, `conf_ligas_nacionais/`, `conf_estadual/`).
- Restaurar um backup completo nunca sobrescreve saves (`sav/`) nem `options.bcf` que já existam: o progresso das carreiras é sempre mantido. Saves que não existem mais são devolvidos.
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
| `--remove rosters,season,live,crests` | Remove componentes (`all` remove tudo); as carreiras salvas não mudam |
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
