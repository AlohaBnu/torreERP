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
# MODAL DE EDIÇÃO
# ----------------------------------------------------
@st.dialog("✏️ Editar Cadastro")
def editar_participante(idx, tipo):
    df = st.session_state.df_clientes if tipo == "Cliente" else st.session_state.df_fornecedores
    p = df.loc[idx]

    with st.form("form_edicao"):
        codigo = st.text_input("Código de Cadastro (pode alterar)", p["Código"])
        nome = st.text_input("Nome / Razão Social", p["Nome"])
        cnpj = st.text_input("CNPJ", p["CNPJ"])
        ie = st.text_input("Inscrição Estadual", p["IE"])
        municipio = st.text_input("Município", p["Município"])

        salvar = st.form_submit_button("💾 Salvar")

        if salvar:
            df.at[idx, "Código"] = codigo
            df.at[idx, "Nome"] = nome
            df.at[idx, "CNPJ"] = cnpj
            df.at[idx, "IE"] = ie
            df.at[idx, "Município"] = municipio
            st.success("Cadastro salvo com sucesso!")


# ----------------------------------------------------
# UPLOAD
# ----------------------------------------------------
uploaded_file = st.file_uploader(
    "📤 Envie o arquivo SPED Fiscal (.txt)",
    type=["txt"]
)

if uploaded_file:
    empresa, participantes, produtos, notas, itens_nota, icms_cfop, apuracao = ler_sped(uploaded_file.read())

    st.subheader("🏢 Empresa")
    st.dataframe(pd.DataFrame([empresa]), use_container_width=True)

    df_part = pd.DataFrame(participantes)
    df_notas = pd.DataFrame(notas)
    df_prod = pd.DataFrame(produtos)
    df_itens = pd.DataFrame(itens_nota)

    # --------------------------------------------
    # CLIENTES / FORNECEDORES
    # --------------------------------------------
    cod_for = df_notas[df_notas["Operação"] == "Entrada"]["Participante"].unique()
    cod_cli = df_notas[df_notas["Operação"] == "Saída"]["Participante"].unique()

    if "df_clientes" not in st.session_state:
        st.session_state.df_clientes = df_part[df_part["Código"].isin(cod_cli)].copy()

    if "df_fornecedores" not in st.session_state:
        st.session_state.df_fornecedores = df_part[df_part["Código"].isin(cod_for)].copy()

    # CLIENTES
    st.subheader("👥 Clientes")
    st.dataframe(st.session_state.df_clientes, use_container_width=True)

    if st.button("✏️ Editar Cliente"):
        editar_participante(0, "Cliente")

    # FORNECEDORES
    st.subheader("🏭 Fornecedores")
    st.dataframe(st.session_state.df_fornecedores, use_container_width=True)

    if st.button("✏️ Editar Fornecedor"):
        editar_participante(0, "Fornecedor")

    # --------------------------------------------
    # DOWNLOADS
    # --------------------------------------------
    st.subheader("💾 Downloads")

    c1, c2, c3, c4 = st.columns(4)

    c1.download_button(
        "Clientes (CSV)",
        st.session_state.df_clientes.to_csv(index=False, encoding="utf-8-sig"),
        "clientes.csv"
    )

    c2.download_button(
        "Fornecedores (CSV)",
        st.session_state.df_fornecedores.to_csv(index=False, encoding="utf-8-sig"),
        "fornecedores.csv"
    )

    c3.download_button(
        "Produtos (CSV)",
        df_prod.to_csv(index=False, encoding="utf-8-sig"),
        "produtos.csv"
    )

    c4.download_button(
        "Itens (CSV)",
        df_itens.to_csv(index=False, encoding="utf-8-sig"),
        "itens.csv"
    )

else:
    st.info("Envie um arquivo SPED Fiscal para iniciar.")