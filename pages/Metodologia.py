import os
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI

# ============================================================
# CONFIGURAÇÃO GEMINI
# ============================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-1.5-flash"

# ============================================================
# CARREGAR E PREPARAR PDF
# ============================================================
loader = PyPDFLoader("docs/arquivo.pdf")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=150
)

docs = text_splitter.split_documents(documents)

# ============================================================
# EMBEDDINGS DO GEMINI
# ============================================================
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

vectordb = Chroma.from_documents(docs, embeddings)

retriever = vectordb.as_retriever(search_kwargs={"k": 4})

# ============================================================
# MODELO GEMINI PARA RESPOSTAS
# ============================================================
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0.2
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff"
)

# ============================================================
# CHATBOT
# ============================================================
print("\n💬 Chatbot RAG + Gemini iniciado!")
print("Digite 'sair' para encerrar.\n")

while True:
    pergunta = input("Você: ")

    if pergunta.lower() in ["sair", "exit", "quit"]:
        print("Encerrando chatbot...")
        break

    resposta = qa_chain.run(pergunta)
    print("\n🤖 Bot:", resposta, "\n")