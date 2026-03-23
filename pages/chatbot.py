from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
import os

# 1. Configuração da chave (ou use Azure/OpenAI compatível)
os.environ["OPENAI_API_KEY"] = "SUA_API_KEY_AQUI"

# 2. Carregar PDF
loader = PyPDFLoader("PO-250.pdf")
documents = loader.load()

# 3. Dividir o texto em pedaços
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
docs = text_splitter.split_documents(documents)

# 4. Criar embeddings + índice vetorial
embeddings = OpenAIEmbeddings()
vectordb = Chroma.from_documents(docs, embeddings)

# 5. Criar mecanismo de busca
retriever = vectordb.as_retriever()

# 6. Criar pipeline RAG (busca + LLM)
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(temperature=0),
    chain_type="stuff",
    retriever=retriever,
)

# 7. Loop de chatbot
print("Chatbot iniciado! Pergunte algo sobre o PDF.\n")
while True:
    pergunta = input("Você: ")
    if pergunta.lower() in ["sair", "exit", "quit"]:
        print("Encerrando chatbot...")
        break
    
    resposta = qa_chain.run(pergunta)
    print("\nBot:", resposta, "\n")