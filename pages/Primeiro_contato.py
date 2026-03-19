import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime
import requests
import json

st.set_page_config(layout="wide")

# Extração do ServiceNow 
# https://seniorprod.service-now.com/now/nav/ui/classic/params/target/tsp1_project_list.do%3Fsysparm_query%3DstateIN-5%252C1%252C2%252C5%252C6%252C7%255Eassignment_group%253Da2bbdcfd87713510241863930cbb355f%255Eu_type_serviceINimplementation_project%252Cfactory_project%252Cseparete_project%252Cservices_included_recurrence%255Eu_tipo_de_metodologiaIN10%252C30%252C40%252C50%252C60%252C70%252C80%252C90%252C100%255Esys_created_onONThis%25２０year%40javascript%3Ags.beginningOfThisYear()%40javascript%3Ags.endOfThisYear()%26sysparm_first_row%3D1%２6sysparm_view%3D
# Projetos com base no ano de 2026


# -----------------------------
# 🔵 WEBHOOK TEAMS
# -----------------------------
def enviar_teams(mensagem):

    url = "https://seniorsistemassa.webhook.office.com/webhookb2/b964e08b-735f-4b1c-97e3-3f4ffdbf8419@62c7b02d-a95c-498b-9a7f-6e00acab728d/IncomingWebhook/b4b99bcc640a440bb279ff77af06d33a/5ba9219d-0082-4f37-85b4-2e8c7b765ebb/V25uCPmkKD6JSuTQlkkD7E4RCZBM7r9Ksmkt2_Q4B88qw1"

    payload = {"text": mensagem}
    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return r.status_code == 200
    except:
        return False


# -----------------------------
# 🔵 LIMPAR TEXTO
# -----------------------------
def limpar_texto(texto):

    if pd.isna(texto):
        return ""

    texto = str(texto).strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII','ignore').decode('ASCII')

    return texto


# -----------------------------
# 🔵 DASHBOARD
# -----------------------------
st.title("📊 Monitor de Projetos - Torre ERP")

arquivo = st.file_uploader("📂 Envie a planilha Excel", type=["xlsx"])

if arquivo:

    df = pd.read_excel(arquivo)

    colunas_limpas = [limpar_texto(c) for c in df.columns]
    mapa = dict(zip(colunas_limpas, df.columns))

    col_projeto = None
    col_fase = None
    col_criacao = None
    col_contato = None
    col_termino = None
    col_gerente = None

    for col in mapa:

        if "nome" in col and "projeto" in col:
            col_projeto = mapa[col]

        if "fase" in col:
            col_fase = mapa[col]

        if "criacao" in col:
            col_criacao = mapa[col]

        if "primeiro" in col and "contato" in col:
            col_contato = mapa[col]

        if "termino" in col:
            col_termino = mapa[col]

        if "gerente" in col:
            col_gerente = mapa[col]

    # -----------------------------
    # 🔵 TRATAMENTO DATAS
    # -----------------------------

    df[col_criacao] = pd.to_datetime(df[col_criacao], errors="coerce").dt.date
    df[col_termino] = pd.to_datetime(df[col_termino], errors="coerce")

    df[col_contato] = df[col_contato].astype(str).apply(limpar_texto)

    hoje = datetime.today().date()

    df["Primeiro Contato"] = df[col_contato].isin(["true","sim","verdadeiro"])

    df["Dias Sem Contato"] = None

    df.loc[df["Primeiro Contato"] == False, "Dias Sem Contato"] = (
        hoje - df[col_criacao]
    ).apply(lambda x: x.days if pd.notnull(x) else None)

    # -----------------------------
    # 🔵 FAROL SLA
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

    # 🔹 FILTRO PROJETO
    if col_projeto:

        projetos = st.sidebar.multiselect(
            "Projeto",
            sorted(df[col_projeto].dropna().unique())
        )

        if projetos:
            df_filtrado = df_filtrado[df_filtrado[col_projeto].isin(projetos)]

    # 🔹 FILTRO FASE
    if col_fase:

        fases = sorted(df[col_fase].dropna().unique())

        fase = st.sidebar.multiselect(
            "Fase",
            fases
        )

        if fase:
            df_filtrado = df_filtrado[df_filtrado[col_fase].isin(fase)]

    # 🔹 FILTRO DATA TÉRMINO (MÊS/ANO)

    if col_termino:

        df_filtrado["MesAnoTermino"] = df_filtrado[col_termino].dt.strftime("%m/%Y")

        meses = sorted(df_filtrado["MesAnoTermino"].dropna().unique())

        mes = st.sidebar.multiselect(
            "Data Término Planejada (Mês/Ano)",
            meses
        )

        if mes:
            df_filtrado = df_filtrado[df_filtrado["MesAnoTermino"].isin(mes)]

    # 🔹 FILTRO PRIMEIRO CONTATO

    contato = st.sidebar.multiselect(
        "Primeiro Contato",
        ["Com Contato","Sem Contato"]
    )

    if contato:

        if "Com Contato" in contato and "Sem Contato" not in contato:
            df_filtrado = df_filtrado[df_filtrado["Primeiro Contato"] == True]

        elif "Sem Contato" in contato and "Com Contato" not in contato:
            df_filtrado = df_filtrado[df_filtrado["Primeiro Contato"] == False]

    # -----------------------------
    # 🔵 MÉTRICAS
    # -----------------------------

    total = df_filtrado.shape[0]
    com_contato = df_filtrado[df_filtrado["Primeiro Contato"] == True].shape[0]
    sem_contato = df_filtrado[df_filtrado["Primeiro Contato"] == False].shape[0]

    c1,c2,c3 = st.columns(3)

    c1.metric("📁 Total", total)
    c2.metric("📞 Com 1º Contato", com_contato)
    c3.metric("🚨 Sem Contato", sem_contato)

    # -----------------------------
    # 🔵 FAROL SLA
    # -----------------------------

    df_risco = df_filtrado[df_filtrado["Primeiro Contato"] == False]

    verde = df_risco[df_risco["Farol SLA"] == "🟢 Dentro SLA"].shape[0]
    amarelo = df_risco[df_risco["Farol SLA"] == "🟡 Atenção"].shape[0]
    vermelho = df_risco[df_risco["Farol SLA"] == "🔴 Estourado"].shape[0]

    st.subheader("🚦 Farol SLA Primeiro Contato")

    f1,f2,f3 = st.columns(3)

    f1.metric("🟢 Dentro SLA", verde)
    f2.metric("🟡 Atenção", amarelo)
    f3.metric("🔴 Estourado", vermelho)

    # -----------------------------
    # 🔵 MENSAGEM TEAMS
    # -----------------------------

    mensagem = ""

    if not df_risco.empty:

        mensagem = "🚨 ALERTA DE PROJETOS SEM PRIMEIRO CONTATO\n\n"
        mensagem += "Projeto | Gerente | Criado em | Dias\n"
        mensagem += "--- | --- | --- | ---\n"

        for _, row in df_risco.iterrows():

            projeto = row[col_projeto] if col_projeto else "N/A"
            gerente = row[col_gerente] if col_gerente else "N/A"

            data_criacao = row[col_criacao]

            if pd.notna(data_criacao):
                data_criacao = data_criacao.strftime("%d/%m/%Y")
            else:
                data_criacao = "N/A"

            dias = row["Dias Sem Contato"]

            mensagem += f"{projeto} | {gerente} | {data_criacao} | {dias}\n"

    # -----------------------------
    # 🔵 BOTÃO TEAMS
    # -----------------------------

    st.divider()

    st.subheader("📢 Enviar alerta ao Teams")

    if mensagem:

        if st.button("📤 Enviar alerta"):

            sucesso = enviar_teams(mensagem)

            if sucesso:
                st.success("✅ Alerta enviado ao Teams")
            else:
                st.error("❌ Falha ao enviar mensagem")

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

else:

    st.info("👆 Envie a planilha para visualizar o dashboard")