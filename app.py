"""
Rifa KRT — Sistema de Gerenciamento de Rifas
=============================================
Streamlit + Google Sheets

Estrutura da planilha "Rifa KRT" (uma aba para cada uso):
  - rifa          : numero | vendido | comprador
  - solicitacoes  : timestamp | nome | numeros | status   (status: pendente|aprovada|recusada)
  - ganhador      : numero | nome

Secrets necessários em .streamlit/secrets.toml:

    [gcp_service_account]
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
    client_email = "..."
    client_id = "..."
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "..."

    [admin]
    usuario = "admin"
    senha   = "trocar-esta-senha"
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, List

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


# ─────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Rifa KRT", layout="wide")

NUM_INICIAL = 4847
NUM_FINAL = 4977
NOME_PLANILHA = "Rifa KRT"

ABA_RIFA = "rifa"
ABA_SOLICITACOES = "solicitacoes"
ABA_GANHADOR = "ganhador"

HEADERS_RIFA = ["numero", "vendido", "comprador"]
HEADERS_SOLIC = ["timestamp", "nome", "numeros", "status"]
HEADERS_GANHADOR = ["numero", "nome"]


# ─────────────────────────────────────────────────────────────
# Conexão com Google Sheets
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def conectar_spreadsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)
    return client.open(NOME_PLANILHA)


def _get_or_create_ws(title: str, headers: List[str]):
    ss = conectar_spreadsheet()
    try:
        ws = ss.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=2000, cols=max(5, len(headers)))
        ws.update("A1", [headers])
    # Garante cabeçalhos válidos
    valores = ws.get_all_values()
    if not valores or valores[0][: len(headers)] != headers:
        ws.clear()
        ws.update("A1", [headers])
    return ws


def ws_rifa():
    return _get_or_create_ws(ABA_RIFA, HEADERS_RIFA)


def ws_solic():
    return _get_or_create_ws(ABA_SOLICITACOES, HEADERS_SOLIC)


def ws_ganhador():
    return _get_or_create_ws(ABA_GANHADOR, HEADERS_GANHADOR)


# ─────────────────────────────────────────────────────────────
# Inicialização e leitura
# ─────────────────────────────────────────────────────────────
def inicializar_numeros():
    ws = ws_rifa()
    valores = ws.get_all_values()
    if len(valores) <= 1:
        dados = [[n, 0, ""] for n in range(NUM_INICIAL, NUM_FINAL + 1)]
        ws.update("A2", dados)


@st.cache_data(ttl=10)
def obter_rifa() -> pd.DataFrame:
    ws = ws_rifa()
    valores = ws.get_all_values()
    if len(valores) <= 1:
        return pd.DataFrame(columns=HEADERS_RIFA)
    df = pd.DataFrame(valores[1:], columns=valores[0][: len(HEADERS_RIFA)])
    df["numero"] = pd.to_numeric(df["numero"], errors="coerce").astype("Int64")
    df["vendido"] = pd.to_numeric(df["vendido"], errors="coerce").fillna(0).astype(int)
    df["comprador"] = df.get("comprador", "").fillna("")
    return df.dropna(subset=["numero"]).reset_index(drop=True)


@st.cache_data(ttl=10)
def obter_solicitacoes() -> pd.DataFrame:
    ws = ws_solic()
    valores = ws.get_all_values()
    if len(valores) <= 1:
        return pd.DataFrame(columns=HEADERS_SOLIC)
    return pd.DataFrame(valores[1:], columns=valores[0][: len(HEADERS_SOLIC)])


@st.cache_data(ttl=10)
def obter_ganhador() -> pd.DataFrame:
    ws = ws_ganhador()
    valores = ws.get_all_values()
    if len(valores) <= 1:
        return pd.DataFrame(columns=HEADERS_GANHADOR)
    return pd.DataFrame(valores[1:], columns=valores[0][: len(HEADERS_GANHADOR)])


def limpar_caches():
    obter_rifa.clear()
    obter_solicitacoes.clear()
    obter_ganhador.clear()


# ─────────────────────────────────────────────────────────────
# Operações de escrita
# ─────────────────────────────────────────────────────────────
def registrar_solicitacao(nome: str, numeros: List[int]):
    ws = ws_solic()
    ws.append_row([
        dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        nome.strip(),
        ", ".join(str(n) for n in sorted(numeros)),
        "pendente",
    ])


def atualizar_status_solicitacao(linha_idx: int, novo_status: str):
    """linha_idx é o índice 0-based dentro do DataFrame (sem cabeçalho)."""
    ws = ws_solic()
    # +2: linha 1 é cabeçalho, planilha é 1-based
    ws.update_cell(linha_idx + 2, HEADERS_SOLIC.index("status") + 1, novo_status)


def marcar_numeros_vendidos(numeros: List[int], comprador: str):
    """Atualiza em lote os números vendidos."""
    ws = ws_rifa()
    df = obter_rifa()
    updates = []
    for n in numeros:
        match = df.index[df["numero"] == n]
        if len(match) == 0:
            continue
        linha = int(match[0]) + 2  # +2 por cabeçalho
        updates.append({"range": f"B{linha}:C{linha}", "values": [[1, comprador]]})
    if updates:
        ws.batch_update(updates)


def liberar_numero(numero: int):
    ws = ws_rifa()
    df = obter_rifa()
    match = df.index[df["numero"] == numero]
    if len(match) == 0:
        return
    linha = int(match[0]) + 2
    ws.batch_update([{"range": f"B{linha}:C{linha}", "values": [[0, ""]]}])


def salvar_ganhador(numero: int, nome: str):
    ws = ws_ganhador()
    ws.clear()
    ws.update("A1", [HEADERS_GANHADOR, [numero, nome]])


# ─────────────────────────────────────────────────────────────
# UI — Aba do Comprador
# ─────────────────────────────────────────────────────────────
def render_comprador():
    st.subheader("Escolha seus números")
    df = obter_rifa()
    vendidos = set(df.loc[df["vendido"] == 1, "numero"].astype(int).tolist())

    # Solicitações pendentes ainda não confirmadas → mostrar como "reservado"
    sol = obter_solicitacoes()
    reservados: set[int] = set()
    if not sol.empty:
        for nums in sol.loc[sol["status"] == "pendente", "numeros"]:
            for token in str(nums).split(","):
                token = token.strip()
                if token.isdigit():
                    reservados.add(int(token))
    reservados -= vendidos

    total = NUM_FINAL - NUM_INICIAL + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("Disponíveis", total - len(vendidos) - len(reservados))
    c2.metric("Reservados (pendentes)", len(reservados))
    c3.metric("Vendidos", len(vendidos))

    st.markdown("**Legenda:** 🟢 disponível · 🟡 reservado · 🔴 vendido")

    if "selecao" not in st.session_state:
        st.session_state.selecao = set()

    COLS = 10
    numeros = list(range(NUM_INICIAL, NUM_FINAL + 1))
    for i in range(0, len(numeros), COLS):
        cols = st.columns(COLS)
        for j, n in enumerate(numeros[i : i + COLS]):
            with cols[j]:
                if n in vendidos:
                    st.button(f"🔴 {n}", key=f"n{n}", disabled=True, use_container_width=True)
                elif n in reservados:
                    st.button(f"🟡 {n}", key=f"n{n}", disabled=True, use_container_width=True)
                else:
                    marcado = n in st.session_state.selecao
                    label = f"✅ {n}" if marcado else f"🟢 {n}"
                    if st.button(label, key=f"n{n}", use_container_width=True):
                        if marcado:
                            st.session_state.selecao.discard(n)
                        else:
                            st.session_state.selecao.add(n)
                        st.rerun()

    st.divider()
    st.subheader("Solicitar reserva")
    selecionados = sorted(st.session_state.selecao)
    st.write(f"**Números escolhidos:** {', '.join(map(str, selecionados)) or '—'}")

    with st.form("form_reserva", clear_on_submit=True):
        nome = st.text_input("Seu nome completo")
        enviar = st.form_submit_button("Enviar solicitação", type="primary")
        if enviar:
            if not nome.strip():
                st.error("Informe seu nome.")
            elif not selecionados:
                st.error("Selecione ao menos um número.")
            else:
                registrar_solicitacao(nome, selecionados)
                st.session_state.selecao = set()
                limpar_caches()
                st.success(
                    "Solicitação enviada! O administrador irá confirmar após o pagamento."
                )
                st.rerun()


# ─────────────────────────────────────────────────────────────
# UI — Gerência
# ─────────────────────────────────────────────────────────────
def render_login():
    st.subheader("🔐 Acesso restrito")
    with st.form("login"):
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", type="primary"):
            if (
                u == st.secrets["admin"]["usuario"]
                and s == st.secrets["admin"]["senha"]
            ):
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Credenciais inválidas.")


def render_solicitacoes():
    st.subheader("📥 Solicitações de compra")
    df = obter_solicitacoes()
    if df.empty:
        st.info("Nenhuma solicitação registrada.")
        return

    rifa = obter_rifa()
    vendidos = set(rifa.loc[rifa["vendido"] == 1, "numero"].astype(int).tolist())

    for idx, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(f"**{row['nome']}**  \n`{row['numeros']}`")
            c2.write(f"🕒 {row['timestamp']}")
            status = row["status"]
            badge = {"pendente": "🟡 Pendente", "aprovada": "🟢 Aprovada", "recusada": "🔴 Recusada"}.get(status, status)
            c3.write(badge)

            if status == "pendente":
                b1, b2 = st.columns(2)
                numeros = [int(x) for x in str(row["numeros"]).split(",") if x.strip().isdigit()]
                conflito = [n for n in numeros if n in vendidos]
                if conflito:
                    st.warning(f"Conflito — já vendidos: {conflito}")
                if b1.button("✅ Aprovar e marcar como vendido", key=f"ap{idx}", type="primary"):
                    marcar_numeros_vendidos([n for n in numeros if n not in vendidos], row["nome"])
                    atualizar_status_solicitacao(idx, "aprovada")
                    limpar_caches()
                    st.rerun()
                if b2.button("❌ Recusar", key=f"rc{idx}"):
                    atualizar_status_solicitacao(idx, "recusada")
                    limpar_caches()
                    st.rerun()


def render_controle():
    st.subheader("📊 Controle de números")
    df = obter_rifa().copy()
    df["status"] = df["vendido"].map({1: "Vendido", 0: "Disponível"})

    f1, f2 = st.columns([1, 3])
    filtro = f1.selectbox("Filtrar", ["Todos", "Vendidos", "Disponíveis"])
    busca = f2.text_input("Buscar por nome do comprador")

    if filtro == "Vendidos":
        df = df[df["vendido"] == 1]
    elif filtro == "Disponíveis":
        df = df[df["vendido"] == 0]
    if busca.strip():
        df = df[df["comprador"].str.contains(busca.strip(), case=False, na=False)]

    st.dataframe(
        df[["numero", "status", "comprador"]].rename(
            columns={"numero": "Número", "status": "Status", "comprador": "Comprador"}
        ),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    st.divider()
    st.markdown("**Liberar um número** (desfazer venda):")
    c1, c2 = st.columns([1, 3])
    num_lib = c1.number_input(
        "Número", min_value=NUM_INICIAL, max_value=NUM_FINAL, step=1, value=NUM_INICIAL
    )
    if c2.button("Liberar número"):
        liberar_numero(int(num_lib))
        limpar_caches()
        st.success(f"Número {num_lib} liberado.")
        st.rerun()


def render_manual_e_ganhador():
    st.subheader("✍️ Registro manual de venda")
    rifa = obter_rifa()
    disponiveis = rifa.loc[rifa["vendido"] == 0, "numero"].astype(int).tolist()

    with st.form("manual", clear_on_submit=True):
        nome = st.text_input("Nome do comprador")
        nums = st.multiselect("Números", disponiveis)
        if st.form_submit_button("Registrar venda", type="primary"):
            if not nome.strip() or not nums:
                st.error("Preencha nome e selecione ao menos um número.")
            else:
                marcar_numeros_vendidos(nums, nome.strip())
                limpar_caches()
                st.success(f"Venda registrada para {nome}: {nums}")
                st.rerun()

    st.divider()
    st.subheader("🏆 Ganhador da rifa")
    atual = obter_ganhador()
    if not atual.empty:
        st.success(f"Ganhador atual: **{atual.iloc[0]['nome']}** — número **{atual.iloc[0]['numero']}**")

    vendidos_df = rifa[rifa["vendido"] == 1]
    if vendidos_df.empty:
        st.info("Nenhum número vendido ainda.")
        return

    with st.form("ganhador"):
        opcoes = {
            f"{int(r['numero'])} — {r['comprador']}": (int(r["numero"]), r["comprador"])
            for _, r in vendidos_df.iterrows()
        }
        escolha = st.selectbox("Selecione o número sorteado", list(opcoes.keys()))
        if st.form_submit_button("Salvar ganhador", type="primary"):
            n, nome = opcoes[escolha]
            salvar_ganhador(n, nome)
            limpar_caches()
            st.success(f"Ganhador registrado: {nome} ({n})")
            st.rerun()


def render_gerencia():
    if not st.session_state.get("autenticado"):
        render_login()
        return

    col_a, col_b = st.columns([4, 1])
    col_a.success(f"Logado como **{st.secrets['admin']['usuario']}**")
    if col_b.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

    t1, t2, t3 = st.tabs(["Solicitações", "Controle de números", "Registro manual / Ganhador"])
    with t1:
        render_solicitacoes()
    with t2:
        render_controle()
    with t3:
        render_manual_e_ganhador()


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
def main():
    st.title("🎫 Rifa KRT")
    try:
        inicializar_numeros()
    except Exception as e:
        st.error(f"Falha ao conectar ao Google Sheets: {e}")
        st.stop()

    aba_comprador, aba_gerencia = st.tabs(["🛒 Comprador", "🔧 Gerência"])
    with aba_comprador:
        render_comprador()
    with aba_gerencia:
        render_gerencia()


if __name__ == "__main__":
    main()
