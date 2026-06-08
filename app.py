import streamlit as st

# Configuração da página
st.set_page_config(page_title="Rifa KRT", layout="wide")

st.title("🎫 Controle Seguro - Rifa KRT")
st.write("Gerencie os números com travas de segurança contra cliques acidentais.")

# 1. Definição do intervalo de números
NUM_INICIAL = 4847
NUM_FINAL = 4977
total_numeros = NUM_FINAL - NUM_INICIAL + 1

# 2. Inicialização do estado de vendas (Persistente na sessão)
if "vendas" not in st.session_state:
    st.session_state.vendas = {num: False for num in range(NUM_INICIAL, NUM_FINAL + 1)}

# --- PAINEL LATERAL (CONTROLE COM CONFIRMAÇÃO) ---
st.sidebar.header("⚙️ Painel de Controle")

# Filtrar listas para os seletores
numeros_livres = [num for num, vendido in st.session_state.vendas.items() if not vendido]
numeros_vendidos = [num for num, vendido in st.session_state.vendas.items() if vendido]

# SEÇÃO 1: Marcar como Vendido
st.sidebar.subheader("🛒 Registrar Venda")
if numeros_livres:
    # Usamos o index=None para começar vazio e forçar a escolha consciente
    num_para_vender = st.sidebar.selectbox(
        "Selecione o número vendido:", 
        options=numeros_livres, 
        index=None, 
        placeholder="Escolha um número...",
        key="sb_venda"
    )
    
    if st.sidebar.button("🔒 Confirmar Venda", type="primary", use_container_width=True):
        if num_para_vender:
            st.session_state.vendas[num_para_vender] = True
            st.toast(f"Número {num_para_vender} marcado como VENDIDO!", icon="✅")
            st.rerun()
else:
    st.sidebar.success("🎉 Todos os números foram vendidos!")

st.sidebar.markdown("---")

# SEÇÃO 2: Área de Segurança para Cancelar Venda
st.sidebar.subheader("🔄 Cancelar Venda (Estorno)")
if numeros_vendidos:
    num_para_liberar = st.sidebar.selectbox(
        "Selecione o número para liberar:", 
        options=numeros_vendidos, 
        index=None, 
        placeholder="Escolha um número...",
        key="sb_liberar"
    )
    
    # Botão com cor de aviso para exigir atenção
    if st.sidebar.button("⚠️ Confirmar Liberação", type="secondary", use_container_width=True):
        if num_para_liberar:
            st.session_state.vendas[num_para_liberar] = False
            st.toast(f"Número {num_para_liberar} voltou a ficar LIVRE!", icon="🔄")
            st.rerun()
else:
    st.sidebar.info("Nenhum número vendido ainda.")


# --- RESUMO DE MÉTRICAS ---
col1, col2, col3 = st.columns(3)
vendidos_count = len(numeros_vendidos)
livres_count = total_numeros - vendidos_count

col1.metric("Total de Números", total_numeros)
col2.metric("🟢 Disponíveis", livres_count)
col3.metric("🔴 Vendidos", vendidos_count)

st.markdown("---")

# --- LISTA TEXTUAL DE VENDIDOS (O que você pediu) ---
st.subheader("📋 Relatório de Bilhetes Vendidos")
if numeros_vendidos:
    # Exibe os números vendidos formatados lado a lado de forma limpa
    st.markdown(
        f"""
        <div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid #ff4b4b;">
            <strong style="color: #ff4b4b;">Números já reservados:</strong><br>
            <span style="font-size: 1.1em; letter-spacing: 1px;">
                {', '.join(map(str, sorted(numeros_vendidos)))}
            </span>
        </div>
        """, 
        unsafe_allow_html=True
    )
else:
    st.info("Nenhum número foi vendido até o momento.")

st.markdown("---")

# --- MATRIZ VISUAL ---
st.subheader("📊 Matriz de Visualização")

COLUNAS_GRADE = 10
numeros_lista = list(range(NUM_INICIAL, NUM_FINAL + 1))

for i in range(0, len(numeros_lista), COLUNAS_GRADE):
    bloco = numeros_lista[i:i + COLUNAS_GRADE]
    cols = st.columns(COLUNAS_GRADE)
    
    for idx, num in enumerate(bloco):
        com_col = cols[idx]
        esta_vendido = st.session_state.vendas[num]
        
        cor_fundo = "#ff4b4b" if esta_vendido else "#28a745"
        
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