from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages, jsonify
import pandas as pd
import os
import json
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import shutil
import datetime
import subprocess
import sys

# Importar funções de login
from login import check_credentials, create_default_user

app = Flask(__name__, 
            static_folder='styles', 
            template_folder='styles/templates')

# Definir uma chave secreta forte para a sessão
app.secret_key = secrets.token_hex(16)  # Gera uma chave hexadecimal aleatória
print(f"Secret key gerada: {app.secret_key}")  # Para fins de depuração, remover em produção

# Caminho para o arquivo Excel de usuários
EXCEL_PATH = 'db/users.xlsx'
# Diretório para os grupos de empresas
GROUPS_DIR = 'db/groups'
# Diretório para os status das empresas
STATUS_DIR = 'db/status'

# Configurações para upload de arquivos
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_available_groups():
    """Retorna a lista de grupos disponíveis."""
    try:
        if not os.path.exists(GROUPS_DIR):
            os.makedirs(GROUPS_DIR)
            print(f"Diretório {GROUPS_DIR} criado.")
            
        # Verifique se o diretório existe e liste seu conteúdo
        print(f"Verificando diretório: {GROUPS_DIR}")
        print(f"Existe? {os.path.exists(GROUPS_DIR)}")
        print(f"Conteúdo: {os.listdir(GROUPS_DIR)}")
        
        groups = [f for f in os.listdir(GROUPS_DIR) 
                 if os.path.isdir(os.path.join(GROUPS_DIR, f))]
        
        print(f"Grupos encontrados: {groups}")
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

def get_company_by_id(group, company_id):
    """Encontra uma empresa pelo ID no grupo especificado."""
    companies = get_group_companies(group)
    
    print(f"Procurando empresa com ID {company_id} no grupo {group}")
    print(f"Empresas disponíveis: {companies}")
    
    # Primeiro tente encontrar usando 'ID' (primeira letra maiúscula)
    company = next((c for c in companies if str(c.get('ID', '')) == str(company_id)), None)
    
    # Se não encontrar, tente com 'id' (minúsculo)
    if not company:
        company = next((c for c in companies if str(c.get('id', '')) == str(company_id)), None)
        
    if company:
        print(f"Empresa encontrada: {company}")
    else:
        print(f"Empresa com ID {company_id} não encontrada no grupo {group}")
        
    return company

def get_company_name(company):
    """Extrai o nome da empresa do dicionário de dados da empresa."""
    if 'empresas' in company:
        return company['empresas']
    elif 'empresa' in company:
        return company['empresa']
    else:
        return f"Empresa_{company.get('ID', company.get('id', 'desconhecido'))}"

def get_company_status_path(group, company):
    """Retorna o caminho para o arquivo de status da empresa específica."""
    # Cria diretório para o grupo se não existir
    group_status_dir = os.path.join(STATUS_DIR, group)
    if not os.path.exists(group_status_dir):
        os.makedirs(group_status_dir)
    
    # Obtém o nome da empresa para usar como nome do arquivo
    company_name = get_company_name(company)
    company_filename = secure_filename(f"{company_name}.xlsx")
    
    return os.path.join(group_status_dir, company_filename)

def get_company_comp_file_path(group, company):
    """Retorna o caminho para o arquivo de competências da empresa específica."""
    # Cria diretório para o grupo se não existir
    group_status_dir = os.path.join(STATUS_DIR, group)
    if not os.path.exists(group_status_dir):
        os.makedirs(group_status_dir)
    
    # Obtém o nome da empresa para usar como nome do arquivo
    company_name = get_company_name(company)
    comp_dir = os.path.join(group_status_dir, secure_filename(company_name))
    
    # Cria diretório para arquivos da empresa se não existir
    if not os.path.exists(comp_dir):
        os.makedirs(comp_dir)
    
    return comp_dir

def get_company_stats(group, company_id):
    """Obtém estatísticas específicas de uma empresa a partir do arquivo de status."""
    company = get_company_by_id(group, company_id)
    if not company:
        return {
            'processos_totais': 0,
            'processos_concluidos': 0,
            'processos_pendentes': 0,
            'processos_falha': 0,
            'ultimo_processamento': 'Nunca',
            'status': 'Não iniciado',
            'historico': []
        }
    
    status_path = get_company_status_path(group, company)
    if not os.path.exists(status_path):
        return {
            'processos_totais': 0,
            'processos_concluidos': 0,
            'processos_pendentes': 0,
            'processos_falha': 0,
            'ultimo_processamento': 'Nunca',
            'status': 'Não iniciado',
            'historico': []
        }
    
    try:
        # Lê dados do arquivo de status
        status_df = pd.read_excel(status_path)
        
        # Verifica se temos o formato novo de status com as colunas Sucesso, falha, pendente
        if 'Sucesso' in status_df.columns and 'falha' in status_df.columns and 'pendente' in status_df.columns:
            # Contagem de processos com base nas colunas específicas
            total_processos = len(status_df)
            processos_concluidos = status_df['Sucesso'].sum()
            processos_falha = status_df['falha'].sum()
            processos_pendentes = status_df['pendente'].sum()
        else:
            # Contagem baseada na coluna 'status' (formato antigo)
            total_processos = len(status_df)
            processos_concluidos = len(status_df[status_df['status'] == 'Concluído'])
            processos_falha = len(status_df[status_df['status'] == 'Falha'])
            processos_pendentes = total_processos - processos_concluidos - processos_falha
        
        # Data do último processamento
        if 'data' in status_df.columns and not status_df.empty:
            ultimo_processamento = status_df['data'].max()
            if isinstance(ultimo_processamento, pd.Timestamp):
                ultimo_processamento = ultimo_processamento.strftime('%d/%m/%Y')
        else:
            ultimo_processamento = 'Desconhecido'
        
        # Status geral
        if processos_pendentes > 0:
            status_geral = 'Em andamento'
        elif processos_falha > 0 and processos_concluidos == 0:
            status_geral = 'Falha'
        elif processos_concluidos > 0:
            status_geral = 'Concluído'
        else:
            status_geral = 'Não iniciado'
        
        # Histórico de ações (últimas 10)
        historico = []
        if not status_df.empty and 'data' in status_df.columns:
            for _, row in status_df.sort_values('data', ascending=False).head(10).iterrows():
                data = row['data']
                if isinstance(data, pd.Timestamp):
                    data = data.strftime('%d/%m/%Y')
                
                # Determinar status com base nas novas colunas
                if 'Sucesso' in row and row['Sucesso']:
                    status = 'Concluído'
                elif 'falha' in row and row['falha']:
                    status = 'Falha'
                elif 'pendente' in row and row['pendente']:
                    status = 'Pendente'
                else:
                    status = row.get('status', 'Desconhecido')
                
                historico.append({
                    'data': data,
                    'acao': row.get('acao', 'Restituição'),
                    'status': status,
                    'competencia': row.get('competencia', '')
                })
        
        return {
            'processos_totais': total_processos,
            'processos_concluidos': processos_concluidos,
            'processos_pendentes': processos_pendentes,
            'processos_falha': processos_falha,
            'ultimo_processamento': ultimo_processamento,
            'status': status_geral,
            'historico': historico
        }
    except Exception as e:
        print(f"Erro ao ler arquivo de status: {str(e)}")
        return {
            'processos_totais': 0,
            'processos_concluidos': 0,
            'processos_pendentes': 0,
            'processos_falha': 0,
            'ultimo_processamento': 'Erro',
            'status': 'Erro ao ler status',
            'historico': []
        }

def get_company_existing_data(group, company_id):
    """Obtém dados existentes da empresa para pré-preenchimento dos formulários."""
    company = get_company_by_id(group, company_id)
    if not company:
        return {}
    
    status_path = get_company_status_path(group, company)
    if not os.path.exists(status_path):
        return {}
    
    try:
        # Lê o arquivo de status para obter dados existentes
        status_df = pd.read_excel(status_path)
        
        # Verifica se existem metadados sobre os dados bancários
        if 'metadata' in status_df.columns and not status_df.empty:
            metadata_row = status_df.iloc[0]
            metadata_str = metadata_row.get('metadata', '{}')
            
            if isinstance(metadata_str, str):
                try:
                    metadata = json.loads(metadata_str)
                    return metadata
                except:
                    return {}
        
        return {}
    except Exception as e:
        print(f"Erro ao ler dados existentes: {str(e)}")
        return {}

def get_existing_comp_file(group, company):
    """Verifica se existe arquivo de competências para a empresa."""
    comp_dir = get_company_comp_file_path(group, company)
    
    try:
        files = os.listdir(comp_dir)
        comp_files = [f for f in files if f.endswith(('.xlsx', '.xls'))]
        if comp_files:
            return comp_files[0]
        return None
    except Exception as e:
        print(f"Erro ao verificar arquivos de competência: {str(e)}")
        return None

def ensure_example_data():
    """Garante que temos dados de exemplo funcionando (grupos e empresas)."""
    try:
        # Verifique se o diretório de grupos existe
        if not os.path.exists(GROUPS_DIR):
            os.makedirs(GROUPS_DIR)
            print(f"Diretório {GROUPS_DIR} criado.")
        
        # Verifique se existe pelo menos um grupo de exemplo (save)
        save_group_dir = os.path.join(GROUPS_DIR, 'save')
        if not os.path.exists(save_group_dir):
            os.makedirs(save_group_dir)
            print(f"Grupo de exemplo 'save' criado em {save_group_dir}")
        
        # Verifique se existe o arquivo de empresas para o grupo save
        save_excel_path = os.path.join(save_group_dir, 'save.xlsx')
        if not os.path.exists(save_excel_path):
            # Criar DataFrame de exemplo
            data = {
                'ID': [1, 2, 3],
                'empresas': ['Empresa A', 'Empresa B', 'Empresa C'],
                'CNPJ': ['12.345.678/0001-99', '98.765.432/0001-10', '11.222.333/0001-44'],
                'Certificado': ['cert_a.pfx', 'cert_b.pfx', 'cert_c.pfx'],
                'Senha_certificado': ['senha123', 'senha456', 'senha789']
            }
            example_df = pd.DataFrame(data)
            example_df.to_excel(save_excel_path, index=False)
            print(f"Arquivo de exemplo {save_excel_path} criado.")
        
        return True
    except Exception as e:
        print(f"Erro ao criar dados de exemplo: {str(e)}")
        return False

def get_dados_bancarios_path(group):
    """Retorna o caminho para o arquivo de dados bancários do grupo."""
    dados_bancarios_dir = os.path.join(STATUS_DIR, "dados_bancarios", group)
    if not os.path.exists(dados_bancarios_dir):
        os.makedirs(dados_bancarios_dir)
    return os.path.join(dados_bancarios_dir, "Dados_bancarios.xlsx")

def salvar_dados_bancarios(group, company, cpf, banco, agencia, conta, dv):
    """Salva os dados bancários da empresa em uma planilha centralizada."""
    try:
        dados_bancarios_path = get_dados_bancarios_path(group)
        company_name = get_company_name(company)
        cnpj = company.get('CNPJ', company.get('cnpj', ''))
        
        # Prepara os novos dados
        novo_registro = pd.DataFrame({
            'empresa': [company_name],
            'cnpj': [cnpj],
            'cpf': [cpf],
            'banco': [banco],
            'agencia': [agencia],
            'conta': [conta],
            'dv': [dv],
            'atualizado_em': [datetime.datetime.now()]
        })
        
        # Verifica se o arquivo já existe
        if os.path.exists(dados_bancarios_path):
            # Carrega os dados existentes
            df_dados = pd.read_excel(dados_bancarios_path)
            
            # Verifica se a empresa já existe
            empresa_exists = df_dados['empresa'] == company_name
            if empresa_exists.any():
                # Atualiza os dados da empresa
                df_dados.loc[empresa_exists, 'cpf'] = cpf
                df_dados.loc[empresa_exists, 'banco'] = banco
                df_dados.loc[empresa_exists, 'agencia'] = agencia
                df_dados.loc[empresa_exists, 'conta'] = conta
                df_dados.loc[empresa_exists, 'dv'] = dv
                df_dados.loc[empresa_exists, 'atualizado_em'] = datetime.datetime.now()
            else:
                # Adiciona nova empresa
                df_dados = pd.concat([df_dados, novo_registro], ignore_index=True)
        else:
            # Cria novo arquivo com o primeiro registro
            df_dados = novo_registro
        
        # Salva os dados
        df_dados.to_excel(dados_bancarios_path, index=False)
        print(f"Dados bancários da empresa {company_name} salvos com sucesso em {dados_bancarios_path}")
        return dados_bancarios_path
    except Exception as e:
        print(f"Erro ao salvar dados bancários: {str(e)}")
        return None

def criar_planilha_status_empresa(group, company, comp_filepath):
    """Cria uma planilha de status para a empresa com base no arquivo de competências."""
    try:
        # Obtém o nome da empresa
        company_name = get_company_name(company)
        
        # Define o caminho para a planilha de status
        grupo_status_dir = os.path.join(STATUS_DIR, group)
        if not os.path.exists(grupo_status_dir):
            os.makedirs(grupo_status_dir)
            
        status_filepath = os.path.join(grupo_status_dir, f"{secure_filename(company_name)}.xlsx")
        
        # Carrega o arquivo de competências
        df_comp = pd.read_excel(comp_filepath)
        
        # Verifica se existe uma coluna chamada 'COMP' ou 'comp'
        comp_col = None
        if 'COMP' in df_comp.columns:
            comp_col = 'COMP'
        elif 'comp' in df_comp.columns:
            comp_col = 'comp'
        elif 'COMP_STR' in df_comp.columns:
            comp_col = 'COMP_STR'
        else:
            # Tenta encontrar coluna com competências
            for col in df_comp.columns:
                if isinstance(col, str) and ('comp' in col.lower() or 'data' in col.lower()):
                    comp_col = col
                    break
            
            if not comp_col:
                print(f"Erro: Não foi possível encontrar coluna de competências no arquivo {comp_filepath}")
                return None
                
        # Extrai as competências
        competencias = df_comp[comp_col].astype(str).str.strip().unique()
        
        # Cria DataFrame de status
        df_status = pd.DataFrame({
            'comp': competencias,
            'Sucesso': False,
            'falha': False,
            'pendente': True
        })
        
        # Salva o DataFrame
        df_status.to_excel(status_filepath, index=False)
        print(f"Planilha de status criada para {company_name} em {status_filepath}")
        
        return status_filepath
    except Exception as e:
        print(f"Erro ao criar planilha de status: {str(e)}")
        return None

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
        is_valid, result = check_credentials(username, password, EXCEL_PATH)
        
        if is_valid:
            # Credenciais válidas - configura a sessão
            session['logged_in'] = True
            session['user_id'] = int(result)
            session['username'] = username
            
            # Redireciona para a página de seleção de grupo após login
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('select_group'))
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
    
    # Obtém o grupo selecionado e opcionalmente a empresa específica
    selected_group = request.args.get('group')
    company_id = request.args.get('company_id')
    
    # Se não houver grupo selecionado, redirecionar para selecionar um grupo primeiro
    if not selected_group:
        return redirect(url_for('select_group'))
    
    # Se tiver um grupo selecionado, mostrar dashboard do grupo
    group_info = get_group_info(selected_group)
    
    # Se tiver uma empresa específica, mostrar informações da empresa
    selected_company = None
    company_stats = None
    if company_id:
        selected_company = get_company_by_id(selected_group, company_id)
        if selected_company:
            company_stats = get_company_stats(selected_group, company_id)
    
    # Obtém as empresas do grupo para exibir no modal
    companies = get_group_companies(selected_group)
    
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
                           group_info=group_info,
                           selected_company=selected_company,
                           company_stats=company_stats,
                           companies=companies)

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

@app.route('/get_companies/<group>')
def get_companies(group):
    """API para obter a lista de empresas de um grupo via AJAX."""
    if not session.get('logged_in'):
        return jsonify({'error': 'Não autorizado'}), 401
    
    companies = get_group_companies(group)
    print(f"Empresas do grupo {group}: {companies}")
    
    # Formatar os dados para compatibilidade com diferentes nomes de campos
    formatted_companies = []
    for company in companies:
        formatted_company = {
            'id': company.get('ID', '') or company.get('id', ''),
            'name': company.get('empresas', '') or company.get('empresa', ''),
            'cnpj': company.get('CNPJ', '') or company.get('cnpj', ''),
            'certificate': company.get('Certificado', '') or company.get('certificado', '')
        }
        formatted_companies.append(formatted_company)
    
    print(f"Empresas formatadas: {formatted_companies}")
    return jsonify(formatted_companies)

@app.route('/start_process')
def start_process():
    """Redireciona para o dashboard com uma empresa selecionada para visualização."""
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        flash('Você precisa fazer login para acessar esta página', 'error')
        return redirect(url_for('login'))
    
    # Obtém o grupo e o ID da empresa
    group = request.args.get('group')
    company_id = request.args.get('company_id')
    
    if not group:
        flash('Nenhum grupo selecionado', 'error')
        return redirect(url_for('dashboard'))
    
    if not company_id:
        flash('É necessário selecionar uma empresa específica para visualizar', 'warning')
        return redirect(url_for('dashboard', group=group))
    
    # Redireciona para o dashboard com a empresa selecionada
    return redirect(url_for('dashboard', group=group, company_id=company_id))

@app.route('/execute_rpa')
def execute_rpa():
    """Redireciona para a página RPA para configuração inicial."""
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        flash('Você precisa fazer login para acessar esta página', 'error')
        return redirect(url_for('login'))
    
    # Obtém o grupo e o ID da empresa
    group = request.args.get('group')
    company_id = request.args.get('company_id')
    
    if not group or not company_id:
        flash('É necessário selecionar um grupo e uma empresa para iniciar o RPA', 'error')
        return redirect(url_for('dashboard'))
    
    # Encontra os detalhes da empresa
    company = get_company_by_id(group, company_id)
    
    if not company:
        flash('Empresa não encontrada', 'error')
        return redirect(url_for('dashboard', group=group))
    
    # Redireciona para a página RPA com os dados da empresa
    return redirect(url_for('rpa_page', group=group, company_id=company_id))

@app.route('/rpa')
def rpa_page():
    """Página para configurar e iniciar o processo RPA."""
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        flash('Você precisa fazer login para acessar esta página', 'error')
        return redirect(url_for('login'))
    
    # Obtém o grupo e o ID da empresa
    group = request.args.get('group')
    company_id = request.args.get('company_id')
    
    if not group or not company_id:
        flash('É necessário selecionar um grupo e uma empresa para iniciar o RPA', 'error')
        return redirect(url_for('dashboard'))
    
    # Encontra os detalhes da empresa
    company = get_company_by_id(group, company_id)
    
    if not company:
        flash('Empresa não encontrada', 'error')
        return redirect(url_for('dashboard', group=group))
    
    # Coleta mensagens flash para exibição no template
    messages = []
    for category, message in get_flashed_messages(with_categories=True):
        messages.append((category, message))
    
    # Verifica se já existem dados salvos para esta empresa
    existing_data = get_company_existing_data(group, company_id)
    existing_comp_file = get_existing_comp_file(group, company)
    
    return render_template('rpa.html',
                          username=session.get('username', 'Usuário'),
                          messages=messages,
                          group=group,
                          company_id=company_id,
                          company=company,
                          existing_data=existing_data,
                          existing_comp_file=existing_comp_file)

def start_rpa_process(company_name, comp_filepath, cpf, banco, agencia, conta, dv):
    """Inicia o processo RPA executando o script app.py"""
    try:
        print(f"Iniciando processo RPA para: {company_name}")
        print(f"Arquivo de competências: {comp_filepath}")
        
        # Copia o arquivo comp.xlsx para o diretório raiz do RPA
        rpa_comp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comp.xlsx')
        shutil.copy2(comp_filepath, rpa_comp_path)
        
        # Constrói o comando para executar o app.py
        python_executable = sys.executable
        app_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
        
        # Executa o script app.py em um processo separado
        cmd = [python_executable, app_script]
        
        # Executa o processo RPA em um processo separado sem bloquear o Flask
        proc = subprocess.Popen(cmd, 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdin=subprocess.PIPE,
                               text=True,
                               bufsize=1,
                               universal_newlines=True)
        
        # Envia os inputs necessários para o processo
        proc.stdin.write(f"{company_name}\n")
        proc.stdin.write(f"{cpf}\n")
        
        print(f"Processo RPA iniciado com PID: {proc.pid}")
        
        return True
    except Exception as e:
        print(f"Erro ao iniciar processo RPA: {str(e)}")
        return False

@app.route('/save_rpa_data', methods=['POST'])
def save_rpa_data():
    """Salva os dados do RPA e inicia o processo."""
    # Verifica se o usuário está logado
    if not session.get('logged_in'):
        flash('Você precisa fazer login para acessar esta página', 'error')
        return redirect(url_for('login'))
    
    # Obtém o grupo e o ID da empresa do formulário
    group = request.form.get('group')
    company_id = request.form.get('company_id')
    
    if not group or not company_id:
        flash('Dados incompletos. Grupo ou empresa não fornecidos.', 'error')
        return redirect(url_for('dashboard'))
    
    # Encontra os detalhes da empresa
    company = get_company_by_id(group, company_id)
    
    if not company:
        flash('Empresa não encontrada', 'error')
        return redirect(url_for('dashboard', group=group))
    
    # Obtém os dados do formulário
    cpf = request.form.get('cpf', '')
    banco = request.form.get('banco', '')
    agencia = request.form.get('agencia', '')
    conta = request.form.get('conta', '')
    dv = request.form.get('dv', '')  # Adicionado campo de DV
    
    # Valida os dados obrigatórios
    if not all([cpf, banco, agencia, conta]):
        flash('Todos os campos são obrigatórios', 'error')
        return redirect(url_for('rpa_page', group=group, company_id=company_id))
    
    # Prepara o diretório para os arquivos da empresa
    company_name = get_company_name(company)
    status_path = get_company_status_path(group, company)
    comp_dir = get_company_comp_file_path(group, company)
    
    # Trata o upload do arquivo de competências
    comp_file = request.files.get('compFile')
    comp_filename = None
    comp_filepath = None
    
    if comp_file and comp_file.filename and allowed_file(comp_file.filename):
        comp_filename = secure_filename(f"comp_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx")
        comp_filepath = os.path.join(comp_dir, comp_filename)
        
        # Remove arquivos existentes de competência
        try:
            for file in os.listdir(comp_dir):
                if file.endswith(('.xlsx', '.xls')):
                    os.remove(os.path.join(comp_dir, file))
        except Exception as e:
            print(f"Erro ao limpar arquivos antigos: {str(e)}")
        
        # Salva o novo arquivo
        comp_file.save(comp_filepath)
    else:
        # Verifica se já existe um arquivo de competência
        existing_comp_file = get_existing_comp_file(group, company)
        if existing_comp_file:
            comp_filepath = os.path.join(comp_dir, existing_comp_file)
        else:
            flash('É necessário fazer upload de um arquivo de competências', 'error')
            return redirect(url_for('rpa_page', group=group, company_id=company_id))
    
    # Salva os dados bancários no arquivo centralizado
    dados_bancarios_path = salvar_dados_bancarios(group, company, cpf, banco, agencia, conta, dv)
    
    # Cria a planilha de status com as competências
    status_filepath = criar_planilha_status_empresa(group, company, comp_filepath)
    
    # Copia o arquivo de competências para o diretório raiz para uso do app.py
    try:
        rpa_comp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comp.xlsx')
        shutil.copy2(comp_filepath, rpa_comp_path)
        print(f"Arquivo de competências copiado para {rpa_comp_path}")
    except Exception as e:
        print(f"Erro ao copiar arquivo de competências: {str(e)}")
        flash(f'Erro ao copiar arquivo de competências: {str(e)}', 'error')
        return redirect(url_for('rpa_page', group=group, company_id=company_id))
    
    try:
        # Inicia o processo RPA
        rpa_started = start_rpa_process(company_name, comp_filepath, cpf, banco, agencia, conta, dv)
        
        if rpa_started:
            flash(f'Processo RPA iniciado para {company_name}', 'success')
        else:
            flash(f'Erro ao iniciar processo RPA para {company_name}', 'error')
        
        return redirect(url_for('dashboard', group=group, company_id=company_id))
    except Exception as e:
        flash(f'Erro ao iniciar processo: {str(e)}', 'error')
        return redirect(url_for('rpa_page', group=group, company_id=company_id))

def start_rpa_process(company_name, comp_filepath, cpf, banco, agencia, conta, dv):
    """Inicia o processo RPA executando o script app.py"""
    try:
        print(f"Iniciando processo RPA para: {company_name}")
        
        # Constrói o comando para executar o app.py
        python_executable = sys.executable
        app_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
        
        # Executa o script app.py em um processo separado
        cmd = [python_executable, app_script]
        
        # Executa o processo RPA em um processo separado sem bloquear o Flask
        proc = subprocess.Popen(cmd, 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdin=subprocess.PIPE,
                               text=True,
                               bufsize=1,
                               universal_newlines=True)
        
        # Envia os inputs necessários para o processo (apenas o nome da empresa)
        # O app.py vai buscar os dados bancários e outros na planilha
        proc.stdin.write(f"{company_name}\n")
        proc.stdin.flush()
        
        print(f"Processo RPA iniciado com PID: {proc.pid}")
        
        return True
    except Exception as e:
        print(f"Erro ao iniciar processo RPA: {str(e)}")
        return False

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

@app.route('/logout')
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    flash('Você foi desconectado com sucesso', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Verificar e criar usuário padrão se necessário
    create_default_user(EXCEL_PATH)
    
    # Garantir que temos dados de exemplo
    ensure_example_data()
    
    # Criar diretório para status se não existir
    if not os.path.exists(STATUS_DIR):
        os.makedirs(STATUS_DIR)
    
    # Verifica os grupos disponíveis
    available_groups = get_available_groups()
    group_counts = get_group_counts()
    print(f"Grupos disponíveis: {available_groups}")
    print(f"Contagem de empresas por grupo: {group_counts}")
    
    # Inicia o servidor Flask
    print("Iniciando servidor Flask na porta 5000...")
    print("Acesse http://localhost:5000 para usar o sistema.")
    app.run(debug=True)