import os
import streamlit as st
import google.generativeai as genai

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# ============================================================
# CONFIGURAÇÃO GEMINI
# ============================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-1.5-flash"


# ============================================================
# FUNÇÃO COM CACHE PARA CARREGAR O PDF E CRIAR BASE VETORIAL
# ============================================================
@st.cache_resource
def carregar_rag():
    pdf_path = "PO-250.pdf"

    if not os.path.exists(pdf_path):
        st.error(f"Arquivo não encontrado: {pdf_path}")
        return None

    loader = PyPDFLoader(pdf_path)
    docs_raw = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = splitter.split_documents(docs_raw)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    vectorstore = Chroma.from_documents(docs, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.2)

    prompt = ChatPromptTemplate.from_template(
        """
        Use o contexto abaixo para responder a pergunta.

        Contexto:
        {context}

        Pergunta:
        {question}
        """
    )

    chain = RunnableParallel(
        context=retriever,
        question=RunnablePassthrough()
    ) | prompt | llm

    return chain


# ============================================================
# INTERFACE STREAMLIT
# ============================================================
st.title("📘 Chatbot RAG + Gemini – Metodologia Atualizada")
st.write("Pergunte algo sobre o PDF carregado.")

chain = carregar_rag()

if chain is None:
    st.stop()

user_input = st.text_input("Digite sua pergunta:")

if user_input:
    resposta = chain.invoke(user_input)
    st.write("### 🤖 Resposta:")
    st.write(resposta.content)