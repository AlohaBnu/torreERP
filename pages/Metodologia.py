import os
import streamlit as st
import google.generativeai as genai

# Importações atualizadas do LangChain moderno
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
# FUNÇÃO COM CACHE PARA CARREGAR PDF E MONTAR O RAG
# ============================================================
@st.cache_resource
def montar_rag():

    pdf_path = "PO-250.pdf"

    if not os.path.exists(pdf_path):
        st.error(f"Arquivo não encontrado: {pdf_path}")
        return None

    # 1. Carregar PDF
    loader = PyPDFLoader(pdf_path)
    documentos = loader.load()

    # 2. Dividir PDF em chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    docs = splitter.split_documents(documentos)

    # 3. Embeddings corretos do Gemini (modelo novo)
    embeddings = GoogleGenerativeAIEmbeddings(
        model_name="models/text-embedding-004"
    )

    # 4. Criar base vetorial Chroma
    vectorstore = Chroma.from_documents(docs, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # 5. Modelo de linguagem Gemini
    llm = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0.2
    )

    # 6. Novo prompt oficial do LCEL
    prompt = ChatPromptTemplate.from_template(
        """
        Você é um assistente especializado.
        Use SOMENTE o contexto abaixo para responder.

        CONTEXTO:
        {context}

        PERGUNTA:
        {question}
        """
    )

    # 7. Pipeline moderno LangChain (2025+)
    chain = (
        RunnableParallel(
            context=retriever,
            question=RunnablePassthrough()
        )
        | prompt
        | llm
    )

    return chain


# ============================================================
# INTERFACE STREAMLIT
# ============================================================
st.title("📘 Chatbot de Metodologia — RAG + Gemini")
st.write("Faça perguntas sobre o conteúdo do PDF carregado.")

chain = montar_rag()

if chain is None:
    st.stop()

# Entrada do usuário
pergunta = st.text_input("Digite sua pergunta:")

if pergunta:
    resposta = chain.invoke(pergunta)
    st.write("### 🤖 Resposta:")
    st.write(resposta.content)