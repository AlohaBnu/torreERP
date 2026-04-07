import streamlit as st
import nltk
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# Baixar recursos do nltk (executar uma vez)
nltk.download('punkt')
nltk.download('stopwords')

st.set_page_config(page_title="Resumo de Arquivos", layout="centered")

st.title("📄 Resumo Automático de Arquivo")

uploaded_file = st.file_uploader(
    "Faça upload de um arquivo .txt",
    type=["txt"]
)

def resumir_texto(texto, n_sentencas=5):
    sentencas = sent_tokenize(texto)
    palavras = word_tokenize(texto.lower())

    stop_words = set(stopwords.words("portuguese"))
    palavras_filtradas = [p for p in palavras if p.isalnum() and p not in stop_words]

    frequencia = Counter(palavras_filtradas)

    ranking = {}
    for s in sentencas:
        for palavra in word_tokenize(s.lower()):
            if palavra in frequencia:
                ranking[s] = ranking.get(s, 0) + frequencia[palavra]

    sentencas_resumo = sorted(ranking, key=ranking.get, reverse=True)[:n_sentencas]
    return " ".join(sentencas_resumo)

if uploaded_file:
    texto = uploaded_file.read().decode("utf-8")

    st.subheader("📑 Conteúdo do Arquivo")
    st.text_area("Texto carregado", texto, height=200)

    if st.button("🔍 Gerar resumo"):
        resumo = resumir_texto(texto)
        st.subheader("✅ Resumo")
        st.write(resumo)