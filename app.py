import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página para um visual mais amplo
st.set_page_config(page_title="Rifa KRT", layout="wide")

st.title("🎫 Controle da Rifa KRT")
st.write("Gerencie os números disponíveis e vendidos em tempo real.")

# 1. Definição do intervalo de números
NUM_INICIAL = 4847
NUM_FINAL = 4977
total_numeros = NUM_FINAL - NUM_INICIAL + 1

# 2. Inicialização do estado de vendas (se não existir)
if "vendas" not in st.session_state:
    # False significa Livre, True significa Vendido
    st.session_state.vendas = {num: False for num in range(NUM_INICIAL, NUM_FINAL + 1)}

# --- PAINEL LATERAL (CONTROLE) ---
st.sidebar.header("⚙️ Gerenciar Bilhetes")

# Seleção múltipla para marcar como vendido ou livre de forma fácil
numeros_venda = st.sidebar.multiselect(
    "Selecionar números vendidos:",
    options=list(range(NUM_INICIAL, NUM_FINAL + 1)),
    default=[num for num, vendido in st.session_state.vendas.items() if vendido]
)

# Atualizar o estado com base na seleção do sidebar
for num in st.session_state.vendas.keys():
    st.session_state.vendas[num] = num in numeros_venda


# --- RESUMO DE MÉTRICAS ---
col1, col2, col3 = st.columns(3)
vendidos_count = sum(st.session_state.vendas.values())
livres_count = total_numeros - vendidos_count

col1.metric("Total de Números", total_numeros)
col2.metric("🟢 Disponíveis", livres_count)
col3.metric("🔴 Vendidos", vendidos_count)

st.markdown("---")

# --- MATRIZ VISUAL ---
st.subheader("📊 Matriz de Números")

# Criando a estrutura de grade/matriz (ex: 10 colunas por linha)
COLUNAS_GRADE = 10
numeros_lista = list(range(NUM_INICIAL, NUM_FINAL + 1))

# Divide os números em blocos de tamanho COLUNAS_GRADE
for i in range(0, len(numeros_lista), COLUNAS_GRADE):
    bloco = numeros_lista[i:i + COLUNAS_GRADE]
    cols = st.columns(COLUNAS_GRADE)
    
    for idx, num in enumerate(bloco):
        com_col = cols[idx]
        esta_vendido = st.session_state.vendas[num]
        
        # Define a cor com base no status
        cor_fundo = "#ff4b4b" if esta_vendido else "#28a745"
        cor_texto = "#ffffff"
        
        # Renderiza um card estilizado em HTML/CSS
        com_col.markdown(
            f"""
            <div style="
                background-color: {cor_fundo}; 
                color: {cor_texto}; 
                padding: 10px; 
                border-radius: 5px; 
                text-align: center; 
                font-weight: bold;
                margin-bottom: 10px;
                box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
            ">
                {num}
            </div>
            """, 
            unsafe_allow_html=True
        )