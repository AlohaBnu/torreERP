import os
import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Chat PO-250", page_icon="📄", layout="wide")
st.title("📄 Chatbot PO-250")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@st.cache_data
def carregar_documento():
    with open("PO-250.txt", "r", encoding="utf-8") as f:
        return f.read()

documento = carregar_documento()

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Pergunte algo sobre o PO-250")

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})

    with st.chat_message("user"):
        st.markdown(pergunta)

    prompt = f"""
Você é um assistente que responde apenas com base no conteúdo abaixo.

Regras:
- Não invente informações.
- Se não encontrar a resposta, diga:
  "Não encontrei essa informação claramente no documento."
- Seja objetivo e claro.

Documento:
{documento}

Pergunta:
{pergunta}
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    resposta = model.generate_content(prompt)

    texto = resposta.text if hasattr(resposta, "text") else "Não foi possível responder."

    with st.chat_message("assistant"):
        st.markdown(texto)

    st.session_state.mensagens.append({"role": "assistant", "content": texto})