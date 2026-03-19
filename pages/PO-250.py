import streamlit as st
import os
import requests
import json

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# 🔑 SUA API KEY (SEM "Bearer")
OPENAI_API_KEY = "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"

st.set_page_config(layout="wide")
st.title("📄 Análise Inteligente de PDF com OpenAI")

# Upload do PDF
uploaded_file = st.file_uploader("Envie seu PDF", type="pdf")

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    st.success("PDF carregado com sucesso!")

    # -----------------------------
    # 📄 PROCESSAMENTO DO PDF
    # -----------------------------
    loader = PyPDFLoader("temp.pdf")
    documents = loader.load()

    splitter = CharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    docs = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    db = FAISS.from_documents(docs, embeddings)

    retriever = db.as_retriever()

    # -----------------------------
    # 💬 PERGUNTA LIVRE
    # -----------------------------
    pergunta = st.text_input("Faça uma pergunta sobre o PDF:")

    def perguntar_openai(contexto, pergunta):
        url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""
        Responda com base SOMENTE no contexto abaixo.

        CONTEXTO:
        {contexto}

        PERGUNTA:
        {pergunta}
        """

        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Você é um assistente que responde baseado em documentos."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        response = requests.post(url, headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]

    if pergunta:
        docs_encontrados = retriever.get_relevant_documents(pergunta)
        contexto = "\n\n".join([doc.page_content for doc in docs_encontrados])

        resposta = perguntar_openai(contexto, pergunta)

        st.subheader("🧠 Resposta")
        st.write(resposta)

    # -----------------------------
    # 📊 INSIGHTS AUTOMÁTICOS
    # -----------------------------
    if st.button("📊 Gerar Insights do Documento"):
        docs_encontrados = retriever.get_relevant_documents("resumo do documento")
        contexto = "\n\n".join([doc.page_content for doc in docs_encontrados])

        prompt_insights = """
        Analise o documento e gere:

        1. Resumo Executivo
        2. Principais Pontos de Atenção
        3. Aspectos Positivos
        4. Aspectos Negativos
        5. Recomendações

        Baseie-se SOMENTE no conteúdo fornecido.
        Não invente informações.
        """

        insights = perguntar_openai(contexto, prompt_insights)

        st.subheader("📊 Insights")
        st.write(insights)