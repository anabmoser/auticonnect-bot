# README.md - AutiConnect Bot com Mediadores de IA

## Visão Geral

AutiConnect Bot é um bot do Telegram projetado para facilitar a interação entre pessoas autistas, com mediação de agentes de IA disponíveis 24/7 e supervisão de Auxiliares Terapêuticos (AT). O bot oferece um ambiente digital estruturado e previsível onde pessoas com Transtorno do Espectro Autista (TEA) podem participar de grupos temáticos e atividades estruturadas.

## Funcionalidades

- **Registro de usuários**: Diferenciação entre pessoas autistas e Auxiliares Terapêuticos (ATs)
- **Perfil detalhado**: Armazenamento de informações como idade, gênero, interesses, gatilhos de ansiedade e preferências de comunicação
- **Grupos temáticos**: Criação e participação em grupos organizados por temas de interesse
- **Atividades estruturadas**: Discussões temáticas, projetos colaborativos, jogos sociais
- **Mediação por IA**: Agentes de IA disponíveis 24/7 para facilitar interações e oferecer suporte
- **Suporte individual**: Conversas privadas com agentes de IA para regulação emocional
- **Sistema de alertas**: Detecção de situações que requerem intervenção profissional
- **Supervisão humana**: ATs recebem alertas e podem intervir quando necessário

## Comandos do Bot

- `/start` - Iniciar o bot e criar perfil de usuário
- `/grupos` - Listar grupos temáticos disponíveis
- `/atividades` - Ver atividades programadas
- `/perfil` - Atualizar informações do perfil
- `/criar_grupo` - (Apenas ATs) Criar um novo grupo temático
- `/iniciar_atividade` - (Apenas ATs) Iniciar uma atividade estruturada
- `/ajuda` - Mostrar informações de ajuda
- `/cancel` - Cancelar operação atual

## Requisitos Técnicos

- Python 3.7+
- python-telegram-bot (versão 13+)
- MongoDB
- python-dotenv
- Acesso à API do OpenAI (GPT-4)

## Estrutura do Projeto

- `main.py` - Arquivo principal do bot
- `db.py` - Módulo para interação com o banco de dados
- `llm_integration.py` - Módulo para integração com LLMs
- `prompt_templates.json` - Templates de prompts para diferentes cenários
- `requirements.txt` - Dependências do projeto
- `Procfile` - Configuração para deployment
- `.env.example` - Exemplo de arquivo de variáveis de ambiente

## Configuração

1. Renomeie o arquivo `.env.example` para `.env`
2. Preencha as variáveis de ambiente:
   - `BOT_TOKEN`: Token do seu bot do Telegram (obtido via BotFather)
   - `MONGO_URI`: URI de conexão do MongoDB
   - `LLM_API_KEY`: Chave de API do OpenAI
   - `LLM_API_ENDPOINT`: Endpoint da API (padrão: https://api.openai.com/v1/chat/completions)
   - `LLM_MODEL`: Modelo a ser usado (padrão: gpt-4)
   - `ALERT_THRESHOLD`: Limiar para alertas profissionais (0-100, padrão: 70)

## Mediadores de IA

### Funcionalidades dos Mediadores

1. **Facilitação de Conversas em Grupo**
   - Intervém durante silêncios prolongados
   - Garante que todos os participantes sejam incluídos
   - Sugere tópicos baseados nos interesses dos participantes
   - Mantém a conversa animada e engajadora

2. **Suporte Individual**
   - Oferece conversas privadas para regulação emocional
   - Detecta sinais de ansiedade ou desconforto
   - Fornece estratégias de adaptação personalizadas
   - Ajuda na reintegração ao grupo quando apropriado

3. **Orientação de Atividades**
   - Estrutura atividades com instruções claras
   - Gerencia turnos de participação
   - Mantém o foco no objetivo da atividade
   - Oferece elogios específicos por contribuições

4. **Sistema de Alertas**
   - Monitora níveis de tensão nas conversas
   - Detecta potenciais conflitos ou mal-entendidos
   - Alerta ATs quando intervenção profissional é necessária
   - Fornece contexto para que o AT possa intervir efetivamente

### Personalização

Os mediadores de IA utilizam informações detalhadas do perfil do usuário para personalizar as interações:
- Idade e gênero
- Interesses especiais
- Gatilhos conhecidos de ansiedade
- Preferências de comunicação (direta vs. detalhada)
- Histórico acadêmico e profissionais
- Contatos de emergência

## Como Implantar no Railway

Railway é uma plataforma que facilita o deployment de aplicações sem necessidade de usar terminal ou linha de comando. Siga estes passos para implantar o AutiConnect Bot:

1. **Crie uma conta no Railway**:
   - Acesse [railway.app](https://railway.app/)
   - Registre-se usando sua conta GitHub ou e-mail

2. **Crie um novo projeto**:
   - Clique no botão "New Project" no dashboard
   - Selecione "Deploy from GitHub repo"
   - Conecte sua conta GitHub se ainda não estiver conectada
   - Selecione o repositório onde você armazenou o código do AutiConnect Bot

3. **Configure as variáveis de ambiente**:
   - No projeto criado, clique na aba "Variables"
   - Adicione todas as variáveis listadas no arquivo `.env.example`:
     - `BOT_TOKEN`: Cole o token do seu bot do Telegram
     - `MONGO_URI`: Cole a URI de conexão do MongoDB
     - `LLM_API_KEY`: Cole sua chave de API do OpenAI
     - `LLM_API_ENDPOINT`: Use o valor padrão ou seu endpoint personalizado
     - `LLM_MODEL`: Use "gpt-4" (recomendado) ou outro modelo compatível
     - `ALERT_THRESHOLD`: Defina um valor entre 0-100 (recomendado: 70)

4. **Configure o banco de dados MongoDB**:
   - No Railway, clique em "New" e selecione "Database" > "MongoDB"
   - Após a criação, vá para a aba "Connect" e copie a "MongoDB Connection URL"
   - Use esta URL como valor para a variável `MONGO_URI`

5. **Verifique o deployment**:
   - Railway detectará automaticamente o Procfile e iniciará o bot
   - Vá para a aba "Deployments" para verificar se o bot está rodando
   - Se tudo estiver correto, você verá um status "Success"

6. **Teste o bot**:
   - Abra o Telegram e procure pelo seu bot (usando o nome que você definiu no BotFather)
   - Envie o comando `/start` para verificar se o bot está funcionando

## Como Implantar no Replit (Alternativa)

Replit é outra plataforma amigável para iniciantes que permite hospedar o bot sem usar terminal:

1. **Crie uma conta no Replit**:
   - Acesse [replit.com](https://replit.com/)
   - Registre-se usando sua conta Google, GitHub ou e-mail

2. **Crie um novo repl**:
   - Clique em "+ Create Repl"
   - Selecione "Python" como template
   - Dê um nome ao seu projeto e clique em "Create Repl"

3. **Configure o projeto**:
   - No painel esquerdo, clique no ícone de arquivos
   - Faça upload de todos os arquivos do projeto ou crie-os manualmente
   - Certifique-se de incluir `main.py`, `db.py`, `llm_integration.py`, `prompt_templates.json`, `requirements.txt` e `Procfile`

4. **Configure as variáveis de ambiente**:
   - No painel esquerdo, clique no ícone de cadeado (Secrets)
   - Adicione todas as variáveis listadas no arquivo `.env.example`

5. **Execute o bot**:
   - Clique no botão "Run" no topo da página
   - O Replit instalará automaticamente as dependências e iniciará o bot
   - Você verá a saída do console indicando que o bot está rodando

6. **Mantenha o bot ativo**:
   - Para manter o bot rodando 24/7, você precisará de um plano pago do Replit
   - Alternativamente, você pode usar um serviço de "pinging" como UptimeRobot para manter o repl ativo

## Custos e Considerações

### API do OpenAI
- A integração com GPT-4 requer uma conta na OpenAI com créditos disponíveis
- Os custos variam de acordo com o uso, mas considere aproximadamente:
  - $0.03 por 1K tokens de entrada
  - $0.06 por 1K tokens de saída
  - Um grupo ativo pode gerar custos de $5-20 por mês, dependendo do volume de interações

### Hospedagem
- Railway oferece um plano gratuito com limitações
- Para uso contínuo, considere o plano starter ($5-10/mês)
- Replit também oferece planos pagos para manter aplicações rodando 24/7

## Próximos Passos e Evolução

1. **Testes com Usuários Reais**
   - Comece com um grupo pequeno de usuários autistas e ATs
   - Colete feedback sobre a eficácia dos mediadores de IA
   - Ajuste os prompts e configurações com base no feedback

2. **Expansão de Funcionalidades**
   - Implementação de notificações para atividades programadas
   - Recursos avançados de acessibilidade
   - Ferramentas de análise para ATs monitorarem progresso

3. **Evolução para Solução SaaS**
   - Desenvolvimento de interface web personalizada
   - Integração com outros serviços de mensagens
   - Recursos avançados de personalização

## Notas Importantes

- Este é um MVP (Produto Mínimo Viável) com mediadores de IA
- Em uma implementação completa, o bot seria integrado a grupos reais do Telegram
- Certifique-se de proteger suas credenciais e nunca compartilhar seu arquivo .env
- Os mediadores de IA são supervisionados por ATs humanos para garantir segurança
- Para suporte ou dúvidas, entre em contato com a equipe do AutiConnect
