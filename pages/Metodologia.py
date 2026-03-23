import os
import re
from typing import List, Dict, Optional

import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Chatbot PO-250",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Chatbot PO-250")
st.caption("Consulta inteligente ao documento PO-250 com memória, fontes e trechos relevantes.")


# ============================================================
# ESTILO
# ============================================================
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
}
[data-testid="stSidebar"] {
    min-width: 320px;
    max-width: 320px;
}
.source-box {
    background: #f8fafc;
    border: 1px solid #dbe2ea;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
}
.small-muted {
    color: #6b7280;
    font-size: 0.9rem;
}
.chat-title {
    font-weight: 600;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# VARIÁVEIS DE AMBIENTE
# ============================================================
load_dotenv()

CAMINHO_ARQUIVO = "PO-250.txt"
MODELO_GEMINI = "gemini-2.5-flash"


# ============================================================
# CHAVE GEMINI
# ============================================================
def obter_gemini_api_key() -> Optional[str]:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


api_key = obter_gemini_api_key()

if not api_key:
    st.error("GEMINI_API_KEY não configurada. Defina nos Secrets do Streamlit Cloud ou no arquivo .env.")
    st.stop()

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"Erro ao configurar a API do Gemini: {e}")
    st.stop()


# ============================================================
# FUNÇÕES DE LEITURA
# ============================================================
@st.cache_data(show_spinner=False)
def carregar_linhas(caminho_arquivo: str) -> Optional[List[str]]:
    if not os.path.exists(caminho_arquivo):
        return None

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        return f.readlines()


@st.cache_data(show_spinner=False)
def criar_blocos(linhas: List[str], linhas_por_bloco: int = 120) -> List[Dict]:
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


def normalizar_texto(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", " ", texto, flags=re.UNICODE)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def buscar_blocos_relevantes(pergunta: str, blocos: List[Dict], top_k: int = 4) -> List[Dict]:
    termos = [t for t in normalizar_texto(pergunta).split() if len(t) > 2]
    ranking = []

    for bloco in blocos:
        texto_bloco = normalizar_texto(bloco["texto"])
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


def montar_contexto(blocos: List[Dict]) -> str:
    partes = []

    for i, bloco in enumerate(blocos, start=1):
        partes.append(
            f"[Fonte {i} | Linhas {bloco['inicio']} a {bloco['fim']}]\n{bloco['texto']}"
        )

    return "\n\n".join(partes)


def resumir_historico(historico: List[str], limite: int = 6) -> str:
    return "\n".join(historico[-limite:])


# ============================================================
# RESPOSTA IA
# ============================================================
def gerar_resposta_po250(pergunta: str, contexto: str, historico: str) -> str:
    model = genai.GenerativeModel(MODELO_GEMINI)

    prompt = f"""
Você é especialista sênior em implantação de ERP e documentação funcional.

Responda com base EXCLUSIVAMENTE nos trechos recebidos do documento PO-250.

REGRAS:
- Responder apenas com base no conteúdo enviado
- Não inventar informações
- Se a resposta não estiver clara, responder exatamente:
  "Não encontrei essa informação claramente no documento PO-250."
- Linguagem objetiva, clara e profissional
- Sempre citar as linhas de onde a resposta foi tirada, quando possível
- Se houver passo a passo no documento, apresentar em ordem
- Se houver regra, condição ou parâmetro técnico, destacar isso claramente
- Não usar emojis
- Não usar markdown em excesso
- Não mencionar que foi gerado por IA

HISTÓRICO RECENTE:
{historico if historico else "Sem histórico anterior."}

TRECHOS RELEVANTES DO DOCUMENTO:
{contexto}

PERGUNTA:
{pergunta}
"""
    response = model.generate_content(prompt)
    return response.text.strip() if hasattr(response, "text") and response.text else "Não foi possível gerar resposta."


def limpar_conversa():
    st.session_state.mensagens = []
    st.session_state.historico = []
    st.session_state.fontes = []


# ============================================================
# CARREGAMENTO DO DOCUMENTO
# ============================================================
linhas = carregar_linhas(CAMINHO_ARQUIVO)

if linhas is None:
    st.error(f"Arquivo não encontrado em: {CAMINHO_ARQUIVO}")
    st.info("Confirme se o arquivo PO-250.txt está dentro da pasta 'documentos'.")
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "historico" not in st.session_state:
    st.session_state.historico = []

if "fontes" not in st.session_state:
    st.session_state.fontes = []


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("Configuração")

    top_k = st.slider(
        "Quantidade de trechos enviados",
        min_value=2,
        max_value=6,
        value=4,
        step=1
    )

    linhas_por_bloco = st.slider(
        "Linhas por bloco",
        min_value=60,
        max_value=200,
        value=120,
        step=20
    )

    blocos = criar_blocos(linhas, linhas_por_bloco=linhas_por_bloco)

    st.divider()

    st.info(f"**Arquivo carregado:** {CAMINHO_ARQUIVO}")
    st.metric("Linhas do arquivo", len(linhas))
    st.metric("Blocos gerados", len(blocos))
    st.metric("Mensagens no chat", len(st.session_state.mensagens))

    st.divider()

    if st.button("🗑️ Limpar conversa", use_container_width=True):
        limpar_conversa()
        st.rerun()


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================
col1, col2 = st.columns([2.4, 1])

with col1:
    st.subheader("Conversa")

    for msg in st.session_state.mensagens:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pergunta = st.chat_input("Pergunte algo sobre o PO-250")

    if pergunta:
        st.session_state.mensagens.append({
            "role": "user",
            "content": pergunta
        })

        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Analisando documento..."):
                try:
                    fontes = buscar_blocos_relevantes(
                        pergunta=pergunta,
                        blocos=blocos,
                        top_k=top_k
                    )

                    contexto = montar_contexto(fontes)
                    historico_resumido = resumir_historico(
                        st.session_state.historico,
                        limite=6
                    )

                    resposta = gerar_resposta_po250(
                        pergunta=pergunta,
                        contexto=contexto,
                        historico=historico_resumido
                    )

                except Exception as e:
                    resposta = f"Erro ao gerar resposta: {e}"
                    fontes = []

                st.markdown(resposta)

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": resposta
        })

        st.session_state.historico.append(f"Usuário: {pergunta}")
        st.session_state.historico.append(f"Assistente: {resposta}")
        st.session_state.fontes = fontes


with col2:
    st.subheader("Fontes da última resposta")

    if st.session_state.fontes:
        for i, fonte in enumerate(st.session_state.fontes, start=1):
            preview = fonte["texto"][:400] + ("..." if len(fonte["texto"]) > 400 else "")

            st.markdown(
                f"""
                <div class="source-box">
                    <strong>Fonte {i}</strong><br>
                    <span class="small-muted">Linhas {fonte['inicio']} a {fonte['fim']}</span>
                    <hr style="margin:8px 0;">
                    <span>{preview}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.caption("As fontes aparecerão após a primeira pergunta.")