import os
import streamlit as st
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA

# ============================================================
# CONFIGURAÇÃO GEMINI
# ============================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-1.5-flash"


# ============================================================
# FUNÇÃO PARA CARREGAR E PROCESSAR O PDF (COM CACHE)
# ============================================================
@st.cache_resource
def carregar_base_vetorial():
    pdf_path = "PO-250.pdf"

    if not os.path.exists(pdf_path):
        st.error(f"Arquivo PDF não encontrado: {pdf_path}")
        return None, None

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150
    )

    docs = text_splitter.split_documents(documents)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    vectordb = Chroma.from_documents(docs, embeddings)
    retriever = vectordb.as_retriever(search_kwargs={"k": 4})

    return retriever, documents


# ============================================================
# CONFIGURA O MODELO DE RESPOSTA
# ============================================================
@st.cache_resource
def criar_chain(retriever):
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0.3
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff"
    )


# ============================================================
# INTERFACE STREAMLIT
# ============================================================
st.title("📘 Chatbot RAG + Gemini – Metodologia")
st.write("Faça perguntas sobre o conteúdo do PDF carregado.")

retriever, documento_raw = carregar_base_vetorial()

if retriever is None:
    st.stop()

qa_chain = criar_chain(retriever)

# Entrada do usuário
pergunta = st.text_input("Sua pergunta:")

if pergunta:
    resposta = qa_chain.run(pergunta)
    st.write("### 🤖 Resposta:")
    st.write(resposta)