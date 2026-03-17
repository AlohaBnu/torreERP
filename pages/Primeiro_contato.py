import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json
import mysql.connector as mc
from mysql.connector import Error
import os

st.set_page_config(layout="wide")

# -----------------------------
# 🔵 CONFIG BANCO
# -----------------------------
USER_DB_FAST = os.environ.get('USER_DB_FAST')
PASS_DB_FAST = os.environ.get('PASS_DB_FAST')

hostname = '172.31.20.168'
database = 'fast'
user = USER_DB_FAST if USER_DB_FAST else 'consulta'
password = PASS_DB_FAST if PASS_DB_FAST else 'wH@xQd'

# -----------------------------
# 🔵 CONEXÃO
# -----------------------------
def create_connection():
    try:
        connection = mc.connect(
            host=hostname,
            database=database,
            user=user,
            password=password,
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        return None

# -----------------------------
# 🔵 BUSCAR DADOS
# -----------------------------
def buscar_dados():

    conn = create_connection()

    if conn is None:
        return pd.DataFrame()

    query = """
    SELECT 
        p.CriadoEm,
        p.numero,
        p.NomeProjeto,
        p.GerenteProjetos,
        p.ClassificacaoProjeto,
        p.PorcentagemConclusao,
        p.Fase,
        p.DataTerminoReal,
        p.TipoMetodologia,
        p.UnidadeNegócios,

        CASE 
            WHEN p.u_contact_client IS NULL THEN 0
            WHEN LOWER(TRIM(p.u_contact_client)) IN ('true','1','sim','verdadeiro') THEN 1
            ELSE 0
        END AS u_contact_client,

        p.estado

    FROM projetosservicenow p

    WHERE p.GrupoResponsavel = 'Senior - Torre ERP'
        AND p.UnidadeNegócios = 'Senior'
        AND p.Estado NOT IN ('Cancelado', 'Encerrado')
        AND p.CriadoEm >= '2026-01-01'

    ORDER BY p.CriadoEm DESC
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return df

# -----------------------------
# 🔵 TEAMS
# -----------------------------
def enviar_teams(mensagem):


    url = "https://seniorsistemassa.webhook.office.com/webhookb2/2ec08012-d3e0-4d18-be82-b95599cc930f@62c7b02d-a95c-498b-9a7f-6e00acab728d/IncomingWebhook/6ac41ddb5ab948a4807134eba796d50d/5ba9219d-0082-4f37-85b4-2e8c7b765ebb/V2Yce2GRpGah5YqEisv4OzDPg91rLg6dZy1IJkJv5d5P01"

    payload = {"text": mensagem}
    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return r.status_code == 200
    except:
        return False

# -----------------------------
# 🔵 DASHBOARD
# -----------------------------
st.title("📊 Monitor de Projetos - Torre ERP")

# Atualizar
if st.button("🔄 Atualizar dados"):
    st.cache_data.clear()

@st.cache_data(ttl=300)
def carregar():
    return buscar_dados()

df = carregar()

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado.")
    st.stop()

# -----------------------------
# 🔵 TRATAMENTO
# -----------------------------
df["CriadoEm"] = pd.to_datetime(df["CriadoEm"], errors="coerce").dt.date
df["DataTerminoReal"] = pd.to_datetime(df["DataTerminoReal"], errors="coerce")

# 🔥 AGORA SIM CORRETO
df["Primeiro Contato"] = df["u_contact_client"] == 1

hoje = datetime.today().date()

df["Dias Sem Contato"] = None

df.loc[df["Primeiro Contato"] == False, "Dias Sem Contato"] = (
    hoje - df["CriadoEm"]
).apply(lambda x: x.days if pd.notnull(x) else None)

# -----------------------------
# 🔵 SLA
# -----------------------------
def classificar(dias):

    if pd.isna(dias):
        return "OK"

    if dias <= 1:
        return "🟢 Dentro SLA"
    elif dias <= 2:
        return "🟡 Atenção"
    else:
        return "🔴 Estourado"

df["Farol SLA"] = df["Dias Sem Contato"].apply(classificar)

# -----------------------------
# 🔵 FILTROS
# -----------------------------
st.sidebar.title("🎛️ Filtros")

df_filtrado = df.copy()

projetos = st.sidebar.multiselect(
    "Projeto",
    sorted(df["NomeProjeto"].dropna().unique())
)

if projetos:
    df_filtrado = df_filtrado[df_filtrado["NomeProjeto"].isin(projetos)]

fases = st.sidebar.multiselect(
    "Fase",
    sorted(df["Fase"].dropna().unique())
)

if fases:
    df_filtrado = df_filtrado[df_filtrado["Fase"].isin(fases)]

df_filtrado["MesAno"] = df_filtrado["DataTerminoReal"].dt.strftime("%m/%Y")

mes = st.sidebar.multiselect(
    "Data Término",
    sorted(df_filtrado["MesAno"].dropna().unique())
)

if mes:
    df_filtrado = df_filtrado[df_filtrado["MesAno"].isin(mes)]

contato = st.sidebar.multiselect(
    "Primeiro Contato",
    ["Com Contato", "Sem Contato"]
)

if contato:
    if "Com Contato" in contato and "Sem Contato" not in contato:
        df_filtrado = df_filtrado[df_filtrado["Primeiro Contato"] == True]
    elif "Sem Contato" in contato and "Com Contato" not in contato:
        df_filtrado = df_filtrado[df_filtrado["Primeiro Contato"] == False]

# -----------------------------
# 🔵 MÉTRICAS
# -----------------------------
total = len(df_filtrado)
com_contato = df_filtrado[df_filtrado["Primeiro Contato"]].shape[0]
sem_contato = df_filtrado[~df_filtrado["Primeiro Contato"]].shape[0]

c1, c2, c3 = st.columns(3)

c1.metric("📁 Total", total)
c2.metric("📞 Com Contato", com_contato)
c3.metric("🚨 Sem Contato", sem_contato)

# -----------------------------
# 🔵 FAROL
# -----------------------------
df_risco = df_filtrado[~df_filtrado["Primeiro Contato"]]

verde = df_risco[df_risco["Farol SLA"] == "🟢 Dentro SLA"].shape[0]
amarelo = df_risco[df_risco["Farol SLA"] == "🟡 Atenção"].shape[0]
vermelho = df_risco[df_risco["Farol SLA"] == "🔴 Estourado"].shape[0]

st.subheader("🚦 Farol SLA Primeiro Contato")

f1, f2, f3 = st.columns(3)

f1.metric("🟢 Dentro SLA", verde)
f2.metric("🟡 Atenção", amarelo)
f3.metric("🔴 Estourado", vermelho)

# -----------------------------
# 🔵 TEAMS AUTOMÁTICO
# -----------------------------
mensagem = ""

if not df_risco.empty:

    mensagem = "🚨 ALERTA DE PROJETOS SEM PRIMEIRO CONTATO\n\n"
    mensagem += "Projeto | Gerente | Criado em | Dias\n"
    mensagem += "--- | --- | --- | ---\n"

    for _, row in df_risco.iterrows():

        data_criacao = row["CriadoEm"]
        data_criacao = data_criacao.strftime("%d/%m/%Y") if pd.notna(data_criacao) else "N/A"

        mensagem += f"{row['NomeProjeto']} | {row['GerenteProjetos']} | {data_criacao} | {row['Dias Sem Contato']}\n"

st.divider()
st.subheader("📢 Envio automático Teams")

if mensagem:

    if True and True:

        sucesso = enviar_teams(mensagem)

        if sucesso:
            True
            st.success("✅ Alerta enviado automaticamente hoje")
        else:
            st.error("❌ Falha no envio automático")

    else:
        st.info("⏳ Já enviado hoje ou fora do horário")

else:
    st.info("Nenhum projeto sem primeiro contato")

# -----------------------------
# 🔵 TABELA
# -----------------------------
st.subheader("📋 Projetos")

df_filtrado = df_filtrado.sort_values(
    by="Dias Sem Contato",
    ascending=False,
    na_position="last"
)

df_exibicao = df_filtrado.reset_index(drop=True)
df_exibicao.index += 1

st.dataframe(df_exibicao, use_container_width=True)