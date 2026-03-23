import os
import tempfile
from typing import List, Tuple

import fitz  # PyMuPDF
import streamlit as st
import google.generativeai as genai

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Chat com PDF - Gemini",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Chatbot com PDF")
st.caption("Perguntas e respostas sobre o PDF, com memória, páginas e fontes da resposta.")


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
    min-width: 330px;
    max-width: 330px;
}
.source-box {
    background: #f7f8fc;
    border: 1px solid #dbe2f0;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
}
.small-muted {
    color: #6b7280;
    font-size: 0.9rem;
}
.chat-title {
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def obter_gemini_key() -> str:
    """
    Busca a chave GEMINI_API_KEY do ambiente.
    """
    return os.getenv("GEMINI_API_KEY")


def configurar_gemini():
    """
    Configura o Gemini com a chave de ambiente.
    """
    api_key = obter_gemini_key()
    if not api_key:
        raise ValueError("A variável de ambiente GEMINI_API_KEY não foi definida.")
    genai.configure(api_key=api_key)


def extrair_documentos_pdf(uploaded_file) -> List[Document]:
    """
    Extrai o texto do PDF e cria documentos por página.
    """
    documentos = []

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        temp_path = tmp_file.name

    try:
        pdf = fitz.open(temp_path)

        for numero_pagina, pagina in enumerate(pdf, start=1):
            texto = pagina.get_text("text").strip()

            if texto:
                documentos.append(
                    Document(
                        page_content=texto,
                        metadata={
                            "arquivo": uploaded_file.name,
                            "pagina": numero_pagina
                        }
                    )
                )

        pdf.close()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return documentos


def dividir_documentos(documentos: List[Document]) -> List[Document]:
    """
    Divide em chunks menores preservando metadados.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=180,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    return splitter.split_documents(documentos)


@st.cache_resource(show_spinner=False)
def carregar_embeddings():
    """
    Carrega modelo local de embeddings.
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def criar_vectorstore(chunks: List[Document]):
    """
    Cria o índice vetorial FAISS.
    """
    embeddings = carregar_embeddings()
    return FAISS.from_documents(chunks, embeddings)


def inicializar_memoria():
    """
    Inicializa memória de conversa.
    """
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )


def formatar_historico_memoria(memoria) -> str:
    """
    Converte memória em texto para o prompt.
    """
    mensagens = memoria.chat_memory.messages
    linhas = []

    for msg in mensagens:
        nome_classe = msg.__class__.__name__.lower()
        if "human" in nome_classe:
            linhas.append(f"Usuário: {msg.content}")
        elif "ai" in nome_classe:
            linhas.append(f"Assistente: {msg.content}")

    return "\n".join(linhas).strip()


def buscar_contexto(retriever, pergunta: str, memoria, k: int = 4) -> List[Document]:
    """
    Busca contexto relevante usando a pergunta + histórico recente.
    """
    historico = formatar_historico_memoria(memoria)

    consulta = pergunta
    if historico:
        consulta = f"""
Considere o histórico da conversa abaixo para entender o contexto.

Histórico:
{historico}

Pergunta atual:
{pergunta}
""".strip()

    docs = retriever.get_relevant_documents(consulta)
    return docs[:k]


def montar_prompt(pergunta: str, documentos_contexto: List[Document], memoria) -> str:
    """
    Monta o prompt final para o Gemini.
    """
    historico = formatar_historico_memoria(memoria)

    contexto_blocos = []
    for i, doc in enumerate(documentos_contexto, start=1):
        arquivo = doc.metadata.get("arquivo", "arquivo.pdf")
        pagina = doc.metadata.get("pagina", "?")
        trecho = doc.page_content.strip()

        contexto_blocos.append(
            f"[Fonte {i}] Arquivo: {arquivo} | Página: {pagina}\n{trecho}"
        )

    contexto_final = "\n\n".join(contexto_blocos)

    prompt = f"""
Você é um assistente que responde perguntas com base EXCLUSIVAMENTE no conteúdo do PDF enviado.

Regras obrigatórias:
1. Responda apenas com base no contexto fornecido.
2. Se a resposta não estiver no material, responda exatamente:
   "Não encontrei essa informação claramente no PDF."
3. Seja claro, objetivo e organizado.
4. Sempre que possível, cite as páginas usadas.
5. Considere o histórico da conversa para manter continuidade.
6. Não invente informações.

Histórico da conversa:
{historico if historico else "Sem histórico anterior."}

Contexto do PDF:
{contexto_final}

Pergunta do usuário:
{pergunta}

Resposta:
""".strip()

    return prompt


def gerar_resposta_gemini(prompt: str) -> str:
    """
    Gera resposta usando Gemini.
    """
    configurar_gemini()
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    if hasattr(response, "text") and response.text:
        return response.text.strip()

    return "Não foi possível gerar uma resposta no momento."


def deduplicar_fontes(documentos: List[Document]) -> List[Tuple[str, int, str]]:
    """
    Remove duplicidade das fontes para exibição.
    """
    vistos = set()
    fontes_unicas = []

    for doc in documentos:
        arquivo = doc.metadata.get("arquivo", "arquivo.pdf")
        pagina = doc.metadata.get("pagina", "?")
        trecho = doc.page_content.strip().replace("\n", " ")

        chave = (arquivo, pagina, trecho[:180])

        if chave not in vistos:
            vistos.add(chave)
            fontes_unicas.append((arquivo, pagina, trecho))

    return fontes_unicas


def resetar_chat():
    """
    Limpa o estado da sessão.
    """
    for chave in [
        "messages",
        "vectorstore",
        "retriever",
        "memory",
        "pdf_processado",
        "nome_arquivo",
        "fontes_ultima_resposta"
    ]:
        if chave in st.session_state:
            del st.session_state[chave]


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("Configuração")

    uploaded_file = st.file_uploader(
        "Envie um PDF",
        type=["pdf"]
    )

    k_busca = st.slider(
        "Quantidade de trechos buscados",
        min_value=2,
        max_value=8,
        value=4,
        step=1
    )

    mostrar_fontes = st.toggle("Mostrar fontes utilizadas", value=True)

    st.divider()

    if st.button("🗑️ Limpar conversa", use_container_width=True):
        resetar_chat()
        st.rerun()

    st.divider()
    st.markdown("""
**Como funciona**

1. Você envia um PDF  
2. O sistema extrai o texto  
3. Divide em trechos  
4. Busca os mais relevantes  
5. O Gemini responde com base no documento
""")


# ============================================================
# ESTADO INICIAL
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "fontes_ultima_resposta" not in st.session_state:
    st.session_state.fontes_ultima_resposta = []

if "pdf_processado" not in st.session_state:
    st.session_state.pdf_processado = False


# ============================================================
# PROCESSAMENTO DO PDF
# ============================================================
if uploaded_file and not st.session_state.get("pdf_processado", False):
    api_key = obter_gemini_key()

    if not api_key:
        st.error("Defina a variável de ambiente GEMINI_API_KEY antes de continuar.")
        st.stop()

    with st.spinner("Lendo e indexando o PDF..."):
        documentos = extrair_documentos_pdf(uploaded_file)

        if not documentos:
            st.warning("Não foi possível extrair texto deste PDF.")
            st.stop()

        chunks = dividir_documentos(documentos)
        vectorstore = criar_vectorstore(chunks)
        retriever = vectorstore.as_retriever(search_kwargs={"k": k_busca})
        memory = inicializar_memoria()

        st.session_state.vectorstore = vectorstore
        st.session_state.retriever = retriever
        st.session_state.memory = memory
        st.session_state.pdf_processado = True
        st.session_state.nome_arquivo = uploaded_file.name
        st.session_state.messages = []
        st.session_state.fontes_ultima_resposta = []

    st.success(f"PDF processado com sucesso: {uploaded_file.name}")


# ============================================================
# INTERFACE PRINCIPAL
# ============================================================
if st.session_state.get("pdf_processado", False):
    col1, col2 = st.columns([2.3, 1])

    with col1:
        st.subheader("Conversa")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        pergunta = st.chat_input("Faça uma pergunta sobre o conteúdo do PDF")

        if pergunta:
            st.session_state.messages.append({
                "role": "user",
                "content": pergunta
            })

            with st.chat_message("user"):
                st.markdown(pergunta)

            with st.chat_message("assistant"):
                with st.spinner("Analisando o documento..."):
                    try:
                        retriever = st.session_state.retriever
                        memory = st.session_state.memory

                        docs_relevantes = buscar_contexto(
                            retriever=retriever,
                            pergunta=pergunta,
                            memoria=memory,
                            k=k_busca
                        )

                        prompt = montar_prompt(
                            pergunta=pergunta,
                            documentos_contexto=docs_relevantes,
                            memoria=memory
                        )

                        resposta = gerar_resposta_gemini(prompt)

                        memory.save_context(
                            {"input": pergunta},
                            {"answer": resposta}
                        )

                        st.markdown(resposta)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": resposta
                        })

                        st.session_state.fontes_ultima_resposta = deduplicar_fontes(docs_relevantes)

                    except Exception as e:
                        st.error(f"Erro ao gerar resposta: {str(e)}")

    with col2:
        st.subheader("Informações")

        nome_arquivo = st.session_state.get("nome_arquivo", "PDF")
        st.info(f"**Arquivo carregado:** {nome_arquivo}")

        st.metric("Mensagens na sessão", len(st.session_state.messages))

        if mostrar_fontes:
            st.subheader("Fontes da última resposta")

            fontes = st.session_state.get("fontes_ultima_resposta", [])

            if fontes:
                for idx, (arquivo, pagina, trecho) in enumerate(fontes, start=1):
                    trecho_curto = trecho[:500] + ("..." if len(trecho) > 500 else "")
                    st.markdown(
                        f"""
                        <div class="source-box">
                            <strong>Fonte {idx}</strong><br>
                            <span class="small-muted">Arquivo: {arquivo} | Página: {pagina}</span>
                            <hr style="margin:8px 0;">
                            <span>{trecho_curto}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.caption("As fontes aparecerão após a primeira resposta.")
else:
    st.info("Envie um PDF na barra lateral para começar.")


# ============================================================
# RODAPÉ
# ============================================================
st.divider()
st.caption("Dica: se o PDF for escaneado em imagem, pode ser necessário OCR.")