import streamlit as st
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

st.title("Resumo de Documento com Gemini")

texto = st.text_area("Cole o texto do documento")

if st.button("Resumir"):
    resposta = model.generate_content(
        f"Resuma o texto abaixo em tópicos objetivos:\n\n{texto}"
    )
    st.markdown(resposta.text)
