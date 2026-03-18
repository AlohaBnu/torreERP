import pandas as pd
from datetime import datetime
import requests
import json

# 🔵 WEBHOOK
def enviar_teams(mensagem):
    url = "https://seniorsistemassa.webhook.office.com/webhookb2/2ec08012-d3e0-4d18-be82-b95599cc930f@62c7b02d-a95c-498b-9a7f-6e00acab728d/IncomingWebhook/6ac41ddb5ab948a4807134eba796d50d/5ba9219d-0082-4f37-85b4-2e8c7b765ebb/V2Yce2GRpGah5YqEisv4OzDPg91rLg6dZy1IJkJv5d5P01"

    payload = {"text": mensagem}
    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return r.status_code == 200
    except:
        return False


# 🔵 CARREGAR PLANILHA
arquivo = "caminho/da/sua_planilha.xlsx"
df = pd.read_excel(arquivo)

# 🔵 SUA LÓGICA (resumida aqui)
hoje = datetime.today().date()

df["criacao"] = pd.to_datetime(df["criacao"]).dt.date

df["dias"] = (hoje - df["criacao"]).apply(lambda x: x.days)

df_risco = df[df["dias"] > 2]

# 🔵 MENSAGEM
mensagem = "🚨 ALERTA AUTOMÁTICO\n\n"

for _, row in df_risco.iterrows():
    mensagem += f"{row['projeto']} - {row['dias']} dias\n"

# 🔵 ENVIO
if not df_risco.empty:
    enviar_teams(mensagem)