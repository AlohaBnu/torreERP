import os
import streamlit as st
import google.generativeai as genai

try:
    import fitz  # PyMuPDF
except ImportError:
    st.error("PyMuPDF não instalado. Adicione 'pymupdf' no requirements.txt.")
    st.stop()


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Chat PO-250",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Chatbot PO-250")
st.caption("Faça perguntas sobre o documento PO-250.")


# ============================================================
# CONFIGURAÇÃO GEMINI
# ============================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# ============================================================
# FUNÇÕES
# ============================================================
@st.cache_data
def ler_pdf_por_paginas(caminho_pdf):
    """
    Lê o PDF e retorna uma lista com texto por página.
    """
    paginas = []

    if not os.path.exists(caminho_pdf):
        return None

    pdf = fitz.open(caminho_pdf)

    for i, pagina in enumerate(pdf, start=1):
        texto = pagina.get_text("text").strip()
        if texto:
            paginas.append({
                "pagina": i,
                "texto": texto
            })

    pdf.close()
    return paginas


def montar_contexto_pdf(paginas):
    """
    Junta o conteúdo do PDF com marcação de página.
    """
    blocos = []
    for item in paginas:
        blocos.append(f"[Página {item['pagina']}]\n{item['texto']}")
    return "\n\n".join(blocos)


def perguntar_ao_gemini(pergunta, contexto_pdf, historico):
    """
    Envia pergunta + contexto + histórico para o Gemini.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
Você é um assistente que responde perguntas com base EXCLUSIVAMENTE no documento PO-250.

Regras:
- Responda apenas com base no conteúdo do documento.
- Não invente informações.
- Se não encontrar a resposta, diga exatamente:
  "Não encontrei essa informação claramente no documento PO-250."
- Sempre que possível, informe a página onde encontrou a resposta.
- Seja claro, objetivo e útil.

Histórico da conversa:
{historico}

Conteúdo do documento:
{contexto_pdf}

Pergunta do usuário:
{pergunta}
"""

    resposta = model.generate_content(prompt)
    return resposta.text if hasattr(resposta, "text") else "Não foi possível gerar resposta."


# ============================================================
# CAMINHO DO PDF
# ============================================================
CAMINHO_PDF = "PO-250.pdf"


# ============================================================
# CARREGAMENTO DO PDF
# ============================================================
paginas_pdf = ler_pdf_por_paginas(CAMINHO_PDF)

if paginas_pdf is None:
    st.error(f"Arquivo não encontrado em: {CAMINHO_PDF}")
    st.stop()

contexto_pdf = montar_contexto_pdf(paginas_pdf)


# ============================================================
# ESTADO DA SESSÃO
# ============================================================
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "historico_texto" not in st.session_state:
    st.session_state.historico_texto = ""


# ============================================================
# LAYOUT
# ============================================================
col1, col2 = st.columns([2.2, 1])

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
            with st.spinner("Consultando documento..."):
                resposta = perguntar_ao_gemini(
                    pergunta=pergunta,
                    contexto_pdf=contexto_pdf,
                    historico=st.session_state.historico_texto
                )

                st.markdown(resposta)

        st.session_state.mensagens.append({"role": "assistant", "content": resposta})

        st.session_state.historico_texto += f"\nUsuário: {pergunta}\nAssistente: {resposta}\n"

with col2:
    st.subheader("Informações")
    st.info(f"**Arquivo carregado:** {CAMINHO_PDF}")
    st.metric("Páginas lidas", len(paginas_pdf))
    st.metric("Mensagens", len(st.session_state.mensagens))

    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.mensagens = []
        st.session_state.historico_texto = ""
        st.rerun()