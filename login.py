from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
import pandas as pd
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, 
            static_folder='styles', 
            template_folder='styles/templates')

# Caminho para o arquivo Excel
EXCEL_PATH = 'db/users.xlsx'
# Diretório para os grupos de empresas
GROUPS_DIR = 'db/groups'

def check_credentials(username, password, excel_path='db/users.xlsx'):
    """Verifica as credenciais do usuário no arquivo Excel."""
    try:
        # Carrega o arquivo Excel
        df = pd.read_excel(excel_path)
        
        # Procura o usuário
        user_row = df[df['user'] == username]
        
        if user_row.empty:
            return False, "Usuário não encontrado"
        
        # Verifica a senha
        stored_password = user_row['password'].values[0]
        if password == stored_password:  # Em produção, use hash de senha
            return True, user_row['id'].values[0]
        else:
            return False, "Senha incorreta"
            
    except Exception as e:
        print(f"Erro ao verificar credenciais: {str(e)}")
        return False, f"Erro ao processar login: {str(e)}"

def create_default_user(excel_path='db/users.xlsx'):
    """Cria um usuário padrão se o arquivo de usuários não existir."""
    if not os.path.exists(excel_path):
        print(f"AVISO: Arquivo {excel_path} não encontrado!")
        print("Criando diretório 'db' se não existir...")
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)
        
        # Cria um arquivo de exemplo com usuário e senha
        df = pd.DataFrame({
            'id': [1],
            'user': ['lucas.costa'],
            'password': ['admin']
        })
        df.to_excel(excel_path, index=False)
        print(f"Arquivo {excel_path} criado com usuário padrão: lucas.costa / admin")
        return True
    return False

def get_available_groups():
    """Retorna a lista de grupos disponíveis."""
    try:
        if not os.path.exists(GROUPS_DIR):
            os.makedirs(GROUPS_DIR)
            print(f"Diretório {GROUPS_DIR} criado.")
            
        groups = [f for f in os.listdir(GROUPS_DIR) 
                 if os.path.isdir(os.path.join(GROUPS_DIR, f))]
            
        return groups
    except Exception as e:
        print(f"Erro ao obter grupos: {str(e)}")
        return []

def get_group_counts():
    """Obtém a contagem de empresas por grupo."""
    counts = {}
    for group in get_available_groups():
        try:
            excel_path = os.path.join(GROUPS_DIR, group, f"{group}.xlsx")
            if os.path.exists(excel_path):
                df = pd.read_excel(excel_path)
                counts[group] = len(df)
            else:
                counts[group] = 0
                print(f"Aviso: Arquivo {excel_path} não encontrado para o grupo {group}")
                    
        except Exception as e:
            print(f"Erro ao contar empresas do grupo {group}: {str(e)}")
            counts[group] = 0
    return counts

def get_group_companies(group):
    """Retorna as empresas de um grupo específico."""
    try:
        excel_path = os.path.join(GROUPS_DIR, group, f"{group}.xlsx")
        if os.path.exists(excel_path):
            df = pd.read_excel(excel_path)
            return df.to_dict('records')
        else:
            print(f"Aviso: Arquivo {excel_path} não encontrado")
            return []
    except Exception as e:
        print(f"Erro ao obter empresas do grupo {group}: {str(e)}")
        return []

def get_group_info(group):
    """Obtém informações consolidadas do grupo."""
    try:
        # Obter número de empresas
        excel_path = os.path.join(GROUPS_DIR, group, f"{group}.xlsx")
        if not os.path.exists(excel_path):
            print(f"Aviso: Arquivo {excel_path} não encontrado")
            return {
                'company_count': 0,
                'processed_count': 0,
                'pending_count': 0
            }
            
        df = pd.read_excel(excel_path)
        company_count = len(df)
        
        # Em uma implementação real, aqui você contaria os processos
        # concluídos e pendentes de um banco de dados ou arquivo de log
        # Por enquanto, vamos usar valores fictícios
        processed_count = 0
        pending_count = 0
        
        # Verificar se existe um arquivo de log para esse grupo
        log_path = os.path.join(GROUPS_DIR, group, 'logs.xlsx')
        if os.path.exists(log_path):
            try:
                log_df = pd.read_excel(log_path)
                processed_count = len(log_df[log_df['status'] == 'concluído'])
                pending_count = len(log_df[log_df['status'] == 'pendente'])
            except Exception as e:
                print(f"Erro ao ler arquivo de logs: {str(e)}")
        
        return {
            'company_count': company_count,
            'processed_count': processed_count,
            'pending_count': pending_count
        }
    except Exception as e:
        print(f"Erro ao obter informações do grupo {group}: {str(e)}")
        return {
            'company_count': 0,
            'processed_count': 0,
            'pending_count': 0
        }

@app.route('/')
def index():
    """Redireciona para a página de login."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Gerencia a página de login."""
    error = None
    success = None
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verifica as credenciais
        is_valid, result = check_credentials(username, password)
        
        if is_valid:
            # Credenciais válidas - configura a sessão
            session['logged_in'] = True
            session['user_id'] = int(result)
            session['username'] = username
            
            # Redireciona para a página principal após login
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Credenciais inválidas
            error = result
    
    return render_template('login.html', error=error, success=success)

@app.route('/dashboard')
def dashboard():
    """Página principal após login bem-sucedido."""
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        flash('Você precisa fazer login para acessar esta página', 'error')
        return redirect(url_for('login'))
    
    # Obtém o grupo selecionado (se houver)
    selected_group = request.args.get('group')
    
    # Se não houver grupo selecionado, mostrar página de seleção de grupo
    if not selected_group:
        available_groups = get_available_groups()
        group_counts = get_group_counts()
        
        # Coleta mensagens flash para exibição no template
        messages = []
        for category, message in get_flashed_messages(with_categories=True):
            messages.append((category, message))
        
        return render_template('main.html',
                               username=session.get('username', 'Usuário'),
                               messages=messages,
                               selected_group=None,
                               available_groups=available_groups,
                               group_counts=group_counts)
    
    # Se tiver um grupo selecionado, mostrar dashboard do grupo
    group_info = get_group_info(selected_group)
    
    # Coleta mensagens flash para exibição no template
    messages = []
    for category, message in get_flashed_messages(with_categories=True):
        messages.append((category, message))
    
    # Armazena o grupo selecionado na sessão
    session['selected_group'] = selected_group
    
    return render_template('main.html',
                           username=session.get('username', 'Usuário'),
                           messages=messages,
                           selected_group=selected_group,
                           group_info=group_info)

@app.route('/select_group')
def select_group():
    """Página para selecionar um grupo de empresas."""
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        flash('Você precisa fazer login para acessar esta página', 'error')
        return redirect(url_for('login'))
    
    available_groups = get_available_groups()
    group_counts = get_group_counts()
    
    # Coleta mensagens flash para exibição no template
    messages = []
    for category, message in get_flashed_messages(with_categories=True):
        messages.append((category, message))
    
    return render_template('select_group.html',
                           username=session.get('username', 'Usuário'),
                           messages=messages,
                           available_groups=available_groups,
                           group_counts=group_counts)

@app.route('/select_company')
def select_company():
    """Página para selecionar uma empresa de um grupo."""
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        flash('Você precisa fazer login para acessar esta página', 'error')
        return redirect(url_for('login'))
    
    # Obtém o grupo da URL ou da sessão
    group = request.args.get('group') or session.get('selected_group')
    if not group:
        flash('Nenhum grupo selecionado', 'error')
        return redirect(url_for('select_group'))
    
    # Obtém as empresas do grupo
    companies = get_group_companies(group)
    
    if not companies:
        flash(f'Nenhuma empresa encontrada para o grupo {group}. Verifique se o arquivo {group}.xlsx existe e está correto.', 'warning')
    
    # Coleta mensagens flash para exibição no template
    messages = []
    for category, message in get_flashed_messages(with_categories=True):
        messages.append((category, message))
    
    return render_template('select_company.html',
                           group=group,
                           companies=companies,
                           messages=messages)

@app.route('/start_process')
def start_process():
    """Inicia o processo de automação RPA para uma única empresa."""
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        flash('Você precisa fazer login para acessar esta página', 'error')
        return redirect(url_for('login'))
    
    # Obtém o grupo e o ID da empresa
    group = request.args.get('group')
    company_id = request.args.get('company_id')
    
    if not group:
        flash('Nenhum grupo selecionado', 'error')
        return redirect(url_for('select_group'))
    
    if not company_id:
        flash('É necessário selecionar uma empresa específica para iniciar o processo', 'warning')
        return redirect(url_for('select_company', group=group))
    
    # Encontra os detalhes da empresa
    companies = get_group_companies(group)
    
    # Primeiro tente encontrar usando 'ID' (primeira letra maiúscula)
    company = next((c for c in companies if str(c.get('ID')) == company_id), None)
    
    # Se não encontrar, tente com 'id' (minúsculo)
    if not company:
        company = next((c for c in companies if str(c.get('id')) == company_id), None)
        
    if not company:
        flash('Empresa não encontrada', 'error')
        return redirect(url_for('select_company', group=group))
    
    # Aqui você implementaria o código para iniciar o processo de automação
    # Para o exemplo, apenas exibimos uma mensagem
    # Verificar se a chave é 'empresas' ou 'empresa'
    if 'empresas' in company:
        company_name = company['empresas']
    elif 'empresa' in company:
        company_name = company['empresa']
    else:
        company_name = f"ID: {company_id}"
        
    flash(f'Iniciando processo para a empresa {company_name}', 'success')
    
    # Redireciona de volta para o dashboard
    return redirect(url_for('dashboard', group=group))

@app.route('/logout')
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    flash('Você foi desconectado com sucesso', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Certifique-se de que o arquivo Excel de usuários existe
    create_default_user(EXCEL_PATH)
    
    # Verifica os grupos disponíveis
    available_groups = get_available_groups()
    group_counts = get_group_counts()
    print(f"Grupos disponíveis: {available_groups}")
    print(f"Contagem de empresas por grupo: {group_counts}")
    
    # Inicia o servidor Flask
    print("Iniciando servidor Flask na porta 5000...")
    print("Acesse http://localhost:5000 para usar o sistema.")
    app.run(debug=True)
