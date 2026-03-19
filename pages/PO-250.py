import streamlit as st
from gpt4all import GPT4All
from utils import extract_text, split_text, create_index, search

# Carregar documento
pdf_path = "PO-250.pdf"
document_text = extract_text(pdf_path)
chunks = split_text(document_text)

# Criar índice FAISS
model, index, chunks = create_index(chunks)

# Carregar LLM local (modelo gratuito)
llm = GPT4All("gpt4all-falcon-q4.bin")  # baixe o modelo antes

# Função do agente
def ask_agent(query):
    context = search(query, model, index, chunks)
    prompt = f"Baseado no documento PO-250, responda:\n\n{context}\n\nPergunta: {query}\nResposta:"
    response = llm.generate(prompt)
    return response

# Interface Streamlit
st.title("Agente PO-250 📘")
query = st.text_input("Digite sua pergunta:")

if query:
    answer = ask_agent(query)
    st.write("### Resposta:")
    st.write(answer)