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
st.caption("Consulta rápida ao documento com busca por trechos relevantes e resposta via Gemini.")


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
</style>
""", unsafe_allow_html=True)


# ============================================================
# CARREGAMENTO DE VARIÁVEIS
# ============================================================
load_dotenv()

CAMINHO_ARQUIVO = "PO-250.txt"
MODELOS_CANDIDATOS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


# ============================================================
# CHAVE DA API
# ============================================================
def obter_gemini_api_key() -> Optional[str]:
    """
    Busca a chave do Gemini na seguinte ordem:
    1. st.secrets
    2. variável de ambiente (.env/local)
    """
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
# FUNÇÕES DE LEITURA E INDEXAÇÃO
# ============================================================
@st.cache_data(show_spinner=False)
def carregar_linhas(caminho_arquivo: str) -> Optional[List[str]]:
    if not os.path.exists(caminho_arquivo):
        return None

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        return f.readlines()


@st.cache_data(show_spinner=False)
def criar_blocos(linhas: List[str], linhas_por_bloco: int = 120) -> List[Dict]:
    """
    Divide o documento em blocos de linhas para acelerar a busca.
    """
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
    """
    Busca simples por relevância lexical.
    """
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
# FUNÇÕES GEMINI
# ============================================================
def gerar_prompt(pergunta: str, contexto: str, historico: str) -> str:
    return f"""
Você é um assistente que responde EXCLUSIVAMENTE com base nos trechos do documento PO-250.

Regras obrigatórias:
1. Não invente informações.
2. Responda apenas com base nos trechos recebidos.
3. Se a resposta não estiver clara, diga exatamente:
   "Não encontrei essa informação claramente no documento PO-250."
4. Seja claro, objetivo e útil.
5. Sempre que possível, cite as linhas de onde a resposta foi tirada.

Histórico recente da conversa:
{historico if historico else "Sem histórico anterior."}

Trechos relevantes do documento:
{contexto}

Pergunta do usuário:
{pergunta}
""".strip()


def perguntar_gemini(pergunta: str, contexto: str, historico: str) -> str:
    """
    Tenta modelos em sequência para evitar NotFound/modelo indisponível.
    """
    prompt = gerar_prompt(pergunta, contexto, historico)
    erros = []

    for nome_modelo in MODELOS_CANDIDATOS:
        try:
            model = genai.GenerativeModel(nome_modelo)
            response = model.generate_content(prompt)

            texto = getattr(response, "text", None)
            if texto and str(texto).strip():
                return str(texto).strip()

            erros.append(f"{nome_modelo}: resposta vazia")
        except Exception as e:
            erros.append(f"{nome_modelo}: {e}")

    return (
        "Não foi possível gerar resposta no momento.\n\n"
        "Verifique:\n"
        "- se a chave do Gemini está correta\n"
        "- se o projeto tem acesso aos modelos\n"
        "- se há restrição de modelo/região\n\n"
        "Detalhes técnicos:\n" + "\n".join(erros)
    )


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
# ESTADO DA SESSÃO
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
col1, col2 = st.columns([2.3, 1])

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
            with st.spinner("Buscando os trechos mais relevantes..."):
                try:
                    fontes = buscar_blocos_relevantes(
                        pergunta=pergunta,
                        blocos=blocos,
                        top_k=top_k
                    )

                    contexto = montar_contexto(fontes)
                    historico_resumido = resumir_historico(st.session_state.historico, limite=6)

                    resposta = perguntar_gemini(
                        pergunta=pergunta,
                        contexto=contexto,
                        historico=historico_resumido
                    )
                except Exception as e:
                    resposta = f"Erro ao processar a pergunta: {e}"
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