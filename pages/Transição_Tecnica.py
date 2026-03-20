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

MODEL_NAME = "gemini-1.5-flash"

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Assistente de Metodologia de Projetos",
    page_icon="📘",
    layout="wide"
)

# ============================================================
# PROMPT BASE
# ============================================================
PROMPT_SISTEMA = """
Você é um especialista sênior em metodologia de projetos, PMO e governança corporativa.

Seu objetivo é responder dúvidas e orientar usuários sobre processos, documentos, ritos, papéis, controles e boas práticas de gerenciamento de projetos.

Você domina:
- PMBOK
- Agile, Scrum e Kanban
- metodologia híbrida
- governança de projetos e portfólio
- cronograma
- escopo
- riscos
- custos
- qualidade
- comunicação
- stakeholders
- indicadores
- status report
- RAID
- change request
- lições aprendidas
- RACI
- kickoff
- encerramento de projeto

Regras:
- responda sempre em português do Brasil
- use linguagem clara, profissional e objetiva
- priorize aplicação prática no ambiente corporativo
- sempre que possível, apresente a resposta com:
  1. conceito
  2. como aplicar
  3. exemplo prático1
  4. recomendação
- quando a pergunta estiver genérica, responda considerando o cenário corporativo mais comum
- não invente processos internos que não foram informados
- se houver mais de uma abordagem, apresente a mais recomendada e cite alternativas
- ajude o usuário a tomar decisão com segurança e clareza

Se a pergunta envolver criação de artefatos de projeto, também ajude com modelos, exemplos e estrutura sugerida.
"""

# ============================================================
# FUNÇÃO PARA CONSULTAR O GEMINI
# ============================================================
def perguntar_ia(pergunta, historico=None):
    try:
        model = genai.GenerativeModel(MODEL_NAME)

        contexto_historico = ""
        if historico:
            for msg in historico[-10:]:
                papel = "Usuário" if msg["role"] == "user" else "Assistente"
                contexto_historico += f"{papel}: {msg['content']}\n"

        prompt_final = f"""
{PROMPT_SISTEMA}

Histórico da conversa:
{contexto_historico}

Pergunta atual do usuário:
{pergunta}

Responda de forma organizada, útil e prática.
"""

        response = model.generate_content(prompt_final)
        return response.text

    except Exception as e:
        return f"Erro ao consultar a IA: {str(e)}"

# ============================================================
# INTERFACE
# ============================================================
st.title("📘 Assistente de Metodologia de Projetos")
st.caption("Faça perguntas sobre PMO, governança, cronograma, riscos, status report, RAID, RACI e boas práticas de projetos.")

with st.sidebar:
    st.header("Configuração")
    st.info("Este assistente usa um prompt fixo para responder sobre metodologia de projetos.")
    
    st.subheader("Sugestões de perguntas")
    st.markdown("""
- Como estruturar um kickoff de projeto?
- O que deve ter em um status report executivo?
- Como montar uma matriz RACI?
- Como tratar riscos em projetos?
- Qual a diferença entre issue e risco?
- Como padronizar a governança de projetos?
""")

# ============================================================
# ESTADO DA CONVERSA
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Botão para limpar histórico
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# MOSTRAR HISTÓRICO
# ============================================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ============================================================
# ENTRADA DO USUÁRIO
# ============================================================
pergunta = st.chat_input("Digite sua pergunta sobre metodologia de projetos")

if pergunta:
    # Exibe pergunta
    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    # Gera resposta
    with st.chat_message("assistant"):
        with st.spinner("Pensando na melhor resposta..."):
            resposta = perguntar_ia(pergunta, st.session_state.messages)

        st.markdown(resposta)

    # Salva resposta no histórico
    st.session_state.messages.append({"role": "assistant", "content": resposta})