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
    chrome_options.add_argument("user-agent=Seu User-Agent Aqui")

    service = Service('C:/Program Files/Google/Chrome/Application/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

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
    tipo_credito.select_by_visible_text("Pagamento Indevido ou a Maior")

    qualificacao = Select(WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "qualificacaoContribuinte"))
    ))
    qualificacao.select_by_visible_text("Outra Qualificação")

    detalhamento_credito = Select(WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "tipoIdentificacaoCredito"))
    ))
    detalhamento_credito.select_by_visible_text("O crédito será detalhado neste documento")

    apelido_doc = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "apelidoDocumento"))
    )
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
            # Obtém todas as datas de arrecadação dentro da linha
            datas_arrecadacao = linha.find_elements(By.XPATH, './/div[contains(@class, "gs-col3")]/a')
            if datas_arrecadacao:
                ultima_data_texto = datas_arrecadacao[-1].text.strip()  # Pega a última data
                print(f"Última data encontrada: {ultima_data_texto}")

                if "/12/" in ultima_data_texto:
                    print(f"13º salário detectado em {ultima_data_texto}. Ignorando...")
                    continue  # pula essa linha

                # Se a última data NÃO for dezembro, clica para abrir
                print(f"Abrindo período com data de arrecadação: {ultima_data_texto}")
                linha.click()
                return True
    except Exception as e:
        print(f"Erro ao verificar data de arrecadação (janeiro comum): {e}")

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
                    print(f"Abrindo período com data de arrecadação do 13º: {ultima_data_texto}")
                    linha.click()
                    return True
                else:
                    print(f"Data {ultima_data_texto} não é dezembro. Ignorando este período...")
    except Exception as e:
        print(f"Erro ao verificar data de arrecadação (13º): {e}")

    return False

def informar_credito(driver, competencia_str):
    """
    Preenche os campos de crédito de acordo com:
      - Se for '13/AAAA', fazemos uma busca de 01/01/AAAA até 31/01/AAAA e abrimos 
        somente o período cuja data de arrecadação é em dezembro.
      - Se for mês/ano comum, parseamos normalmente e abrimos o período cujo mês 
        não seja dezembro quando estivermos em janeiro.
    """
    action = ActionChains(driver)

    # Detentor: "Crédito apurado pelo próprio contribuinte"
    detentor = Select(WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "detentor"))
    ))
    detentor.select_by_visible_text("Crédito apurado pelo próprio contribuinte")

    # Clica em "Pagamento" (ou algo similar)
    selecionar_pagamento = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="page-content-wrapper"]/perdcomp-template-documento/div/perdcomp-informar-credito/perdcomp-tabs/perdcomp-tab[1]/div/perdcomp-pgim-unificado-identificar-credito/div/div/div/div/div/div/div/input'))
    )
    selecionar_pagamento.click()

    # Localizar campo de código da receita e inserir "1410"
    codigo_receita = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="codigoReceitaPesquisa"]/input'))
    )
    codigo_receita.click()
    codigo_receita.send_keys("1410")

    # --- Verifica se é 13/AAAA ou não
    if competencia_str.startswith("13/"):
        # Extrai o ano
        ano_str = competencia_str.split("/")[1]
        ano = int(ano_str)

        data_inicio = f"01/01/{ano}"
        data_fim = f"31/01/{ano}"

        # Selecionar e digitar a data no campo de início
        periodo_data_inicio = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'inicioApuracaoPesquisa'))
        )
        periodo_data_inicio.click()
        action.send_keys(data_inicio).perform()

        # Selecionar e digitar a data no campo de fim
        periodo_data_fim = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'fimApuracaoPesquisa'))
        )
        periodo_data_fim.click()
        action.send_keys(data_fim).perform()

        # Clica em pesquisar
        pesquisar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="page-content-wrapper"]/perdcomp-template-documento/div/perdcomp-informar-credito/perdcomp-tabs/perdcomp-tab[1]/div/perdcomp-pgim-unificado-identificar-credito/div/perdcomp-pesquisa-pagamento/perdcomp-modal[1]/div/div[1]/div/div[1]/div[5]/div/button'))
        )
        pesquisar.click()

        # Verifica se há datas de dezembro e abre
        if not verificar_data_arrecadacao_13(driver):
            print("Nenhum período de dezembro encontrado para 13º.")
            return

    else:
        # Mês/Ano comum -> parse normal
        # Tenta converter para datetime
        comp_dt = pd.to_datetime(competencia_str, format='%m/%Y', errors='coerce')
        if pd.isna(comp_dt):
            print(f"Competência inválida ou não parseada: {competencia_str}")
            return

        mes = comp_dt.month
        ano = comp_dt.year

        # Monta datas de início e fim
        data_inicio = f"01/{mes:02d}/{ano}"
        ultimo_dia = monthrange(ano, mes)[1]
        data_fim = f"{ultimo_dia:02d}/{mes:02d}/{ano}"

        # Selecionar e digitar a data no campo de início
        periodo_data_inicio = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'inicioApuracaoPesquisa'))
        )
        periodo_data_inicio.click()
        action.send_keys(data_inicio).perform()

        # Selecionar e digitar a data no campo de fim
        periodo_data_fim = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'fimApuracaoPesquisa'))
        )
        periodo_data_fim.click()
        action.send_keys(data_fim).perform()

        # Clica em pesquisar
        pesquisar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="page-content-wrapper"]/perdcomp-template-documento/div/perdcomp-informar-credito/perdcomp-tabs/perdcomp-tab[1]/div/perdcomp-pgim-unificado-identificar-credito/div/perdcomp-pesquisa-pagamento/perdcomp-modal[1]/div/div[1]/div/div[1]/div[5]/div/button'))
        )
        pesquisar.click()

        # Se for janeiro (mês=1), ignorar períodos de dezembro; do contrário, abre normal.
        if mes == 1:
            if not verificar_data_arrecadacao_janeiro(driver):
                print("Nenhum período válido encontrado para janeiro (excluindo 13º).")
                return
        else:
            # Se não for janeiro, basta abrir qualquer período existente (se quiser).
            # Caso queira clicar no primeiro, por exemplo:
            try:
                linhas_pagamento = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "row-pagamento")]'))
                )
                if linhas_pagamento:
                    print("Abrindo primeiro período encontrado para mês != janeiro.")
                    linhas_pagamento[0].click()
            except Exception as e:
                print(f"Erro ao tentar abrir período para mês != janeiro: {e}")

    botao_prosseguir = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "btnProsseguir"))
    )
    botao_prosseguir.click()

def detalhamento_do_credito(driver, df):
    for idx, row in df.iterrows():
        # Supondo que row["COMP_STR"] é "01/2022", então montamos "01/01/2022"
        competencia_str = row["COMP_STR"]

        # 1) Ajustar para como o site exibe o período. Exemplo simples (dia 1):
        periodo_site = converter_competencia_para_site(competencia_str)
        # Ex: "01/2022" -> "01/01/2022"

        # 2) Montar dicionário de valores
        valores_por_codigo = {
            "1082-01": row.get("1082-01", 0),
            "1138-01": row.get("1138-01", 0),
            "1646-01": row.get("1646-01", 0),
            "1170-01": row.get("1170-01", 0),
            "1176-01": row.get("1176-01", 0),
            "1191-01": row.get("1191-01", 0),
            "1196-01": row.get("1196-01", 0),
            "1200-01": row.get("1200-01", 0)
        }

        print(f"\n=== Preenchendo valores para competencia {competencia_str} ({periodo_site}) ===")

        # 3) Chamar a função que scaneia as linhas e preenche
        preencher_valores_na_tabela(driver, periodo_site, valores_por_codigo)

    print("✅ Fim do detalhamento de créditos.")

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

def preencher_valores_na_tabela(driver, competencia_site, valores_por_codigo):
    """
    - `competencia_site`: string do período como aparece no site (ex: "01/01/2022").
    - `valores_por_codigo`: dict, ex: {"1082-01": 1000.50, "1138-01": 300.20, ...}
    """

    # Encontra TODAS as linhas que correspondem a cada “pagamentoNumeradoDesmembramentoX”
    rows = driver.find_elements(By.XPATH, "//div[contains(@id,'pagamentoNumeradoDesmembramento')]")

    for row_element in rows:
        try:
            cod_receita = row_element.find_element(By.XPATH, ".//*[@id='codReceita']").text.strip()
            periodo_coluna = row_element.find_elements(By.XPATH, ".//div[@class='gs-col2 align-center sc-clickable']")
            if not periodo_coluna:
                continue

            # Em geral, a segunda coluna (ou a "próxima" do codReceita) traz "01/01/2022".
            # Ajuste conforme seu HTML real (às vezes é [0], às vezes [1]).
            periodo_apuracao = periodo_coluna[0].text.strip()

            # Se esta linha tem o código e o período que queremos preencher...
            if cod_receita in valores_por_codigo and periodo_apuracao == competencia_site:
                valor_a_preencher = valores_por_codigo[cod_receita]
                if not valor_a_preencher or pd.isna(valor_a_preencher):
                    continue

                # Dentro desta mesma row, encontre o input e digite o valor
                input_valor = row_element.find_element(By.XPATH, ".//*[@id='valorUtilizadoTxt']")
                input_valor.click()
                input_valor.clear()
                input_valor.send_keys(str(valor_a_preencher))

                print(f"✔ Preenchido {cod_receita} com {valor_a_preencher} para {periodo_apuracao}")

        except Exception as e:
            print(f"Erro ao processar linha: {e}")

def main():
    df = pd.read_excel('comp.xlsx')
    
    # Garante tudo como string; não fazemos sort
    df['COMP_STR'] = df['COMP'].astype(str).str.strip()

    # Marca quais são 13° (isso ajuda na hora de informar o crédito)
    df['IS_13'] = df['COMP_STR'].str.startswith("13/")
    
    # Opcional: cria coluna datetime para os "não-13"
    df['COMP_DT'] = pd.to_datetime(
        df.loc[~df['IS_13'], 'COMP_STR'],
        format='%m/%Y',
        errors='coerce'
    )
    
    # NÃO faça df.sort_values(...) se quiser preservar a ordem original do Excel!
    # NÃO faça df.dropna(...) em COMP_DT, pois isso apaga as linhas de 13° e 
    # qualquer formato que não parseie corretamente.

    driver = iniciar_selenium()

    for idx, row in df.iterrows():
        comp_str = row['COMP_STR']
        apelido = f"INSS - {comp_str}"
        
        # Chamadas do Selenium
        indentificar_documento(driver, apelido)
        informar_credito(driver, comp_str)
        detalhamento_do_credito(driver, df)

if __name__ == "__main__":
    main()
