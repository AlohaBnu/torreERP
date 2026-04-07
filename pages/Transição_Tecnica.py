import streamlit as st
import pandas as pd
from pypdf import PdfReader
from docx import Document
import google.generativeai as genai
import os

# =====================================
# CONFIGURAÇÃO DO GEMINI
# =====================================
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("A variável de ambiente GEMINI_API_KEY não foi encontrada.")
    st.stop()

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"

# =====================================
# FUNÇÃO DE RESUMO
# =====================================
def gerar_resumo(texto: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
    Leia o texto abaixo e gere um resumo claro,
    organizado em tópicos (bullet points),
    destacando os principais pontos.

    Texto:
    {texto}
    """

    response = model.generate_content(prompt)
    return response.text


# =====================================
# FUNÇÕES DE LEITURA DE ARQUIVO
# =====================================
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
    elif nome.endswith(".pdf"):
        return ler_pdf(file)
    elif nome.endswith(".docx"):
        return ler_docx(file)
    elif nome.endswith(".xlsx") or nome.endswith(".xls"):
        return ler_excel(file)
    else:
        return None


# =====================================
# INTERFACE STREAMLIT
# =====================================
st.set_page_config(page_title="Leitor de Documentos", layout="wide")
st.title("📄 Leitura e Resumo de Documentos")

uploaded_file = st.file_uploader(
    "Envie um arquivo (TXT, PDF, Word ou Excel)",
    type=["txt", "pdf", "docx", "xlsx", "xls"]
)

if uploaded_file:
    texto = extrair_texto(uploaded_file)

    if not texto:
        st.error("Formato de arquivo não suportado.")
        st.stop()

    st.subheader("📑 Texto extraído")
    st.text_area("Conteúdo", texto, height=300)

    if st.button("✨ Gerar resumo"):
        with st.spinner("Gerando resumo com Gemini..."):
            resumo = gerar_resumo(texto)

        st.subheader("✅ Resumo")
        st.markdown(resumo)