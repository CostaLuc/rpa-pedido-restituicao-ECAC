# Sistema de Login com Excel

Este é um sistema de login simples que utiliza um arquivo Excel como banco de dados.

## Configuração

1. Certifique-se de que o arquivo `users.xlsx` está na raiz do projeto
2. O arquivo deve ter as colunas: ID, user, password
3. O usuário padrão é:
   - **Usuário**: lucas.costa
   - **Senha**: admin

## Executando o sistema

1. Instale as dependências: `pip install flask pandas openpyxl`
2. Execute o arquivo `login.py`: `python login.py`
3. Acesse `http://localhost:5000` no navegador
4. Faça login com as credenciais acima

## Estrutura de arquivos

- `login.py` - Script principal do sistema
- `users.xlsx` - Banco de dados de usuários
- `styles/templates/login.html` - Template HTML da página de login
- `styles/css/login.css` - Estilos CSS da página de login
