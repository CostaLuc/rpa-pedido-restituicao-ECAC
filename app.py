import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from calendar import monthrange
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def iniciar_selenium():
    chrome_options = Options()
    chrome_options.debugger_address = '127.0.0.1:9995'
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")

    service = Service('C:/Program Files/Google/Chrome/Application/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def converter_competencia_para_site(comp_str):
    """Exemplo: se comp_str = '01/2022', retorna '01/01/2022'.
       Se comp_str = '13/2022', pode ser que o sistema use '01/12/2022' (depende da regra do 13º).
    """
    if comp_str.startswith("13/"):
        ano = comp_str.split("/")[1]
        # Verifique na prática se o site mostra "01/12/2022" ou "01/12/2021"...
        # Aqui é só um exemplo
        return f"01/12/{ano}"
    else:
        mes, ano = comp_str.split("/")
        return f"01/{mes}/{ano}"

def indentificar_documento(driver, apelido):
    """Clica nos botões iniciais necessários e preenche o apelido."""
    
    
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="page-content-wrapper"]/perdcomp-template-documento/div/perdcomp-identificacao-documento/form/div/div[2]/div/div[2]/label'))
    ).click()

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="page-content-wrapper"]/perdcomp-template-documento/div/perdcomp-identificacao-documento/form/div[2]/div/div/div/div/div[2]/div/label'))
    ).click()

    tipo_credito = Select(WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "tipoCredito"))
    ))
    time.sleep(0.5)
    tipo_credito.select_by_visible_text("Pagamento Indevido ou a Maior")

    qualificacao = Select(WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "qualificacaoContribuinte"))
    ))
    time.sleep(0.5)
    qualificacao.select_by_visible_text("Outra Qualificação")

    detalhamento_credito = Select(WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "tipoIdentificacaoCredito"))
    ))
    time.sleep(0.5)
    detalhamento_credito.select_by_visible_text("O crédito será detalhado neste documento")

    apelido_doc = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "apelidoDocumento"))
    )
    time.sleep(0.5)
    apelido_doc.send_keys(apelido)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.NAME, "btnProsseguir"))
    ).click()

    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div/perdcomp-root/div/div[2]/perdcomp-template-documento/div/perdcomp-identificacao-documento/form/div[2]/perdcomp-modal[1]/div/div[1]/div[1]/div[2]/div/div/label'))
    ).click()

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "botaoOkTermoAceito"))
    ).click()

def verificar_data_arrecadacao_janeiro(driver):
    """
    Para janeiro 'comum': Verifica a última data de arrecadação na tabela 
    para evitar 13º salário (datas que contenham '/12/').
    Retorna True se conseguiu abrir um período válido (não dezembro), False caso contrário.
    """
    try:
        linhas_pagamento = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "row-pagamento")]'))
        )

        for linha in linhas_pagamento:
            # Obtém todas as datas de arrecadacao dentro da linha
            datas_arrecadacao = linha.find_elements(By.XPATH, './/div[contains(@class, "gs-col3")]/a')
            if datas_arrecadacao:
                ultima_data_texto = datas_arrecadacao[-1].text.strip()  # Pega a última data
                print(f"Última data encontrada: {ultima_data_texto}")

                if "/12/" in ultima_data_texto:
                    print(f"13º salário detectado em {ultima_data_texto}. Ignorando...")
                    continue  # pula essa linha

                # Se a última data NÃO for dezembro, clica para abrir
                print(f"Abrindo período com data de arrecadacao: {ultima_data_texto}")
                linha.click()
                return True
    except Exception as e:
        print(f"Erro ao verificar data de arrecadacao (janeiro comum): {e}")

    return False

def verificar_data_arrecadacao_13(driver):
    """
    Para o 13º: Precisamos abrir justamente o período que tem data em dezembro 
    (pois esse é o pagamento do 13º).
    Retorna True se encontrou e abriu o período de dezembro, caso contrário False.
    """
    try:
        linhas_pagamento = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "row-pagamento")]'))
        )

        for linha in linhas_pagamento:
            datas_arrecadacao = linha.find_elements(By.XPATH, './/div[contains(@class, "gs-col3")]/a')
            if datas_arrecadacao:
                ultima_data_texto = datas_arrecadacao[-1].text.strip()
                print(f"Última data encontrada: {ultima_data_texto}")

                if "/12/" in ultima_data_texto:
                    # É justamente o que queremos para o 13º
                    print(f"Abrindo período com data de arrecadacao do 13º: {ultima_data_texto}")
                    linha.click()
                    return True
                else:
                    print(f"Data {ultima_data_texto} não é dezembro. Ignorando este período...")
    except Exception as e:
        print(f"Erro ao verificar data de arrecadacao (13º): {e}")

    return False

def informar_credito(driver, competencia_str):
    try:
        action = ActionChains(driver)

        # Detentor: "Crédito apurado pelo próprio contribuinte"
        detentor = Select(WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div/perdcomp-root/div/div[2]/perdcomp-template-documento/div/perdcomp-informar-credito/perdcomp-tabs/perdcomp-tab[1]/div/perdcomp-pgim-unificado-identificar-credito/div/perdcomp-detentor-credito-pj/div/div[1]/div/div/select"))
        ))
        time.sleep(0.5)
        detentor.select_by_visible_text("Crédito apurado pelo próprio contribuinte")

        # Clica em "Pagamento" (ou algo similar) - Corrigido para usar JavaScript para evitar o click intercepted
        selecionar_pagamento = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="page-content-wrapper"]/perdcomp-template-documento/div/perdcomp-informar-credito/perdcomp-tabs/perdcomp-tab[1]/div/perdcomp-pgim-unificado-identificar-credito/div/div/div/div/div/div/div/input'))
        )
        time.sleep(0.5)
        selecionar_pagamento.click()

        # Localizar campo de código da receita e inserir "1410"
        codigo_receita = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="codigoReceitaPesquisa"]/input'))
        )
        time.sleep(0.5)
        codigo_receita.click()
        codigo_receita.send_keys("1410")
        print("Preenchido código de receita 1410")

        # Verifica se estamos buscando 13º salário ou uma competência normal
        eh_13_salario = competencia_str.startswith("13/")
        print(f"Buscando {'13º salário' if eh_13_salario else 'competência normal'} para {competencia_str}")

        # --- Configura datas de pesquisa para qualquer tipo de competência
        if eh_13_salario:
            # Extrai o ano
            ano_str = competencia_str.split("/")[1]
            ano = int(ano_str)

            data_inicio = f"01/01/{ano}"
            data_fim = f"31/01/{ano}"
        else:
            # Mês/Ano comum -> parse normal
            # Tenta converter para datetime
            comp_dt = pd.to_datetime(competencia_str, format='%m/%Y', errors='coerce')
            if pd.isna(comp_dt):
                print(f"Competência inválida ou não parseada: {competencia_str}")
                return None

            mes = comp_dt.month
            ano = comp_dt.year

            # Monta datas de início e fim
            data_inicio = f"01/{mes:02d}/{ano}"
            ultimo_dia = monthrange(ano, mes)[1]
            data_fim = f"{ultimo_dia:02d}/{mes:02d}/{ano}"

        # Aplica as datas de pesquisa nos campos correspondentes
        periodo_data_inicio = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'inicioApuracaoPesquisa'))
        )
        periodo_data_inicio.click()
        action.send_keys(data_inicio).perform()
        print(f"Preenchida data inicial: {data_inicio}")

        # Selecionar e digitar a data no campo de fim
        periodo_data_fim = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'fimApuracaoPesquisa'))
        )
        periodo_data_fim.click()
        action.send_keys(data_fim).perform()
        print(f"Preenchida data final: {data_fim}")

        # Clica em pesquisar usando JavaScript para evitar o erro
        try:
            pesquisar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "Pesquisar")]'))
            )
            driver.execute_script("arguments[0].click();", pesquisar)
            print("Clicado em Pesquisar usando JavaScript")
        except Exception as e:
            print(f"Erro ao clicar no botão Pesquisar: {e}")
            # Tenta um seletor alternativo
            try:
                pesquisar = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/body/div/perdcomp-root/div/div[2]/perdcomp-template-documento/div/perdcomp-informar-credito/perdcomp-tabs/perdcomp-tab[1]/div/perdcomp-pgim-unificado-identificar-credito/div/perdcomp-pesquisa-pagamento/perdcomp-modal-prime[1]/p-dialog/div/div/div[2]/div/div[1]/div[5]/div/button'))
                )
                driver.execute_script("arguments[0].click();", pesquisar)
                print("Clicado em Pesquisar usando seletor alternativo")
            except Exception as e2:
                print(f"Erro ao clicar no botão Pesquisar com seletor alternativo: {e2}")
                return None

        # Adiciona espera após clicar em pesquisar
        time.sleep(2)

        # Verifica o tipo de competência para aplicar a verificação correta
        resultado_verificacao = False
        if eh_13_salario:
            print("Verificando datas para 13º salário (buscando períodos de dezembro)")
            resultado_verificacao = verificar_data_arrecadacao_13(driver)
        else:
            print("Verificando datas para competência normal (evitando períodos de dezembro)")
            resultado_verificacao = verificar_data_arrecadacao_janeiro(driver)

        # Aguarda um tempo para o sistema processar a seleção
        time.sleep(2)
        
        # Tenta expandir documentos após a verificação de datas
        analise_docs = expandir_documentos(driver, eh_13_salario)
        if analise_docs:
            return analise_docs
        else:
            print("Não foi possível expandir os documentos após verificação de datas.")
            return None
            
    except Exception as e:
        print(f"Erro ao informar crédito: {str(e)}")
    
    # Se chegou aqui, é porque não conseguiu realizar o fluxo normal
    # Vamos verificar se já existem documentos na tela que possam ser analisados
    try:
        print("Tentando analisar documentos já presentes na tela...")
        eh_13_salario = competencia_str.startswith("13/")
        return expandir_documentos(driver, eh_13_salario)
    except Exception as e:
        print(f"Erro na análise de documentos já presentes: {str(e)}")
        return None

def expandir_documentos(driver, eh_13_salario=False):
    """
    Expande todas as linhas e analisa os códigos de receita por número de documento.
    Identifica tanto códigos com final -01 (competência normal) quanto -21 (13º salário).
    
    Args:
        driver: Instância do WebDriver
        eh_13_salario: Flag que indica se estamos buscando documentos de 13º salário
        
    Returns:
        Dicionário com os documentos e seus códigos encontrados
    """
    try:
        print(f"\n==== EXPANDINDO DOCUMENTOS PARA {'13º SALÁRIO' if eh_13_salario else 'COMPETÊNCIA NORMAL'} ====")
        # Aguarda carregamento inicial
        time.sleep(1)
        
        # Verifica se há botões para expandir
        try:
            botoes_expandir = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "i.icon-plus-square-o.sc-clickable"))
            )
            
            print(f"Encontrados {len(botoes_expandir)} botões para expandir")
            
            # Expande cada linha
            for i, botao in enumerate(botoes_expandir, 1):
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", botao)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", botao)
                    print(f"Expandido item {i} de {len(botoes_expandir)}")
                    time.sleep(1)
                except Exception as e:
                    print(f"Erro ao expandir item {i}: {str(e)}")
                    continue
        except Exception as e:
            print(f"Aviso: Não foi possível encontrar botões para expandir: {e}")
            print("Tentando analisar mesmo sem expandir...")

        # Aguarda expansão completa
        time.sleep(1)
        
        analise_documentos = {}
        
        # Localiza todas as linhas de documentos - MELHORADOS OS SELETORES
        linhas_documentos = driver.find_elements(By.CSS_SELECTOR, ".row-pagamento")
        print(f"Encontradas {len(linhas_documentos)} linhas de pagamento")
        
        # Para cada linha, procura o número do documento (padrão XX.XX.XXXXX.XXXXXXX-X)
        for linha in linhas_documentos:
            try:
                # Primeiro, vamos procurar especificamente por links que contêm o número do documento
                # O número do documento tem formato específico: XX.XX.XXXXX.XXXXXXX-X
                links = linha.find_elements(By.TAG_NAME, "a")
                
                num_doc = None
                for link in links:
                    texto = link.text.strip()
                    # Procura por padrão de documento (XX.XX.XXXXX.XXXXXXX-X)
                    if len(texto) > 10 and "." in texto and "-" in texto:
                        # Verifica se tem formato de documento e não de CNPJ
                        if texto.count(".") == 3 and texto.count("-") == 1:
                            num_doc = texto
                            print(f"Identificado documento: {num_doc}")
                            break
                
                if not num_doc:
                    continue
                
                # Verifica a data de arrecadação deste documento para confirmar se é 13º ou competência normal
                datas_arrecadacao = linha.find_elements(By.XPATH, './/div[contains(@class, "gs-col3")]/a')
                if datas_arrecadacao:
                    ultima_data_texto = datas_arrecadacao[-1].text.strip()
                    eh_dezembro = "/12/" in ultima_data_texto
                    
                    # Se estivermos procurando 13º e a data não for de dezembro, ou vice-versa, pula este documento
                    if eh_13_salario != eh_dezembro:
                        print(f"Documento {num_doc} com data {ultima_data_texto} não corresponde ao tipo de busca {'13º' if eh_13_salario else 'normal'}. Pulando...")
                        continue
                    
                    print(f"Documento {num_doc} com data {ultima_data_texto} identificado como {'13º SALÁRIO' if eh_dezembro else 'competência normal'}")
                
                # Agora procura pelos detalhes dentro da linha expandida
                # Se a linha foi expandida, ela deve conter os códigos de receita
                detalhes = linha.find_elements(By.CSS_SELECTOR, ".row-detalhamento")
                
                codigos = []
                for detalhe in detalhes:
                    try:
                        # Em cada linha de detalhe, o código aparece em uma célula específica
                        celulas = detalhe.find_elements(By.CSS_SELECTOR, "div.gs-col2")
                        for celula in celulas:
                            texto_celula = celula.text.strip()
                            # Verifica se o texto tem formato de código (XXXX-XX)
                            if len(texto_celula) == 7 and texto_celula[4:5] == "-":
                                # Identifica corretamente códigos de 13º (-21) e competência normal (-01)
                                eh_codigo_13 = texto_celula.endswith("-21") 
                                eh_codigo_normal = texto_celula.endswith("-01")
                                
                                # Só adiciona os códigos do tipo correto de acordo com a flag eh_13_salario
                                if (eh_13_salario and eh_codigo_13) or (not eh_13_salario and eh_codigo_normal):
                                    codigos.append(texto_celula)
                                    print(f"Código compatível encontrado: {texto_celula}")
                                else:
                                    print(f"Código incompatível com o tipo de busca: {texto_celula}. Ignorando...")
                                    
                    except Exception as e:
                        print(f"Erro ao processar detalhe: {e}")
                        continue
                
                if codigos:
                    analise_documentos[num_doc] = sorted(list(set(codigos)))
                    print(f"Adicionado documento {num_doc} com {len(codigos)} códigos compatíveis.")
                else:
                    print(f"Documento {num_doc} não possui códigos compatíveis com o tipo {'13º' if eh_13_salario else 'normal'}. Ignorando.")
                    
            except Exception as e:
                print(f"Erro ao processar linha: {e}")
                continue
        
        # Imprime resultados simplificados
        print("\n==== DOCUMENTOS E CÓDIGOS ENCONTRADOS ====")
        total_documentos = len(analise_documentos)
        if total_documentos == 0:
            print(f"⚠️ Nenhum documento de {'13º salário' if eh_13_salario else 'competência normal'} encontrado!")
            return {}
            
        print(f"Total de documentos de {'13º salário' if eh_13_salario else 'competência normal'}: {total_documentos}")
        
        for doc, codigos in analise_documentos.items():
            print(f"\nDocumento: {doc}")
            print(f"Total de códigos: {len(codigos)}")
            print(f"Códigos: {', '.join(codigos)}")
            
        return analise_documentos
        
    except Exception as e:
        print(f"Erro na análise: {str(e)}")
        return None

def verificar_codigos_validos(codigos, row_data):
    """
    Verifica se há códigos válidos (existentes e não-zerados) na planilha para um documento.
    
    Args:
        codigos: Lista de códigos encontrados no documento
        row_data: Linha do DataFrame contendo os valores para cada código
        
    Returns:
        Tuple(bool, dict): (Tem códigos válidos?, {Detalhes dos códigos})
    """
    print(f"\n==== VERIFICANDO VALIDADE DOS CÓDIGOS ====")
    codigos_validos = False
    resultados = {"total": len(codigos), "validos": 0, "invalidos": 0, "detalhes": {}}
    
    for codigo in codigos:
        # Converte o código para o formato da planilha se for código 13º (-21)
        codigo_planilha = codigo
        if codigo.endswith("-21"):
            codigo_planilha = codigo[:-2] + "01"
            print(f"Convertendo código 13º {codigo} para formato da planilha: {codigo_planilha}")
        
        # Verifica se o código existe na planilha
        if codigo_planilha not in row_data.index:
            status = "Não existe na planilha"
            resultados["invalidos"] += 1
            resultados["detalhes"][codigo] = status
            print(f"❌ Código {codigo} ({codigo_planilha}): {status}")
            continue
        
        # Verifica se o valor não é nulo/vazio
        valor = row_data[codigo_planilha]
        if pd.isna(valor) or str(valor).strip() == "" or float(str(valor).replace(",", ".")) == 0:
            status = "Zerado ou nulo na planilha"
            resultados["invalidos"] += 1
            resultados["detalhes"][codigo] = status
            print(f"❌ Código {codigo} ({codigo_planilha}): {status}")
            continue
        
        # Se chegou aqui, o código é válido
        valor_str = str(valor).replace(".", ",")
        status = f"Válido - Valor: {valor_str}"
        resultados["validos"] += 1
        resultados["detalhes"][codigo] = status
        codigos_validos = True
        print(f"✅ Código {codigo} ({codigo_planilha}): {status}")
    
    # Resumo
    print(f"\nResumo da análise de códigos:")
    print(f"Total de códigos: {resultados['total']}")
    print(f"Códigos válidos: {resultados['validos']}")
    print(f"Códigos inválidos: {resultados['invalidos']}")
    print(f"O documento {'TEM' if codigos_validos else 'NÃO TEM'} códigos válidos para processamento")
    
    return codigos_validos, resultados

def analisar_documento(analise_documentos, row_data=None):
    """
    Analisa os documentos encontrados e verifica:
    1. Quantos documentos existem
    2. Quais códigos estão em cada documento
    3. Se algum código se repete nos documentos
    4. Se o número dos documentos se repetem
    5. Se fornecido row_data, verifica quais documentos têm códigos válidos
    
    Retorna:
    - None, se houver repetições (indicando que deve encerrar)
    - Um dicionário com a análise, se tudo estiver correto
    """
    if not analise_documentos:
        print("Não foram encontrados documentos para análise")
        return None
    
    qtd_documentos = len(analise_documentos)
    print(f"\n==== ANÁLISE DE DOCUMENTOS ====")
    print(f"Total de documentos encontrados: {qtd_documentos}")
    
    # Verifica se há documentos repetidos
    documentos_unicos = set(analise_documentos.keys())
    if len(documentos_unicos) < qtd_documentos:
        print("ERRO: Foram encontrados documentos com números repetidos")
        return None
    
    # Verifica todos os códigos e documentos
    todos_codigos = []
    resultado_analise = {
        "quantidade": qtd_documentos,
        "documentos": {},
        "codigos_por_documento": {},
        "documentos_validos": True,
        "status_documentos": {}  # Novo campo para rastrear status de cada documento
    }
    
    for doc, codigos in analise_documentos.items():
        resultado_analise["documentos"][doc] = codigos
        resultado_analise["codigos_por_documento"][doc] = len(codigos)
        todos_codigos.extend(codigos)
        
        print(f"\nDocumento: {doc}")
        print(f"Total de códigos: {len(codigos)}")
        print(f"Códigos: {', '.join(codigos)}")
        
        # Se temos dados da planilha, verificamos se os códigos são válidos
        if row_data is not None:
            tem_codigos_validos, detalhes_codigos = verificar_codigos_validos(codigos, row_data)
            resultado_analise["status_documentos"][doc] = {
                "valido": tem_codigos_validos,
                "detalhes": detalhes_codigos
            }
            
            if tem_codigos_validos:
                print(f"✅ Documento {doc} possui {detalhes_codigos['validos']} código(s) válido(s) e será processado")
            else:
                print(f"❌ Documento {doc} não possui códigos válidos e será ignorado")
    
    # Verifica códigos repetidos
    codigo_contagem = {}
    for codigo in todos_codigos:
        if codigo in codigo_contagem:
            codigo_contagem[codigo] += 1
        else:
            codigo_contagem[codigo] = 1
    
    codigos_repetidos = {codigo: contagem for codigo, contagem in codigo_contagem.items() if contagem > 1}
    
    if codigos_repetidos:
        print("\nERRO: Foram encontrados códigos repetidos entre os documentos")
        print("Códigos repetidos:")
        for codigo, contagem in codigos_repetidos.items():
            print(f"  - {codigo}: aparece {contagem} vezes")
        
        resultado_analise["documentos_validos"] = False
        return None
    
    print("\nANÁLISE CONCLUÍDA: Todos os documentos e códigos são únicos")
    
    # Adiciona informação de documentos válidos para processamento
    if row_data is not None:
        documentos_validos = [doc for doc, status in resultado_analise["status_documentos"].items() if status["valido"]]
        documentos_invalidos = [doc for doc, status in resultado_analise["status_documentos"].items() if not status["valido"]]
        
        resultado_analise["total_documentos_validos"] = len(documentos_validos)
        resultado_analise["total_documentos_invalidos"] = len(documentos_invalidos)
        
        print(f"\nDocumentos válidos para processamento: {len(documentos_validos)} de {qtd_documentos}")
        print(f"Documentos que serão ignorados: {len(documentos_invalidos)} de {qtd_documentos}")
    
    return resultado_analise

def selecionar_documento(driver, num_documento):
    """
    Seleciona um documento específico clicando no seu número.
    
    Args:
        driver: Instância do WebDriver
        num_documento: Número do documento a ser selecionado (formato XX.XX.XXXXX.XXXXXXX-X)
        
    Returns:
        True se o documento foi selecionado com sucesso, False caso contrário
    """
    try:
        print(f"\n==== SELECIONANDO DOCUMENTO {num_documento} ====")
        
        # Procura por elementos que contenham o número do documento
        xpath_doc = f"//a[contains(text(), '{num_documento}')]"
        
        # Aguarda o elemento ficar visível e clicável
        elemento_documento = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath_doc))
        )
        elemento_documento.click()
        time.sleep(1)
        
        # Se chegou até aqui, considera que a seleção foi bem-sucedida, mas com ressalvas
        print("Documento possivelmente selecionado, continuando o fluxo...")
        return True
        
    except Exception as e:
        print(f"Erro ao selecionar documento {num_documento}: {str(e)}")
        return False

def preencher_dados(driver, row_data, codigos_documento):
    """
    Preenche os dados de restituição para cada código encontrado no documento.
    IMPORTANTE: Na planilha, todos os códigos terminam com -01, independente 
    de ser 13º salário ou não. Para códigos de 13º salário (-21), será feita 
    a conversão automática para buscar o valor na planilha.
    
    Args:
        driver: Instância do WebDriver
        row_data: Linha do DataFrame contendo os valores para cada código
        codigos_documento: Lista de códigos encontrados no documento atual
        
    Returns:
        Tuple(bool, bool): (Preenchimento bem sucedido, Tem erro de valor maior que disponível)
    """
    try:
        # Separa os códigos por tipo para melhor visualização no log
        codigos_01 = [c for c in codigos_documento if c.endswith("-01")]
        codigos_21 = [c for c in codigos_documento if c.endswith("-21")]
        
        print(f"\n==== PREENCHENDO DADOS PARA {len(codigos_documento)} CÓDIGOS ====")
        if codigos_01:
            print(f"Códigos normais (-01): {', '.join(codigos_01)}")
        if codigos_21:
            print(f"Códigos 13º salário (-21): {', '.join(codigos_21)}")
            print("NOTA: Para códigos de 13º (-21), serão buscados valores usando o código equivalente com final -01 na planilha")
        
        try:
            botoes_continuar = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div/perdcomp-root/div/div[2]/perdcomp-template-documento/perdcomp-barra-botoes/div/div[2]/button")
                )
            )
            time.sleep(1)
            botoes_continuar.click()

        except Exception as e:
            print(f"Erro ao clicar em Continuar: {str(e)}")
            return False, False

        elementos_codigo = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span#tooltip"))
        )
        
        print(f"Encontrados {len(elementos_codigo)} elementos de código na página")
        
        # Flag para controlar se encontramos erro de valor maior que disponível
        erro_valor_maior = False
        
        # Para cada código no site, verifica se corresponde a um dos códigos que precisamos preencher
        for elemento_codigo in elementos_codigo:
            try:
                # Obtém o texto do código do elemento
                codigo_site = elemento_codigo.text.strip()
                print(f"Analisando código na página: {codigo_site}")
                
                # Verifica se este código está na nossa lista de códigos para preencher
                if codigo_site not in codigos_documento:
                    print(f"Código {codigo_site} não está na lista de códigos para este documento. Pulando...")
                    continue
                
                # Converte o código para o formato da planilha se for código 13º (-21)
                codigo_planilha = codigo_site
                if codigo_site.endswith("-21"):
                    codigo_planilha = codigo_site[:-2] + "01"
                    print(f"Convertendo código 13º {codigo_site} para formato da planilha: {codigo_planilha}")
                
                # Verifica se temos o valor para este código na planilha
                if codigo_planilha not in row_data.index:
                    print(f"Código {codigo_planilha} não encontrado na planilha! Pulando...")
                    continue
                
                # Obtém o valor a ser preenchido
                valor_str = str(row_data[codigo_planilha])
                
                # Verifica se o valor não é nulo/vazio
                if pd.isna(row_data[codigo_planilha]) or valor_str.strip() == "":
                    print(f"Nenhum valor definido na planilha para o código {codigo_planilha}. Pulando...")
                    continue
                
                # Converte para o formato esperado pelo site (vírgula como separador decimal)
                valor = str(valor_str).replace(".", ",")
                print(f"Valor a preencher para {codigo_site} (usando {codigo_planilha} da planilha): {valor}")
                
                elemento_pai = elemento_codigo
                for _ in range(10):  # limite de segurança para não entrar em loop infinito
                    elemento_pai = elemento_pai.find_element(By.XPATH, "./..")
                    if "gs-row" in elemento_pai.get_attribute("class"):
                        break
                
                # Agora procura o input de valor dentro desta linha
                campo_input = elemento_pai.find_element(By.CSS_SELECTOR, "input#valorUtilizadoTxt")
                
                # Rola a tela até o elemento para garantir que ele está visível
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", campo_input)
                
                # Apagar com ctrl + a 
                campo_input.send_keys(Keys.CONTROL + "a")
                # Apagar com backspace
                campo_input.send_keys(Keys.BACKSPACE)
                campo_input.send_keys(valor)
                print(f"Preenchido valor {valor} para o código {codigo_site}")
                
                # Pressiona Tab para confirmar o valor e ir para o próximo campo
                campo_input.send_keys(Keys.TAB)
                
                # Verifica se há mensagem de erro após preencher (valor maior que disponível)
                time.sleep(0.5)  # Espera um momento para a mensagem aparecer
                try:
                    mensagem_erro = elemento_pai.find_element(By.CSS_SELECTOR, "div.validator-message div")
                    if mensagem_erro and "Valor informado maior do que o valor disponível" in mensagem_erro.text:
                        print(f"⚠️ ALERTA: Valor {valor} para código {codigo_site} é maior que o valor disponível!")
                        erro_valor_maior = True
                        # Não interrompemos, continuamos preenchendo todos os valores
                except:
                    # Sem mensagem de erro para este campo, continue normalmente
                    pass
                
            except Exception as e:
                print(f"Erro ao processar código {codigo_site}: {str(e)}")
                continue
        
        print("Dados preenchidos com sucesso!")

        # Independentemente de termos um erro ou não, sempre clicamos em prosseguir
        # para avançar para a tela de dados bancários
        try:
            prosseguir2 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div/perdcomp-root/div/div[2]/perdcomp-template-documento/perdcomp-barra-botoes/div/div[2]/button'))
            )
            
            # Rola até o botão para garantir que ele está visível
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", prosseguir2)
            time.sleep(1)
            
            print("Clicando em Prosseguir para avançar à tela de dados bancários...")
            prosseguir2.click()
            time.sleep(2)  # Aguarda a navegação para a próxima tela
            
            # Se encontramos erro de valor maior que disponível, registramos o fato
            # mas mesmo assim continuamos o fluxo (só mudaremos o comportamento depois)
            if erro_valor_maior:
                print("⚠️ ATENÇÃO: Foi detectado erro de valor maior que disponível.")
                print("Prosseguindo para dados bancários, depois salvaremos em vez de enviar.")
            
            return True, erro_valor_maior
            
        except Exception as e:
            print(f"Erro ao clicar no botão Prosseguir: {str(e)}")
            # Mesmo com erro, tentamos continuar o processo
            return True, erro_valor_maior
    
    except Exception as e:
        print(f"Erro ao preencher dados: {str(e)}")
        return False, False

def salvar_documento(driver):
    """
    Salva o documento atual sem prosseguir, utilizado quando
    há erro de valor maior que disponível.
    
    Args:
        driver: Instância do WebDriver
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        print("\n==== SALVANDO DOCUMENTO (SEM PROSSEGUIR) ====")
        
        # Procura pelo botão Salvar
        botao_salvar = None
        
        # Tenta diferentes seletores para encontrar o botão Salvar
        seletores_salvar = [
            "button[name='btnSalvar']", 
            "button:contains('Salvar')",
            "//button[text()='Salvar']",
            "//button[contains(text(), 'Salvar')]"
        ]
        
        for seletor in seletores_salvar:
            try:
                if seletor.startswith("//"):
                    botao_salvar = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, seletor))
                    )
                else:
                    botao_salvar = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, seletor))
                    )
                if botao_salvar:
                    print(f"Botão Salvar encontrado com seletor: {seletor}")
                    break
            except:
                continue
                
        if not botao_salvar:
            print("⚠️ Botão Salvar não encontrado! Tentando localizá-lo com JavaScript...")
            try:
                # Tenta localizar o botão usando JavaScript
                botao_salvar = driver.execute_script("return document.querySelector('button[name=\"btnSalvar\"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Salvar'))")
                if botao_salvar:
                    print("Botão Salvar encontrado via JavaScript!")
                else:
                    print("❌ Não foi possível encontrar o botão Salvar!")
                    return False
            except Exception as js_error:
                print(f"Erro ao tentar localizar botão via JavaScript: {js_error}")
                return False
        
        # Rola até o botão e clica nele
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", botao_salvar)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", botao_salvar)
        
        print("Documento salvo com sucesso!")
        
        # Aguarda um momento para finalização do salvamento
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"Erro ao salvar documento: {str(e)}")
        return False

def dados_bancarios(driver, cpf_responsavel, banco, agencia, conta, dv, erro_valor_maior=False):
    """
    Preenche os dados bancários necessários para a restituição.
    Simula digitação humana para todos os campos.
    
    Args:
        driver: Instância do WebDriver
        cpf_responsavel: CPF do responsável para receber a restituição
        banco: Código do banco (padrão: 001 - Banco do Brasil)
        agencia: Número da agência
        conta: Número da conta
        dv: Dígito verificador
        erro_valor_maior: Flag indicando se há erro de valor maior que disponível
    
    Returns:
        True se os dados foram preenchidos com sucesso, False caso contrário
    """
    try:
        print("\n==== PREENCHENDO DADOS BANCÁRIOS ====")
        
        # Se não há erro de valor maior, prossegue para a tela de dados bancários
        # Caso contrário, assume que já estamos na tela correta
        if not erro_valor_maior:
            prosseguir = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div/perdcomp-root/div/div[2]/perdcomp-template-documento/perdcomp-barra-botoes/div/div[2]/button'))
            )
            print("Clicando no botão de prosseguir para tela de dados bancários...")
            prosseguir.click()
            time.sleep(2)  # Espera para a página carregar
        
        # Cria a action chain para simular digitação humana
        action = ActionChains(driver)
        
        # Função auxiliar para simular digitação humana em qualquer campo
        def digitar_como_humano(campo, texto, destacar=True):
            if not texto:
                print(f"Campo vazio, pulando...")
                return True
                
            try:                
                # Rola até o elemento e clica para garantir foco
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", campo)
                time.sleep(0.5)
                campo.click()

                # Digita cada caractere com pausas aleatórias para simular digitação humana
                for i, caractere in enumerate(texto):
                    # Pausa aleatória entre digitações (100-300ms)
                    pausa = random.uniform(0.1, 0.3)
                    time.sleep(pausa)
                    
                    # Envia o caractere atual
                    action.send_keys(caractere).perform()
                    
                    # Pausa mais longa a cada 3 caracteres (simula ritmo humano)
                    if i > 0 and i % 3 == 0:
                        time.sleep(random.uniform(0.1, 0.4))
                        
                # Pressiona Tab para finalizar a entrada (confirma o valor)
                time.sleep(0.5)
                action.send_keys(Keys.TAB).perform()
                return True
                
            except Exception as e:
                print(f"Erro ao digitar texto '{texto}': {str(e)}")
                return False

        # Insere o CPF do responsável simulando digitação humana
        try:
            print(f"Preenchendo CPF do responsável: {cpf_responsavel}")
            
            # Formata o CPF (removendo pontos e traço)
            cpf_limpo = cpf_responsavel.replace('.', '').replace('-', '')
            
            # Lista de possíveis seletores para o campo de CPF
            seletores_cpf = [
                "p-inputmask[formcontrolname='cpfResponsavelPreenchimento'] input", 
                "input.p-inputmask",
                "input[placeholder='999.999.999-99']",
                "#cpfResponsavelPreenchimento"
            ]
            
            cpf_input = None
            # Tenta cada seletor até encontrar o campo
            for seletor in seletores_cpf:
                try:
                    print(f"Tentando localizar campo de CPF com seletor: {seletor}")
                    cpf_input = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, seletor))
                    )
                    if cpf_input:
                        print(f"Campo de CPF encontrado com seletor: {seletor}")
                        break
                except:
                    continue
            
            if not cpf_input:
                # Última tentativa com XPath mais específico baseado no HTML fornecido
                try:
                    cpf_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//p-inputmask[@formcontrolname='cpfResponsavelPreenchimento']/input"))
                    )
                    print("Campo de CPF encontrado pelo XPath específico")
                except:
                    print("⚠️ Não foi possível encontrar o campo de CPF. Continuando mesmo assim...")
                    
            if cpf_input:
                digitar_como_humano(cpf_input, cpf_limpo)
                print("CPF preenchido com sucesso usando simulação de digitação humana!")
            else:
                print("Campo de CPF não encontrado para preenchimento.")
                
        except Exception as e:
            print(f"Erro ao preencher CPF: {str(e)}")
            
        # Seleção do tipo de conta bancária
        try:
            print("Selecionando tipo de conta: Conta Corrente")
            tipodeconta = Select(WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tipoContaBancaria"))
            ))
            time.sleep(0.5)
            tipodeconta.select_by_visible_text("Conta Corrente")
            time.sleep(1)
        except Exception as e:
            print(f"Erro ao selecionar tipo de conta: {str(e)}")
            
        # Preenchimento do código do banco
        try:
            print(f"Preenchendo código do banco: {banco}")
            banco_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div/perdcomp-root/div/div[2]/perdcomp-template-documento/div/perdcomp-dados-gerais/form/perdcomp-fieldset[4]/div/div/div[2]/div/div[2]/div/div[2]/div[1]/p-inputmask'))
            )
            time.sleep(0.5)
            digitar_como_humano(banco_input, banco)
            print("Código do banco preenchido com sucesso!")
        except Exception as e:
            print(f"Erro ao preencher código do banco: {str(e)}")
            
        # --- Agência ---
        print(f"Preenchendo agência: {agencia}")
        agencia_input = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input#agencia"))
        )
        digitar_como_humano(agencia_input, agencia)

        # --- Conta Corrente ---
        print(f"Preenchendo conta: {conta}")
        conta_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input#numeroConta"))
        )
        digitar_como_humano(conta_input, conta)

        # --- Dígito Verificador ---
        if dv:
            print(f"Preenchendo DV: {dv}")
            dv_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input#dvConta"))
            )
            digitar_como_humano(dv_input, dv)

        # Se tem erro de valor maior, chama a função salvar em vez de prosseguir
        if erro_valor_maior:
            return salvar_documento(driver)
            
        # Caso contrário, prossegue normalmente
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Prosseguir')]"))
        ).click()
        print("Dados bancários preenchidos com sucesso!")
        return True

    except Exception as e:
        print(f"Erro nos dados bancários: {str(e)}")
        return False

def conferencia(driver, row_data, codigos_documento, erro_valor_maior=False):
    """
    Realiza o encerramento do processo verificando se os valores correspondem.
    Preenche o campo "Crédito Original na Data de Entrega" quando os valores conferem.
    IMPORTANTE: Os valores devem ser EXATAMENTE iguais, sem tolerância para arredondamentos.
    
    Args:
        driver: Instância do WebDriver
        row_data: Linha do DataFrame contendo os valores para cada código
        codigos_documento: Lista de códigos encontrados no documento atual
        erro_valor_maior: Flag que indica se houve erro de valor maior que disponível
        
    Returns:
        True se o encerramento foi bem-sucedido ou se decidiu prosseguir mesmo com erro, False caso contrário
    """
    try:
        print("\n==== REALIZANDO ENCERRAMENTO DO DOCUMENTO ====")
        
        # Se já sabemos que há erro de valor maior, não fazemos verificação
        # e simplesmente prosseguimos para o próximo passo
        if erro_valor_maior:
            print("⚠️ Detectado erro de 'valor maior que disponível' previamente.")
            print("Avançando para próxima tela sem verificar valores nem preencher crédito original.")
            
            # Clica no botão de prosseguir para avançar para a próxima tela
            try:
                prosseguir = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Prosseguir')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", prosseguir)
                time.sleep(1)
                print("Clicando em Prosseguir para continuar com o fluxo...")
                prosseguir.click()
                time.sleep(2)
                return True
            except Exception as e:
                print(f"Erro ao clicar em Prosseguir após detecção de erro de valor maior: {str(e)}")
                return False
        
        # Fluxo normal quando não há erro de valor maior
        # Calcula o total esperado da planilha para os códigos deste documento
        total_esperado = 0
        for codigo in codigos_documento:
            # Converte o código para o formato da planilha se for código 13º (-21)
            codigo_planilha = codigo
            if codigo.endswith("-21"):
                codigo_planilha = codigo[:-2] + "01"
                print(f"Convertendo código 13º {codigo} para formato da planilha: {codigo_planilha}")
            
            if codigo_planilha in row_data.index and not pd.isna(row_data[codigo_planilha]):
                valor_str = str(row_data[codigo_planilha]).replace(',', '.').strip()
                try:
                    valor = float(valor_str)
                    total_esperado += valor
                    print(f"Código {codigo} (usando {codigo_planilha} da planilha): {valor}")
                except ValueError:
                    print(f"Valor inválido para código {codigo_planilha}: '{valor_str}'")
        
        # Formatação do valor esperado com 2 casas decimais
        total_esperado_formatado = f"{total_esperado:.2f}".replace('.', ',')
        print(f"Total esperado (planilha): {total_esperado_formatado}")
        
        # Localiza o campo de valor original do crédito na página
        try:
            valor_credito_elemento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "valorOriginalCreditoInicial"))
            )
            
            # Obtém o valor do elemento (pode estar no atributo value ou no texto)
            valor_site = valor_credito_elemento.get_attribute("value") or valor_credito_elemento.text
            
            # Remove possíveis formatações (R$, espaços, etc)
            valor_site = valor_site.replace('R$', '').strip()
            print(f"Valor encontrado no site: {valor_site}")
            
            # Convertendo para números para comparação precisa
            # Garante que ambos os valores tenham exatamente 2 casas decimais para comparação
            valor_site_numerico = round(float(valor_site.replace('.', '').replace(',', '.')), 2)
            
            # Arredonda o valor esperado também para 2 casas decimais
            valor_esperado_numerico = round(total_esperado, 2)
            
            # Comparação exata sem tolerância para arredondamentos
            if valor_site_numerico == valor_esperado_numerico:
                print(f"✅ VALORES CONFEREM EXATAMENTE: Site ({valor_site}) = Planilha ({total_esperado_formatado})")
                
                # Localiza e preenche o campo "Crédito Original na Data de Entrega"
                try:
                    # Localiza o campo pelo ID
                    campo_credito_entrega = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "creditoOriginalDataEntrega"))
                    )
                    
                    # Rola a tela até o elemento para garantir que ele está visível
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", campo_credito_entrega)
                    time.sleep(0.5)
                    
                    # Limpa o campo e insere o valor EXATO da planilha
                    campo_credito_entrega.send_keys(Keys.CONTROL + "a")
                    campo_credito_entrega.send_keys(Keys.BACKSPACE)
                    campo_credito_entrega.send_keys(total_esperado_formatado)
                    print(f"Preenchido campo 'Crédito Original na Data de Entrega' com o valor {total_esperado_formatado}")
                    
                    # Dá foco a outro elemento para confirmar o valor
                    campo_credito_entrega.send_keys(Keys.TAB)
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"ERRO ao preencher campo 'Crédito Original na Data de Entrega': {str(e)}")
                    return False
                
                # Se tudo estiver correto, podemos prosseguir com o envio do documento
                print("Encerramento bem-sucedido! Documento pronto para envio.")
                return True
            else:
                print(f"❌ VALORES DIVERGEM: Site ({valor_site}) ≠ Planilha ({total_esperado_formatado})")
                print(f"Valor site (numérico): {valor_site_numerico}")
                print(f"Valor planilha (numérico): {valor_esperado_numerico}")
                print("Exigimos igualdade exata sem arredondamentos. Verifique os valores e tente novamente.")
                return False
                
        except Exception as e:
            print(f"Erro ao localizar ou ler o valor do crédito no site: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Erro no processo de encerramento: {str(e)}")
        return False

def enviar_documento(driver):
    """
    Verifica se o documento está apto para envio e finaliza o processo de envio.
    
    Args:
        driver: Instância do WebDriver
        
    Returns:
        True se o documento foi enviado com sucesso, False caso contrário
    """
    try:
        print("\n==== VERIFICANDO SE DOCUMENTO ESTÁ APTO PARA ENVIO ====")
        
        # Aguarda o carregamento da página de envio
        time.sleep(2)
        
        # Verifica se há mensagem positiva indicando que o documento está apto
        try:
            # Primeiro, tenta encontrar a mensagem de sucesso
            mensagem_apto = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'O Documento está apto para envio') or contains(@class, 'info')]"))
            )
            
            print("✅ Documento está apto para envio!")
            
            # Clica no botão de enviar/prosseguir
            botao_enviar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Prosseguir') or contains(text(), 'Enviar')]"))
            )
            
            # Rola até o botão para garantir que está visível
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", botao_enviar)
            time.sleep(1)
            
            print("Clicando no botão para enviar documento...")
            botao_enviar.click()
            
            # Aguarda para ver se aparece algum popup de confirmação
            time.sleep(2)
            
            # Verifica se há algum popup de confirmação final
            try:
                botao_confirmar = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sim') or contains(text(), 'Confirmar') or contains(text(), 'OK')]"))
                )
                print("Confirmando envio final...")
                botao_confirmar.click()
                time.sleep(2)
            except:
                print("Nenhum popup de confirmação encontrado, o documento provavelmente já foi enviado.")
            
            # Aguarda a conclusão do envio
            time.sleep(3)
            
            print("✅ Documento enviado com sucesso!")
            return True
            
        except Exception as e:
            # Se não encontrou mensagem de apto, verifica se há mensagem de erro
            try:
                mensagem_erro = driver.find_element(By.XPATH, "//div[contains(text(), 'O Documento não está apto para envio')]")
                erro_texto = mensagem_erro.text
                print(f"❌ {erro_texto}")
                print("Documento não pode ser enviado devido a erros. Verifique os problemas e tente novamente.")
                return False
            except:
                print(f"Não foi possível determinar se o documento está apto para envio: {e}")
                return False
    
    except Exception as e:
        print(f"Erro no processo de envio do documento: {str(e)}")
        return False

def main():
    df = pd.read_excel('comp.xlsx')
    
    df['COMP_STR'] = df['COMP'].astype(str).str.strip()
    df['IS_13'] = df['COMP_STR'].str.startswith("13/")
    df['COMP_DT'] = pd.to_datetime(
        df.loc[~df['IS_13'], 'COMP_STR'],
        format='%m/%Y',
        errors='coerce'
    )
    
    colunas_codigos = [col for col in df.columns if isinstance(col, str) and len(col) == 7 and col[4:5] == "-"]
    
    # Solicita o CPF do responsável via input
    cpf_responsavel = '02621314201'
    
    # Validação básica do CPF
    cpf_responsavel = cpf_responsavel.strip().replace('.', '').replace('-', '')
    if len(cpf_responsavel) != 11 or not cpf_responsavel.isdigit():
        print("CPF inválido! O CPF deve conter 11 dígitos numéricos.")
        return
    
    print(f"CPF do responsável: {cpf_responsavel}")
    
    banco = "033"
    agencia = "0400"
    conta = "0300"
    dv = "20"

    driver = iniciar_selenium()
    
    # URL da página inicial para retornar após cada competência
    url_inicial = "https://www3.cav.receita.fazenda.gov.br/perdcomp-web/#/documento/identificacao?reset=true"
    
    for idx, row in df.iterrows():
        comp_str = row['COMP_STR']
        print(f"\nPROCESSANDO COMPETÊNCIA: {comp_str}")
        
        # Para controlar os documentos disponíveis
        documentos_processados = []
        total_documentos = 0
        documentos_disponiveis = []
        parte_atual = 1
        
        # Garantir que estamos na página inicial ao iniciar cada competência
        driver.get(url_inicial)
        time.sleep(2)  # Espera para carregamento da página
        
        # Criar primeira parte para descobrir quantos documentos existem
        apelido = f"INSS - {comp_str}"
        print(f"\nCRIANDO DOCUMENTO: {apelido}")
        
        try:
            indentificar_documento(driver, apelido)
        except Exception as e:
            print(f"Erro ao criar documento: {e}")
            continue
        
        # Na primeira parte, descobre quantos documentos existem no total
        analise_docs = informar_credito(driver, comp_str)
        if not analise_docs:
            print("Nenhum documento encontrado para esta competência. Pulando para próxima.")
            # Retorna à página inicial antes de pular para próxima competência
            driver.get(url_inicial)
            continue
        
        # Agora passar os dados da planilha para verificar quais documentos têm códigos válidos
        resultado_analise = analisar_documento(analise_docs, row[colunas_codigos])
        if not resultado_analise:
            print("Erro na análise. Pulando para próxima competência.")
            # Retorna à página inicial antes de pular para próxima competência
            driver.get(url_inicial)
            continue
        
        # Obtém apenas os documentos com códigos válidos (existentes e não zerados na planilha)
        documentos_validos = [doc for doc, status in resultado_analise["status_documentos"].items() if status["valido"]]
        
        if not documentos_validos:
            print(f"Nenhum documento com códigos válidos para a competência {comp_str}. Pulando para próxima.")
            driver.get(url_inicial)
            continue
        
        # Atualiza a lista de documentos disponíveis apenas com os válidos
        documentos_disponiveis = documentos_validos
        total_documentos = len(documentos_disponiveis)
        
        print(f"Total de documentos válidos para competência {comp_str}: {total_documentos}")
        
        # Processa a primeira parte
        if documentos_disponiveis:
            num_doc = documentos_disponiveis[0]
            codigos_doc = resultado_analise["documentos"][num_doc]
            
            if selecionar_documento(driver, num_doc):
                sucesso, erro_valor_maior = preencher_dados(driver, row[colunas_codigos], codigos_doc)
                
                if sucesso:
                    # Passamos erro_valor_maior para a função conferencia
                    # Se erro_valor_maior for True, a função conferencia não tenta verificar valores
                    # nem preencher o campo de crédito original, apenas prossegue
                    if conferencia(driver, row[colunas_codigos], codigos_doc, erro_valor_maior):
                        if dados_bancarios(driver, cpf_responsavel, banco, agencia, conta, dv, erro_valor_maior):
                            if not erro_valor_maior and enviar_documento(driver):
                                documentos_processados.append(num_doc)
                                print(f"Documento {num_doc} processado e {'salvo' if erro_valor_maior else 'enviado'} na parte {parte_atual}!")
                            elif erro_valor_maior:
                                documentos_processados.append(num_doc)
                                print(f"Documento {num_doc} processado e salvo na parte {parte_atual}!")
                            else:
                                print("Falha no envio do documento. Continuando para próxima competência.")
                                driver.get(url_inicial)
                                continue
                        else:
                            print("Falha no preenchimento dos dados bancários. Continuando para próxima competência.")
                            driver.get(url_inicial)
                            continue
                    else:
                        print("Falha na verificação de valores. Continuando para próxima competência.")
                        driver.get(url_inicial)
                        continue
                else:
                    print("Falha no preenchimento. Continuando para próxima competência.")
                    driver.get(url_inicial)
                    continue
            else:
                print("Falha na seleção. Continuando para próxima competência.")
                driver.get(url_inicial)
                continue
        
        # Verifica se ainda há documentos para processar
        documentos_restantes = [doc for doc in documentos_disponiveis if doc not in documentos_processados]
        
        # Se não houver mais documentos, prossegue para a próxima competência
        if not documentos_restantes:
            print(f"Todos os {total_documentos} documentos válidos da competência {comp_str} foram processados!")
            # Retorna à página inicial antes de pular para próxima competência
            driver.get(url_inicial)
            continue
            
        # Calcula quantas partes adicionais são necessárias
        partes_restantes = len(documentos_restantes)
        print(f"Serão necessárias mais {partes_restantes} partes para processar todos os documentos válidos desta competência.")
        
        # Processa as demais partes necessárias
        for doc_idx, doc_num in enumerate(documentos_restantes):
            parte_atual += 1
            
            apelido = f"INSS - {comp_str} Parte {parte_atual}"
            print(f"\nCRIANDO DOCUMENTO PARTE {parte_atual}/{total_documentos}: {apelido}")
            
            # Reinicia o fluxo para nova parte
            driver.get(url_inicial)
            time.sleep(2)  # Espera para carregamento da página
            
            try:
                indentificar_documento(driver, apelido)
            except Exception as e:
                print(f"Erro ao criar documento parte {parte_atual}: {e}")
                continue
            
            # Para as partes subsequentes, não precisamos analisar novamente
            analise_docs = informar_credito(driver, comp_str)
            if not analise_docs:
                print(f"Erro ao informar crédito na parte {parte_atual}. Tentando próxima parte.")
                continue
                
            # Confirma a análise para garantir que ainda temos acesso aos documentos
            # Não precisamos verificar a validade novamente, pois já sabemos que este documento é válido
            resultado_analise_parcial = analisar_documento(analise_docs)
            if not resultado_analise_parcial:
                print(f"Erro na análise da parte {parte_atual}. Tentando próxima parte.")
                continue
            
            # Seleciona o documento específico para esta parte
            codigos_doc = resultado_analise_parcial["documentos"].get(doc_num, [])
            
            if not codigos_doc:
                print(f"Documento {doc_num} não encontrado na parte {parte_atual}. Tentando próximo documento.")
                continue
            
            if selecionar_documento(driver, doc_num):
                sucesso, erro_valor_maior = preencher_dados(driver, row[colunas_codigos], codigos_doc)
                
                if sucesso:
                    # Passamos erro_valor_maior para conferencia - mesmo tratamento da primeira parte
                    if conferencia(driver, row[colunas_codigos], codigos_doc, erro_valor_maior):
                        if dados_bancarios(driver, cpf_responsavel, banco, agencia, conta, dv, erro_valor_maior):
                            if not erro_valor_maior and enviar_documento(driver):
                                documentos_processados.append(doc_num)
                                print(f"Documento {doc_num} processado e {'salvo' if erro_valor_maior else 'enviado'} na parte {parte_atual}!")
                            elif erro_valor_maior:
                                documentos_processados.append(doc_num)
                                print(f"Documento {doc_num} processado e salvo na parte {parte_atual}!")
                            else:
                                print(f"Falha no envio do documento na parte {parte_atual}. Tentando próxima parte.")
                                continue
                        else:
                            print(f"Falha no preenchimento dos dados bancários na parte {parte_atual}. Tentando próxima parte.")
                            continue
                    else:
                        print(f"Falha na verificação de valores da parte {parte_atual}. Tentando próxima parte.")
                        continue
                else:
                    print(f"Falha no preenchimento da parte {parte_atual}. Tentando próxima parte.")
                    continue
            else:
                print(f"Falha na seleção do documento na parte {parte_atual}. Tentando próxima parte.")
                continue
        
        print(f"Processamento da competência {comp_str} concluído! {len(documentos_processados)} de {total_documentos} documentos válidos processados.")
        
        # Após finalizar todas as partes da competência atual, retorna à página inicial para iniciar a próxima
        print(f"\nRetornando à página inicial para próxima competência...")
        driver.get(url_inicial)
        time.sleep(2)  # Espera para garantir o carregamento completo da página
        
if __name__ == "__main__":
    main()