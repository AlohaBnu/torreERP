import streamlit as st

st.set_page_config(page_title="Portal Torre ERP", page_icon="📊", layout="centered")

st.title("📊 Portal Torre ERP")

st.write("Bem-vindo ao portal.")
st.write("Aqui você encontrará tudo sobre a Torre ERP.")

st.subheader("📄 Documentação")

# Link clicável e bonito
st.markdown(
    """
    🔗 **Acesse o PO-250:**  
    [Clique aqui para abrir o documento](https://seniorsistemassa.sharepoint.com/sites/SGPinicial/SitePages/PO250.aspx?csf=1&web=1&e=aqMc6F&CID=38dd7acc-1564-455a-8e0b-941daf733808)
    """
)

# Imagem PNG abaixo
st.image("squadFoundation.png", caption="Portal Torre ERP", use_container_width=True)