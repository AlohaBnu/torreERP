import streamlit as st
import requests

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

# 🔑 TOKEN HUGGING FACE
HF_TOKEN = "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"

st.set_page_config(layout="wide")
st.title("📄 Chat com PDF (100% Gratuito)")

uploaded_file = st.file_uploader("Envie seu PDF", type="pdf")

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    st.success("PDF carregado!")

    # -----------------------------
    # 📄 PROCESSAMENTO
    # -----------------------------
    loader = PyPDFLoader("temp.pdf")
    documents = loader.load()

    splitter = CharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    docs = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    db = FAISS.from_documents(docs, embeddings)
    retriever = db.as_retriever()

    # -----------------------------
    # 🤖 FUNÇÃO IA (HF API)
    # -----------------------------
    def perguntar_hf(contexto, pergunta):

        API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

        headers = {
            "Authorization": f"Bearer {HF_TOKEN}"
        }

        prompt = f"""
        Responda baseado apenas no contexto abaixo.

        Contexto:
        {contexto}

        Pergunta:
        {pergunta}
        """

        payload = {
            "inputs": prompt
        }

        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()[0]["generated_text"]

    # -----------------------------
    # 💬 PERGUNTA
    # -----------------------------
    pergunta = st.text_input("Faça sua pergunta:")

    if pergunta:
        docs_encontrados = retriever.get_relevant_documents(pergunta)
        contexto = "\n\n".join([doc.page_content for doc in docs_encontrados])

        resposta = perguntar_hf(contexto, pergunta)

        st.subheader("🧠 Resposta")
        st.write(resposta)

    # -----------------------------
    # 📊 INSIGHTS
    # -----------------------------
    if st.button("📊 Gerar Insights"):
        docs_encontrados = retriever.get_relevant_documents("resumo do documento")
        contexto = "\n\n".join([doc.page_content for doc in docs_encontrados])

        prompt = """
        Gere:

        1. Resumo Executivo
        2. Pontos de Atenção
        3. Aspectos Positivos
        4. Aspectos Negativos
        5. Recomendações

        Baseado SOMENTE no contexto.
        """

        resposta = perguntar_hf(contexto, prompt)

        st.subheader("📊 Insights")
        st.write(resposta)