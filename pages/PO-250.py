from openai import OpenAI
from pypdf import PdfReader

# 🔑 cliente
client = OpenAI()

# 📄 ler PDF
reader = PdfReader("PO-250.pdf")
texto = ""

for page in reader.pages:
    texto += page.extract_text() + "\n"

# ❓ sua pergunta
pergunta = "Liste somente as siglas dos artefatos"

# 🧠 prompt
prompt = f"""
Você é um especialista em PMO.

Baseado no texto abaixo, responda:

REGRAS:
- Retorne apenas siglas
- Não explique nada

TEXTO:
{texto[:15000]}  # limita para não estourar

PERGUNTA:
{pergunta}
"""

# 🚀 chamada
response = client.responses.create(
    model="gpt-5.3",
    input=prompt
)

print(response.output[0].content[0].text)