import streamlit as st
import pandas as pd

# ----------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------
st.set_page_config(
    page_title="Analisador SPED Fiscal1111",
    page_icon="📘",
    layout="wide"
)

# ----------------------------------------------------
# HEADER MODERNO + LOGO (VISUAL APENAS)
# ----------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 3.5rem;
}

.app-header {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 60px;
    background: linear-gradient(90deg, #0f172a, #020617);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 32px;
    z-index: 999;
    border-bottom: 1px solid #1e293b;
}

.app-title {
    font-size: 18px;
    font-weight: 600;
    color: #e5e7eb;
    letter-spacing: 0.3px;
}

.app-logo {
    font-size: 20px;
    font-weight: 700;
    color: #38bdf8;
    letter-spacing: 1px;
}

.app-logo span {
    color: #e5e7eb;
    font-weight: 500;
    margin-left: 4px;
}
</style>

<div class="app-header">
    <div class="app-title">Analisador SPED Fiscal</div>
    <div class="app-logo">Torre<span>ERP</span></div>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# TÍTULO E DESCRIÇÃO (VISUAL APENAS)
# ----------------------------------------------------
st.markdown("""
<h1 style="font-size: 34px; font-weight: 700; margin-bottom: 0;">
📘 Analisador de SPED Fiscal
</h1>
<p style="color: #6b7280; font-size: 16px; margin-top: 4px;">
EFD ICMS/IPI • Auditoria • Análise Tributária
</p>
""", unsafe_allow_html=True)

st.markdown("""
### 🔍 Funcionalidades
- 🏢 **Identificação da Empresa**
- 👥 **Clientes e Fornecedores editáveis**
- 📦 **Cadastro de Produtos (0200)**
- 🧾 **Notas Fiscais**
- 💰 **ICMS por CFOP**
- 📊 **Apuração do ICMS**
""")

# ----------------------------------------------------
# FUNÇÕES AUXILIARES (INALTERADAS)
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

    empresa, participantes, produtos = {}, [], []
    notas, itens_nota, icms_cfop = [], [], []
    apuracao, nota_atual = {}, None

    for linha in linhas:
        if not linha.startswith("|"):
            continue

        campos = linha.strip().split("|")
        reg = campos[1]

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

        elif reg == "E110":
            apuracao = {
                "Débitos": to_float(campos[2]),
                "Créditos": to_float(campos[3]),
                "ICMS a Recolher": to_float(campos[9]),
                "Saldo Credor": to_float(campos[11])
            }

    return empresa, participantes, produtos, notas, itens_nota, icms_cfop, apuracao


# ----------------------------------------------------
# MODAL DE EDIÇÃO (INALTERADO)
# ----------------------------------------------------
@st.dialog("✏️ Editar Cadastro")
def editar_participante(pos, tipo):
    df = st.session_state.df_clientes if tipo == "Cliente" else st.session_state.df_fornecedores
    p = df.iloc[pos]

    with st.form("form_edicao"):
        codigo = st.text_input("Código do Cadastro", p["Código"])
        nome = st.text_input("Nome / Razão Social", p["Nome"])
        cnpj = st.text_input("CNPJ", p["CNPJ"])
        ie = st.text_input("Inscrição Estadual", p["IE"])
        municipio = st.text_input("Município", p["Município"])

        if st.form_submit_button("💾 Salvar"):
            df.iloc[pos] = [codigo, nome, p["Código País"], cnpj, p["CPF"], ie, municipio]
            st.success("Cadastro atualizado com sucesso!")


# ----------------------------------------------------
# UPLOAD E RELATÓRIO (100% INTACTO)
# ----------------------------------------------------
uploaded_file = st.file_uploader("📤 Envie o arquivo SPED Fiscal (.txt)", type=["txt"])

if uploaded_file:
    empresa, participantes, produtos, notas, itens_nota, icms_cfop, apuracao = ler_sped(uploaded_file.read())

    st.subheader("🏢 Empresa")
    st.dataframe(pd.DataFrame([empresa]), use_container_width=True)

    df_part = pd.DataFrame(participantes)
    df_prod = pd.DataFrame(produtos)
    df_notas = pd.DataFrame(notas)
    df_itens = pd.DataFrame(itens_nota)

    cod_cli = df_notas[df_notas["Operação"] == "Saída"]["Participante"].unique()
    cod_for = df_notas[df_notas["Operação"] == "Entrada"]["Participante"].unique()

    if "df_clientes" not in st.session_state:
        st.session_state.df_clientes = df_part[df_part["Código"].isin(cod_cli)].copy().reset_index(drop=True)

    if "df_fornecedores" not in st.session_state:
        st.session_state.df_fornecedores = df_part[df_part["Código"].isin(cod_for)].copy().reset_index(drop=True)

    st.subheader("👥 Clientes")
    st.metric("Total de Clientes", len(st.session_state.df_clientes))
    st.dataframe(st.session_state.df_clientes, use_container_width=True)

    idx_cli = st.selectbox(
        "Selecione o cliente para editar",
        st.session_state.df_clientes.index,
        format_func=lambda i: st.session_state.df_clientes.loc[i, "Nome"]
    )
    if st.button("✏️ Editar Cliente"):
        editar_participante(idx_cli, "Cliente")

    st.subheader("🏭 Fornecedores")
    st.metric("Total de Fornecedores", len(st.session_state.df_fornecedores))
    st.dataframe(st.session_state.df_fornecedores, use_container_width=True)

    idx_for = st.selectbox(
        "Selecione o fornecedor para editar",
        st.session_state.df_fornecedores.index,
        format_func=lambda i: st.session_state.df_fornecedores.loc[i, "Nome"]
    )
    if st.button("✏️ Editar Fornecedor"):
        editar_participante(idx_for, "Fornecedor")

    st.subheader("📦 Produtos (0200)")
    st.metric("Total de Produtos", len(df_prod))
    st.dataframe(df_prod, use_container_width=True)

    st.subheader("🧾 Notas de Entrada")
    st.metric("Total de Entradas", len(df_notas[df_notas["Operação"] == "Entrada"]))
    st.dataframe(df_notas[df_notas["Operação"] == "Entrada"], use_container_width=True)

    st.subheader("🧾 Notas de Saída")
    st.metric("Total de Saídas", len(df_notas[df_notas["Operação"] == "Saída"]))
    st.dataframe(df_notas[df_notas["Operação"] == "Saída"], use_container_width=True)

    st.subheader("📋 Itens das Notas (C170)")
    st.metric("Total de Itens", len(df_itens))
    st.dataframe(df_itens, use_container_width=True)

    st.subheader("💰 ICMS por CFOP (C190)")
    df_icms = pd.DataFrame(icms_cfop)
    resumo = df_icms.groupby("CFOP").agg(
        Valor_Operacao=("Valor Operação", "sum"),
        ICMS=("ICMS", "sum")
    ).reset_index()
    st.dataframe(resumo, use_container_width=True)

    st.subheader("📊 Apuração ICMS (E110)")
    st.dataframe(pd.DataFrame([apuracao]), use_container_width=True)

    st.subheader("💾 Downloads")
    c1, c2, c3, c4, c5 = st.columns(5)

    c1.download_button("Clientes (CSV)", st.session_state.df_clientes.to_csv(index=False, encoding="utf-8-sig"), "clientes.csv")
    c2.download_button("Fornecedores (CSV)", st.session_state.df_fornecedores.to_csv(index=False, encoding="utf-8-sig"), "fornecedores.csv")
    c3.download_button("Produtos (CSV)", df_prod.to_csv(index=False, encoding="utf-8-sig"), "produtos.csv")
    c4.download_button("Notas (CSV)", df_notas.to_csv(index=False, encoding="utf-8-sig"), "notas.csv")
    c5.download_button("Itens (CSV)", df_itens.to_csv(index=False, encoding="utf-8-sig"), "itens.csv")

else:
    st.info("Envie um arquivo SPED Fiscal para iniciar.")