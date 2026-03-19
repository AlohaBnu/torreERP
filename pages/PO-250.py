import streamlit as st
from utils import extract_text, split_text, create_index, search

# Caminho do documento PDF
pdf_path = "PO-250.pdf"

# Extrair texto do PDF
document_text = extract_text(pdf_path)

# Dividir em chunks menores
chunks = split_text(document_text)

# Criar índice FAISS com embeddings
model, index, chunks = create_index(chunks)

# Função principal do agente
def ask_agent(query):
    context = search(query, model, index, chunks)
    if not context:
        return "Nenhum trecho relevante encontrado no documento."
    return "\n\n".join(context)

# Interface Streamlit
st.title("Agente PO-250 ⚡ (versão rápida)")
st.write("Faça perguntas sobre o documento PO-250 e receba os trechos relevantes.")

query = st.text_input("Digite sua pergunta:")

if query:
    answer = ask_agent(query)
    st.write("### Trechos encontrados:")
    st.write(answer)