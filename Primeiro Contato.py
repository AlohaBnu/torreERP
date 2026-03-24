import streamlit as st

st.set_page_config(page_title="Portal Torre ERP", page_icon="📊", layout="centered")

st.title("📊 Portal Torre ERP")

st.write("Bem-vindo ao portal.")
st.write("Aqui você encontrará tudo sobre a nossa Torre.")

st.subheader("📄 Documentações")

# Link clicável e bonito
st.markdown(
    """
    🔗 **Acesse o PO-250:**  
    [Clique aqui para abrir o documento](https://seniorsistemassa.sharepoint.com/sites/SGPinicial/SitePages/PO250.aspx?csf=1&web=1&e=aqMc6F&CID=38dd7acc-1564-455a-8e0b-941daf733808)
    """
)

st.markdown(
    """
    🔗 **Acesso as documentações da Central PMO:**  
    [Clique aqui para abrir o documento](https://seniorsistemassa.sharepoint.com/sites/CentralDSE/SitePages/Central%20PMO.aspx?xsdata=MDV8MDJ8fGNkMjM0NTBiMjJkNTRiMWNhOWYwMDhkZDI2N2Q1ODMyfDYyYzdiMDJkYTk1YzQ5OGI5YTdmNmUwMGFjYWI3MjhkfDB8MHw2Mzg3MDkwNDE5NDg5NjEyNjR8VW5rbm93bnxWR1ZoYlhOVFpXTjFjbWwwZVZObGNuWnBZMlY4ZXlKV0lqb2lNQzR3TGpBd01EQWlMQ0pRSWpvaVYybHVNeklpTENKQlRpSTZJazkwYUdWeUlpd2lWMVFpT2pFeGZRPT18MXxMMk5vWVhSekx6RTVPalZpWVRreU1UbGtMVEF3T0RJdE5HWXpOeTA0TldJMExUSmxPR00zWWpjMk5XVmlZbDlpWTJKaE9ERmhPQzAxWlROaUxUUTFNV010WVdJeFlTMDNaVFEwWWprMk1XVXdaakJBZFc1eExtZGliQzV6Y0dGalpYTXZiV1Z6YzJGblpYTXZNVGN6TlRNd056TTVORFU1Tnc9PXwyM2ZhZmRiYjU1OTA0NjgzYTlmMDA4ZGQyNjdkNTgzMnwxMDAxOWM4YWU2NDU0MmIwOTQyNTE5ZmY2YTQ2MTkxNA%3D%3D&sdata=YkQxcnRyVWtrWnJCaXAreGQrZkhUb0tIV0dxcjV5OFBQZUhuNEhnMU0zWT0%3D&ovuser=62c7b02d-a95c-498b-9a7f-6e00acab728d%2Crafael.audibert%40senior.com.br&OR=Teams-HL&CT=1751913964761&clickparams=eyJBcHBOYW1lIjoiVGVhbXMtRGVza3RvcCIsIkFwcFZlcnNpb24iOiI0OS8yNTA2MTIxNjQyMSIsIkhhc0ZlZGVyYXRlZFVzZXIiOmZhbHNlfQ%3D%3D)
    """
)

st.subheader("📄 Ferramentas para Projetos")

st.markdown(
    """
    🔗 **ServiceNow: Ferramenta para Recepção de Projetos, Plano de Recursos, Apontamento de Horas** <br>
    **Área Responsável**: Governança <br>
    <a href="https://seniorprod.service-now.com">Clique aqui para abrir o ServiceNow</a>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    🔗 **Fast Project: Ferramenta para Gestão de Projetos** <br>
    **Área Responsável**: Torre ERP (Rafael Audibert) <br>
    [Clique aqui para abrir o FastProject](https://fastproject.senior.com.br)
    """,
    unsafe_allow_html=True
)


st.subheader("📄 Ferramentas de Suporte")


st.markdown(
    """
    🔗 **ZenDesk: Ferramenta de Suporte** <br>
    **Área Responsável**: Suporte Senior - Produto e IT Services  
    [Clique aqui para abrir o ZenDesk](https://suporte.senior.com.br)
    """,
    unsafe_allow_html=True
)

