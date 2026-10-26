Você será o \*\*TECH LEAD, ARQUITETO PRINCIPAL E ORQUESTRADOR MULTIAGENTE\*\* do projeto Brasfoot Mega Patch.



A especificação integral do projeto será fornecida logo após esta instrução. Trate-a como a fonte principal dos requisitos. Preserve-a no repositório e não resuma nem descarte requisitos.



\## SUA MISSÃO



Executar a implementação integral do projeto usando o Alethe para delegar tarefas, minimizar consumo de tokens, coordenar agentes e integrar resultados.



Não quero apenas um planejamento. Quero execução real.



\## ORQUESTRAÇÃO



1\. Utilize o Alethe Orchestrate como mecanismo principal de delegação.

2\. Você, GPT-6 Astra, será o coordenador técnico.

3\. Configure o perfil econômico `savings`, privilegiando os agentes mais baratos capazes de concluir cada tarefa.

4\. Reserve seu próprio contexto para arquitetura, decisões difíceis, integração e resolução de bloqueadores.

5\. Delegue auditorias, pesquisas, implementação, refatoração, documentação e testes sempre que a delegação for economicamente vantajosa.

6\. Use playbooks como `scout-then-build`, `plan-big-execute-small`, `parallel-worktrees` e `advisor-escalation`, conforme a natureza da tarefa.

7\. Utilize Git worktrees para isolar alterações paralelas.

8\. Limite inicialmente a dois workers simultâneos para preservar memória RAM.

9\. Não execute auditorias redundantes nem repasse o prompt mestre inteiro a todos os trabalhadores.

10\. Cada worker deverá receber um contrato pequeno, com objetivo, arquivos relevantes, critérios de aceite e validações.



\## CONTINUIDADE SEM INTERVENÇÃO



Minha prioridade é não precisar enviar mensagens como "continue", "prossiga" ou "pode fazer".



Na primeira etapa, implemente uma infraestrutura de execução persistente que permita:



\- Salvar estado e progresso em disco.

\- Registrar tarefas pendentes e concluídas.

\- Retomar automaticamente tarefas interrompidas.

\- Reiniciar execuções após falhas recuperáveis.

\- Aguardar recuperação das cotas quando necessário, sem contornar limites dos provedores.

\- Executar novas etapas quando houver orçamento disponível.

\- Instalar um agendador independente das conversas do Codex.

\- Continuar operando mesmo quando uma sessão de agente terminar.

\- Executar a atualização esportiva diariamente.

\- Publicar automaticamente builds aprovadas pelas verificações técnicas.



O Alethe deverá ser utilizado para as ondas de trabalho que ele suporta. Construa o serviço de continuidade necessário para controlar execuções entre sessões.



Não dependa exclusivamente de `/alethe always`, pois isso não é um serviço permanente de execução.



\## CONSUMO DE RECURSOS



Otimize consumo de tokens, quotas e recursos computacionais.



\- Reutilize resultados de pesquisas anteriores.

\- Mantenha snapshots e resumos técnicos.

\- Use agentes econômicos em tarefas mecânicas.

\- Não escale para modelos pagos sem orçamento previamente autorizado.

\- Não aumente o paralelismo quando isso provocar problemas de memória.

\- Evite contextos gigantescos em workers.

\- Aproveite cache, execução incremental e saídas estruturadas.

\- Reserve modelos mais fortes para problemas comprovadamente complexos.

\- Configure limites de consumo e registre o uso real.



\## ORGANIZAÇÃO



Transforme a especificação integral em um backlog persistente com dependências, prioridades e critérios de aceite.



Organize os trabalhos de forma que as áreas independentes avancem em paralelo.



Implemente inicialmente a infraestrutura de coordenação, recuperação e persistência do estado. Em seguida, avance pelos módulos técnicos em ordem de dependência.



Não crie conflitos entre trabalhadores editando os mesmos arquivos simultaneamente.



Integre alterações somente após verificações automáticas apropriadas.



\## PUBLICAÇÃO



Você está autorizado a configurar a automação de commits, push, releases, documentação e deploy dentro do escopo do projeto.



Não exija homologação humana recorrente.



Não publique artefatos inválidos, não corrompa saves e não invente resultados de testes.



Preserve a última versão funcional em caso de falhas.



\## DOCUMENTAÇÃO PARA AGENTES



Crie um AGENTS.md e documentação persistente que permitam a qualquer agente recuperar:



\- A especificação integral.

\- O estado atual da implementação.

\- As decisões arquiteturais.

\- O backlog.

\- Os bloqueadores reais.

\- A última operação executada.

\- O próximo trabalho a executar.

\- As regras de orquestração.

\- As regras de publicação.



\## RESULTADO ESPERADO



Quero fornecer a especificação uma única vez.



Depois disso, a infraestrutura deverá coordenar o desenvolvimento e a operação contínua, retomando automaticamente o trabalho quando tecnicamente possível e respeitando os limites dos provedores.



Sua primeira ação deverá ser verificar o ambiente e o repositório, configurar o Alethe, persistir a especificação e começar a implementação real do mecanismo de continuidade.



Não me devolva somente um plano. Execute.



\---



A SEGUIR ESTÁ A ESPECIFICAÇÃO INTEGRAL DO BRASFOOT MEGA PATCH:



\[COLE AQUI, SEM CORTES, O PROMPT MESTRE COMPLETO QUE DEFINIMOS ANTERIORMENTE]



# PROMPT MESTRE — BRASFOOT MEGA PATCH



\## MISSÃO: RECONSTRUÇÃO GLOBAL, ENGENHARIA REVERSA, IDENTIDADE VISUAL E AUTOMAÇÃO DIÁRIA



Você está assumindo a responsabilidade técnica integral pelo projeto \*\*Brasfoot Mega Patch\*\*, uma evolução completa do antigo Brassfoot/Brasfoot Patch 2026.



Sua função não é simplesmente atualizar elencos, fazer pequenas correções ou produzir um novo instalador.



\*\*Sua missão é transformar o projeto em uma plataforma mundial de atualização, modernização, distribuição e preservação da experiência original do Brasfoot, com operação automatizada e manutenção contínua.\*\*



Esta será uma reconstrução substancial do projeto, abrangendo:



\- O próprio jogo e suas estruturas internas.

\- Engenharia reversa e adaptação da engine.

\- Ligas, clubes, jogadores e treinadores do mundo inteiro.

\- Competições nacionais e internacionais.

\- Seleções e Copas do Mundo.

\- Histórico de premiações, incluindo Bola de Ouro.

\- Identidade visual do jogo e seus recursos gráficos.

\- Instaladores para Windows, macOS e Linux.

\- Site oficial inteiramente novo.

\- Publicação de releases no GitHub.

\- Atualização diária de informações esportivas.

\- Geração automatizada de novas versões.

\- Documentação técnica e operacional.

\- Monitoramento, versionamento, recuperação e continuidade de operação.



\*\*Nome oficial e definitivo: Brasfoot Mega Patch.\*\*



O projeto permanecerá gratuito para todos os usuários.



A experiência original do Brasfoot deve continuar reconhecível. Nosso objetivo é modernizar e expandir o jogo, preservando sua essência de gerenciamento de futebol.



\---



\# 1. CONTEXTO E PONTO DE PARTIDA



\## 1.1. Repositório e infraestrutura



Repositório principal conhecido:



`https://github.com/yzPeedro/brassfoot-patch`



Site atualmente publicado:



`https://yzpeedro.github.io/brassfoot-patch/`



Branch principal:



`main`



O projeto já possui um histórico de atualizações de elencos, divisão de clubes, exportação de dados, geração de instaladores e publicação de releases.



Foram realizadas anteriormente operações envolvendo:



\- Atualizações de clubes das Séries A, B e C.

\- Exportação e manipulação de arquivos de clubes.

\- Investigação de arquivos de configuração do Brasfoot.

\- Correções na distribuição de clubes pelas divisões.

\- Correções de seletores de clubes e temporadas.

\- Atualizações de camisas, escudos e jogadores.

\- Desenvolvimento de site com catálogo de clubes.

\- Geração de instalador para Windows.

\- Backups do executável original.

\- Scripts PowerShell e Python.

\- Publicação de releases sem depender obrigatoriamente de GitHub Actions.

\- Utilização do GitHub CLI autenticado.



Essas experiências e descobertas precisam ser preservadas como conhecimento técnico.



\*\*Não assuma que a estrutura atual está correta, mas também não descarte conhecimento útil já conquistado.\*\*



Antes de modificar qualquer coisa, investigue o estado atual do projeto, seus commits, releases, scripts, arquivos, documentação, decisões anteriores e eventuais alterações não commitadas.



Localize e analise os artefatos de referência disponíveis, inclusive arquivos ZIP de equipes originais e relatórios de compatibilidade quando presentes.



A nomenclatura histórica do repositório pode ser mantida inicialmente para evitar quebra de URLs. A identidade pública, entretanto, deve ser Brasfoot Mega Patch.



\## 1.2. Restrições históricas que devem ser reavaliadas



Anteriormente, foram identificadas limitações importantes na estrutura das divisões brasileiras.



As Séries A, B e C foram trabalhadas com 20 clubes cada, enquanto a Série D apresentou particularidades de armazenamento, organização e capacidade.



Esse comportamento não deve ser esquecido.



Entretanto, a nova proposta não pode continuar limitada à organização anterior.



Investigue quais restrições são:



1\. Simplesmente decisões do nosso código.

2\. Limitações de formatos de arquivo.

3\. Restrições de estruturas internas do jogo.

4\. Limitações da interface gráfica.

5\. Restrições da lógica de simulação.

6\. Limitações realmente impossíveis de alterar sem reescrever componentes da engine.



Todas as limitações tecnicamente superáveis deverão ser tratadas na nova arquitetura.



Não altere cegamente o formato dos dados: descubra primeiro como o jogo interpreta cada estrutura.



\---



\# 2. FILOSOFIA DO NOVO PROJETO



O Brasfoot Mega Patch precisa seguir estes princípios permanentes:



\*\*Primeiro: cobertura mundial.\*\*



O sistema não deve ser projetado exclusivamente para o Brasil ou para um conjunto fixo de campeonatos.



\*\*Segundo: dados atualizados diariamente.\*\*



A aplicação deverá conferir o futebol mundial todos os dias, identificar diferenças reais e aplicar as atualizações necessárias.



\*\*Terceiro: automação de ponta a ponta.\*\*



Não quero participar manualmente da coleta, compilação, geração do instalador, criação da release ou atualização do site.



\*\*Quarto: simplicidade extrema para o usuário.\*\*



Quem joga não deve precisar conhecer diretórios, configurações, arquivos ou comandos.



\*\*Quinto: identidade visual profissional.\*\*



O jogo, os instaladores, o site e a documentação pública precisam transmitir a identidade do mesmo produto.



\*\*Sexto: preservação do Brasfoot.\*\*



Modernize o que for necessário sem transformar o Brasfoot em outro simulador irreconhecível.



\*\*Sétimo: consistência técnica.\*\*



Não crie versões incompatíveis, elencos inventados ou clubes duplicados apenas para cumprir métricas.



\*\*Oitavo: continuidade.\*\*



Toda rotina deve funcionar mesmo quando o agente original não estiver mais presente.



\*\*Nono: gratuidade.\*\*



Não introduza cobrança obrigatória, assinatura, paywall ou dependência de serviços pagos sem autorização.



\*\*Décimo: evolução contínua.\*\*



A arquitetura deverá permitir novas ligas, campeonatos, plataformas, dados e melhorias futuras sem reconstruções recorrentes.



\---



\# 3. RECONSTRUÇÃO DA ARQUITETURA



Quero que você avalie a necessidade de reorganizar completamente o repositório.



A nova arquitetura deve separar, no mínimo, os seguintes domínios:



1\. Engine e engenharia reversa.

2\. Modelo de dados do futebol mundial.

3\. Coleta e atualização de informações.

4\. Normalização e reconciliação dos dados.

5\. Catálogo de competições e temporadas.

6\. Gerenciamento de recursos gráficos.

7\. Geração de arquivos consumidos pelo jogo.

8\. Modificações e adaptações do executável.

9\. Integrações específicas de cada sistema operacional.

10\. Construção e empacotamento.

11\. Instaladores e atualizadores.

12\. Site e serviços de distribuição.

13\. Publicação de releases.

14\. Monitoramento e automação.

15\. Documentação.

16\. Testes e validações automatizadas.



A arquitetura pode ser um monorepositório, desde que exista uma divisão clara de responsabilidades.



Evite:



\- Scripts gigantescos com responsabilidades misturadas.

\- Dados esportivos inseridos manualmente no código.

\- Configurações globais inconsistentes.

\- Dependência de caminhos absolutos.

\- Duplicação de lógica por plataforma.

\- Acoplamento entre scraping, transformação de dados e publicação.

\- Dependência de memória informal de conversas.

\- Releases geradas a partir de estados não reproduzíveis.



Toda etapa precisa possuir entradas, saídas, contratos, logs estruturados e tratamento de falhas.



O processo completo deve ser reproduzível.



\---



\# 4. COBERTURA MUNDIAL DE CLUBES E CAMPEONATOS



Esta é uma das maiores mudanças do projeto.



\*\*O Brasfoot Mega Patch deverá ser projetado para suportar todas as ligas, de todos os países do mundo, sem limites artificiais definidos pelo nosso projeto.\*\*



Não quero uma pequena seleção de países considerados populares.



O objetivo é construir um catálogo global.



\## 4.1. Países



Crie um catálogo central de países e territórios com identidade estável, códigos padronizados e relacionamento com suas estruturas futebolísticas.



O catálogo não deve pressupor que todos os países possuem a mesma organização de competições.



Considere diferenças entre federações nacionais, regiões, territórios, associações esportivas e sistemas de ligas.



\## 4.2. Competições



Mapeie, conforme existirem e forem verificáveis:



\- Primeiras divisões nacionais.

\- Segundas, terceiras e demais divisões.

\- Ligas regionais.

\- Copas nacionais.

\- Supercopas.

\- Torneios continentais.

\- Competições internacionais.

\- Competições de acesso e rebaixamento.

\- Competições extintas, quando relevantes para o histórico.

\- Competições com calendários diferentes do ano civil.



Não imponha o mesmo modelo de temporada a todos os países.



Algumas competições funcionam por ano civil; outras atravessam dois anos.



A estrutura deve comportar ambos os casos.



\## 4.3. Clubes



Cada clube deverá possuir uma identidade persistente, independente da posição que ocupe na tabela ou da divisão em que esteja.



Armazene, conforme a disponibilidade de dados verificáveis:



\- Identificador interno.

\- Nome oficial.

\- Nome curto.

\- Nomes alternativos.

\- País.

\- Federação.

\- Região.

\- Competições.

\- Divisão atual.

\- Estádio.

\- Cidade.

\- Cores.

\- Escudo.

\- Uniformes.

\- Treinador.

\- Plantel.

\- Histórico de participação.

\- Status de atividade.

\- Data da última atualização.

\- Fontes utilizadas.

\- Grau de confiança de cada informação.



Um clube que subir de divisão não deverá se transformar em um novo registro.



\## 4.4. Capacidade do jogo



O cadastro global e a capacidade de simulação deverão ser tratados separadamente.



Se o Brasfoot originalmente possuir limitações em número de países, equipes, divisões ou clubes, investigue como essas limitações funcionam.



Quando for viável alterar a lógica interna de maneira estável, implemente a expansão.



Quando determinada estrutura exigir redesenho substancial, desenvolva a adaptação necessária com compatibilidade de dados e testes.



Não declare uma competição jogável apenas porque ela existe no catálogo.



É necessário que:



\- Seja possível selecionar corretamente seus participantes.

\- O calendário funcione.

\- As partidas sejam simuladas.

\- A classificação esteja correta.

\- As regras sejam respeitadas.

\- Os acessos e rebaixamentos sejam coerentes.

\- Os confrontos sejam válidos.

\- A interface represente corretamente a competição.

\- As informações persistam nos arquivos de carreira.



Crie métricas distintas para países catalogados, ligas catalogadas, ligas geradas e ligas efetivamente jogáveis.



\*\*Cobertura de dados não deve ser confundida com compatibilidade funcional.\*\*



\---



\# 5. ATUALIZAÇÃO MUNDIAL DE JOGADORES



Todos os clubes deverão possuir elencos atualizados com o maior grau possível de precisão.



\## 5.1. Informações individuais



Cada jogador deverá ter, sempre que verificável:



\- Nome.

\- Identidade única.

\- Clube atual.

\- Nacionalidade.

\- Data de nascimento.

\- Idade calculada.

\- Posição principal.

\- Posições secundárias.

\- Número da camisa.

\- Altura e outros atributos relevantes disponíveis.

\- Status no clube.

\- Informações de empréstimo.

\- Transferências confirmadas.

\- Histórico de movimentações.

\- Dados necessários à representação no Brasfoot.

\- Fonte e data da informação.



\## 5.2. Posições



Quero eliminar a situação de jogadores cadastrados em posições erradas ou excessivamente genéricas.



Utilize os dados encontrados para construir um mapeamento entre as posições reais e aquelas suportadas pela engine.



O mapeamento deve preservar a especificidade da fonte sempre que possível.



Se o Brasfoot permitir apenas uma posição, a escolha precisa seguir uma regra documentada e consistente.



Nunca atribua posições aleatoriamente.



\## 5.3. Transferências



A atualização diária deve identificar:



\- Contratações.

\- Saídas.

\- Empréstimos.

\- Retornos.

\- Jogadores sem clube.

\- Alterações confirmadas de inscrição.

\- Promoções para o elenco principal.

\- Mudanças de numeração.

\- Transferências futuras anunciadas oficialmente.



Não confunda negociação especulada com transferência efetivada.



O algoritmo precisa diferenciar data do anúncio, data de vigência e situação atual.



\## 5.4. Identidade e duplicação



Jogadores com nomes iguais não devem ser fundidos incorretamente.



Da mesma forma, diferenças na grafia não devem gerar duplicações do mesmo atleta.



Desenvolva um sistema robusto de identificação e reconciliação.



\---



\# 6. ATUALIZAÇÃO GLOBAL DE TREINADORES



O novo patch deverá manter treinadores atualizados para todos os clubes alcançados pelo catálogo.



Inclua:



\- Nome.

\- Identificador persistente.

\- Nacionalidade.

\- Clube ou seleção.

\- Data de início do vínculo, quando conhecida.

\- Estado atual do vínculo.

\- Informações compatíveis com os campos internos do Brasfoot.



Detecte alterações de comando técnico diariamente.



Considere treinadores interinos, efetivações, demissões, técnicos sem clube e mudanças entre clubes e seleções.



Nenhuma troca deve ser inventada.



Quando uma confirmação não existir, preserve o último dado confiável e registre a pendência.



\---



\# 7. FONTES DE DADOS E ESTRATÉGIA DE COLETA



Historicamente, utilizamos informações de fontes oficiais e tivemos integração com a API-Football.



Também identificamos o 365Scores como uma fonte particularmente útil para elencos, clubes e posições de jogadores.



\*\*Quero utilizar o 365Scores como uma fonte preferencial de consulta e conferência quando seu acesso e reutilização forem permitidos.\*\*



Entretanto, não presuma que qualquer fonte seja infalível ou possua cobertura literalmente completa.



\## 7.1. Hierarquia



Priorize, conforme o tipo de informação:



1\. Fontes oficiais dos clubes.

2\. Fontes oficiais das competições e federações.

3\. FIFA, confederações e organizações oficiais para competições internacionais.

4\. 365Scores, quando os termos permitirem o uso pretendido.

5\. Outras fontes esportivas confiáveis.

6\. API-Football como contingência autorizada, preferencialmente desabilitada por padrão.



A hierarquia pode variar conforme a natureza da informação.



Use evidências verificáveis para resolver conflitos entre fontes.



\## 7.2. Coleta responsável



Implemente:



\- Cache persistente.

\- Requisições incrementais.

\- Controle de frequência.

\- Backoff exponencial.

\- Respeito a limites de acesso.

\- Deduplicação.

\- Detecção de alteração.

\- Proveniência por campo.

\- Registro de falhas.

\- Retentativas limitadas.

\- Mecanismo de atualização parcial recuperável.



Não implemente contorno de autenticação, CAPTCHA, bloqueios técnicos ou restrições contratuais.



Se uma fonte impedir coleta automatizada, procure alternativas autorizadas.



\## 7.3. Qualidade dos dados



Diferencie:



\- Informação confirmada.

\- Informação provável.

\- Informação desatualizada.

\- Informação indisponível.

\- Informação conflitante.



Estabeleça políticas para resolver cada situação.



Não substitua informação conhecida por conteúdo vazio apenas porque uma coleta falhou.



\## 7.4. Auditoria temporal



Todos os dados esportivos precisam registrar:



\- Quando foram coletados.

\- Quando foram publicados pela fonte.

\- Quando passaram a valer.

\- Quando foram incorporados ao catálogo.

\- Em qual release apareceram.



Isso permitirá reproduzir versões anteriores e investigar inconsistências.



\---



\# 8. SELEÇÕES NACIONAIS E COPAS DO MUNDO



O Brasfoot Mega Patch deverá atualizar integralmente as informações relevantes às seleções.



A referência principal será a \*\*última Copa do Mundo masculina concluída\*\*, não a próxima Copa programada.



Exemplos:



\- Em 2026, depois da conclusão do torneio, a edição de referência é 2026.

\- Em 2029, a referência continua sendo 2026.

\- Em 2031, a referência passa a ser 2030.



Não confunda ano de vigência do patch com edição de referência da Copa do Mundo.



\## 8.1. Dados das seleções



Atualize:



\- Seleções participantes.

\- Nome oficial.

\- Identificadores.

\- País.

\- Escudos ou símbolos permitidos.

\- Uniformes.

\- Jogadores convocados.

\- Posições.

\- Treinadores.

\- Organização compatível com a engine.

\- Estrutura dos torneios.

\- Fases e grupos, quando representados pelo jogo.



Os elencos históricos da Copa deverão refletir aquela edição, enquanto os dados das seleções atuais poderão seguir uma atualização separada.



Nunca misture automaticamente elenco de Copa histórica com convocação atual.



\## 8.2. Atualização entre Copas



A rotina diária deverá continuar acompanhando as seleções, mas não deverá substituir a edição histórica de referência por torneios ainda não concluídos.



Quando uma nova Copa terminar, a rotina deverá identificar a mudança e preparar a atualização correspondente.



\## 8.3. Compatibilidade



Investigue quais partes da estrutura de seleções estão no executável e quais estão em arquivos externos.



Corrija possíveis referências antigas que afetem a representação dos torneios.



Preserve regras históricas que sejam intencionalmente parte de registros já concluídos.



\---



\# 9. BOLA DE OURO E PREMIAÇÕES



O Brasfoot Mega Patch deverá contemplar a atualização dos dados e funcionalidades existentes relacionados à Bola de Ouro.



Primeiro, descubra como o Brasfoot representa essas premiações.



Investigue:



\- Textos.

\- Tabelas.

\- Algoritmos.

\- Históricos.

\- Telas.

\- Regras de atribuição.

\- Registros persistentes.

\- Dependências de temporada.



Atualize os dados dos vencedores reais de edições já concluídas, quando o jogo possuir campos ou estruturas correspondentes.



Considere diferentes categorias de premiação apenas quando forem relevantes e adequadas ao modelo.



\*\*Não invente vencedores de anos futuros.\*\*



Não confunda o histórico real de prêmios com premiações simuladas durante uma carreira.



Se o jogo possuir um mecanismo próprio de escolha de melhores jogadores, preserve a natureza simulada da funcionalidade, corrigindo erros quando necessário.



Os históricos reais e os resultados da simulação devem ser claramente separados.



\---



\# 10. ENGENHARIA REVERSA PROFUNDA DO BRASFOOT



Este é um dos pilares do novo projeto.



A abordagem anterior consistia principalmente em atualizar recursos e adaptar partes do executável original.



Agora quero estudar profundamente a arquitetura do Brasfoot e identificar o que podemos melhorar.



\## 10.1. Investigação inicial



Antes de alterar binários, investigue:



\- Linguagem e tecnologias utilizadas no executável.

\- Arquitetura de processador.

\- Dependências.

\- Bibliotecas carregadas.

\- Formatos de dados.

\- Estrutura das instalações.

\- Mecanismos de leitura de clubes.

\- Recursos gráficos.

\- Renderização de texto.

\- Seleção de temporadas.

\- Seleção de campeonatos.

\- Regras de simulação.

\- Tratamento de arquivos de carreira.

\- Regras de instalação e atualização.

\- Armazenamento de configurações.

\- Interações entre executável e arquivos externos.



Documente os achados com evidências técnicas.



Não assuma que determinado comportamento existe apenas porque parece lógico.



\## 10.2. Mudanças na engine



Investigue e, quando tecnicamente viável e autorizado, corrija ou expanda:



\- Limites artificiais de clubes.

\- Limites de divisões.

\- Limites de países.

\- Estruturas de competições.

\- Organização dos participantes.

\- Distribuição de confrontos.

\- Calendários.

\- Seletores.

\- Nomes de temporadas.

\- Referências antigas de anos.

\- Estruturas de seleções.

\- Renderização de recursos.

\- Fontes.

\- Contraste de interface.

\- Persistência de dados.

\- Problemas conhecidos de travamento.

\- Comportamentos inconsistentes na criação de carreiras.



Não quero que o agente se limite à hipótese inicial de que determinados arquivos são imutáveis.



Investigue alternativas e avalie modificações estruturais.



\## 10.3. Limites legais



Engenharia reversa para compreensão, interoperabilidade e desenvolvimento de componentes próprios não equivale automaticamente à permissão para redistribuir código, binários ou recursos proprietários.



Antes de criar uma versão independente contendo partes protegidas do Brasfoot, verifique as permissões aplicáveis.



Caso não exista autorização para redistribuir o jogo completo, mantenha o produto como um patch/atualizador capaz de trabalhar sobre uma instalação legítima.



Nesse cenário, o resultado deve continuar parecendo um produto unificado para o usuário, mas a distribuição deverá conter somente os componentes que podemos distribuir legalmente.



Não remova proteção de licença ou mecanismos de ativação.



\## 10.4. Documentação das descobertas



Mantenha um registro técnico contendo:



\- Componente investigado.

\- Comportamento original.

\- Limitação identificada.

\- Estratégia de modificação.

\- Riscos.

\- Compatibilidade.

\- Evidências de funcionamento.

\- Testes associados.

\- Formato dos arquivos envolvidos.



Esse conhecimento precisa sobreviver à troca de agentes.



\---



\# 11. NOVO EXECUTÁVEL E DISTRIBUIÇÃO



Quero que a nova versão seja planejada \*\*como um produto completo e modernizado\*\*, não como uma coleção improvisada de arquivos.



O usuário deve receber um instalador claro e coeso.



A geração do produto deverá ser automatizada.



O pacote final deve incorporar, conforme a implementação e os direitos de distribuição:



\- Recursos atualizados.

\- Catálogo esportivo.

\- Adaptadores da engine.

\- Componentes de compatibilidade.

\- Recursos gráficos.

\- Interface modernizada.

\- Configurações apropriadas.

\- Instalador.

\- Atualizador.

\- Sistema de recuperação.



Não substitua indiscriminadamente arquivos originais sem necessidade.



A instalação deve saber exatamente quais recursos precisa modificar.



\---



\# 12. PRESERVAÇÃO DA EXPERIÊNCIA E DAS CARREIRAS



O objetivo não é apagar a identidade do Brasfoot.



Preserve, sempre que possível:



\- Fluxo geral da experiência original.

\- Mecânicas centrais.

\- Terminologia do jogo.

\- Organização conceitual de telas.

\- Características de gerenciamento.

\- Comportamentos consolidados.

\- Familiaridade visual e funcional.



As modernizações devem melhorar o produto sem descaracterizá-lo.



\## 12.1. Saves



A instalação deverá preservar carreiras existentes.



Antes de aplicar qualquer atualização estrutural, verifique se as mudanças podem afetar saves.



Sempre que necessário:



\- Faça backup.

\- Mantenha compatibilidade.

\- Desenvolva migrações.

\- Detecte formatos antigos.

\- Evite sobrescrever arquivos pessoais.

\- Permita restauração.



Uma incompatibilidade incontornável deve ser reconhecida e isolada; não corrompa o save para fingir compatibilidade.



\## 12.2. Backup do executável



Preserve a ideia original do projeto:



\*\*O usuário sempre deve ter uma maneira automática de recuperar o executável anterior.\*\*



Implemente backup versionado quando necessário.



O sistema deve evitar duplicações desnecessárias e reconhecer instalações já atualizadas.



\## 12.3. Atualização transacional



A aplicação do patch deverá funcionar, idealmente, como uma transação:



1\. Inspecionar a instalação.

2\. Verificar compatibilidade.

3\. Preparar arquivos.

4\. Criar backups necessários.

5\. Aplicar as modificações.

6\. Verificar o resultado.

7\. Confirmar a instalação.

8\. Recuperar automaticamente em caso de erro.



Não deixe o jogo parcialmente modificado quando ocorrer uma falha recuperável.



\---



\# 13. TEMPORADAS E REFERÊNCIAS A ANOS ANTIGOS



Uma das modificações históricas do projeto foi corrigir o seletor de temporada do Brasfoot.



O jogo original apresentava referências a 2023 e 2024.



Quero eliminar essas referências quando representarem a temporada atual do jogo e estiverem desatualizadas.



\## 13.1. Ano de vigência



A aplicação deverá utilizar um valor central:



`PATCH\_YEAR`



O ano deve derivar da edição efetiva do patch.



Atualmente, o projeto está na edição de 2026.



O valor deverá orientar:



\- Temporada inicial.

\- Opções de seleção de ano.

\- Apresentação de temporadas.

\- Dados associados ao início de carreira.

\- Identidade da release.

\- Identidade do site.

\- Informações do instalador.

\- Documentação.

\- Metadados relevantes.



\## 13.2. Seleção de ano



Se o jogo permitir selecionar uma temporada para iniciar uma nova carreira, quero que as opções correspondam à edição efetivamente distribuída.



Para a edição 2026, a opção inicial deverá ser 2026, substituindo as opções antigas de 2023/2024 quando estas forem apenas defaults ultrapassados.



Não basta alterar uma string na interface: o calendário, os clubes, as competições e os dados carregados precisam corresponder à temporada selecionada.



\## 13.3. Não falsificar história



Não substitua cegamente todos os anos antigos existentes nos binários.



Anos que representem conquistas históricas, resultados reais, datas de fundação ou registros legítimos devem permanecer corretos.



Distinga referências obsoletas de dados históricos.



\---



\# 14. ESCUDOS E UNIFORMES EM ALTA QUALIDADE



Quero elevar substancialmente a qualidade do acervo gráfico.



Os escudos e uniformes deverão ser sempre tão atualizados e nítidos quanto possível.



\## 14.1. Escudos



Priorize arquivos oficiais ou recursos cuja utilização seja autorizada.



Sempre que tecnicamente viável:



\- Preserve originais vetoriais.

\- Evite upscaling artificial.

\- Gere resoluções adequadas.

\- Preserve proporções.

\- Evite distorções.

\- Preserve transparência.

\- Use formatos compatíveis com o jogo.

\- Verifique legibilidade em tamanhos pequenos.

\- Detecte mudanças oficiais de identidade.



O processamento deve possuir cache e geração determinística.



Não recodifique imagens desnecessariamente a cada execução diária.



\## 14.2. Uniformes



Para cada equipe, trabalhe com:



\- Uniforme principal.

\- Uniforme reserva.

\- Terceiro uniforme, quando aplicável.

\- Variações relevantes suportadas pela engine.

\- Temporada correspondente.

\- Identidade visual oficial.

\- Mapeamento de cores e padrões.



Não invente uniformes oficiais inexistentes.



Quando um uniforme ainda não estiver disponível em fonte confiável, preserve a última versão válida ou utilize um recurso genérico explicitamente classificado.



\## 14.3. Conversão para o jogo



Investigue as limitações do formato gráfico do Brasfoot.



Crie um pipeline de transformação que preserve o máximo possível da qualidade original dentro dessas limitações.



Implemente verificações para:



\- Dimensões.

\- Canais de cor.

\- Transparência.

\- Tamanho dos arquivos.

\- Arquivos corrompidos.

\- Compatibilidade.

\- Integridade visual.



O site poderá utilizar resoluções superiores às suportadas pela engine.



\## 14.4. Direitos sobre as imagens



Catalogação de clubes não concede automaticamente o direito de redistribuir logotipos e uniformes.



Registre origem, licença ou autorização quando aplicável.



Prefira recursos permitidos e não copie indiscriminadamente catálogos de terceiros.



\---



\# 15. MODERNIZAÇÃO VISUAL DO JOGO



O Brasfoot é um jogo altamente orientado a textos e dados.



A legibilidade precisa ser tratada como prioridade.



\## 15.1. Tipografia



Investigue a possibilidade de atualizar a fonte utilizada internamente.



Avalie fontes modernas, profissionais e legíveis, como:



\- Inter.

\- IBM Plex Sans.

\- Source Sans 3.

\- Atkinson Hyperlegible.



Essas são referências, não uma escolha obrigatória.



A decisão final deve considerar:



\- Compatibilidade com a renderização existente.

\- Legibilidade em resoluções baixas.

\- Suporte a caracteres internacionais.

\- Números e tabelas.

\- Alinhamento.

\- Largura dos elementos.

\- Hierarquia de informação.

\- Licença de distribuição.

\- Performance.



Se o jogo utilizar componentes legados que dificultem a substituição, investigue alternativas compatíveis.



\## 15.2. Contraste



Quero corrigir problemas de textos que se misturam ao fundo.



Faça uma auditoria de:



\- Textos primários.

\- Textos secundários.

\- Cabeçalhos.

\- Tabelas.

\- Estados selecionados.

\- Botões.

\- Menus.

\- Listas.

\- Informações de desempenho.

\- Números.

\- Alertas.



Padronize contraste e legibilidade.



Evite cores diferentes sem significado.



\## 15.3. Preservação textual



\*\*Não reescreva os textos originais do jogo apenas para modernizar a interface.\*\*



Meu objetivo neste momento é melhorar a apresentação visual, e não mudar a identidade linguística do Brasfoot.



Corrija apenas textos tecnicamente incorretos ou referências antigas cuja atualização seja necessária.



\## 15.4. Resoluções e escala



Investigue o comportamento em diferentes resoluções e configurações de escala.



Evite cortes, elementos fora da tela, textos sobrepostos e botões inacessíveis.



\---



\# 16. SUPORTE A WINDOWS, MACOS E LINUX



O Brasfoot Mega Patch deverá contemplar três grandes plataformas:



\*\*Windows, macOS e Linux.\*\*



Não quero que a arquitetura permaneça exclusivamente Windows.



\## 16.1. Investigação por plataforma



Primeiro, identifique se existem versões legítimas nativas do Brasfoot para essas plataformas.



Caso não existam, estude as possibilidades reais de interoperabilidade.



Considere, conforme viabilidade:



\- Execução nativa.

\- Camadas de compatibilidade.

\- Wine.

\- Proton.

\- CrossOver.

\- Wrappers.

\- Componentes reimplementados.

\- Portabilidade de módulos próprios.



Não apresente uma aplicação executada via Wine como se fosse um port nativo.



Documente corretamente a tecnologia utilizada.



\## 16.2. Windows



Preserve uma experiência simples:



\- Instalador executável.

\- Detecção de instalação.

\- Backup automático.

\- Atualização em poucos passos.

\- Suporte a atualizações futuras.

\- Tratamento claro de falhas.

\- Desinstalação e recuperação.



\## 16.3. Linux



Investigue distribuições e ambientes gráficos relevantes.



Avalie formatos de distribuição como:



\- AppImage.

\- Pacotes `.deb`.

\- Pacotes `.rpm`.

\- Outro formato apropriado, conforme a estratégia final.



Evite exigir que o usuário instale manualmente dezenas de dependências.



Caso seja necessária uma camada de compatibilidade, configure-a da maneira mais transparente e automatizada possível.



\## 16.4. macOS



Investigue arquiteturas Intel e Apple Silicon.



Avalie:



\- Compatibilidade do jogo.

\- Empacotamento.

\- Aplicações `.app`.

\- Distribuição `.dmg` ou `.pkg`.

\- Assinatura e notarização quando disponíveis.

\- Restrições do sistema.

\- Camadas de compatibilidade quando necessárias.



Não declare compatibilidade com determinada arquitetura sem validar.



\## 16.5. Validação



O processo precisa ser capaz de testar o comportamento do produto em ambientes reais ou adequadamente virtualizados.



Nunca marque macOS ou Linux como totalmente compatíveis com base apenas em compilação cruzada bem-sucedida.



\## 16.6. Distribuição



O sistema de releases deverá identificar quais artefatos existem para cada plataforma.



Cada arquivo deve possuir:



\- Plataforma.

\- Arquitetura.

\- Versão.

\- Identificador de build.

\- Hash SHA-256.

\- Tamanho.

\- Estado de compatibilidade.



\---



\# 17. INSTALADOR COMPLETAMENTE RENOVADO



Quero reconstruir visualmente o instalador.



O público-alvo inclui usuários que não entendem absolutamente nada de computadores.



A experiência precisa ser autoexplicativa.



\## 17.1. Filosofia de interface



O usuário não deve precisar ler um manual para instalar o patch.



O instalador deverá ser:



\- Bonito.

\- Moderno.

\- Acessível.

\- Objetivo.

\- Visualmente consistente.

\- Rápido.

\- Fácil de compreender.

\- Seguro.

\- Discreto.

\- Sem excesso de texto.



\## 17.2. Identidade visual



Utilize a nova identidade azul do Brasfoot Mega Patch.



Considere:



\- Ícones claros.

\- Animações suaves.

\- Indicadores de progresso.

\- Tipografia moderna.

\- Hierarquia visual.

\- Botões grandes e compreensíveis.

\- Espaçamento confortável.

\- Estados visuais consistentes.



Não utilize gráficos e animações que atrapalhem a instalação.



\## 17.3. Fluxo principal



O fluxo ideal é:



\*\*Abrir → identificar o jogo → instalar/atualizar → concluir.\*\*



Se a instalação for encontrada automaticamente, o usuário não deve precisar selecioná-la manualmente.



Se não for encontrada, ofereça uma interface gráfica simples para escolher a pasta.



\## 17.4. Tela inicial



Apresente somente informações essenciais:



\- Brasfoot Mega Patch.

\- Edição vigente.

\- Estado da instalação detectada.

\- Ação principal.



Não exiba explicações técnicas desnecessárias.



\## 17.5. Progresso



Apresente mensagens curtas, como:



\- Preparando arquivos.

\- Criando backup.

\- Atualizando clubes.

\- Instalando melhorias.

\- Finalizando.



Não exponha comandos, stack traces ou caminhos internos.



\## 17.6. Conclusão



Ao terminar, mostre claramente:



\- Atualização concluída.

\- Edição instalada.

\- Botão para jogar.

\- Botão para fechar.



Quando possível, ofereça a opção de iniciar o jogo imediatamente.



\## 17.7. Erros



Mensagens de erro devem ser curtas, diretas e úteis.



Exemplos:



"Não encontramos o Brasfoot."



"O jogo precisa estar fechado."



"Não foi possível concluir a instalação."



"Os arquivos anteriores foram restaurados."



Forneça uma ação de correção sempre que possível.



Registre detalhes técnicos nos logs, sem expô-los obrigatoriamente na interface.



\## 17.8. Logs



O instalador não precisa conter uma enorme tela de logs.



Armazene logs detalhados em local apropriado e documentado.



Quando realmente necessário, disponibilize uma opção secundária para diagnóstico.



O usuário comum não deve ser obrigado a lidar com logs.



\## 17.9. Atualizações futuras



O instalador deverá reconhecer versões anteriores do Mega Patch.



Deve ser possível atualizar uma instalação existente sem reinstalar tudo nem destruir configurações ou saves.



\## 17.10. Acessibilidade



Implemente, conforme o toolkit suportar:



\- Navegação por teclado.

\- Foco visível.

\- Contraste adequado.

\- Áreas clicáveis confortáveis.

\- Compatibilidade com escala de interface.

\- Mensagens compreensíveis.

\- Suporte a tecnologias assistivas.



Evite depender exclusivamente de cores para transmitir estados.



\---



\# 18. NOVA IDENTIDADE VISUAL — BRASFOOT MEGA PATCH



A identidade visual antiga do site deverá ser completamente abandonada.



\*\*Não quero uma simples troca da cor verde pela azul.\*\*



Quero um redesign integral.



\## 18.1. Cor principal



A identidade deverá utilizar azul inspirado na tonalidade tradicional associada ao Cruzeiro Esporte Clube.



Essa escolha representa apenas uma preferência de cor.



\*\*O site não deverá conter escudo, nome, mascote, referências visuais ou conteúdo do Cruzeiro em sua identidade.\*\*



O produto deve ser neutro em relação a clubes.



\## 18.2. Direção artística



Quero uma estética moderna, refinada, esportiva e tecnológica.



A identidade pode trabalhar com:



\- Azul intenso.

\- Azul profundo.

\- Branco.

\- Tons neutros.

\- Superfícies escuras quando apropriado.

\- Contrastes bem definidos.

\- Elementos gráficos originais.

\- Movimento fluido.

\- Tipografia de personalidade.



Defina uma paleta completa de design tokens.



Não use verde como identidade principal.



\## 18.3. Marca



Desenvolva a identidade do nome:



\*\*Brasfoot Mega Patch\*\*



Crie um sistema visual coerente para:



\- Logotipo.

\- Símbolo.

\- Favicon.

\- Site.

\- Instalador.

\- Documentação.

\- Ícones.

\- Recursos de divulgação.

\- Cards de release.

\- Imagens sociais.



Não utilize marcas de clubes como base do logotipo.



Verifique também as condições de uso do nome Brasfoot e de eventuais marcas associadas.



\---



\# 19. RECONSTRUÇÃO TOTAL DO SITE



O site atual deverá ser substituído por uma implementação nova.



Não quero reaproveitamento automático de componentes, estilos, animações, ilustrações e layouts da versão antiga.



Os dados e conhecimentos aproveitáveis podem ser migrados.



\*\*A experiência visual precisa ser criada novamente.\*\*



\## 19.1. Objetivo



O site será a principal vitrine do Brasfoot Mega Patch.



Ele precisa explicar rapidamente o que o produto faz e permitir o download com o mínimo de esforço.



\## 19.2. Hero principal



A primeira seção deverá transmitir:



\- Nome do projeto.

\- Ano de vigência.

\- Proposta do Mega Patch.

\- Compatibilidade com plataformas.

\- Acesso imediato ao download.



O ano precisa estar claramente visível.



Exemplo conceitual:



"Brasfoot Mega Patch 2026"



"Seu futebol, atualizado."



O texto definitivo deve ser desenvolvido editorialmente, sem clichês excessivos.



\## 19.3. Botão de download inteligente



O site deverá identificar o sistema operacional do visitante usando mecanismos apropriados do navegador.



A partir disso, deve apresentar prioritariamente o instalador compatível.



Exemplos:



\- Windows → download Windows.

\- macOS → download macOS.

\- Linux → download Linux.



A detecção pode falhar ou ser limitada pelas configurações do navegador.



Por isso, o usuário sempre deverá poder selecionar outro sistema manualmente.



Nunca esconda os downloads alternativos.



Não anuncie como disponível uma build inexistente ou não validada.



\## 19.4. Downloads alternativos



Inclua uma área clara para escolher plataforma e arquitetura.



Apresente somente informações relevantes:



\- Plataforma.

\- Arquitetura, quando necessária.

\- Versão.

\- Tamanho aproximado.

\- Download.



Informações técnicas adicionais podem ficar em detalhes expansíveis ou na documentação.



\## 19.5. Seções do site



Construa uma arquitetura de conteúdo que possa contemplar:



\- Página inicial.

\- Download.

\- Recursos do Mega Patch.

\- Países.

\- Competições.

\- Clubes.

\- Elencos.

\- Atualizações.

\- Histórico de versões.

\- Guia rápido de instalação.

\- Compatibilidade.

\- Perguntas frequentes.

\- Documentação.

\- Doações.

\- Créditos e informações legais.



Evite criar seções apenas para preencher espaço.



\## 19.6. Catálogo mundial



O site deverá refletir o novo universo de dados.



O usuário poderá explorar:



\- Países.

\- Ligas.

\- Divisões.

\- Clubes.

\- Jogadores.

\- Treinadores.

\- Informações das seleções.

\- Versões disponíveis.



Projete filtros eficientes, pesquisa rápida, ordenação e navegação compreensível.



Não carregue o catálogo mundial inteiro no navegador de uma única vez.



Implemente paginação, indexação, carregamento incremental ou outra solução adequada.



\## 19.7. Páginas de clubes



As páginas deverão mostrar, conforme os dados disponíveis:



\- Escudo.

\- Nome.

\- País.

\- Competição.

\- Divisão.

\- Treinador.

\- Elenco.

\- Posições.

\- Uniformes.

\- Temporada.

\- Data da atualização.



Evite campos preenchidos artificialmente.



\## 19.8. Histórico de atualizações



Apresente versões do patch e alterações relevantes.



O usuário deve conseguir identificar rapidamente o que mudou entre releases.



Não exiba logs de commits como substituto de notas de versão compreensíveis.



\---



\# 20. ANIMAÇÕES, MOVIMENTO E EXPERIÊNCIA



Quero que o novo site seja visualmente impressionante, mas sem parecer uma demonstração genérica criada por inteligência artificial.



\## 20.1. Animações



Utilize animações quando contribuírem para:



\- Apresentação do produto.

\- Orientação.

\- Feedback.

\- Transição.

\- Narrativa visual.

\- Destaque de informações relevantes.



Considere:



\- Scroll reveal.

\- Transições suaves.

\- Microinterações.

\- Parallax discreto.

\- Animações vetoriais.

\- Transições entre estados.

\- Elementos esportivos abstratos.

\- Efeitos de profundidade.

\- Smooth scrolling.



Não transforme a página em um carnaval de efeitos.



\## 20.2. Menos estética genérica de IA



Evite:



\- Gradientes aleatórios.

\- Glow exagerado.

\- Glassmorphism em todos os componentes.

\- Cartões idênticos repetidos indefinidamente.

\- Emojis como substitutos de ícones profissionais.

\- Textos promocionais artificiais.

\- Espaçamentos inconsistentes.

\- Animações sem propósito.

\- Seções redundantes.

\- Ilustrações genéricas.

\- Layout com aparência de template não personalizado.



Quero uma linguagem visual deliberada e consistente.



\## 20.3. Performance



Animações não podem comprometer a usabilidade.



Prefira propriedades eficientes para renderização.



Evite bibliotecas pesadas sem justificativa.



Respeite `prefers-reduced-motion`.



Em dispositivos modestos, a navegação precisa continuar fluida.



\## 20.4. Responsividade



Projete de maneira cuidadosa para:



\- Desktop.

\- Notebook.

\- Tablet.

\- Celular.



Nenhuma experiência deve depender de hover ou de uma tela grande.



\---



\# 21. SEO EXTREMAMENTE BEM ESTRUTURADO



Quero que o Brasfoot Mega Patch seja facilmente descoberto por mecanismos de busca.



O site precisa deixar claro que existe uma edição atualizada do patch.



\## 21.1. Arquitetura técnica



Avalie adotar geração estática ou pré-renderização de páginas relevantes.



Como o site está hospedado no GitHub Pages, não dependa exclusivamente de uma SPA renderizada no cliente para indexação.



Investigue ferramentas como Astro, Eleventy ou soluções equivalentes.



A escolha deverá considerar indexação, performance, manutenção e compatibilidade com a hospedagem.



\## 21.2. Metadados



Implemente:



\- Titles únicos.

\- Meta descriptions.

\- Canonical URLs.

\- Open Graph.

\- Twitter Cards.

\- Structured data.

\- Sitemap XML.

\- Robots.txt.

\- URLs semânticas.

\- Redirecionamentos adequados.

\- Metadados de idioma.

\- Tratamento de páginas removidas.

\- Evitar conteúdo duplicado.



\## 21.3. Dados estruturados



Utilize tipos schema.org adequados, conforme aplicabilidade real.



Considere representações apropriadas para software, downloads, organização e páginas de conteúdo.



Não adicione avaliações fictícias, classificações fabricadas ou metadados enganosos.



\## 21.4. Indexação do catálogo



Planeje URLs indexáveis para:



\- Países.

\- Competições.

\- Clubes.

\- Páginas relevantes do projeto.



Não gere indiscriminadamente milhões de páginas vazias ou praticamente idênticas.



Estabeleça regras de qualidade para publicação de páginas indexáveis.



\## 21.5. Atualização anual



Quando o patch mudar de edição, atualize automaticamente:



\- Títulos.

\- Descrições.

\- Páginas de download.

\- Informações de versão.

\- Sitemap.

\- Dados estruturados.

\- Links internos.

\- Histórico de edições.



O ano vigente deve ser evidente.



Preserve URLs históricas relevantes e evite quebrar links já divulgados.



\## 21.6. SEO real



SEO não é simplesmente repetir a expressão "Brasfoot 2026 download" dezenas de vezes.



Priorize informação útil, correta e verificável.



Monitore Core Web Vitals e acessibilidade.



Não prometa posicionamento específico no Google: implemente as condições técnicas que favoreçam a descoberta e acompanhe os resultados.



\---



\# 22. PIX, DOAÇÕES E GRATUIDADE



O projeto permanecerá completamente gratuito.



Quero manter a possibilidade de doações voluntárias.



\## 22.1. PIX



Recupere do projeto ou do contexto histórico a chave/código PIX previamente fornecido pelo proprietário.



Valide a integridade do payload antes de utilizá-lo.



Não invente nem substitua os dados de pagamento.



\## 22.2. QR Code



Disponibilize um QR Code funcional para doação.



O usuário poderá:



\- Escanear o QR Code.

\- Copiar o código PIX.

\- Contribuir voluntariamente.



\## 22.3. Onde aparecerá



A doação poderá aparecer:



\- No site.

\- No instalador, de forma discreta.

\- Em uma página dedicada.



Não apresente solicitações insistentes.



\## 22.4. Regras



Não haverá:



\- Paywall.

\- Propaganda enganosa.

\- Restrição de funcionalidades.

\- Cobrança pela instalação.

\- Tela de doação obrigatória.

\- Bloqueio de atualização por ausência de contribuição.



\## 22.5. PayPal futuro



Prepare a arquitetura para permitir PayPal futuramente.



\*\*Não habilite PayPal agora.\*\*



O método ativo deverá continuar sendo somente PIX até nova instrução.



\---



\# 23. AUTOMAÇÃO DIÁRIA — PRINCIPAL EXIGÊNCIA OPERACIONAL



Este é um requisito central.



\*\*Quero que o Brasfoot Mega Patch seja atualizado diariamente sem minha participação manual.\*\*



Não quero precisar:



\- Abrir o ChatGPT.

\- Executar comandos.

\- Aprovar deploy.

\- Criar release.

\- Enviar instalador.

\- Fazer upload de ZIP.

\- Alterar links.

\- Atualizar páginas.

\- Modificar números de versão.

\- Corrigir manualmente documentação.

\- Informar mudanças de elenco.



Você deverá implementar uma infraestrutura persistente capaz de executar essas atividades automaticamente.



\## 23.1. Horário



Na ausência de configuração anterior, utilize:



\*\*06:00, horário de Brasília (America/Sao\_Paulo), todos os dias.\*\*



O horário deverá ser configurável.



Considere variações de disponibilidade das fontes e alterações publicadas depois da execução.



\## 23.2. Etapas diárias



A rotina deverá realizar:



\*\*Etapa 1 — Inspeção\*\*



\- Verificar o estado da última execução.

\- Identificar a última release.

\- Verificar os arquivos publicados.

\- Conferir o ano vigente.

\- Detectar problemas pendentes.



\*\*Etapa 2 — Coleta\*\*



\- Atualizar catálogo de países.

\- Atualizar catálogo de competições.

\- Verificar clubes.

\- Verificar divisões.

\- Verificar jogadores.

\- Verificar posições.

\- Verificar transferências.

\- Verificar treinadores.

\- Verificar uniformes.

\- Verificar escudos.

\- Verificar informações de seleções.

\- Verificar premiações concluídas.

\- Verificar alterações estruturais relevantes.



\*\*Etapa 3 — Reconciliação\*\*



\- Comparar dados novos com o snapshot anterior.

\- Identificar divergências.

\- Resolver conflitos quando existir evidência suficiente.

\- Preservar informações confiáveis.

\- Produzir um relatório de diferenças.



\*\*Etapa 4 — Transformação\*\*



\- Atualizar o catálogo normalizado.

\- Gerar os dados exigidos pelo Brasfoot.

\- Atualizar recursos gráficos.

\- Atualizar referências de temporada, quando necessário.

\- Atualizar os metadados do produto.



\*\*Etapa 5 — Construção\*\*



\- Construir artefatos do jogo.

\- Gerar os instaladores suportados.

\- Montar pacotes distribuíveis.

\- Calcular hashes.

\- Gerar manifestos.



\*\*Etapa 6 — Validação automatizada\*\*



\- Validar dados.

\- Validar integridade.

\- Verificar instaladores.

\- Verificar estrutura das builds.

\- Executar testes automatizados relevantes.

\- Verificar compatibilidade das alterações.

\- Validar backups e migrações quando afetados.



\*\*Etapa 7 — Publicação\*\*



\- Criar commits necessários.

\- Publicar mudanças no repositório.

\- Criar ou atualizar a release apropriada.

\- Fazer upload dos artefatos.

\- Atualizar os metadados públicos.

\- Publicar o site.

\- Atualizar a documentação.



\*\*Etapa 8 — Verificação pós-publicação\*\*



\- Conferir arquivos publicados.

\- Conferir links.

\- Conferir hashes.

\- Conferir a versão exposta pelo site.

\- Conferir o download correspondente a cada plataforma.

\- Registrar o resultado da execução.



\## 23.3. Mudanças inexistentes



Se nenhum dado relevante mudou, não gere uma nova versão fictícia.



Registre a execução diária como concluída e preserve a release atual.



Se somente dados esportivos mudarem, gere uma atualização de conteúdo.



Se houver alteração de código, compatibilidade ou estrutura, gere a versão correspondente.



\## 23.4. Histórico



Mantenha snapshots diários ou registros de diferenças suficientes para reconstruir o histórico.



Cada release deverá ser rastreável ao conjunto exato de dados utilizado.



\---



\# 24. EXECUÇÃO SEM DEPENDER DO CHAT ABERTO



\*\*Uma conversa do ChatGPT não é um agendador persistente nem um servidor de compilação.\*\*



Portanto, você deverá configurar uma infraestrutura real de execução.



Não quero um sistema que dependa de eu iniciar uma nova conversa para funcionar.



\## 24.1. Opções de execução



Avalie:



\- Agendador de Tarefas do Windows.

\- Serviço persistente.

\- Runner auto-hospedado.

\- VPS.

\- Servidor dedicado.

\- Orquestrador independente.

\- GitHub Actions, se houver capacidade disponível futuramente.

\- Combinação de scheduler e agente executável.



Não dependa obrigatoriamente de GitHub Actions, pois o projeto já enfrentou limitações de uso.



Priorize uma estratégia sem custo adicional quando viável.



\## 24.2. Ambiente



O desenvolvimento anterior utilizou Windows e ferramentas como:



\- Git.

\- GitHub CLI.

\- PowerShell.

\- Python.

\- Ferramentas de compilação e empacotamento.



Descubra o ambiente atual antes de definir os scripts finais.



Não introduza uma dependência obrigatória de WSL quando a tarefa puder ser executada de maneira mais estável diretamente no Windows.



\## 24.3. Autonomia real



A automação deverá ter condições de:



\- Buscar alterações.

\- Processar dados.

\- Executar builds.

\- Validar resultados.

\- Criar commits.

\- Fazer push.

\- Publicar releases.

\- Atualizar o site.

\- Recuperar falhas transitórias.



Utilize credenciais já disponíveis de forma segura, sem expô-las.



Se forem necessárias credenciais que não existem, documente precisamente o requisito. Não simule acesso ou sucesso.



\## 24.4. Recuperação



Se a máquina estiver desligada no horário programado, a rotina deverá reconhecer a execução perdida e tentar recuperá-la na próxima oportunidade.



Se uma fonte estiver indisponível, a rotina não deverá destruir o catálogo existente.



Se uma build falhar, preserve a versão anterior.



Se uma publicação falhar parcialmente, execute recuperação ou conclua a operação de forma idempotente.



\---



\# 25. PUBLICAÇÃO AUTOMÁTICA NO GITHUB



Não quero aprovações humanas para cada release.



O agente deverá utilizar os acessos concedidos ao repositório.



\## 25.1. Git



Todas as mudanças deverão possuir commits coerentes.



Evite commits enormes sem necessidade.



Não utilize force push para ocultar problemas.



Preserve histórico e rastreabilidade.



\## 25.2. Releases



Crie releases automaticamente conforme a política de versionamento definida.



O título deverá refletir a edição e a versão.



Exemplo conceitual:



`Brasfoot Mega Patch 2026 — v2026.x.y`



Não assuma que a versão utilizada no exemplo é a release corrente. Consulte o repositório.



\## 25.3. Artefatos



Cada release deverá disponibilizar, conforme as plataformas realmente suportadas:



\- Instalador Windows.

\- Pacote macOS.

\- Pacote Linux.

\- Checksums.

\- Manifesto de versão.

\- Documentação de instalação, quando necessária.

\- Notas de atualização.



Não publique arquivos de exemplo ou executáveis vazios como se fossem versões funcionais.



\## 25.4. Sem homologação humana



\*\*A publicação não deve depender de um usuário aprovar manualmente a release.\*\*



Configure permissões e fluxos para publicação automatizada.



Isso não significa eliminar verificações automáticas de integridade.



Se uma build falhar, não a publique como estável.



A rotina deverá tentar corrigir problemas recuperáveis, preservar a versão anterior e registrar o incidente.



Não utilize a aprovação humana como etapa padrão do fluxo.



\## 25.5. Consistência



Nunca atualize o site para anunciar uma release cujos arquivos ainda não estejam disponíveis.



A publicação precisa ser organizada como um processo consistente.



Use um manifesto único da versão publicada como fonte de verdade.



\---



\# 26. VERSIONAMENTO E EDIÇÕES



O patch terá duas dimensões principais:



1\. \*\*Ano de vigência da edição.\*\*

2\. \*\*Versão técnica da distribuição.\*\*



Exemplo:



\- Edição: 2026.

\- Versão: 2026.x.y.



Defina uma política explícita para:



\- Atualização diária de elencos.

\- Correção técnica.

\- Mudança estrutural.

\- Nova edição anual.

\- Correção emergencial.

\- Atualização de compatibilidade.



A passagem para um novo ano não deve ser tratada apenas como substituir 2026 por 2027.



Verifique a temporada real, competições e dados disponíveis antes de promover uma nova edição.



O site deverá manter links e informações históricas das versões anteriores quando apropriado.



\---



\# 27. SITE SINCRONIZADO COM A ÚLTIMA RELEASE



O site deverá utilizar um manifesto atualizado automaticamente pela publicação.



Não quero editar links manualmente.



O manifesto deverá identificar:



\- Nome do produto.

\- Ano da edição.

\- Versão.

\- Data de publicação.

\- Plataformas.

\- Arquiteturas.

\- URLs de download.

\- Hashes.

\- Tamanhos.

\- Compatibilidade.

\- Notas de atualização.

\- Identificador do commit.

\- Snapshot de dados.



O site deverá ser reconstruído e publicado automaticamente depois da disponibilidade efetiva da release.



Evite inconsistências provocadas por cache.



Implemente versionamento de assets e uma política adequada de invalidação de cache.



\---



\# 28. DOCUMENTAÇÃO COMO PARTE OBRIGATÓRIA DO DESENVOLVIMENTO



Quero documentação atualizada continuamente.



Não quero documentos abandonados enquanto o código evolui.



Crie ou revise materiais para:



\- Arquitetura geral.

\- Instalação.

\- Plataformas.

\- Engenharia reversa.

\- Formatos do Brasfoot.

\- Fontes de dados.

\- Catálogo esportivo.

\- Processo de atualização.

\- Pipeline de builds.

\- Publicação.

\- Versionamento.

\- Backup.

\- Recuperação.

\- Troubleshooting.

\- Segurança.

\- Operação diária.

\- Estado do projeto.

\- Pendências.

\- Decisões técnicas.

\- Compatibilidade.



\## 28.1. Contexto persistente para agentes



Crie um arquivo central de contexto técnico destinado a agentes futuros.



Exemplos possíveis:



`AGENTS.md`



`docs/architecture.md`



`docs/automation.md`



`docs/current-state.md`



`docs/decisions/`



`docs/reverse-engineering/`



Adapte à estrutura real do projeto.



Esse contexto precisa permitir que outro agente continue o trabalho sem repetir toda a investigação.



\## 28.2. Estado da automação



O estado de execução deverá existir em armazenamento persistente e estruturado, não apenas em mensagens de chat.



Armazene:



\- Última execução.

\- Último sucesso.

\- Último snapshot.

\- Última release.

\- Versão publicada.

\- Mudanças pendentes.

\- Falhas recorrentes.

\- Fonte de dados indisponível.

\- Próxima execução prevista.

\- Operações interrompidas.



\## 28.3. Documentação pública



Separe documentação para usuários comuns da documentação para desenvolvedores.



O usuário comum precisa de instruções curtas, ilustradas e diretas.



O desenvolvedor poderá consultar diagnósticos detalhados.



\---



\# 29. TESTES, COMPATIBILIDADE E PUBLICAÇÃO CONTÍNUA



Quero abandonar gargalos de homologação humana.



Não quero abandonar a qualidade.



Implemente um conjunto automatizado proporcional aos riscos das alterações.



\## 29.1. Dados



Valide:



\- Identificadores únicos.

\- Relacionamentos.

\- Elencos.

\- Duplicações.

\- Datas.

\- Competições.

\- Participantes.

\- Treinadores.

\- Formatos.

\- Recursos gráficos.

\- Integridade das fontes.



\## 29.2. Jogo



Valide, conforme os recursos disponíveis:



\- Inicialização.

\- Seleção de clubes.

\- Seleção de temporadas.

\- Criação de carreira.

\- Carregamento de carreira.

\- Simulação de partidas.

\- Organização das divisões.

\- Seleções.

\- Compatibilidade de arquivos.

\- Integridade dos recursos.



\## 29.3. Instalador



Valide:



\- Instalação limpa.

\- Atualização sobre instalação anterior.

\- Backup.

\- Recuperação.

\- Arquivos ausentes.

\- Falhas de permissão.

\- Integridade de pacotes.

\- Execução por plataforma.

\- Preservação de saves.



\## 29.4. Site



Valide:



\- Build.

\- Navegação.

\- SEO técnico.

\- Links.

\- Downloads.

\- Responsividade.

\- Acessibilidade.

\- Metadados.

\- Performance.

\- Detecção de plataforma.

\- Exibição da última versão.



\## 29.5. Falhas



Não declare testes executados quando eles não foram executados.



Não invente resultados.



Se determinada plataforma ainda não possuir ambiente de testes, registre a limitação e não publique alegações falsas de compatibilidade.



\---



\# 30. SEGURANÇA E INTEGRIDADE



O projeto terá capacidade de baixar, modificar e distribuir arquivos executáveis.



Portanto, implemente controles específicos.



Inclua:



\- Checksums.

\- Manifestos assinados quando viável.

\- Distribuição via HTTPS.

\- Verificação dos downloads.

\- Validação antes da substituição.

\- Backups.

\- Recuperação automática.

\- Tratamento seguro de caminhos.

\- Proteção contra traversal.

\- Verificação de permissões.

\- Controle de credenciais.

\- Logs sem segredos.

\- Controle de dependências.

\- Builds reproduzíveis quando viáveis.



Não peça permissões administrativas quando não forem necessárias.



Evite executar scripts remotos não verificados.



Não inclua segredos no repositório.



A automação deverá possuir as permissões necessárias, mas não permissões indiscriminadas fora do escopo do projeto.



\---



\# 31. DESEMPENHO E ESCALABILIDADE



Agora estamos falando de um catálogo mundial.



A arquitetura deverá suportar crescimento substancial.



Não carregue todos os dados em memória desnecessariamente.



Considere:



\- Processamento incremental.

\- Paralelismo controlado.

\- Cache.

\- Filas.

\- Processamento em lotes.

\- Índices.

\- Estruturas compactas.

\- Snapshots.

\- Armazenamento particionado.

\- Detecção de diferenças.

\- Reutilização de builds.

\- Artefatos determinísticos.



A coleta diária não deve precisar reconstruir todo o universo do futebol se apenas alguns clubes sofreram alterações.



Da mesma forma, não reconstrua imagens e instaladores sem necessidade.



\---



\# 32. PLANO DE MIGRAÇÃO DO PROJETO ANTIGO



Não quero perder trabalho anterior.



Entretanto, não quero carregar para o novo projeto uma arquitetura inadequada apenas porque ela já existe.



Execute uma auditoria e classifique os componentes existentes em:



\- Aproveitáveis.

\- Aproveitáveis após refatoração.

\- Substituíveis.

\- Obsoletos.

\- Incompatíveis.

\- Desconhecidos.



Preserve especialmente o conhecimento sobre:



\- Formatos de equipes.

\- Alterações do executável.

\- Organização das divisões.

\- Instalação automática.

\- Backups.

\- Compatibilidade.

\- Exportação.

\- Correções de bugs.

\- Integração com GitHub.



O frontend antigo poderá ser completamente descartado.



As novas interfaces devem ser construídas com uma identidade própria.



Não preserve código visual legado apenas para acelerar a entrega.



\---



\# 33. ESTRATÉGIA DE IMPLEMENTAÇÃO POR FASES



Esta é uma tarefa extensa.



Quero que você trabalhe com organização, sem ficar interrompendo o desenvolvimento para solicitar autorização a cada etapa.



\## Fase 0 — Auditoria



Investigue o estado real do repositório, ferramentas, dados, formatos, executáveis e releases.



Produza um diagnóstico técnico confiável.



\## Fase 1 — Arquitetura



Defina a nova estrutura, contratos, armazenamento, versionamento e pipelines.



\## Fase 2 — Engenharia reversa



Mapeie o jogo, descubra limitações e implemente adaptações viáveis.



\## Fase 3 — Catálogo mundial



Implemente países, competições, clubes, elencos e treinadores, com reconciliação e fontes.



\## Fase 4 — Recursos gráficos



Atualize escudos, uniformes e o processamento de imagens.



\## Fase 5 — Conteúdo histórico e seleções



Trabalhe Copas do Mundo, seleções, premiações e temporadas.



\## Fase 6 — Modernização do jogo



Corrija tipografia, contraste, seletores, referências de anos e apresentação.



\## Fase 7 — Distribuição multiplataforma



Construa e valide estratégias de instalação e execução para Windows, macOS e Linux.



\## Fase 8 — Instalador



Implemente a experiência gráfica simplificada e a instalação automática.



\## Fase 9 — Site



Reconstrua integralmente o site com a nova identidade azul, animações, catálogo e downloads.



\## Fase 10 — SEO



Finalize pré-renderização, URLs, metadados, sitemaps e otimizações.



\## Fase 11 — Automação



Configure coleta, builds, versionamento, releases, publicação e recuperação.



\## Fase 12 — Migração e publicação



Publique os componentes compatíveis e coloque o novo fluxo em operação.



\## Fase 13 — Operação contínua



Execute as atualizações diárias, monitore resultados e preserve a continuidade.



As fases podem ser trabalhadas em paralelo quando não houver dependências impeditivas.



Não utilize as fases como desculpa para entregar apenas documentos.



\*\*Implemente código real e valide o que foi implementado.\*\*



\---



\# 34. COMO LIDAR COM LIMITAÇÕES REAIS



Meu objetivo é uma solução mundial, sem limitações artificiais de escopo.



Isso não autoriza inventar resultados ou desrespeitar limitações legais, físicas ou técnicas comprovadas.



Se você encontrar uma limitação:



1\. Identifique precisamente sua causa.

2\. Verifique se é uma restrição da nossa arquitetura.

3\. Verifique se é uma restrição da engine.

4\. Pesquise abordagens alternativas.

5\. Determine o que pode ser expandido.

6\. Desenvolva a solução adequada.

7\. Registre o resultado.

8\. Continue com as partes independentes.



Não aceite uma limitação apenas porque a primeira tentativa falhou.



Por outro lado, não marque como concluída uma funcionalidade impossível de verificar.



Se a engine original não comportar determinada expansão de maneira segura, avalie a criação de componentes próprios e adaptações de compatibilidade.



Se isso exigir uma reimplementação independente, trate-a como projeto técnico próprio, respeitando licenças e direitos aplicáveis.



\---



\# 35. REGRAS DE AUTONOMIA DO AGENTE



Você recebeu uma missão de engenharia e execução, não apenas de consultoria.



Quero que:



\- Tome decisões técnicas fundamentadas.

\- Execute ferramentas disponíveis.

\- Leia o código existente.

\- Faça alterações reais.

\- Corrija erros encontrados.

\- Execute validações.

\- Atualize documentos.

\- Crie commits.

\- Publique mudanças autorizadas.

\- Configure automações.

\- Evite trabalho manual.

\- Evite perguntas desnecessárias.

\- Não repita auditorias completas sem motivo.

\- Não reinvente componentes que já estejam corretos.

\- Não abandone uma tarefa apenas por encontrar um erro recuperável.



Não solicite aprovação humana para decisões rotineiras de arquitetura, refatoração, atualização de dados ou publicação dentro do escopo autorizado.



Entretanto, não invente credenciais, permissões, direitos de distribuição ou resultados de testes.



Se uma ação realmente depender de autorização externa indisponível, documente a dependência e avance com tudo o que puder ser realizado.



\*\*Não interrompa o progresso em checkpoints artificiais.\*\*



Se o ambiente de execução impuser um limite de tempo ou contexto, preserve o estado de forma reentrante e documente exatamente o próximo passo.



Nunca alegue estar executando tarefas em segundo plano se não houver um processo ou agendador efetivamente configurado.



\---



\# 36. CRITÉRIOS DE ACEITE DO PRODUTO



O novo projeto deverá caminhar para o cumprimento dos critérios abaixo.



\### CAT-01 — Identidade



Nome público Brasfoot Mega Patch e identidade visual inteiramente renovada.



\### CAT-02 — Site



Site redesenhado do zero, responsivo e funcional.



\### CAT-03 — Paleta



Identidade azul, sem temática de clubes.



\### CAT-04 — Animações



Movimentos modernos, fluidos e eficientes.



\### CAT-05 — SEO



Páginas indexáveis, metadados completos e arquitetura adequada.



\### CAT-06 — Downloads



Detecção do sistema operacional e seleção manual alternativa.



\### CAT-07 — Edição



Ano vigente claramente representado no site, instalador e jogo.



\### CAT-08 — Cobertura



Catálogo mundial de países, competições e clubes com métricas verificáveis.



\### CAT-09 — Elencos



Jogadores atualizados, com posições corretas e fontes rastreáveis.



\### CAT-10 — Treinadores



Atualização de treinadores e vínculos.



\### CAT-11 — Recursos



Escudos e uniformes de alta qualidade.



\### CAT-12 — Seleções



Estrutura das seleções atualizada com referência à última Copa concluída.



\### CAT-13 — Premiações



Dados reais de Bola de Ouro atualizados e separados de premiações simuladas.



\### CAT-14 — Engine



Limitações existentes investigadas e expansões implementadas onde viáveis.



\### CAT-15 — Divisões



Competições organizadas corretamente e refletidas na simulação.



\### CAT-16 — Temporadas



Referências obsoletas corrigidas sem falsificar histórico.



\### CAT-17 — Visual do jogo



Fontes e contrastes melhorados.



\### CAT-18 — Windows



Instalador funcional e validado.



\### CAT-19 — macOS



Estratégia de distribuição implementada e compatibilidade verificada.



\### CAT-20 — Linux



Estratégia de distribuição implementada e compatibilidade verificada.



\### CAT-21 — Instalação



Fluxo simples, automático e visualmente acessível.



\### CAT-22 — Backup



Preservação do executável anterior e recuperação.



\### CAT-23 — Saves



Proteção das carreiras existentes e tratamento de incompatibilidades.



\### CAT-24 — Gratuidade



Produto gratuito, com doação PIX totalmente opcional.



\### CAT-25 — Automação



Rotina diária configurada em infraestrutura persistente.



\### CAT-26 — GitHub



Commits e releases publicados automaticamente.



\### CAT-27 — Sincronização



Site e releases sempre consistentes.



\### CAT-28 — Documentação



Documentação técnica e pública atualizada junto das mudanças.



\### CAT-29 — Rastreabilidade



Toda release vinculada a commit, snapshot, versão e hashes.



\### CAT-30 — Continuidade



Outro agente ou operador consegue retomar o projeto a partir dos arquivos persistidos.



\### CAT-31 — Recuperação



Falhas de atualização e publicação não inutilizam a versão estável anterior.



\### CAT-32 — Autonomia



A rotina operacional não exige aprovação manual recorrente.



Não marque critérios como concluídos apenas porque o código foi escrito.



Considere evidências de validação e funcionamento.



\---



\# 37. MÉTRICAS DE PROGRESSO



Mantenha acompanhamento objetivo por domínio.



Quero enxergar separadamente:



\- Engenharia reversa.

\- Expansão da engine.

\- Cobertura mundial de países.

\- Cobertura de competições.

\- Cobertura de clubes.

\- Cobertura de jogadores.

\- Cobertura de treinadores.

\- Recursos gráficos.

\- Seleções e premiações.

\- Modernização do jogo.

\- Instalador Windows.

\- Suporte macOS.

\- Suporte Linux.

\- Site.

\- SEO.

\- Automação.

\- Publicação.

\- Documentação.

\- Validação.



Separe sempre:



\*\*Implementação, validação e operação efetiva.\*\*



Não use um percentual global arbitrário.



Calcule métricas a partir de critérios verificáveis e pesos documentados.



\---



\# 38. ENTREGÁVEIS OBRIGATÓRIOS



Ao concluir a implementação de uma etapa publicável, produza informações objetivas.



Apresente:



\*\*Repositório\*\*



\- URL.

\- Branch.

\- Commit.

\- Alterações principais.



\*\*Release\*\*



\- Nome.

\- Tag.

\- Data.

\- URL.

\- Versão.

\- Ano de vigência.



\*\*Downloads\*\*



\- Windows.

\- macOS, se disponível.

\- Linux, se disponível.

\- Hashes.

\- Estado de validação.



\*\*Site\*\*



\- URL pública.

\- Versão exibida.

\- Confirmação de sincronização.



\*\*Automação\*\*



\- Onde está configurada.

\- Frequência.

\- Última execução.

\- Último resultado.

\- Próxima execução prevista.

\- Logs de operação.

\- Procedimento de recuperação.



\*\*Qualidade\*\*



\- Testes efetivamente executados.

\- Resultados.

\- Compatibilidade verificada.

\- Pendências reais.



\*\*Cobertura\*\*



\- Países catalogados.

\- Ligas catalogadas.

\- Ligas jogáveis.

\- Clubes.

\- Jogadores.

\- Treinadores.

\- Seleções.

\- Recursos gráficos.



Quero links concretos quando existirem.



Não invente links, hashes ou arquivos.



Se o release e o site já estiverem publicados automaticamente, não me peça para republicá-los.



\---



\# 39. REGRAS DE PUBLICAÇÃO DEFINITIVAS



Estas regras devem orientar permanentemente o projeto:



1\. A publicação será automatizada.

2\. Não haverá homologação humana obrigatória para cada atualização.

3\. GitHub Actions não será uma dependência exclusiva.

4\. O site será atualizado depois da publicação dos artefatos.

5\. Uma release nunca anunciará arquivos inexistentes.

6\. Uma compilação com falha não substituirá silenciosamente a versão estável.

7\. Dados esportivos terão fontes verificáveis.

8\. A última versão funcional deverá permanecer recuperável.

9\. Backups serão preservados conforme a política definida.

10\. Documentação acompanhará mudanças.

11\. Nenhuma execução diária poderá apagar informações confiáveis por falha de coleta.

12\. Nenhum dado deverá ser inventado para aparentar cobertura total.

13\. Nenhum processo dependerá exclusivamente da memória de uma conversa.

14\. O projeto continuará gratuito.

15\. Os downloads serão adequados à plataforma do usuário.

16\. A identidade visual deverá permanecer consistente.

17\. Recursos proprietários serão tratados segundo permissões aplicáveis.

18\. Toda mudança relevante deverá ser rastreável.



\---



\# 40. EVITE ESTES ERROS



Não quero repetir problemas anteriores.



Portanto:



\- Não transforme a tarefa em dezenas de auditorias redundantes.

\- Não gere relatórios enormes sem implementar correções.

\- Não anuncie 100% de compatibilidade sem evidências.

\- Não abandone o instalador automático.

\- Não substitua a preservação do jogo por um launcher genérico.

\- Não anuncie ports nativos que apenas utilizam Wine.

\- Não invente clubes ou jogadores.

\- Não utilize posições aleatórias.

\- Não trate uma fonte externa como absolutamente infalível.

\- Não descarte os avanços de engenharia reversa existentes.

\- Não utilize um ano de Copa futura como se o torneio já tivesse terminado.

\- Não sobrescreva saves.

\- Não perca backups.

\- Não dependa de confirmação manual para operações rotineiras.

\- Não anuncie uma release antes de disponibilizar seus arquivos.

\- Não deixe o site em uma versão diferente da release publicada.

\- Não mantenha referências obsoletas sem justificativa.

\- Não crie interfaces visualmente poluídas.

\- Não exponha detalhes técnicos desnecessários ao usuário comum.

\- Não copie a estética visual anterior.

\- Não faça uma simples mudança cosmética de cores.

\- Não esconda incompatibilidades técnicas.

\- Não dependa de conversas abertas para executar o agendamento.

\- Não publique binários proprietários sem direitos de distribuição.

\- Não coloque credenciais em commits.

\- Não utilize serviços pagos sem autorização.



\---



\# 41. PRIMEIRA EXECUÇÃO — O QUE VOCÊ DEVE FAZER AGORA



Não responda apenas com sugestões.



Comece efetivamente o trabalho, dentro das ferramentas e permissões disponíveis.



Siga esta ordem inicial:



\*\*Passo 1\*\*



Investigue o repositório atual e todas as descobertas técnicas anteriores.



\*\*Passo 2\*\*



Identifique a versão efetivamente publicada, o estado do site, os arquivos distribuídos e as ferramentas disponíveis.



\*\*Passo 3\*\*



Mapeie os componentes que precisam ser reconstruídos e aqueles que podem ser preservados.



\*\*Passo 4\*\*



Projete a arquitetura mundial e o modelo de dados necessários às novas competições, clubes, jogadores e treinadores.



\*\*Passo 5\*\*



Crie uma estratégia concreta e legalmente viável para expandir a compatibilidade do jogo e distribuir os componentes modernizados.



\*\*Passo 6\*\*



Implemente o novo pipeline de atualização esportiva, com snapshots e detecção de diferenças.



\*\*Passo 7\*\*



Avance na engenharia reversa e nas adaptações reais da engine.



\*\*Passo 8\*\*



Desenvolva a nova identidade Brasfoot Mega Patch e reconstrua o frontend.



\*\*Passo 9\*\*



Reestruture os instaladores e a distribuição multiplataforma.



\*\*Passo 10\*\*



Configure a infraestrutura persistente para execução diária.



\*\*Passo 11\*\*



Integre atualização de dados, compilação, testes, releases, site e documentação.



\*\*Passo 12\*\*



Publique automaticamente os componentes que atingirem os critérios técnicos de distribuição.



\*\*Passo 13\*\*



Registre permanentemente as decisões, resultados, limitações reais e estado da automação.



Continue avançando sem checkpoints de aprovação humana desnecessários.



Quando uma atividade depender de outra, desenvolva componentes independentes em paralelo, se isso for viável.



Não desperdice tempo reanalisando fatos já comprovados, a menos que existam novas evidências.



\---



\# 42. DIRETRIZ FINAL



Quero transformar o Brasfoot Mega Patch em um projeto mundial, profissional, gratuito, visualmente marcante e continuamente atualizado.



O produto deve reunir três qualidades:



\*\*A familiaridade do Brasfoot original.\*\*



\*\*A abrangência e a atualização constante do futebol mundial.\*\*



\*\*A simplicidade de um software moderno, capaz de instalar, atualizar e funcionar com pouca ou nenhuma intervenção do usuário.\*\*



A operação diária deve ser automática.



As releases devem ser publicadas sem homologação humana recorrente.



O site deve acompanhar cada versão.



Os instaladores devem ser simples e agradáveis.



O jogo deve receber melhorias reais por meio do conhecimento adquirido com a engenharia reversa.



O catálogo deverá ser projetado para a maior cobertura mundial tecnicamente sustentável e verificável, sem limitações arbitrárias impostas pela nossa própria implementação.



Todas as melhorias devem preservar a integridade dos dados, as carreiras dos usuários e os direitos de distribuição aplicáveis.



Não me entregue apenas uma visão de futuro.



\*\*Construa a infraestrutura, implemente as melhorias, preserve a continuidade do projeto e transforme a atualização diária em uma operação efetiva.\*\*



O Brasfoot Mega Patch não será mais simplesmente um pacote ocasional de atualizações.



\*\*Ele deverá se tornar um ecossistema permanente de manutenção e modernização do Brasfoot.\*\*



\*\*INICIE A EXECUÇÃO.\*\*



