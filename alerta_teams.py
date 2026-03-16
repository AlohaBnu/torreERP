import pandas as pd
from datetime import datetime
import requests
import json

# WEBHOOK
url = "SEU_WEBHOOK_TEAMS"

def enviar_teams(mensagem):

    payload = {"text": mensagem}
    headers = {"Content-Type": "application/json"}

    r = requests.post(url, data=json.dumps(payload), headers=headers)

    return r.status_code == 200


# -------------------------
# CARREGAR PLANILHA
# -------------------------

arquivo = "projetos.xlsx"

df = pd.read_excel(arquivo)

df["Criacao"] = pd.to_datetime(df["Criacao"], errors="coerce").dt.date

hoje = datetime.today().date()

df["Dias"] = (hoje - df["Criacao"]).apply(lambda x: x.days)

df_risco = df[df["Primeiro Contato"] == False]


mensagem = "🚨 ALERTA PROJETOS SEM CONTATO\n\n"

for _, row in df_risco.iterrows():

    mensagem += f"{row['Projeto']} | {row['Gerente']} | {row['Dias']} dias\n"


if not df_risco.empty:
    enviar_teams(mensagem)