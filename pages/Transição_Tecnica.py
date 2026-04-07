import streamlit as st
import pandas as pd
from pypdf import PdfReader
from docx import Document
import google.generativeai as genai
import os

# =====================================================
# CONFIGURAÇÃO GEMINI
# =====================================================
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY is None or API_KEY.strip() == "":
    st.error("GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
    st.stop()

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"

# =====================================================
# FUNÇÃO DE RESUMO (SEM STRING MULTILINHA)
# =====================================================
def gerar_resumo(texto):
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = (
        "Leia o texto abaixo e gere um resumo claro e objetivo, "
        "organizado em tópicos (bullet points), destacando os principais pontos.\n\n"
        "Texto:\n"
        + texto
    )

    response = model.generate_content(prompt)
    return response.text

# =====================================================
# FUNÇÕES DE LEITURA DE ARQUIVOS
# =====================================================
def ler_txt(file):
    return file.read().decode("utf-8")

def ler_pdf(file):
    reader = PdfReader(file)
    texto = ""
    for page in reader.pages:
        texto += (page.extract_text() or "") + "\n"
    return texto

def ler_docx(file):
    doc = Document(file)
    return "\n".join(p.text for p in doc.paragraphs)

def ler_excel(file):
    df = pd.read_excel(file)
    return df.to_string(index=False)

def extrair_texto(file):
    nome = file.name.lower()

    if nome.endswith(".txt"):
        return ler_txt(file)
    if nome.endswith(".pdf"):
        return ler_pdf(file)
    if nome.endswith(".docx"):
        return ler_docx(file)
    if nome.endswith(".xlsx") or nome.endswith(".xls"):
        return ler_excel(file)

    return None

# =====================================================
# INTERFACE STREAMLIT
# =====================================================
st.set_page_config(page_title="Leitura e Resumo de Documentos", layout="wide")
st.title("📄 Leitura e Resumo de Documentos")

uploaded_file = st.file_uploader(
    "Envie um arquivo (TXT, PDF, Word ou Excel)",
    type=["txt", "pdf", "docx", "xlsx", "xls"]
)

if uploaded_file:
    texto_extraido = extrair_texto(uploaded_file)

    if texto_extraido is None:
        st.error("Formato de arquivo não suportado.")
        st.stop()

    st.subheader("📑 Texto extraído")
    st.text_area(
        "Conteúdo do documento",
        texto_extraido,
        height=300
    )

    if st.button("✨ Gerar resumo"):
        with st.spinner("Gerando resumo com Gemini..."):
            resumo = gerar_resumo(texto_extraido)

        st.subheader("✅ Resumo")
        st.markdown(resumo)
