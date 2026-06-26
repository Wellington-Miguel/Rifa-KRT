import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Configuração da página para visual amplo
st.set_page_config(page_title="Rifa KRT", layout="wide")

st.title("🎫 Controle de Rifa - KRT")

# 1. Definição do intervalo de números
NUM_INICIAL = 4847
NUM_FINAL = 4977
total_numeros = NUM_FINAL - NUM_INICIAL + 1

# --- FUNÇÕES DO GOOGLE SHEETS ---
@st.cache_resource
def conectar_gsheets():
    """Conecta ao Google Sheets usando as credenciais do Streamlit Secrets."""
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)
    # Cole aqui o nome EXATO da sua planilha
    spreadsheet = client.open("Rifa KRT") 
    worksheet = spreadsheet.worksheet("rifa")
    return worksheet

@st.cache_data(ttl=60)
def inicializar_numeros():
    """Popula a planilha com todos os números da rifa se estiver vazia."""
    sheet = conectar_gsheets()
    # Verifica se a planilha tem apenas o cabeçalho
    if len(sheet.get_all_records()) == 0:
        # Cria uma lista de dicionários para inserir
        dados = [{"numero": num, "vendido": 0} for num in range(NUM_INICIAL, NUM_FINAL + 1)]
        # Insere os dados a partir da segunda linha
        sheet.update("A2", [list(d.values()) for d in dados])

@st.cache_data(ttl=10)
def obter_estado_vendas():
    """Busca o status atual de todos os números na planilha."""
    sheet = conectar_gsheets()
    records = sheet.get_all_records()
    # Converte para um dicionário {numero: True/False}
    vendas = {row['numero']: bool(row['vendido']) for row in records}
    return vendas

def atualizar_status_no_banco(numero, vendido):
    """Atualiza o status de um número específico na planilha."""
    sheet = conectar_gsheets()
    status = 1 if vendido else 0
    
    # Encontra a linha correspondente ao número
    # A busca começa na linha 2, pois a linha 1 é o cabeçalho
    try:
        cell = sheet.find(str(numero), in_column=1)
        # Atualiza a célula na coluna 'vendido' (coluna 2)
        sheet.update_cell(cell.row, 2, status)
        # Limpa o cache para que a próxima leitura obtenha os dados atualizados
        st.cache_data.clear()
    except gspread.exceptions.CellNotFound:
        st.error(f"Erro: Número {numero} não encontrado na planilha para atualização.")

# Inicializa a estrutura da planilha
inicializar_numeros()

# Carrega os dados atualizados da planilha
estado_vendas = obter_estado_vendas()

# Listas de apoio para os componentes da tela
# Garante que a chave 'numero' exista antes de tentar acessá-la
numeros_livres = [num for num, vendido in estado_vendas.items() if not vendido]
numeros_vendidos = sorted([num for num, vendido in estado_vendas.items() if vendido])


# --- BARRA LATERAL (RELATÓRIO E EXCLUSÃO) ---
st.sidebar.header("⚙️ Painel de Controle")

# SESSÃO 1: Lista estática dos vendidos
st.sidebar.subheader("📋 Números Vendidos")
if numeros_vendidos:
    st.sidebar.markdown(
        f"""
        <div style="
            background-color: #ff4b4b22; 
            color: #ff4b4b; 
            padding: 12px; 
            border-radius: 6px; 
            border: 1px solid #ff4b4b;
            font-weight: bold;
            font-size: 1.1em;
            word-wrap: break-word;
        ">
            {', '.join(map(str, numeros_vendidos))}
        </div>
        """, 
        unsafe_allow_html=True
    )
else:
    st.sidebar.info("Nenhum número vendido ainda.")

st.sidebar.markdown("---")

# SESSÃO 2: Liberação de número (Voltar para Livre)
st.sidebar.subheader("🔄 Tornar Disponível")
if numeros_vendidos:
    num_para_liberar = st.sidebar.selectbox(
        "Selecione para remover dos vendidos:", 
        options=numeros_vendidos, 
        index=None, 
        placeholder="Escolha o número...",
        key="sb_liberar_unico"
    )
    
    if st.sidebar.button("⚠️ Confirmar Liberação", type="secondary", use_container_width=True):
        if num_para_liberar:
            atualizar_status_no_banco(num_para_liberar, vendido=False)
            st.toast(f"Número {num_para_liberar} voltou a ficar livre!", icon="🔄")
            st.rerun()
else:
    st.sidebar.write("Nada para liberar.")


# --- CORPO PRINCIPAL (MÉTRICAS E REGISTRO) ---
col1, col2, col3 = st.columns(3)
col1.metric("Total de Números", total_numeros)
col2.metric("🟢 Disponíveis", len(numeros_livres))
col3.metric("🔴 Vendidos", len(numeros_vendidos))

st.markdown("---")

# Interface para registrar nova venda
st.subheader("🛒 Registrar Nova Venda")
col_sel, col_btn = st.columns([3, 1])

with col_sel:
    num_para_vender = st.selectbox(
        "Selecione o número que foi vendido:",
        options=numeros_livres,
        index=None,
        placeholder="Digite ou selecione o número do bilhete...",
        key="venda_unica"
    )

with col_btn:
    st.write("") # Alinhamento estético
    st.write("") 
    if st.button("🔒 Marcar como Vendido", type="primary", use_container_width=True):
        if num_para_vender:
            atualizar_status_no_banco(num_para_vender, vendido=True)
            st.toast(f"Número {num_para_vender} registrado no Banco de Dados!", icon="✅")
            st.rerun()

st.markdown("---")


# --- MATRIZ VISUAL DE NÚMEROS ---
st.subheader("📊 Matriz de Visualização")

COLUNAS_GRADE = 10
numeros_lista = list(range(NUM_INICIAL, NUM_FINAL + 1))

for i in range(0, len(numeros_lista), COLUNAS_GRADE):
    bloco = numeros_lista[i:i + COLUNAS_GRADE]
    cols = st.columns(COLUNAS_GRADE)
    
    for idx, num in enumerate(bloco):
        com_col = cols[idx]
        esta_vendido = estado_vendas[num]
        
        # Cores baseadas no status vindo do Banco
        cor_fundo = "#ff4b4b" if esta_vendido else "#28a745"
        
        # Renderização do Card na Matriz
        com_col.markdown(
            f"""
            <div style="
                background-color: {cor_fundo}; 
                color: #ffffff; 
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