import streamlit as st
import pandas as pd

# ----------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------
st.set_page_config(
    page_title="Analisador SPED Fiscal",
    page_icon="📘",
    layout="wide"
)

st.title("📘 Analisador de SPED Fiscal – EFD ICMS/IPI")
st.markdown("""
Leitura de arquivo **SPED Fiscal (.txt)** com extração de:
- 🏢 Empresa  
- 👥 Clientes / Fornecedores  
- 📦 Itens / Produtos  
- 🧾 Notas Fiscais  
- 💰 ICMS por CFOP  
- 📊 Apuração do ICMS  
""")

# ----------------------------------------------------
# FUNÇÕES AUXILIARES
# ----------------------------------------------------
def to_float(v):
    try:
        if not v:
            return 0.0
        return float(v.replace(",", "."))
    except:
        return 0.0


def ler_sped(conteudo: bytes):
    linhas = conteudo.decode("latin1").splitlines()

    empresa = {}
    participantes = []
    produtos = []

    notas = []
    itens_nota = []
    icms_cfop = []
    apuracao = {}

    nota_atual = None

    for linha in linhas:
        if not linha.startswith("|"):
            continue

        campos = linha.strip().split("|")
        reg = campos[1]

        # --------------------------------------------
        # BLOCO 0 – IDENTIFICAÇÃO E CADASTROS
        # --------------------------------------------
        if reg == "0000":
            empresa = {
                "CNPJ": campos[7],
                "Razão Social": campos[6],
                "UF": campos[10],
                "IE": campos[11],
                "Data Inicial": campos[4],
                "Data Final": campos[5],
                "Perfil": campos[14]
            }

        elif reg == "0150":
            participantes.append({
                "Código": campos[2],
                "Nome": campos[3],
                "Código País": campos[4],
                "CNPJ": campos[5],
                "CPF": campos[6],
                "IE": campos[7],
                "Município": campos[9]
            })

        elif reg == "0200":
            produtos.append({
                "Código Item": campos[2],
                "Descrição": campos[3],
                "Código Barra": campos[4],
                "Unidade": campos[6],
                "Tipo Item": campos[7],
                "NCM": campos[8],
                "CEST": campos[9] if len(campos) > 9 else None,
                "Alíquota ICMS": campos[12] if len(campos) > 12 else None
            })

        # --------------------------------------------
        # BLOCO C – DOCUMENTOS FISCAIS
        # --------------------------------------------
        elif reg == "C100":
            nota_atual = {
                "Operação": "Entrada" if campos[2] == "0" else "Saída",
                "Participante": campos[4],
                "Modelo": campos[5],
                "Série": campos[6],
                "Número": campos[8],
                "Chave NF-e": campos[9],
                "Data": campos[11],
                "Valor Total": to_float(campos[12])
            }
            notas.append(nota_atual)

        elif reg == "C170" and nota_atual:
            itens_nota.append({
                "Número NF": nota_atual["Número"],
                "Código Item": campos[3],
                "Quantidade": to_float(campos[4]),
                "Valor Item": to_float(campos[7]),
                "CFOP": campos[11],
                "CST ICMS": campos[10]
            })

        elif reg == "C190":
            icms_cfop.append({
                "CFOP": campos[3],
                "CST": campos[2],
                "Valor Operação": to_float(campos[4]),
                "Base ICMS": to_float(campos[5]),
                "ICMS": to_float(campos[6])
            })

        # --------------------------------------------
        # BLOCO E – APURAÇÃO
        # --------------------------------------------
        elif reg == "E110":
            apuracao = {
                "Débitos": to_float(campos[2]),
                "Créditos": to_float(campos[3]),
                "ICMS a Recolher": to_float(campos[9]),
                "Saldo Credor": to_float(campos[11])
            }

    return empresa, participantes, produtos, notas, itens_nota, icms_cfop, apuracao


# ----------------------------------------------------
# UPLOAD
# ----------------------------------------------------
uploaded_file = st.file_uploader(
    "📤 Envie o arquivo SPED Fiscal (.txt)",
    type=["txt"]
)

if uploaded_file:
    empresa, participantes, produtos, notas, itens_nota, icms_cfop, apuracao = ler_sped(uploaded_file.read())

    # --------------------------------------------
    # EMPRESA
    # --------------------------------------------
    st.subheader("🏢 Empresa")
    st.dataframe(pd.DataFrame([empresa]), use_container_width=True)

    # --------------------------------------------
    # PARTICIPANTES
    # --------------------------------------------
    st.subheader("👥 Clientes / Fornecedores (0150)")
    df_part = pd.DataFrame(participantes)
    st.metric("Total de Participantes", len(df_part))
    st.dataframe(df_part, use_container_width=True)

    # --------------------------------------------
    # PRODUTOS
    # --------------------------------------------
    st.subheader("📦 Cadastro de Itens / Produtos (0200)")
    df_prod = pd.DataFrame(produtos)
    st.metric("Total de Itens", len(df_prod))
    st.dataframe(df_prod, use_container_width=True)

   
    # --------------------------------------------
    # NOTAS
    # --------------------------------------------
    df_notas = pd.DataFrame(notas)

    # NOTAS DE ENTRADA
    st.subheader("🧾 Notas Fiscais de Entrada (C100)")
    df_entrada = df_notas[df_notas["Operação"] == "Entrada"]
    st.metric("Total de Notas de Entrada", len(df_entrada))
    st.dataframe(df_entrada, use_container_width=True)

    # NOTAS DE SAÍDA
    st.subheader("🧾 Notas Fiscais de Saída (C100)")
    df_saida = df_notas[df_notas["Operação"] == "Saída"]
    st.metric("Total de Notas de Saída", len(df_saida))
    st.dataframe(df_saida, use_container_width=True)

    # --------------------------------------------
    # ITENS DAS NOTAS
    # --------------------------------------------
    st.subheader("📋 Itens das Notas (C170)")
    df_itens = pd.DataFrame(itens_nota)
    st.dataframe(df_itens, use_container_width=True)

    # --------------------------------------------
    # ICMS POR CFOP
    # --------------------------------------------
    st.subheader("💰 ICMS por CFOP (C190)")
    df_icms = pd.DataFrame(icms_cfop)
    resumo_cfop = df_icms.groupby("CFOP").agg(
        Valor_Operacao=("Valor Operação", "sum"),
        ICMS=("ICMS", "sum")
    ).reset_index()
    st.dataframe(resumo_cfop, use_container_width=True)

    # --------------------------------------------
    # APURAÇÃO
    # --------------------------------------------
    st.subheader("📊 Apuração ICMS (E110)")
    st.dataframe(pd.DataFrame([apuracao]), use_container_width=True)

    # --------------------------------------------
    # DOWNLOADS
    # --------------------------------------------
    st.subheader("💾 Downloads")

    c1, c2, c3 = st.columns(3)

    c1.download_button("Clientes/Fornecedores (CSV)",
        df_part.to_csv(index=False, encoding="utf-8-sig"),
        "participantes_0150.csv"
    )

    c2.download_button("Produtos (CSV)",
        df_prod.to_csv(index=False, encoding="utf-8-sig"),
        "produtos_0200.csv"
    )

    c3.download_button("Notas (CSV)",
        df_notas.to_csv(index=False, encoding="utf-8-sig"),
        "notas_c100.csv"
    )

else:
    st.info("Envie um arquivo SPED Fiscal para iniciar.")
