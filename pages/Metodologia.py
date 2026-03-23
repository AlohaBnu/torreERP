import os
import re
import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Chat PO-250", page_icon="📄", layout="wide")
st.title("📄 Chatbot PO-250")
st.caption("Consulta rápida ao documento usando trechos relevantes.")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Defina a variável de ambiente GEMINI_API_KEY.")
    st.stop()

genai.configure(api_key=api_key)


@st.cache_data
def carregar_linhas(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        return f.readlines()


@st.cache_data
def criar_blocos(linhas, linhas_por_bloco=120):
    blocos = []

    for i in range(0, len(linhas), linhas_por_bloco):
        trecho = "".join(linhas[i:i + linhas_por_bloco]).strip()
        if trecho:
            blocos.append({
                "inicio": i + 1,
                "fim": min(i + linhas_por_bloco, len(linhas)),
                "texto": trecho
            })

    return blocos


def normalizar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", " ", texto)
    return texto


def buscar_blocos_relevantes(pergunta, blocos, top_k=4):
    termos = [t for t in normalizar(pergunta).split() if len(t) > 2]
    ranking = []

    for bloco in blocos:
        texto_bloco = normalizar(bloco["texto"])
        score = 0

        for termo in termos:
            score += texto_bloco.count(termo)

        if score > 0:
            ranking.append((score, bloco))

    ranking.sort(key=lambda x: x[0], reverse=True)

    melhores = [item[1] for item in ranking[:top_k]]

    if not melhores:
        melhores = blocos[:top_k]

    return melhores


def montar_contexto(blocos):
    partes = []
    for i, bloco in enumerate(blocos, start=1):
        partes.append(
            f"[Fonte {i} | Linhas {bloco['inicio']} a {bloco['fim']}]\n{bloco['texto']}"
        )
    return "\n\n".join(partes)


def resumir_historico(historico, limite=6):
    return "\n".join(historico[-limite:])


def perguntar_gemini(pergunta, contexto, historico):
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
Você responde EXCLUSIVAMENTE com base nos trechos do documento PO-250.

Regras:
- Não invente informações.
- Se a resposta não estiver clara nos trechos recebidos, diga:
  "Não encontrei essa informação claramente no documento PO-250."
- Seja objetivo e útil.
- Sempre que possível, cite as linhas de onde tirou a resposta.

Histórico recente:
{historico}

Trechos relevantes do documento:
{contexto}

Pergunta do usuário:
{pergunta}
"""

    resposta = model.generate_content(prompt)
    if hasattr(resposta, "text") and resposta.text:
        return resposta.text.strip()

    return "Não foi possível gerar resposta."


CAMINHO_ARQUIVO = "PO-250.txt"

if not os.path.exists(CAMINHO_ARQUIVO):
    st.error(f"Arquivo não encontrado: {CAMINHO_ARQUIVO}")
    st.stop()

linhas = carregar_linhas(CAMINHO_ARQUIVO)
blocos = criar_blocos(linhas, linhas_por_bloco=120)

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "historico" not in st.session_state:
    st.session_state.historico = []

if "fontes" not in st.session_state:
    st.session_state.fontes = []

col1, col2 = st.columns([2.4, 1])

with col1:
    st.subheader("Conversa")

    for msg in st.session_state.mensagens:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pergunta = st.chat_input("Pergunte algo sobre o PO-250")

    if pergunta:
        st.session_state.mensagens.append({"role": "user", "content": pergunta})

        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Buscando trechos relevantes..."):
                fontes = buscar_blocos_relevantes(pergunta, blocos, top_k=4)
                contexto = montar_contexto(fontes)
                historico_resumido = resumir_historico(st.session_state.historico, limite=6)

                resposta = perguntar_gemini(
                    pergunta=pergunta,
                    contexto=contexto,
                    historico=historico_resumido
                )

                st.markdown(resposta)

        st.session_state.mensagens.append({"role": "assistant", "content": resposta})
        st.session_state.historico.append(f"Usuário: {pergunta}")
        st.session_state.historico.append(f"Assistente: {resposta}")
        st.session_state.fontes = fontes

with col2:
    st.subheader("Informações")
    st.info(f"**Arquivo:** {CAMINHO_ARQUIVO}")
    st.metric("Linhas", len(linhas))
    st.metric("Blocos", len(blocos))
    st.metric("Mensagens", len(st.session_state.mensagens))

    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.session_state.historico = []
        st.session_state.fontes = []
        st.rerun()

    st.subheader("Fontes da última resposta")

    if st.session_state.fontes:
        for i, fonte in enumerate(st.session_state.fontes, start=1):
            preview = fonte["texto"][:300] + ("..." if len(fonte["texto"]) > 300 else "")
            st.markdown(f"**Fonte {i} — Linhas {fonte['inicio']} a {fonte['fim']}**")
            st.caption(preview)
    else:
        st.caption("As fontes aparecerão após a primeira pergunta.")