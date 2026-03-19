import streamlit as st
from transformers import pipeline
from utils import extract_text, split_text, create_index, search

# Carregar documento
pdf_path = "PO-250.pdf"
document_text = extract_text(pdf_path)
chunks = split_text(document_text)

# Criar índice FAISS
model, index, chunks = create_index(chunks)

# Carregar modelo de linguagem da Hugging Face (gratuito, roda online/local)
qa_pipeline = pipeline("text-generation", model="google/flan-t5-small")

def ask_agent(query):
    context = search(query, model, index, chunks)
    prompt = f"Baseado no documento PO-250, responda:\n\n{context}\n\nPergunta: {query}\nResposta:"
    response = qa_pipeline(prompt, max_length=200, do_sample=False)[0]["generated_text"]
    return response

# Interface Streamlit
st.title("Agente PO-250 📘")
query = st.text_input("Digite sua pergunta:")

if query:
    answer = ask_agent(query)
    st.write("### Resposta:")
    st.write(answer)