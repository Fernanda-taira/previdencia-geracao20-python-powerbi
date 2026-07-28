import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By

print(" INICIANDO PROCESSAMENTO LIMPO E BLINDADO")
print("1. Lendo a planilha de respostas do Google Forms")

# 1. LEITURA INTELIGENTE: Remove linhas vazias/fantasmas do Excel (.dropna) e limpa espaços dos cabeçalhos
df_respostas = pd.read_excel("respostas_forms.xlsx"). dropna(how="all")
df_respostas.columns = df_respostas.columns.str.strip()

personas_voluntarias = df_respostas.to_dict(orient="records")
print(f" Sucesso! {len(personas_voluntarias)} voluntários reais carregado para a simulação. \n ")

# 2. CRIANDO O PORTAL DA CORRETORA
html_corretora = """
<html>
<head><title>Portal de Investimentos - Previdência Privada</title></head>
<body>
    <table id="tabela_fundos">
        <tbody>
            <tr><td>Fundo Alpha Conservador</td><td>Baixo</td><td>9.8</td></tr>
            <tr><td>Fundo Beta Multimercado</td><td>Médio</td><td>11.5</td></tr>
            <tr><td>Fundo Gama Ações Agressivo</td><td>Alto</td><td>15.2</td></tr>
            <tr><td>Fundo Delta Renda Fixa</td><td>Baixo</td><td>10.4</td></tr>
            <tr><td>Fundo Ômega Equilíbrio</td><td>Médio</td><td>12.1</td></tr>
        </tbody>
    </table>
</body>
</html>
"""

with open("portal_corretora.html", "w", encoding= "utf-8") as arquivo:
    arquivo.write(html_corretora)

print("2. Ligando o navegador e extraindo taxas dos fundos...")
opcoes= webdriver.ChromeOptions()
navegador= webdriver.Chrome(options=opcoes)

caminho_pagina = os.path.abspath("portal_corretora.html")
navegador.get(f"file://{caminho_pagina}")
time.sleep(1)

linhas = navegador.find_elements(By.XPATH, "//table[@id='tabela_fundos']/tbody/tr")
fundos_capturados = []

for linha in linhas:
    colunas = linha.find_elements(By.TAG_NAME, "td")
    fundos_capturados.append({
        "Nome": colunas [0].text,
        "Risco": colunas[1].text,
        "Taxa_Anual": float(colunas[2].text)
    })

navegador.quit()
print(f" {len(fundos_capturados)} fundos lidos do catálogo.\n")

print("3. Cruzando dados e simulando os 30 anos ( com Zero à esquerda e proteção LGPD)")
dados_evolucao_total = []

for indice, persona in enumerate(personas_voluntarias, start=1):
    
    # GARANTIA DE ORDEM NUMÉRICA: Cria "Voluntário 01", "Voluntário 02"
    nome_pessoa = f"Voluntário {indice:02d}"
    
    # 1. TRADUTOR DE RISCO (Sem chances de falhar)
    texto_risco = str(persona.get("Risco_Desejado", "")).lower()
    if any(palavra in texto_risco for palavra in ["conservador", "baixo", "seguran"]):
        risco_alvo = "Baixo"
    elif any (palavra in texto_risco for palavra in ["agressivo", "alto", "arrojado"]):
        risco_alvo = "Alto"
    else:
        risco_alvo = "Médio"   # Se não reconhecer a palavra, joga no meio-termo por segurança       
        
    # 2. TRADUTOR DE IDADE
    texto_idade = str(persona.get("Idade_Atual", "25"))
    if "20 a 22" in texto_idade:
        idade_inicial =21
    elif "23 a 25" in texto_idade:
        idade_inicial = 24
    elif "26 a 29" in texto_idade:
        idade_inicial= 27
    elif "30" in texto_idade:
        idade_inicial=30
    else: 
        try:
            idade_inicial = int(texto_idade.replace("anos", "")). strip()
        except:
            idade_inicial = 25
    
    # 3. TRADUTOR DE APORTE MENSAL
    texto_aporte = str(persona.get("Aporte_Mensal", "100"))
    if "30" in texto_aporte and "50" in texto_aporte:
        aporte = 50.0
    elif "50" in texto_aporte and "100" in texto_aporte:
        aporte = 100.0
    elif "100" in texto_aporte and "150" in texto_aporte:
        aporte = 150.0
    elif "Acima" in texto_aporte or "150" in texto_aporte:
        aporte = 200.0
    else:
        try:
            aporte = float(texto_aporte.replace("R$", "").replace(".", "").replace(",", ".").strip())
        except:
            aporte = 100.0
    
    #4. SIMULAÇÃO ANO A ANO
    linhas_geradas_para_pessoa = 0
    for fundo in fundos_capturados:
        if fundo["Risco"] == risco_alvo:
            taxa_anual_decimal = fundo["Taxa_Anual"] / 100
            taxa_mensal = (1+taxa_anual_decimal) ** (1/12) -1
            
            for ano in range (1, 31):
                meses = ano *12
                acumulado = aporte * ((1 + taxa_mensal) ** meses - 1) / taxa_mensal
                total_investido = aporte * meses
                juros_ganhos = acumulado - total_investido
                
                dados_evolucao_total.append({
                    "ID Pessoa": nome_pessoa,
                    "Idade Inicial": idade_inicial,
                    "Idade Projetada": idade_inicial + ano,
                    "Ano de Simulação": ano,
                    "Aporte Mensal": aporte,
                    "Nome do Fundo": fundo["Nome"],
                    "Risco do Fundo": fundo["Risco"],
                    "Taxa Anual (%)": fundo["Taxa_Anual"],
                    "Total Investido": round(total_investido, 2),
                    "Juros Ganhos": round(juros_ganhos, 2),
                    "Patrimônio Acumulado": round(acumulado, 2)                    
                })
                linhas_geradas_para_pessoa += 1
                
    print(f"   👤 {nome_pessoa}: Risco {risco_alvo} | Aporte R$ {aporte} | ✅ {linhas_geradas_para_pessoa} linhas de projeção criadas!")

print("\n4. Gerando base de dados oficial e blindada")
df_final = pd.DataFrame(dados_evolucao_total)

nome_arquivo = "base_para_powerbi.xlsx"
df_final.to_excel(nome_arquivo, index=False)

print(f"🎉 SUCESSO TOTAL! Planilha '{nome_arquivo}' gerada com {len(df_final)} linhas!")
print("👉 Agora abra o Power BI e clique em 'Atualizar' na aba Página Inicial!")                
                
    
            
                    
            
    