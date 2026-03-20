import streamlit as st

st.set_page_config(page_title="Metodologia de Projetos", layout="wide")

PROMPT_BASE = """
Você é um especialista em metodologia de projetos, PMO e governança.
Responda em português do Brasil, de forma objetiva, clara e prática.
Sempre priorize boas práticas e exemplos aplicáveis no ambiente corporativo.
"""

st.title("💬 Assistente de Metodologia de Projetos")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Pergunte sobre metodologia de projetos")

if pergunta:
    st.session_state.messages.append({"role": "user", "content": pergunta})

    with st.chat_message("user"):
        st.markdown(pergunta)

    # Simulação de resposta
    resposta = f"""
Com base na metodologia de projetos, minha orientação para sua pergunta foi:

**Pergunta:** {pergunta}

**Resposta exemplo:**  
Aqui você conectará o modelo de IA usando o prompt base + a pergunta do usuário.
"""

    st.session_state.messages.append({"role": "assistant", "content": resposta})

    with st.chat_message("assistant"):
        st.markdown(resposta)