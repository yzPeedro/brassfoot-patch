# Processo de release — bloqueado

Não existe release pública atualmente. Condições mínimas antes da primeira:

1. Resolver com evidência os 20 clubes no catálogo real e todos os elencos.
2. Corrigir lacunas de nacionalidade, posição detalhada e atributos esportivos; não publicar estimativas como fatos.
3. Validar arquivos `.ban` modificados dentro do Brasfoot instalado no Windows.
4. Integrar escudos/uniformes com direitos de distribuição adequados.
5. Desenvolver e testar instalador Windows gráfico, backup/rollback e limpeza controlada.
6. Garantir checksums, autenticação da origem, CI, público acessível e site com download real.
7. Configurar GitHub remoto e secrets antes de automatizar o ciclo da janela.

O site somente deve alterar `release.json` depois que a release estiver pública e seus hashes/URL estiverem verificados.
