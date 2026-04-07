import streamlit as st
import pandas as pd

# ----------------------------------------------------
# CONFIGURAÇÃO GERAL
# ----------------------------------------------------
st.set_page_config(
    page_title="Analisador SPED Fiscal",
    page_icon="📘",
    layout="wide"
)

st.title("📘 Analisador de SPED Fiscal (EFD ICMS/IPI)")
st.markdown("""
Analise **arquivos SPED Fiscal (.txt)** e visualize:
- 🏢 Dados da empresa  
- 🧾 Notas fiscais (Bloco C)  
- 📦 Itens das notas  
- 💰 ICMS por CFOP  
- 📊 Apuração do ICMS  
""")

# ----------------------------------------------------
# FUNÇÕES AUXILIARES
# ----------------------------------------------------
def to_float(valor):
    try:
        if valor is None or valor == "":
            return 0.0
        return float(valor.replace(",", "."))
    except:
        return 0.0


def ler_sped_fiscal(conteudo: bytes):
    linhas = conteudo.decode("latin1").splitlines()

    empresa = {}
    notas = []
    itens = []
    icms_cfop = []
    apuracao = {}

    nota_atual = None

    for linha in linhas:
        if not linha.startswith("|"):
            continue

        campos = linha.strip().split("|")
        reg = campos[1]

        # ------------------------------------------------
        # BLOCO 0 - EMPRESA
        # ------------------------------------------------
        if reg == "0000":
            empresa = {
                "CNPJ": campos[7],
                "Razão Social": campos[6],
                "UF": campos[10],
                "Data Inicial": campos[4],
                "Data Final": campos[5],
                "Perfil": campos[14]
            }

        # ------------------------------------------------
        # BLOCO C - NOTAS FISCAIS
        # ------------------------------------------------
        elif reg == "C100":
            nota_atual = {
                "Operação": "Entrada" if campos[2] == "0" else "Saída",
                "Modelo": campos[5],
                "Número": campos[8],
                "Chave NF-e": campos[9],
                "Data": campos[11],
                "Valor Total": to_float(campos[12])
            }
            notas.append(nota_atual)

        elif reg == "C170" and nota_atual:
            itens.append({
                "Número NF": nota_atual["Número"],
                "Código Item": campos[3],
                "Quantidade": to_float(campos[4]),
                "Valor Item": to_float(campos[7]),
                "CFOP": campos[11]
            })

        elif reg == "C190":
            icms_cfop.append({
                "CFOP": campos[3],
                "CST": campos[2],
                "Valor Operação": to_float(campos[4]),
                "Base ICMS": to_float(campos[5]),
                "ICMS": to_float(campos[6])
            })

        # ------------------------------------------------
        # BLOCO E - APURAÇÃO
        # ------------------------------------------------
        elif reg == "E110":
            apuracao = {
                "Débitos": to_float(campos[2]),
                "Créditos": to_float(campos[3]),
                "ICMS a Recolher": to_float(campos[9]),
                "Saldo Credor": to_float(campos[11])
            }

    return empresa, notas, itens, icms_cfop, apuracao


# ----------------------------------------------------
# UPLOAD DO ARQUIVO
# ----------------------------------------------------
uploaded_file = st.file_uploader(
    "📤 Envie o arquivo SPED Fiscal (.txt)",
    type=["txt"]
)

if uploaded_file:
    empresa, notas, itens, icms_cfop, apuracao = ler_sped_fiscal(uploaded_file.read())

    # ------------------------------------------------
    # EMPRESA
    # ------------------------------------------------
    st.subheader("🏢 Empresa")
    if empresa:
        st.dataframe(pd.DataFrame([empresa]), use_container_width=True)
    else:
        st.warning("Registro 0000 não encontrado.")

    # ------------------------------------------------
    # NOTAS FISCAIS
    # ------------------------------------------------
    st.subheader("🧾 Notas Fiscais (C100)")
    df_notas = pd.DataFrame(notas)
    if not df_notas.empty:
        col1, col2 = st.columns(2)
        col1.metric("Quantidade de Notas", len(df_notas))
        col2.metric("Valor Total", f"R$ {df_notas['Valor Total'].sum():,.2f}")

        st.dataframe(df_notas, use_container_width=True)
    else:
        st.info("Nenhuma nota fiscal encontrada.")

    # ------------------------------------------------
    # ITENS DAS NOTAS
    # ------------------------------------------------
    st.subheader("📦 Itens das Notas (C170)")
    df_itens = pd.DataFrame(itens)
    if not df_itens.empty:
        st.dataframe(df_itens, use_container_width=True)
    else:
        st.info("Nenhum item encontrado.")

    # ------------------------------------------------
    # ICMS POR CFOP
    # ------------------------------------------------
    st.subheader("💰 ICMS por CFOP (C190)")
    df_icms = pd.DataFrame(icms_cfop)
    if not df_icms.empty:
        resumo_cfop = df_icms.groupby("CFOP").agg({
            "Valor Operação": "sum",
            "ICMS": "sum"
        }).reset_index()

        st.dataframe(resumo_cfop, use_container_width=True)
    else:
        st.info("Nenhum ICMS encontrado.")

    # ------------------------------------------------
    # APURAÇÃO DO ICMS
    # ------------------------------------------------
    st.subheader("📊 Apuração do ICMS (E110)")
    if apuracao:
        st.dataframe(pd.DataFrame([apuracao]), use_container_width=True)
    else:
        st.info("Registro E110 não encontrado.")

    # ------------------------------------------------
    # DOWNLOAD CSV
    # ------------------------------------------------
    st.subheader("💾 Download dos Dados")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "Baixar Notas (CSV)",
            df_notas.to_csv(index=False, encoding="utf-8-sig"),
            "notas_sped.csv",
            "text/csv"
        )

    with col2:
        st.download_button(
            "Baixar Itens (CSV)",
            df_itens.to_csv(index=False, encoding="utf-8-sig"),
            "itens_sped.csv",
            "text/csv"
        )

    with col3:
        st.download_button(
            "Baixar ICMS por CFOP (CSV)",
            resumo_cfop.to_csv(index=False, encoding="utf-8-sig"),
            "icms_cfop_sped.csv",
            "text/csv"
        )

else:
    st.info("Envie um arquivo SPED Fiscal para iniciar a análise.")