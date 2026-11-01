# Contribuindo com o Brasfoot Mega Patch

Obrigado pelo interesse em contribuir. Este guia explica como o projeto é organizado, como preparar o ambiente e o que esperamos de um pull request.

## Antes de começar

- Leia a [arquitetura](docs/architecture.md) e o [guia de módulos](docs/modules.md) para entender onde cada mudança se encaixa.
- Para correções de dados de elencos, siga a [política de dados](docs/data-pipeline.md): toda informação precisa de uma fonte verificável e nada é inventado para preencher lacunas.
- Vulnerabilidades não devem ser abertas como issue pública; veja [SECURITY.md](SECURITY.md).

## Ambiente

| Ferramenta | Versão | Uso |
|---|---|---|
| Go | 1.23 ou superior | hub e atualizadores (`windows-installer/`) |
| Python | 3.12 ou superior | coleta, compilação, build e publicação (`tools/`) |
| JDK | 17 ou superior | codec de equipes, patches do executável e campo animado |
| Node.js | 22 ou superior | testes do site (`site/tests/`) |
| GitHub CLI | atual | publicação de releases |

Nenhum arquivo do Brasfoot faz parte do repositório. Para trabalhar com receitas e patches do executável é preciso ter uma instalação própria do jogo; mantenha cópias de trabalho em `data/private/`, que é ignorado pelo Git.

## Fluxo de trabalho

1. Crie um branch a partir de `main` com um nome descritivo (`fix/backup-restore`, `feat/hub-backups`, `data/serie-b-2026`).
2. Faça mudanças pequenas e focadas. Uma mudança de dados não deve vir junto com uma mudança de código.
3. Compile os módulos afetados:

   ```bash
   cd windows-installer && go build ./...
   ```

   ```bash
   python -m py_compile tools/<modulo>.py
   ```

4. Rode os testes relacionados quando o ambiente permitir:

   ```bash
   cd windows-installer && go test ./...
   ```

   ```bash
   python -m unittest discover -s tests
   ```

   ```bash
   node --test site/tests
   ```

5. Abra o pull request descrevendo o problema, a solução e como você verificou. Todo pull request passa por revisão humana antes do merge.

## Convenções de código

- **Sem comentários explicativos.** O código deve se explicar por nomes claros e funções pequenas. Anotações exigidas por ferramentas são permitidas.
- **Go:** `gofmt`, erros com mensagens em português voltadas ao usuário quando chegam à interface, nenhuma escrita no jogo sem verificação de hash.
- **Python:** biblioteca padrão sempre que possível, `argparse` para interfaces de linha de comando, saída em JSON para resultados consumidos por outras ferramentas.
- **Site:** HTML, CSS e JavaScript sem build; tokens de cor e tipografia em `:root` de `site/styles.css`; textos em português do Brasil.
- **Commits:** mensagens curtas no imperativo com prefixo de área, por exemplo `installer: ...`, `site: ...`, `data: ...`, `docs: ...`, `release: ...`.

## Regras do projeto

- Nunca adicione ao repositório binários, saves ou arquivos proprietários do Brasfoot. Mudanças no jogo são distribuídas somente como receitas delta reconhecidas por SHA-256.
- O motor de simulação do Brasfoot não é alterado. Recursos visuais, como o campo animado, usam apenas informações que o próprio jogo expõe.
- Toda escrita no jogo é precedida de backup e seguida de conferência por SHA-256.
- Não declare compatibilidade, testes ou verificação em jogo que não tenham sido observados.
- Segredos (tokens, chaves, `.env`) nunca entram em commits, logs ou documentação.

## Documentação

Mudanças de comportamento devem atualizar o documento correspondente em [`docs/`](docs/README.md) no mesmo pull request.
