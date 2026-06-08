import streamlit as st
import sqlite3

# Configuração da página para visual amplo
st.set_page_config(page_title="Rifa KRT", layout="wide")

st.title("🎫 Controle de Rifa - KRT (Com Banco de Dados)")

# 1. Definição do intervalo de números
NUM_INICIAL = 4847
NUM_FINAL = 4977
total_numeros = NUM_FINAL - NUM_INICIAL + 1

# --- FUNÇÕES DO BANCO DE DADOS (SQLITE) ---
def conectar_banco():
    """Conecta ao banco SQLite e garante que a tabela exista."""
    conn = sqlite3.connect("rifa_krt.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rifa (
            numero INTEGER PRIMARY KEY,
            vendido INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

def inicializar_numeros():
    """Popula o banco com todos os números da rifa se estiver vazio."""
    conn = conectar_banco()
    cursor = conn.cursor()
    
    # Verifica se já existem registros
    cursor.execute("SELECT COUNT(*) FROM rifa")
    if cursor.fetchone()[0] == 0:
        # Insere todos os números do intervalo como não vendidos (0)
        dados = [(num, 0) for num in range(NUM_INICIAL, NUM_FINAL + 1)]
        cursor.executemany("INSERT INTO rifa (numero, vendido) VALUES (?, ?)", dados)
        conn.commit()
    conn.close()

def obter_estado_vendas():
    """Busca o status atual de todos os números no banco."""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT numero, vendido FROM rifa")
    # Retorna um dicionário {numero: True/False}
    vendas = {row[0]: bool(row[1]) for row in cursor.fetchall()}
    conn.close()
    return vendas

def atualizar_status_no_banco(numero, vendido):
    """Atualiza o status de um número específico (1 para vendido, 0 para livre)."""
    conn = conectar_banco()
    cursor = conn.cursor()
    status = 1 if vendido else 0
    cursor.execute("UPDATE rifa SET vendido = ? WHERE numero = ?", (status, numero))
    conn.commit()
    conn.close()

# Inicializa a estrutura do banco de dados
inicializar_numeros()

# Carrega os dados atualizados do banco
estado_vendas = obter_estado_vendas()

# Listas de apoio para os componentes da tela
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