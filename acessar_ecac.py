import subprocess
import os
import pyautogui as gui
import time
import pandas as pd
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pathlib import Path

# Caminho para o arquivo .bat
caminho_bat = r"C:\Users\lucas.lima\Desktop\Iniciador Chrome.bat"

# Configuração do diretório de imagens
def get_image_path(image_name):
    """
    Retorna o caminho completo para uma imagem no diretório de imagens.
    Verifica primeiro na pasta image/, se não encontrar, verifica em styles/image/
    """
    base_dir = Path(__file__).parent
    # Primeiro procura na pasta image (usada pelo script)
    image_dir = base_dir / "image"
    if not image_dir.exists():
        image_dir.mkdir()
        print(f"Diretório de imagens criado em: {image_dir}")
    
    # Verifica se a imagem existe na pasta image/
    image_path = image_dir / image_name
    if not image_path.exists():
        # Se não existir, verifica em styles/image/
        styles_image_path = base_dir / "styles" / "image" / image_name
        if styles_image_path.exists():
            print(f"Imagem encontrada em styles/image, copiando para image/...")
            # Copia a imagem para a pasta image/
            import shutil
            shutil.copy(str(styles_image_path), str(image_path))
            print(f"Imagem {image_name} copiada com sucesso.")
        else:
            # Se não existir em styles/image, verifica o caminho completo fornecido
            explicit_path = r"C:\Users\lucas.lima\Desktop\Python geral\rpa-pedido-restituicao-ECAC\styles\image\alterar_perfil.png"
            if os.path.exists(explicit_path) and image_name == "alterar_perfil.png":
                # Se for o arquivo específico que estamos buscando, usa-o diretamente
                print(f"Usando caminho explícito para alterar_perfil.png")
                return explicit_path
            
    return str(image_path)

def localizar_e_clicar(imagem_path, confianca=0.8, tempo_espera=1, tentativas=3, mensagem=None):
    """
    Localiza uma imagem na tela e clica nela.
    
    Args:
        imagem_path: Nome da imagem ou caminho completo para o arquivo de imagem
        confianca: Nível de confiança para a correspondência (entre 0 e 1)
        tempo_espera: Tempo de espera após o clique em segundos
        tentativas: Número máximo de tentativas para encontrar a imagem
        mensagem: Mensagem para exibir enquanto procura a imagem
    
    Returns:
        bool: True se a imagem foi encontrada e clicada, False caso contrário
    """
    if mensagem:
        print(f"Procurando: {mensagem}")
    
    # Verificar se é nome de arquivo ou caminho completo
    if not os.path.isabs(imagem_path):
        imagem_path = get_image_path(imagem_path)
    
    # Verificar se o arquivo existe
    if not os.path.exists(imagem_path):
        print(f"ERRO: Imagem não encontrada no caminho: {imagem_path}")
        return False
    
    # Tentar localizar a imagem várias vezes
    for tentativa in range(tentativas):
        try:
            print(f"Tentativa {tentativa+1}/{tentativas}: Procurando imagem '{os.path.basename(imagem_path)}'")
            local = gui.locateOnScreen(imagem_path, confidence=confianca)
            if local:
                centro_x, centro_y = gui.center(local)
                print(f"Imagem encontrada! Clicando na posição: ({centro_x}, {centro_y})")
                gui.click(centro_x, centro_y)
                time.sleep(tempo_espera)
                return True
            else:
                print(f"Imagem não localizada nesta tentativa.")
                time.sleep(1)
        except Exception as e:
            print(f"Erro ao tentar localizar a imagem: {e}")
            time.sleep(1)
    
    print(f"FALHA: Não foi possível encontrar a imagem '{os.path.basename(imagem_path)}' após {tentativas} tentativas.")
    return False

def exemplo_de_uso():
    # Pasta para armazenar as imagens
    pasta_imagens = Path(__file__).parent / "image"
    
    # Criar pasta de imagens se não existir
    if not pasta_imagens.exists():
        pasta_imagens.mkdir()
        print(f"Pasta de imagens criada em: {pasta_imagens}")
        print("Coloque suas imagens de referência nesta pasta antes de usar o script.")
        return
    
    # Exemplo de uso
    print("Aguardando 5 segundos para começar...")
    time.sleep(5)
    
    # Exemplo com um botão fictício (substitua pelo caminho real da sua imagem)
    caminho_imagem = r"C:\Users\lucas.lima\Desktop\Python geral\rpa-pedido-restituicao-ECAC\styles\image\alterar_perfil.png"
    if os.path.exists(caminho_imagem):
        localizar_e_clicar(str(caminho_imagem), 
                          confianca=0.7, 
                          tempo_espera=1, 
                          mensagem="botão Enviar")
    else:
        print(f"Exemplo: Coloque uma imagem chamada 'botao_enviar.png' na pasta {pasta_imagens}")

# Função para mapear CNPJ para o caminho do certificado
def get_certificate_path(cnpj, group=None):
    """
    Retorna o caminho do certificado correspondente ao CNPJ da empresa.
    
    Args:
        cnpj: O CNPJ da empresa para buscar o certificado
        group: O grupo ao qual a empresa pertence (opcional)
    
    Returns:
        tuple: (caminho_do_certificado, senha_do_certificado) ou (None, None) se não encontrado
    """
    try:
        # Normaliza o CNPJ (remove pontos, traços e barras)
        cnpj = ''.join(filter(str.isdigit, cnpj))
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Se o grupo não foi fornecido, tentar encontrar em todos os grupos
        if group is None:
            groups_path = os.path.join(base_path, 'db', 'groups')
            if os.path.exists(groups_path):
                groups = [d for d in os.listdir(groups_path) 
                         if os.path.isdir(os.path.join(groups_path, d))]
            else:
                print(f"Diretório de grupos não encontrado: {groups_path}")
                return None, None
        else:
            groups = [group]
        
        # Procurar a empresa em cada grupo
        for group_name in groups:
            excel_path = os.path.join(base_path, 'db', 'groups', group_name, f'{group_name}.xlsx')
            
            if os.path.exists(excel_path):
                try:
                    # Ler o arquivo Excel
                    df = pd.read_excel(excel_path)
                    
                    # Verificar se as colunas necessárias existem
                    required_columns = ['cnpj', 'certificado', 'senha_certificado']
                    for col in required_columns:
                        if col.lower() not in [c.lower() for c in df.columns]:
                            print(f"Coluna {col} não encontrada no arquivo Excel do grupo {group_name}")
                            continue
                    
                    # Normalizar CNPJ na coluna para comparação (remover formatação)
                    df['cnpj_normalizado'] = df['cnpj'].astype(str).apply(
                        lambda x: ''.join(filter(str.isdigit, x)))
                    
                    # Buscar a empresa pelo CNPJ
                    empresa = df[df['cnpj_normalizado'] == cnpj]
                    
                    if not empresa.empty:
                        # Obter nome do certificado e senha
                        cert_name = empresa['certificado'].values[0]
                        cert_password = empresa['senha_certificado'].values[0]
                        
                        if pd.isna(cert_name) or pd.isna(cert_password):
                            print(f"Certificado ou senha não encontrado para CNPJ {cnpj} no grupo {group_name}")
                            continue
                        
                        # Construir caminho para o certificado
                        cert_path = os.path.join(base_path, 'db', 'certs', str(cert_name))
                        
                        if os.path.exists(cert_path):
                            print(f"Certificado encontrado: {cert_path}")
                            return cert_path, str(cert_password)
                        else:
                            print(f"Arquivo de certificado não encontrado: {cert_path}")
                            
                except Exception as e:
                    print(f"Erro ao ler arquivo Excel do grupo {group_name}: {str(e)}")
            else:
                print(f"Arquivo Excel não encontrado para o grupo {group_name}: {excel_path}")
        
        print(f"Nenhum certificado encontrado para o CNPJ {cnpj} nos grupos disponíveis.")
        return None, None
    except Exception as e:
        print(f"Erro ao buscar certificado para o CNPJ {cnpj}: {str(e)}")
        return None, None

# Função para remover todos os certificados
def remove_all_certificates():
    print("Removendo todos os certificados existentes...")
    list_cmd = "Get-ChildItem -Path Cert:\\CurrentUser\\My | Select-Object -ExpandProperty Thumbprint"
    result = subprocess.run(["powershell.exe", "-Command", list_cmd], capture_output=True, text=True)
    thumbprints = result.stdout.strip().splitlines()
    
    if thumbprints:
        for thumbprint in thumbprints:
            thumbprint = thumbprint.strip()
            remove_cmd = f"Remove-Item -Path Cert:\\CurrentUser\\My\\{thumbprint}"
            subprocess.run(["powershell.exe", "-Command", remove_cmd], check=True)
            print(f"Certificado com thumbprint {thumbprint} removido.")
        print("Todos os certificados foram removidos com sucesso.")
        return True
    else:
        print("Nenhum certificado encontrado para remover.")
        return True

# Função para instalar um novo certificado
def install_certificate(cert_path, cert_password):
    """
    Instala um certificado digital no repositório de certificados do usuário atual.
    """
    print(f"Instalando certificado do caminho: {cert_path}")
    if not os.path.isfile(cert_path):
        print(f"Arquivo de certificado não encontrado: {cert_path}")
        return False

    install_cmd = (
        f"Import-PfxCertificate -FilePath '{cert_path}' "
        f"-Password (ConvertTo-SecureString -String '{cert_password}' -AsPlainText -Force) "
        f"-CertStoreLocation Cert:\\CurrentUser\\My"
    )

    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", install_cmd],
            capture_output=True,
            text=True,
            check=True,
        )
        print("Certificado instalado com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar o certificado. Detalhes:\n{e.stderr}")
        return False

# Função para iniciar o Chrome pelo arquivo .bat
def iniciar_chrome():
    print("Iniciando Chrome através do arquivo .bat...")
    subprocess.Popen(caminho_bat, shell=True)
    time.sleep(5)  # Esperar o Chrome carregar
    print("Chrome iniciado.")
    return True

# Função para realizar sequência de login com localizar_e_clicar
def pyautogui_sequence_with_images(cnpj=None):
    try:
        print("Iniciando sequência de login com reconhecimento de imagens...")
        
        # Abrir o site do ECAC (já deve estar no navegador pelo .bat)
        # Verificar se há botão de entrada
        if not localizar_e_clicar("botao_entrar.png", confianca=0.7, tempo_espera=2, 
                                tentativas=8, mensagem="botão Entrar"):
            print("Falha ao encontrar o botão de entrar.")
            return False
            
        # Clicar na opção de certificado digital
        if not localizar_e_clicar("opcao_certificado.png", confianca=0.7, tempo_espera=2, 
                                tentativas=8, mensagem="opção Certificado Digital"):
            print("Falha ao encontrar a opção de certificado digital.")
            return False
            
        # Aguardar e confirmar no certificado
        time.sleep(3)  # Espera para o diálogo de certificado aparecer
        
        if not localizar_e_clicar("confirmar_certificado.png", confianca=0.7, tempo_espera=3, 
                                tentativas=8, mensagem="botão OK do certificado"):
            print("Falha ao confirmar o certificado. Tentando alternativa...")
            # Tentar clicar na posição padrão como backup
            gui.moveTo(1105, 451, duration=0.5)
            gui.click()
        
        # Aguardar a página carregar após confirmação do certificado
        time.sleep(5)
        
        # NOVA SEQUÊNCIA: Pressionar TAB duas vezes, digitar CNPJ (somente números), TAB e ESPAÇO
        # CNPJ deve ser o da empresa em processamento, sem pontuação nem traços
        if cnpj:
            # Normaliza o CNPJ (remove pontos, traços e barras)
            cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
            print(f"Inserindo CNPJ: {cnpj_limpo}")
            
            # Pressionar TAB duas vezes
            gui.press('tab')
            time.sleep(0.5)
            gui.press('tab')
            time.sleep(0.5)
            
            # Digitar o CNPJ sem formatação
            gui.typewrite(cnpj_limpo)
            time.sleep(1)
            
            # Pressionar TAB e depois ESPAÇO
            gui.press('tab')
            time.sleep(0.5)
            gui.press('space')
            time.sleep(2)
            print("Sequência de CNPJ concluída: TAB > TAB > CNPJ > TAB > ESPAÇO")
        else:
            print("CNPJ não fornecido, pulando etapa de preenchimento automático")
        
        print("Sequência de login concluída com sucesso.")
        return True
    except Exception as e:
        print(f"Erro na sequência de automação GUI: {str(e)}")
        return False

# Função alternativa que usa coordenadas fixas (fallback)
def pyautogui_sequence_with_coordinates():
    try:
        print("Iniciando sequência com coordenadas fixas (apenas 4 coordenadas iniciais)...")
        # Abrir o site do esocial
        gui.moveTo(192, 126, duration=0.5)
        gui.click()
        time.sleep(2)
        # Clicar em entrar
        gui.moveTo(1231, 603, duration=0.5)
        gui.click()
        time.sleep(2)
        # Certificado
        gui.moveTo(1292, 812, duration=0.5)
        gui.click()
        time.sleep(5)
        # Ok certificado
        gui.moveTo(1105, 451, duration=0.5)
        gui.click()
        time.sleep(5)  # Aumentado para dar tempo à página carregar
        
        print("Sequência inicial com coordenadas concluída com sucesso.")
        return True
    except Exception as e:
        print(f"Erro na sequência com coordenadas fixas: {str(e)}")
        return False

# Função para iniciar o WebDriver do Selenium
def iniciar_selenium():
    chrome_options = Options()
    chrome_options.debugger_address = '127.0.0.1:9995'
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("user-agent=Seu User-Agent Aqui")

    service = Service('C:/Program Files/Google/Chrome/Application/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def pyautogui_sequence_alterar_perfil(cnpj=None):
    """
    Clica no botão alterar_perfil.png e faz a sequência TAB, TAB, CNPJ, TAB, SPACE
    """
    print("Tentando clicar em alterar_perfil.png...")
    
    # Caminho explícito para a imagem (para garantir)
    explicit_path = r"C:\Users\lucas.lima\Desktop\Python geral\rpa-pedido-restituicao-ECAC\styles\image\alterar_perfil.png"
    
    # Tenta reconhecer imagem usando o caminho explícito
    success = False
    try:
        local = gui.locateOnScreen(explicit_path, confidence=0.7)
        if local:
            centro_x, centro_y = gui.center(local)
            print(f"Imagem encontrada! Clicando na posição: ({centro_x}, {centro_y})")
            gui.click(centro_x, centro_y)
            time.sleep(1)
            success = True
    except Exception as e:
        print(f"Erro ao tentar localizar usando caminho explícito: {e}")
    
    # Se falhou, tenta o método normal
    if not success:
        if not localizar_e_clicar("alterar_perfil.png", confianca=0.7, tempo_espera=2, 
                                  tentativas=8, mensagem="alterar_perfil"):
            print("Falha ao encontrar alterar_perfil.png.")
            return False

    # Continua com a sequência normal
    if cnpj:
        cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
        gui.press('tab')
        gui.press('tab')
        gui.typewrite(cnpj_limpo)
        time.sleep(1)
        gui.press('tab')
        time.sleep(0.5)
        gui.press('space')
        time.sleep(2)
        print("Sequência com alterar_perfil concluída: click > TAB > TAB > CNPJ > TAB > SPACE")
    return True

def verificar_login_sucesso(driver, cnpj_esperado, tentativas=3):
    """
    Verifica se o login foi bem-sucedido verificando o CNPJ na página.
    
    Args:
        driver: WebDriver do Selenium
        cnpj_esperado: CNPJ que deve aparecer na tela como Procurador
        tentativas: Número de tentativas antes de desistir
    
    Returns:
        bool: True se o login foi bem-sucedido, False caso contrário
    """
    print(f"Verificando se o login foi bem-sucedido para CNPJ: {cnpj_esperado}")
    
    # Normalizar o CNPJ esperado (remover formatação)
    cnpj_esperado = ''.join(filter(str.isdigit, str(cnpj_esperado)))
    
    time.sleep(5)
    for tentativa in range(tentativas):
        try:
            # Aguardar até que o elemento que contém as informações de perfil seja carregado
            print(f"Tentativa {tentativa + 1}: Aguardando carregamento da página...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "informacao-perfil"))
            )
            
            # Esperar mais um pouco para garantir que a página carregou completamente
            time.sleep(2)
            
            # Obter o texto da div de informações do perfil
            info_perfil = driver.find_element(By.ID, "informacao-perfil").text
            print(f"Informações de perfil encontradas: {info_perfil}")
            
            # Verificar se o CNPJ esperado está na seção de "Procurador de:"
            if "Procurador de:" in info_perfil and cnpj_esperado in info_perfil.replace(".", "").replace("/", "").replace("-", ""):
                print(f"Login bem-sucedido! CNPJ {cnpj_esperado} encontrado como Procurador.")
                return True
            else:
                print(f"CNPJ {cnpj_esperado} não encontrado como Procurador. Texto encontrado: {info_perfil}")
                # Capturar screenshot para debug
                screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"login_failed_{tentativa}.png")
                driver.save_screenshot(screenshot_path)
                print(f"Screenshot salvo em: {screenshot_path}")
                
                if tentativa < tentativas - 1:
                    print("Tentando novamente...")
                    time.sleep(2)
                    continue
                return False
                
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Erro ao verificar login (tentativa {tentativa + 1}): {str(e)}")
            # Capturar screenshot para debug
            screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"error_{tentativa}.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot salvo em: {screenshot_path}")
            
            if tentativa < tentativas - 1:
                print("Tentando novamente...")
                time.sleep(2)
                continue
            return False
    
    print("Todas as tentativas de verificação de login falharam.")
    return False

def acessar_pagina_restituicao(driver):
    """
    Acessa a página de restituição PerdComp
    
    Args:
        driver: WebDriver do Selenium
    
    Returns:
        bool: True se a página foi acessada com sucesso, False caso contrário
    """
    try:
        url_perdcomp = "https://www3.cav.receita.fazenda.gov.br/perdcomp-web/#/documento/identificacao-novo"
        print(f"Acessando URL do PerdComp: {url_perdcomp}")
        
        driver.get(url_perdcomp)
        
        # Aguardar carregamento da página
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Verificar se a URL atual contém a URL desejada
        current_url = driver.current_url
        if "perdcomp-web" in current_url:
            print("Página do PerdComp acessada com sucesso!")
            return True
        else:
            print(f"Falha ao acessar a página do PerdComp. URL atual: {current_url}")
            return False
    
    except Exception as e:
        print(f"Erro ao acessar a página de restituição: {str(e)}")
        return False

def fechar_chrome():
    """
    Fecha o Chrome usando Alt+F4
    """
    print("Fechando o Chrome com Alt+F4...")
    gui.hotkey('alt', 'f4')
    time.sleep(2)  # Esperar o navegador fechar
    return True

def iniciar_processo_ecac(cnpj=None, group=None, max_tentativas=3):
    """Função principal para acessar o ECAC com o certificado da empresa específica"""
    driver = None
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            print(f"=== TENTATIVA {tentativa}/{max_tentativas} - INICIANDO ACESSO AO ECAC PARA CNPJ: {cnpj} ===")
            
            # 1) Desinstalar certificados
            if not remove_all_certificates():
                print("Falha ao remover certificados. Continuando...")

            # 2) Instalar novo certificado
            if cnpj:
                cert_path, cert_password = get_certificate_path(cnpj, group)
                if cert_path and cert_password:
                    if not install_certificate(cert_path, cert_password):
                        print("Falha ao instalar certificado. Tentando novamente...")
                        if tentativa < max_tentativas:
                            continue
                        return False
                else:
                    print("Nenhum certificado encontrado. Abortando.")
                    return False
            else:
                print("Nenhum CNPJ fornecido. Continuando sem instalar certificado específico.")

            # 3) Iniciar o Chrome 
            if not iniciar_chrome():
                print("Falha ao iniciar Chrome. Tentando novamente...")
                if tentativa < max_tentativas:
                    continue
                return False

            # 4) Executar sequência inicial com coordenadas fixas
            print("Executando sequência inicial com coordenadas fixas...")
            if not pyautogui_sequence_with_coordinates():
                print("Falha na sequência com coordenadas fixas. Tentando novamente...")
                fechar_chrome()
                if tentativa < max_tentativas:
                    continue
                return False

            # 5) Clicar no botão alterar_perfil.png e depois fazer a sequência de TABs e CNPJ
            print("Procurando e clicando em alterar_perfil.png...")
            if not pyautogui_sequence_alterar_perfil(cnpj):
                print("Falha ao clicar em alterar_perfil.png ou completar sequência de CNPJ. Tentando novamente...")
                fechar_chrome()
                if tentativa < max_tentativas:
                    continue
                return False

            # 6) Iniciar Selenium e verificar login
            print("Iniciando Selenium para verificar login...")
            driver = iniciar_selenium()
            
            # 7) Verificar se o login foi bem-sucedido
            if not verificar_login_sucesso(driver, cnpj):
                print("Verificação de login falhou. Tentando novamente...")
                fechar_chrome()
                if tentativa < max_tentativas:
                    continue
                return False
                
            # 8) Acessar a página de restituição
            if not acessar_pagina_restituicao(driver):
                print("Falha ao acessar página de restituição. Tentando novamente...")
                fechar_chrome()
                if tentativa < max_tentativas:
                    continue
                return False
            
            print("Processo de acesso ao ECAC concluído com sucesso.")
            return True
        
        except Exception as e:
            print(f"Erro na tentativa {tentativa}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Fechar Chrome se ainda estiver aberto
            fechar_chrome()
            
            if tentativa < max_tentativas:
                print(f"Tentando novamente ({tentativa+1}/{max_tentativas})...")
                time.sleep(3)  # Esperar um pouco antes de tentar novamente
                continue
            else:
                print("Número máximo de tentativas atingido.")
                return False

# Executar o script como programa principal
if __name__ == "__main__":
    # Verifica se um CNPJ foi fornecido como argumento
    cnpj = None
    group = None
    
    # Processa argumentos da linha de comando
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg.startswith("--cnpj="):
            cnpj = arg.split("=")[1]
        elif arg.startswith("--group="):
            group = arg.split("=")[1]
        elif i == 1 and not arg.startswith("--"):
            # Para compatibilidade retroativa: primeiro argumento é o CNPJ
            cnpj = arg
        elif i == 2 and not arg.startswith("--"):
            # Para compatibilidade retroativa: segundo argumento é o grupo
            group = arg
    
    success = iniciar_processo_ecac(cnpj, group)
    if success:
        print("Processo de acesso ao ECAC concluído com sucesso.")
        sys.exit(0)  # Código de saída de sucesso
    else:
        print("Processo de acesso ao ECAC falhou.")
        sys.exit(1)  # Código de saída de erro

# Função de ponto de entrada para ser chamada pelo main.py
def main(cnpj=None, group=None):
    print(f"=== INICIANDO MÓDULO ACESSAR_ECAC ===")
    print(f"CNPJ: {cnpj}, Grupo: {group}")
    result = iniciar_processo_ecac(cnpj, group, max_tentativas=3)
    print(f"=== FINALIZADO MÓDULO ACESSAR_ECAC com resultado: {result} ===")
    
    # Se o acesso ao ECAC foi bem sucedido, inicia o app.py automaticamente
    if result:
        print("\n=== INICIANDO AUTOMATICAMENTE O PROCESSAMENTO DE RESTITUIÇÃO ===")
        try:
            import app
            # Localizando a empresa pelo CNPJ para passar ao app.py
            empresa = None
            if cnpj and group:
                try:
                    grupos_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'groups')
                    excel_path = os.path.join(grupos_path, group, f'{group}.xlsx')
                    if os.path.exists(excel_path):
                        df = pd.read_excel(excel_path)
                        # Normaliza o CNPJ para comparação
                        df['cnpj_normalizado'] = df['cnpj'].astype(str).apply(
                            lambda x: ''.join(filter(str.isdigit, x)))
                        cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
                        
                        # Busca a empresa pelo CNPJ
                        empresa_row = df[df['cnpj_normalizado'] == cnpj_limpo]
                        if not empresa_row.empty:
                            empresa = empresa_row.iloc[0].get('empresas', empresa_row.iloc[0].get('empresa', None))
                            print(f"Empresa identificada: {empresa}")
                except Exception as e:
                    print(f"Erro ao buscar empresa pelo CNPJ: {str(e)}")
            
            # Se encontrou a empresa, passa como argumento para app.py
            if empresa:
                print(f"Chamando app.main() para empresa: {empresa}")
                # Executa o app.py com a empresa identificada
                app.main()
            else:
                print("Empresa não identificada. Chamando app.py sem argumentos específicos.")
                app.main()
                
            return True
        except Exception as e:
            print(f"Erro ao iniciar o processamento de restituição: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return result