import os
import pandas as pd
import datetime
from werkzeug.utils import secure_filename

def registrar_evento(group, company_name, tipo, descricao):
    """
    Registra um evento especial para a empresa
    
    Tipos de eventos:
    - upload_competencias: Upload de arquivo de competências
    - atualizacao_dados: Atualização de dados bancários
    - inicio_processo: Início do processo RPA
    - conclusao_processo: Conclusão do processo RPA
    - erro_processo: Erro no processo RPA
    """
    try:
        # Garante que o nome da empresa é seguro para uso em arquivos
        safe_company_name = secure_filename(company_name)
        
        # Define caminho para o arquivo de eventos
        base_dir = 'db/status'
        group_dir = os.path.join(base_dir, group)
        eventos_path = os.path.join(group_dir, 'eventos.xlsx')
        
        # Cria diretórios se não existirem
        if not os.path.exists(group_dir):
            os.makedirs(group_dir)
        
        # Preparar o novo evento
        novo_evento = {
            'data': datetime.datetime.now(),
            'empresa': company_name,
            'tipo': tipo,
            'descricao': descricao
        }
        
        # Verifica se o arquivo já existe
        if os.path.exists(eventos_path):
            try:
                # Carrega os eventos existentes
                df_eventos = pd.read_excel(eventos_path)
                # Adiciona o novo evento
                df_eventos = pd.concat([pd.DataFrame([novo_evento]), df_eventos], ignore_index=True)
            except Exception as e:
                print(f"Erro ao ler arquivo de eventos existente: {str(e)}")
                df_eventos = pd.DataFrame([novo_evento])
        else:
            # Cria um novo arquivo de eventos
            df_eventos = pd.DataFrame([novo_evento])
        
        # Salva o arquivo
        df_eventos.to_excel(eventos_path, index=False)
        print(f"Evento '{tipo}' registrado para {company_name} em {group}")
        
        # Também cria/atualiza arquivo específico da empresa
        empresa_dir = os.path.join(group_dir, safe_company_name)
        if not os.path.exists(empresa_dir):
            os.makedirs(empresa_dir)
            
        empresa_eventos_path = os.path.join(empresa_dir, 'eventos.xlsx')
        
        # Filtra apenas eventos desta empresa
        empresa_eventos = df_eventos[df_eventos['empresa'] == company_name]
        empresa_eventos.to_excel(empresa_eventos_path, index=False)
        
        return True
    except Exception as e:
        print(f"Erro ao registrar evento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def obter_eventos(group, company_name, limit=10):
    """
    Obtém os últimos eventos registrados para a empresa
    """
    try:
        # Garante que o nome da empresa é seguro para uso em arquivos
        safe_company_name = secure_filename(company_name)
        
        # Define caminho para o arquivo de eventos da empresa
        base_dir = 'db/status'
        group_dir = os.path.join(base_dir, group)
        empresa_dir = os.path.join(group_dir, safe_company_name)
        empresa_eventos_path = os.path.join(empresa_dir, 'eventos.xlsx')
        
        if not os.path.exists(empresa_eventos_path):
            return []
            
        # Carrega os eventos da empresa
        df_eventos = pd.read_excel(empresa_eventos_path)
        
        # Ordena por data (mais recente primeiro) e limita o número de entradas
        df_eventos = df_eventos.sort_values('data', ascending=False).head(limit)
        
        # Converte para uma lista de dicionários
        eventos = []
        for _, row in df_eventos.iterrows():
            data = row['data']
            if isinstance(data, pd.Timestamp):
                data = data.strftime('%d/%m/%Y %H:%M')
                
            eventos.append({
                'data': data,
                'tipo': row['tipo'],
                'descricao': row['descricao']
            })
            
        return eventos
    except Exception as e:
        print(f"Erro ao obter eventos: {str(e)}")
        return []

# Exemplos de uso:
if __name__ == "__main__":
    # Registrar alguns eventos de exemplo
    registrar_evento('teste', 'Empresa Exemplo', 'upload_competencias', 'Arquivo comp_20231015.xlsx')
    registrar_evento('teste', 'Empresa Exemplo', 'atualizacao_dados', 'CPF: 123.456.789-00, Banco: 001')
    registrar_evento('teste', 'Empresa Exemplo', 'inicio_processo', 'Iniciado para competências de 2023')
    
    # Obter eventos
    eventos = obter_eventos('teste', 'Empresa Exemplo')
    print("Eventos registrados:")
    for evento in eventos:
        print(f"[{evento['data']}] {evento['tipo']}: {evento['descricao']}")
