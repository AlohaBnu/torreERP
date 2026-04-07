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
Leitura de arquivo **SPED Fiscal (.txt)** com:
- ✅ Diferenciação de **Entrada x Saída**
- ✅ Cadastro correto de **Clientes e Fornecedores**
- ✅ Tratamento fiscal adequado de impostos
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
    participantes = {}
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

        # ------------------------------------------------
        # BLOCO 0 – EMPRESA
        # ------------------------------------------------
        if reg == "0000":
            empresa = {
                "CNPJ": campos[7],
                "Razão Social": campos[6],
                "UF": campos[10],
                "IE": campos[11],
                "Data Inicial": campos[4],
                "Data Final": campos[5],
                "Perfil SPED": campos[14]
            }

        # ------------------------------------------------
        # BLOCO 0 – PARTICIPANTES
        # ------------------------------------------------
        elif reg == "0150":
            cod = campos[2]
            participantes[cod] = {
                "Código": cod,
                "Nome": campos[3],
                "CNPJ": campos[5],
                "CPF": campos[6],
                "IE": campos[7],
                "Município": campos[9],
                "Tipos": set()  # Cliente / Fornecedor
            }

        # ------------------------------------------------
        # BLOCO 0 – PRODUTOS
        # ------------------------------------------------
        elif reg == "0200":
            produtos.append({
                "Código Item": campos[2],
                "Descrição": campos[3],
                "Unidade": campos[6],
                "Tipo Item": campos[7],
                "NCM": campos[8],
                "CEST": campos[9] if len(campos) > 9 else None
            })

        # ------------------------------------------------
        # BLOCO C – NOTAS FISCAIS
        # ------------------------------------------------
        elif reg == "C100":
            ind_oper = campos[2]
            tipo_operacao = "ENTRADA" if ind_oper == "0" else "SAÍDA"
            cod_part = campos[4]

            # marca participante
            if cod_part in participantes:
                if tipo_operacao == "ENTRADA":
                    participantes[cod_part]["Tipos"].add("Fornecedor")
                else:
                    participantes[cod_part]["Tipos"].add("Cliente")

            nota_atual = {
                "Tipo Operação": tipo_operacao,
                "Participante": cod_part,
                "Modelo": campos[5],
                "Série": campos[6],
                "Número": campos[8],
                "Chave NF-e": campos[9],
                "Data": campos[11],
                "Valor Total": to_float(campos[12])
            }

            notas.append(nota_atual)

        # ------------------------------------------------
        # BLOCO C – ITENS
        # ------------------------------------------------
        elif reg == "C170" and nota_atual:
            itens_nota.append({
                "Número NF": nota_atual["Número"],
                "Tipo Operação": nota_atual["Tipo Operação"],
                "Código Item": campos[3],
                "Quantidade": to_float(campos[4]),
                "Valor Item": to_float(campos[7]),
                "CFOP": campos[11],
                "CST ICMS": campos[10]
            })

        # ------------------------------------------------
        # BLOCO C – ICMS
        # ------------------------------------------------
        elif reg == "C190":
            icms_cfop.append({
                "Tipo Operação": nota_atual["Tipo Operação"] if nota_atual else None,
                "CFOP": campos[3],
                "CST": campos[2],
                "Valor Operação": to_float(campos[4]),
                "Base ICMS": to_float(campos[5]),
                "ICMS": to_float(campos[6])
            })

        # ------------------------------------------------
        # BLOCO E – APURAÇÃO
        # ------------------------------------------------
        elif reg == "E110":
            apuracao = {
                "Débitos ICMS": to_float(campos[2]),
                "Créditos ICMS": to_float(campos[3]),
                "ICMS a Recolher": to_float(campos[9]),
                "Saldo Credor": to_float(campos[11])
            }

    # transforma participantes em lista
    participantes = [
        {
            **v,
            "Tipo Cadastro": " / ".join(sorted(v["Tipos"])) if v["Tipos"] else "Sem Movimento"
        }
        for v in participantes.values()
    ]

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

    st.subheader("🏢 Empresa")
    st.dataframe(pd.DataFrame([empresa]), use_container_width=True)

    st.subheader("👥 Clientes / Fornecedores (0150)")
    df_part = pd.DataFrame(participantes)
    st.dataframe(df_part, use_container_width=True)

    st.subheader("📦 Produtos (0200)")
    df_prod = pd.DataFrame(produtos)
    st.dataframe(df_prod, use_container_width=True)

    st.subheader("🧾 Notas Fiscais (C100)")
    df_notas = pd.DataFrame(notas)
    st.dataframe(df_notas, use_container_width=True)

    st.subheader("📋 Itens das Notas (C170)")
    df_itens = pd.DataFrame(itens_nota)
    st.dataframe(df_itens, use_container_width=True)

    st.subheader("💰 ICMS por CFOP e Tipo de Operação")
    df_icms = pd.DataFrame(icms_cfop)
    resumo_cfop = df_icms.groupby(
        ["Tipo Operação", "CFOP"]
    ).agg(
        Valor_Operacao=("Valor Operação", "sum"),
        ICMS=("ICMS", "sum")
    ).reset_index()
    st.dataframe(resumo_cfop, use_container_width=True)

    st.subheader("📊 Apuração do ICMS (E110)")
    st.dataframe(pd.DataFrame([apuracao]), use_container_width=True)

else:
    st.info("Envie um arquivo SPED Fiscal para iniciar.")