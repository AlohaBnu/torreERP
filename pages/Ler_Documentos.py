import streamlit as st
import pandas as pd
from pypdf import PdfReader
from docx import Document
import os
import google.generativeai as genai

# ===============================
# CONFIGURAÇÃO GEMINI
# ===============================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="Leitura de Arquivos", layout="wide")
st.title("📄 Leitura de Arquivos (TXT, PDF, Excel, Word)")

# ===============================
# FUNÇÕES DE LEITURA
# ===============================
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
    return "\n".join([p.text for p in doc.paragraphs])

def ler_excel(file):
    df = pd.read_excel(file)
    return df.to_string(index=False)

def ler_csv(file):
    df = pd.read_csv(file)
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
    elif nome.endswith(".csv"):
        return ler_csv(file)
    else:
        return None

# ===============================
# UPLOAD
# ===============================
uploaded_file = st.file_uploader(
    "📤 Envie um arquivo",
    type=["txt", "pdf", "docx", "xlsx", "xls", "csv"]
)

if uploaded_file:
    texto = extrair_texto(uploaded_file)

    if texto:
        st.subheader("📑 Texto extraído do arquivo")
        st.text_area("Conteúdo", texto, height=300)

        # ===============================
        # RESUMO COM GEMINI
        # ===============================
        if st.button("✨ Resumir em tópicos"):
            prompt = f"""
            Leia o texto abaixo e gere um resumo claro,
            organizado em tópicos (bullet points),
            destacando os pontos mais importantes.

            Texto:
            {texto}
            """

            with st.spinner("Gerando resumo..."):
                response = model.generate_content(prompt)

            st.subheader("✅ Resumo do documento")
            st.markdown(response.text)
    else:
        st.error("Formato de arquivo não suportado.")