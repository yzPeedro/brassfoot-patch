# Política de segurança

## Como relatar uma vulnerabilidade

Use o recurso [Report a vulnerability](https://github.com/yzPeedro/brassfoot-patch/security/advisories/new) do GitHub para relatar problemas de forma privada. Não abra issues públicas para vulnerabilidades. Inclua a versão afetada, os passos para reproduzir e o impacto esperado.

## Versões suportadas

Somente a versão mais recente publicada em [Releases](https://github.com/yzPeedro/brassfoot-patch/releases/latest) recebe correções.

## Garantias do atualizador

- **Sem binários proprietários:** os pacotes contêm apenas receitas delta. Cada arquivo resultante só é gerado a partir de um original com SHA-256 conhecido e é conferido antes da escrita.
- **Escrita restrita:** o atualizador só escreve arquivos de equipe (`teams/*.ban`), a configuração nacional (`conf_ligas_nacionais/BRA.cfg`) e o executável do jogo, sempre dentro da pasta escolhida. Caminhos fora da pasta, links simbólicos e nomes inválidos são recusados.
- **Backups:** antes de instalar, os arquivos que serão alterados são copiados e conferidos por SHA-256. Antes de restaurar um backup, o estado atual é guardado em um backup completo.
- **Sem rede durante a instalação:** o hub não baixa dados nem executáveis de terceiros; links externos abrem somente no navegador do usuário.
- **Sem privilégios elevados:** o executável declara `asInvoker` no manifesto e não solicita permissão de administrador.
- **Integridade das releases:** cada release publica `SHA256SUMS.txt` e `distribution.json` com hash, tamanho e commit de origem de cada artefato.

## Assinatura de código

O build do Windows aceita assinatura Authenticode com um certificado instalado no repositório de certificados do usuário (`--sign-thumbprint` ou `MEGA_PATCH_SIGN_THUMBPRINT`), com carimbo de tempo SHA-256. Releases não assinadas podem exibir o aviso do Microsoft Defender SmartScreen; nesse caso, confira o SHA-256 do arquivo baixado com o publicado na release.

```powershell
Get-FileHash .\Brasfoot-Mega-Patch-windows-x64.exe -Algorithm SHA256
```
