import streamlit as st
from transformers import pipeline
from utils import extract_text, split_text, create_index, search

# Carregar documento
pdf_path = "PO-250.pdf"
document_text = extract_text(pdf_path)
chunks = split_text(document_text)

# Criar índice FAISS
model, index, chunks = create_index(chunks)

# Carregar modelo de QA otimizado (rápido e leve)
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

def ask_agent(query):
    context = search(query, model, index, chunks)
    # Usar apenas o trecho mais relevante
    best_context = context[0] if context else ""
    response = qa_pipeline(question=query, context=best_context)
    return response["answer"]

# Interface Streamlit
st.title("Agente PO-250 ⚡")
query = st.text_input("Digite sua pergunta:")

if query:
    answer = ask_agent(query)
    st.write("### Resposta:")
    st.write(answer)