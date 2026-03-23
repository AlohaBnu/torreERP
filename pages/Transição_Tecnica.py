import streamlit as st
import mysql.connector as mc
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURAÇÃO GEMINI
# ============================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ============================================================
# CONFIGURAÇÃO STREAMLIT
# ============================================================
st.set_page_config(page_title="Resumo Inteligente de Agenda", layout="wide")

# ============================================================
# BANCO
# ============================================================
DB_CONFIG = {
    "host": "172.31.20.168",
    "user": "fast",
    "password": "kK3F6737IER3d-sf*",
    "database": "fast",
}

def get_connection():
    return mc.connect(**DB_CONFIG)

# ============================================================
# BUSCAR PROJETOS ERP
# ============================================================
def buscar_projetos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
    SELECT idProjeto,nome 
    FROM projeto 
    WHERE idProduto = 1 
      AND idProdutoCronograma = 38 
      AND nome LIKE '%ERP%'
    """
    cursor.execute(sql)
    dados = cursor.fetchall()
    conn.close()
    return dados

# ============================================================
# BUSCAR ATIVIDADES
# ============================================================
def buscar_atividades(idProjeto):
    conn = get_connection()
    sql = """
    SELECT 
        p.nome,
        ap.datAtividade,
        ap.atividade
    FROM projeto p
    INNER JOIN atividadesprojeto ap 
        ON ap.idProjeto = p.idProjeto
    WHERE 
        p.idProduto = 1 
        AND p.idProdutoCronograma = 38 
        AND p.nome LIKE '%ERP%'
        AND p.idProjeto = %s
        AND ap.melhoriaRisco = 3
    ORDER BY 
        ap.datAtividade DESC
    """
    df = pd.read_sql(sql, conn, params=(idProjeto,))
    conn.close()
    return df

# ============================================================
# INSERT ATIVIDADE
# ============================================================
def inserir_atividade(idProjeto, resumo):
    import mysql.connector
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # =====================================================
        # 1 - INSERE ATIVIDADE NO FEED
        # =====================================================
        sql_feed = """
        INSERT INTO fast.atividadesprojeto
        (
            idProjeto,
            idUsuario,
            datAtividade,
            atividade,
            melhoriaRisco,
            idMensagem,
            nivel,
            previsao,
            conclusao
        )
        VALUES
        (
            %s,
            %s,
            NOW(),
            %s,
            %s,
            NULL,
            %s,
            NULL,
            NULL
        )
        """
        valores_feed = (idProjeto, 703, resumo, 3, 1)
        cursor.execute(sql_feed, valores_feed)

        # =====================================================
        # 2 - BUSCA PRÓXIMO ID DA METODOLOGIA
        # =====================================================
        cursor.execute("""
        SELECT IFNULL(MAX(idAtividadesMetodologiaProjeto),0)+1
        FROM fast.atividadesmetodologiaprojeto
        """)
        novo_id = cursor.fetchone()[0]

        # =====================================================
        # 3 - INSERE NA METODOLOGIA DO PROJETO
        # =====================================================
        sql_metodologia = """
        INSERT INTO fast.atividadesmetodologiaprojeto
        (
            idAtividadesMetodologiaProjeto,
            idProjeto,
            idUsuario,
            idAtividadesMetodologia,
            datMarcacao,
            tipo
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            NOW(),
            %s
        )
        """
        valores_met = (novo_id, idProjeto, 703, 586, 0)
        cursor.execute(sql_metodologia, valores_met)

        # =====================================================
        # COMMIT FINAL (GRAVA OS DOIS)
        # =====================================================
        conn.commit()

        cursor.close()
        conn.close()
        return True

    except mysql.connector.Error as err:
        conn.rollback()
        st.error(f"Erro MySQL: {err}")
        return False

# ============================================================
# RESUMO IA
# ============================================================
def gerar_resumo(transcricao):
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
Você é especialista sênior em implantação de ERP.
Gere um resumo executivo estruturado em HTML com padrão corporativo.

REGRAS:
- Usar <b> para títulos
- Usar <br> para quebra de linha
- Usar <hr> como divisor elegante
- Linguagem objetiva, clara e executiva
- Não repetir informações
- Não usar emojis
- Não usar markdown
- Não colocar explicações extras
- Não mencionar que foi gerado por IA

FORMATO EXATO:
<b style="font-size:16px;">AGENDA TÉCNICA – PROJETO ERP</b>
<hr>
<b>1. Resumo Geral</b><br>
Texto estruturado em até 5 linhas.
<br><br>
<b>2. Momento do Cliente</b><br>
Análise objetiva do cenário atual.
<br><br>
<b>3. Situação Comercial</b><br>
Status contratual / financeiro se houver.
<br><br>
<b>4. Riscos Identificados</b><br>
Listar riscos usando:
- Item<br>
- Item<br>
<br><br>
<b>5. Próximos Passos</b><br>
Listar ações objetivas:
- Ação + responsável + prazo (se houver)<br>
Transcrição:
{transcricao}
"""
    response = model.generate_content(prompt)
    return response.text

# ============================================================
# TELA PRINCIPAL
# ============================================================
st.title("📝 Transição Técnica ERP")

# SESSION STATE
if "resumo_gerado" not in st.session_state:
    st.session_state.resumo_gerado = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

# PROJETOS
projetos = buscar_projetos()
mapa = {p["nome"]: p["idProjeto"] for p in projetos}
projeto_opcoes = ["Selecionar Projeto"] + list(mapa.keys())
projeto_nome = st.selectbox("Selecione o Projeto ERP", projeto_opcoes)
idProjeto = mapa.get(projeto_nome, None)

# RESUMO DE REUNIÃO
st.subheader("📄 Cole a transcrição da reunião")
texto = st.text_area("Cole aqui o conteúdo da reunião", height=300)

if st.button("🧠 Gerar Resumo com IA"):
    if idProjeto is None:
        st.warning("Selecione um projeto antes de gerar o resumo.")
    elif texto.strip() == "":
        st.warning("Cole algum conteúdo antes de processar.")
    else:
        with st.spinner("Processando reunião com IA..."):
            resumo = gerar_resumo(texto)
            st.session_state.resumo_gerado = resumo

if st.session_state.resumo_gerado != "":
    st.subheader("📌 Resumo Gerado")
    st.text_area("", st.session_state.resumo_gerado, height=350)
    if st.button("📥 Publicar no Feed do Projeto"):
        if inserir_atividade(idProjeto, st.session_state.resumo_gerado):
            st.success("Resumo publicado!")
            st.session_state.resumo_gerado = ""
        else:
            st.error("Erro ao inserir no banco!")

# ===================================
# BOTÃO DE CHAT (ROBOZINHO)
# ===================================
st.markdown(
    """
    <style>
    .chatbot-button {
        position: fixed;
        bottom: 25px;
        right: 25px;
        background-color: #4CAF50;
        color: white;
        border-radius: 50%;
        font-size: 30px;
        width: 60px;
        height: 60px;
        text-align: center;
        cursor: pointer;
        box-shadow: 2px 2px 10px gray;
        z-index:999;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if st.button("🤖", key="open_chat"):
    st.session_state.chat_open = not st.session_state.chat_open

# ===================================
# CHAT LATERAL SIMULADO
# ===================================
if st.session_state.chat_open and idProjeto is not None:
    with st.expander("💬 Chat do Projeto ERP", expanded=True):
        pergunta = st.text_input("Faça uma pergunta ao projeto")
        if st.button("Enviar Pergunta", key="send_chat") and pergunta.strip() != "":
            df_atividades = buscar_atividades(idProjeto)
            contexto = "\n".join(df_atividades["atividade"].tolist())
            prompt_chat = f"""
Você é um assistente especialista em implantação de ERP.
Use as atividades do projeto abaixo como contexto para responder a pergunta do usuário.

Contexto do Projeto:
{contexto}

Pergunta:
{pergunta}

Responda de forma clara, objetiva e profissional, sem explicações extras.
"""
            model = genai.GenerativeModel("gemini-2.5-flash")
            resposta = model.generate_content(prompt_chat).text
            st.session_state.chat_history.append(("Usuário", pergunta))
            st.session_state.chat_history.append(("Bot", resposta))

        for remetente, mensagem in st.session_state.chat_history:
            if remetente == "Usuário":
                st.markdown(f"**Você:** {mensagem}")
            else:
                st.markdown(f"**Bot:** {mensagem}")

# HISTÓRICO DE ATIVIDADES
if idProjeto is not None:
    st.subheader("📜 Histórico de Atividades do Projeto")
    df = buscar_atividades(idProjeto)
    st.dataframe(df, use_container_width=True)