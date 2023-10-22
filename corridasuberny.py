import streamlit as st

import pandas as pd
import numpy as np

import plotly.express as px

# Pré-configurações
st.set_page_config(page_title = "Corridas UBER - NY",
                   page_icon = "https://cdn.icon-icons.com/icons2/2389/PNG/512/uber_logo_icon_144780.png",
                   layout = "wide")

# Configurando o título
st.markdown("<h1 style ='text-align: center; color: white;'>🚗 Corridas de UBER em Nova York 🚗</h1>", unsafe_allow_html = True)

# Obtendo os dados
url_dados = ("https://s3-us-west-2.amazonaws.com/"
             "streamlit-demo-data/uber-raw-data-sep14.csv.gz")

# Atribuindo a coluna para variavel dia
dia = "date/time"

# Reiniciando o cache a cada 1 hora
@st.cache_data(ttl = 3600)

# Função carregamento dos dados pelo pandas
def carregamento(nrows):
    dados = pd.read_csv(url_dados, nrows = nrows)
    minusculo = lambda x: str(x).lower() # Ajuste através da função lambda
    dados.rename(minusculo, axis = "columns", inplace = True)
    dados[dia] = pd.to_datetime(dados[dia]) # Transformando os dados para o formato utilizavel
    return dados

# Bloco do progresso do carregamento
estado_carregamento = st.text("Carregando os dados...")
dados = carregamento(10000)
estado_carregamento.text("Dados carregados com sucesso!")

# Extraindo apenas as horas do dia
hora = dados[dia].dt.hour

# Gerando o histograma de ocorrencias ao longo do dia
st.subheader("Número de corridas por hora :clock4:")
histograma = np.histogram(
    hora, bins = 24, range = (0,24))[0]
st.bar_chart(histograma, color = "#A61717")

st.write("----")

# Habilidando o filtro para o usuario
filtro_horario = st.slider("Hora:", 0, 23, 17)  # minimo -> 00h, maximo -> 23h, padrão -> 17h
dados_filtrados = dados[hora == filtro_horario]

# Contabilizando a qtd de corridas para o filtro escolhido
contagem = len(dados_filtrados)

# Calculando a contagem de corridas para a hora anterior para gerar o delta da métrica a ser exibida
hora_anterior = filtro_horario - 1 if filtro_horario > 0 else 23
dados_hora_anterior = dados[hora == hora_anterior]
contagem_hora_anterior = len(dados_hora_anterior)
delta = contagem - contagem_hora_anterior

# Alocando a métrica na lateral do app
st.sidebar.metric(label = f"Quantidade de corridas as {filtro_horario}:00:", value = contagem, delta = delta)

st.sidebar.write("----")

# Encontrando os horário com o menor & maior número de corridas
horario_menos_corridas = np.argmin(histograma)
horario_mais_corridas = np.argmax(histograma)
menor_numero_corridas = histograma[horario_menos_corridas]
maior_numero_corridas = histograma[horario_mais_corridas]

# Alocando as métrica na lateral do app
st.sidebar.metric(label = f"Horário com menos corridas é {horario_menos_corridas}:00:", value = menor_numero_corridas)
st.sidebar.metric(label = f"Horário com mais corridas é {horario_mais_corridas}:00:", value = maior_numero_corridas)

st.sidebar.write("----")

# Também alocando os dados brutos na lateral do app, para robustez da pesquisa e facilitacao no entendimento da base
if st.sidebar.checkbox("Exibir dados brutos"):
    st.sidebar.subheader("Dados brutos:")
    st.sidebar.write(dados)

# Gerando o mapa da cidade de NY no momento filtrado pelo usuario
st.subheader(f":world_map: Mapa de todas as corridas às {filtro_horario}:00")
st.map(dados_filtrados)

st.write("----")

# Categorizando os periodos do dia
dados["Categoria_Horas"] = "Madrugada"
dados.loc[(hora >= 6) & (hora <= 11), "Categoria_Horas"] = "Dia"
dados.loc[(hora >= 12) & (hora <= 17), "Categoria_Horas"] = "Tarde"
dados.loc[(hora >= 18) & (hora <= 23), "Categoria_Horas"] = "Noite"

# Obtendo a fracao de corridas em cada periodo
porcentagens = dados["Categoria_Horas"].value_counts(normalize = True) * 100

# Costumizando o grafico de rosca
cores = ["#35A1E9", "#5A56B7", "#FAC9BA", "#3C2859"] # As cores são atribuidas da maior à menor incidência percentual
fig = px.pie(porcentagens, names = porcentagens.index, values = porcentagens.values, hole = 0.5)
fig.update_traces(marker = dict(colors = cores), textfont = dict(size = 20, color = "#0D0D0D"))
fig.update_layout(width = 500, height = 500)

# Exibindo o gráfico
st.subheader("Porcentagem de Corridas ao longo do dia :mag:")
st.plotly_chart(fig)

st.write("----")