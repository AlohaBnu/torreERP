import streamlit as st
import pandas as pd
from pypdf import PdfReader
from docx import Document
import google.generativeai as genai
import os

# ===== Gemini =====
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

def gerar_resumo(texto):
    model = genai.GenerativeModel(MODEL_NAME)
    prompt = f"""
    Gere um resumo em tópicos claros e objetivos do texto abaixo:

    {texto}
    """
    return model.generate_content(prompt).text

# ===== Leitura de arquivos =====
def extrair_texto(file):
    nome = file.name.lower()

    if nome.endswith(".txt"):
        return file.read().decode("utf-8")

    if nome.endswith(".pdf"):
        reader = PdfReader(file)
        return "\n".join([p.extract_text() or "" for p in reader.pages])

    if nome.endswith(".docx"):
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)

    if nome.endswith(".xlsx"):
        df = pd.read_excel(file)
        return df.to_string(index=False)

    return None

# ===== Streamlit =====
st.title("📄 Leitura e Resumo de Documentos")

uploaded = st.file_uploader(
    "Envie um arquivo",
    type=["txt", "pdf", "docx", "xlsx"]
)

if uploaded:
    texto = extrair_texto(uploaded)

    if texto:
        st.text_area("Texto extraído", texto, height=300)

        if st.button("Resumir"):
            with st.spinner("Gerando resumo..."):
                resumo = gerar_resumo(texto)
            st.markdown("### ✅ Resumo")
            st.markdown(resumo)
``