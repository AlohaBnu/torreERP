import pandas as pd
from datetime import date, datetime
from sqlalchemy import create_engine
from urllib.parse import quote
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
import os
import io
import mysql.connector as mc
import pyarrow as pa
import pytz
from mysql.connector import Error

USER_DB_FAST = os.environ.get('USER_DB_FAST')
PASS_DB_FAST = os.environ.get('PASS_DB_FAST')

# Configurações do banco de dados
hostname = '172.31.20.168'
user = 'consulta'
password = 'wH@xQd'
database = 'fast'

# Função para conectar ao banco de dados MySQL
def create_connection():
    try:
        connection = mc.connect(
            host=hostname,
            database=database,
            user=user,
            password=password,
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")

connection = create_connection()

st.set_page_config(layout="wide")
st.header('Dashboard - Foundation ERP')

met1, met2, met3, met4, met5, met6 = st.columns(6)

# ------------------------------
# DataFrames principais
# ------------------------------
df = pd.read_sql(
    "select idProjeto, nome, diff as DiasEntradaProjeto,nomeresponsavel, nome_gp,datInicio,DataSolicitacaoFoundation, statusFoundation, UltimoStatus, mercado, financas, suprimentos, temportal,nomeAnalistaTecnico,nomeCliente, datUltimaMarcacao,AtividadesClienteRealizada,primeiraDatMarcacaoCliente,datUltimaMarcacaoAnalista,primeiraDatMarcacaoAnalista,ultimaDatMarcacaoCliente,textoUltimaAtividadeCliente,textoUltimaAtividadeAnalista,statusAmbienteSolicitado as temAmbiente, concluido, foraEscopo, desmarcadas, marcadas, totalAtividades, modelo, concluidoOrientado, foraEscopoOrientado, desmarcadasOrientado, marcadasOrientado, AmbienteOnPremise, totalAtividadesOrientado from v_ea_visao_foundation where (mercado is null and suprimentos is null) and datInicio >= '2023-12-01'",
    connection
)

df = df.rename(columns={
    'idProjeto': 'ID Projeto',
    'nome': 'Nome',
    'statusFoundation': 'StatusFoundation',
    'nomeresponsavel': 'Coordenador',
    'nome_gp': 'Gerente de Projeto',
    'datInicio': 'Inicio Projeto',
    'DataSolicitacaoFoundation': 'Solicitacao do Foundation',
    'primeiraDatMarcacaoCliente': 'Primeira Marcação do Cliente',
    'ultimaDatMarcacaoCliente': 'Ultima Marcação do Cliente',
    'primeiraDatMarcacaoAnalista': 'Primeira Marcação do Analista',
    'datUltimaMarcacaoAnalista': 'Ultima Marcação do Analista',
    'nomeAnalistaTecnico': 'Analista',
    'textoUltimaAtividadeAnalista': 'Ultima Atividade Analista',
    'mercado': 'Mercado',
    'financas': 'Finanças',
    'suprimentos': 'Suprimentos',
    'textoUltimaAtividadeCliente': 'Ultima Atividade Cliente',
    'AmbienteOnPremise': 'Ambiente On Premise'
})

# ------------------------------
# Demandas Foundation
# ------------------------------
query_demandas_foundation = """
      SELECT 
    DATE_FORMAT(d.datCadastro, '%Y-%m') AS Mes,
    d.nomePWA as Nome_Projeto,
    d.horas as Horas_Projeto,
    u.nome AS Gerente_Projeto,
    d.idProjeto as ID_Projeto,
    d.datcadastro as AberturaDemanda,
    COUNT(*) AS Total_Demandas,
    CASE 
	WHEN d.status = 0 then 'ABERTO'
    WHEN d.status = 1 then 'EM ANALISE'
    WHEN d.status = 3 then 'FINALIZADO'
    WHEN d.status = 4 then 'CANCELADO'    
    end as Status,
    CASE WHEN EXISTS (SELECT 1 FROM configuracaocronograma c WHERE c.idProjeto = d.idProjeto AND c.idMensagem = 43732 AND c.tipo = 0) THEN 'Sim' ELSE 'Não' END AS Solicitar_Horas_GP,
    CASE WHEN EXISTS (SELECT 1 FROM configuracaocronograma c WHERE c.idProjeto = d.idProjeto AND c.idMensagem = 43733 AND c.tipo = 0) THEN 'Sim' ELSE 'Não' END AS Apontamento_Cadastros_30,
    CASE WHEN EXISTS (SELECT 1 FROM configuracaocronograma c WHERE c.idProjeto = d.idProjeto AND c.idMensagem = 43736 AND c.tipo = 0) THEN 'Sim' ELSE 'Não' END AS Apontamento_Notas_40,
    CASE WHEN EXISTS (SELECT 1 FROM configuracaocronograma c WHERE c.idProjeto = d.idProjeto AND c.idMensagem = 43739 AND c.tipo = 0) THEN 'Sim' ELSE 'Não' END AS Apontamento_Plataforma_20,
    CASE WHEN EXISTS (SELECT 1 FROM configuracaocronograma c WHERE c.idProjeto = d.idProjeto AND c.idMensagem = 43742 AND c.tipo = 0) THEN 'Sim' ELSE 'Não' END AS Apontamento_Agenda_10
FROM demanda d
JOIN usuario u ON d.idUsuario = u.idUsuario
WHERE d.tipo = 19
GROUP BY mes, d.nomePWA, d.horas, u.nome, d.idProjeto
ORDER BY mes;
"""
df_demandas_mes = pd.read_sql(query_demandas_foundation, connection)

# ------------------------------
# Tratamento datas e colunas
# ------------------------------
df['Inicio Projeto'] = pd.to_datetime(df['Inicio Projeto'])
df['datUltimaMarcacao'] = pd.to_datetime(df['datUltimaMarcacao'])
df['Solicitacao do Foundation'] = pd.to_datetime(df['Solicitacao do Foundation'])
df['Primeira Marcação do Cliente'] = pd.to_datetime(df['Primeira Marcação do Cliente'])
df['Ultima Marcação do Cliente'] = pd.to_datetime(df['Ultima Marcação do Cliente'])
df['Primeira Marcação do Analista'] = pd.to_datetime(df['Primeira Marcação do Analista'])
df['Ultima Marcação do Analista'] = pd.to_datetime(df['Ultima Marcação do Analista'])

# Diferenças de dias
df['Dias Cadadastro x Solicitacao Foundation'] = (df['Inicio Projeto'] - df['Solicitacao do Foundation']).dt.days.abs()
df['Solicitacao Foundation x Primeira Marcação do Cliente'] = (df['Primeira Marcação do Cliente'] - df['Solicitacao do Foundation']).dt.days.abs()
df['Ultima Marcação do Cliente x Primeira Marcação do Analista'] = (df['Ultima Marcação do Cliente'] - df['Primeira Marcação do Analista']).dt.days.abs()

# Formatando datas
df['Data Cadastro Projeto'] = df['Inicio Projeto'].dt.strftime('%d/%m/%Y')
df['Data Solicitacao Foundation'] = df['Solicitacao do Foundation'].dt.strftime('%d/%m/%Y')
df['datUltimaMarcacao'] = df['datUltimaMarcacao'].dt.strftime('%d/%m/%Y')
df['mes_ano'] = df['Inicio Projeto'].dt.strftime('%Y-%m')
df['mes_nome_completo'] = df['Inicio Projeto'].dt.strftime('%B')
df = df.sort_values('Inicio Projeto')

# ------------------------------
# Percentual Foundation
# ------------------------------
condicao = df['modelo'] == 0
formula1 = round(df['concluidoOrientado'] + ((df['foraEscopoOrientado'] / (df['totalAtividadesOrientado'] - df['desmarcadasOrientado'])) * df['marcadasOrientado']),2)
formula2 = round(df['concluido'] + ((df['foraEscopo'] / (df['totalAtividades'] - df['desmarcadas'])) * df['marcadas']),2)
df['PercentualFoundation'] = np.where(condicao, formula1, formula2)

# ------------------------------
# Modelo Implantacao
# ------------------------------
df.loc[df['modelo'] == 0, 'Modelo Implantacao'] = 'Orientado'
df.loc[df['modelo'] != 0, 'Modelo Implantacao'] = 'Padrao'

# ------------------------------
# Ambiente
# ------------------------------
df['Ambiente'] = 'Nao Solicitado'
df.loc[df['Ambiente On Premise'].notnull(), 'Ambiente'] = 'Criado'
df.loc[df['temAmbiente'] == 3, 'Ambiente'] = 'Criado'

# ------------------------------
# Filtros Streamlit
# ------------------------------
nome1 = st.sidebar.multiselect("Nome do projeto", df['Nome'].unique())
nome3 = st.sidebar.multiselect("Coordenador", df['Coordenador'].unique())
nome4 = st.sidebar.multiselect("Nome GP", df['Gerente de Projeto'].unique(), default=[])
nome5 = st.sidebar.multiselect("Modelo", df['Modelo Implantacao'].unique(), default=[])

df_filtered = df
if nome1:
    df_filtered = df[df["Nome"].isin(nome1)]
if nome3:
    df_filtered = df[df["Coordenador"].isin(nome3)]
if nome4:
    df_filtered = df[df["Gerente de Projeto"].isin(nome4)]
if nome5:
    df_filtered = df[df["Modelo Implantacao"].isin(nome5)]

df_filtered[['Suprimentos', 'Mercado']] = df_filtered[['Suprimentos', 'Mercado']].fillna('Sim').applymap(lambda x: 'Sim' if x == 'Sim' else 'Não')

filtro = ~df_filtered['Nome'].isin([
    '190759-Gestão Empresarial - ERP-AGRO NORTE PESQUISA E SEMENTES SUL LTDA',
    '196570-Gestão Empresarial - ERP-SUPERMIX CONCRETO SA',
    '203925-Gestão Empresarial - ERP-RUPLAST',
    '207867-Gestão Empresarial - ERP-CALLINK',
    '208337-Gestão Empresarial - ERP-RICARDO LHOSSUKE HORITA',
    '206671-Gestão Empresarial - ERP-UNIVERSIDADE PARANAENSE - UNIPAR',
    '193192-Gestão Empresarial - ERP-MOLDIMPLAS INDUSTRIA E COMERCIO DE PLASTICOS LTDA'     
])

df_filtered = df_filtered[filtro]

df_filtered.loc[filtro, 'Ambiente'] = 'Criado'

# ------------------------------
# Dataframes específicos
# ------------------------------
df_temfoundationExecucao = df_filtered.query(
    "((`Modelo Implantacao` == 'Padrao' and temportal == 'Portal Foundation ERP') or "
    "(`Modelo Implantacao` == 'Orientado' and PercentualFoundation >= 1 and PercentualFoundation <= 10)) "
    "and (Ambiente == 'Criado') and (AtividadesClienteRealizada == 'SIM') and (PercentualFoundation < 100)"
)

df_temfoundationFinalizado = df_filtered.query(
    "(`Modelo Implantacao` == 'Padrao' and temportal == 'Portal Foundation ERP' and PercentualFoundation >= 100) or "
    "(`Modelo Implantacao` == 'Orientado' and PercentualFoundation >= 10)"
)

df_semfoundation = df_filtered.query(
    "(`Modelo Implantacao` == 'Padrao' and temportal != 'Portal Foundation ERP') or "
    "(`Modelo Implantacao` == 'Orientado' and PercentualFoundation <= 1 and DiasEntradaProjeto >= 100)"
)

df_temAmbiente = df_filtered.query("(temportal == 'Portal Foundation ERP') and (Ambiente == 'Nao Solicitado')")

df_AtividadesClienteRealizada = df_filtered.query(
    "((`Modelo Implantacao` == 'Padrao' and temportal == 'Portal Foundation ERP') or "
    "(`Modelo Implantacao` == 'Orientado' and PercentualFoundation >= 1 and PercentualFoundation <= 10)) "
    "and (Ambiente == 'Criado') and (AtividadesClienteRealizada != 'SIM')"
)

# Tratar null na legenda do grafico Nome GP
df_filtered['Gerente de Projeto'] = df_filtered['Gerente de Projeto'].fillna('Sem Recurso')

df_agrupado = df_demandas_mes.groupby('Mes', as_index=False)['Total_Demandas'].sum()
projetos_por_mes_ano = df.groupby(['mes_ano', 'Modelo Implantacao']).size().reset_index(name='total_projetos')
projetos_por_mes_ano.sort_values(by='mes_ano', ascending=False, inplace=True)

# ------------------------------
# Métricas Modernas - Dashboard Foundation
# ------------------------------

# Calculando valores das métricas
total_projetos = len(df_filtered)

total_projetos_foundation = len(df_temfoundationExecucao)
porcentagem_em_andamento = round((total_projetos_foundation / total_projetos) * 100, 2)

total_finalizados = len(df_temfoundationFinalizado)
porcentagem_finalizados = round((total_finalizados / total_projetos) * 100, 2)

total_paradosclientes = len(df_AtividadesClienteRealizada)

temAmbiente = len(df_temAmbiente)

# Projetos previstos
df_semfoundation['Data Cadastro Projeto'] = pd.to_datetime(df_semfoundation['Data Cadastro Projeto'], errors='coerce')
data_corte = pd.Timestamp('2024-12-01')
df_dez2024_em_diante = df_semfoundation[df_semfoundation['Data Cadastro Projeto'] >= data_corte]
total_df_previstos = len(df_dez2024_em_diante)
porcentagem_previstos = round((total_df_previstos / total_projetos) * 100, 2)

# CSS para todos os cartões
st.markdown("""
<style>
.metric-card {
    background-color: #f0f4f8;  /* fundo claro */
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 6px 15px rgba(0,0,0,0.15);
    font-family: 'Segoe UI', sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-width: 180px;
    min-height: 120px;
    margin-bottom: 15px;
}
.metric-title {
    font-size: 16px;
    color: #2c3e50;
    font-weight: 600;
    margin-bottom: 5px;
}
.metric-value {
    font-size: 28px;
    color: #1f77b4;
    font-weight: bold;
}
.metric-delta {
    font-size: 14px;
    color: #27ae60;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# Função para criar cada cartão
def metric_card(title, value, delta=None):
    delta_html = f"<div class='metric-delta'>{delta}</div>" if delta else ""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
    """, unsafe_allow_html=True)

# Exibindo todos os cartões lado a lado
col1, col2, col3, col4, col5 = st.columns(5)

with col4:
    metric_card("Executando", total_projetos_foundation, f"{porcentagem_em_andamento} %")
with col5:
    metric_card("Finalizados", total_finalizados, f"{porcentagem_finalizados} %")
with col3:
    metric_card("Demanda com o cliente", total_paradosclientes)
with col2:
    metric_card("Found. Solici. sem Ambiente", temAmbiente)
with col1:
    metric_card("Previstos", total_df_previstos, f"{porcentagem_previstos} %")

# ------------------------------
# Expanders com tabelas
# ------------------------------
with st.expander("Projetos previstos para o Foundation", expanded=False):
    st.dataframe(
        df_dez2024_em_diante[['ID Projeto', 'Nome', 'Coordenador', 'Gerente de Projeto',
                              'Modelo Implantacao', 'DiasEntradaProjeto','Data Cadastro Projeto',
                              'Ambiente', 'Mercado', 'Finanças', 'Suprimentos','UltimoStatus']]
    )

with st.expander("Projetos com Foundation Solicitado, mas sem ambiente criado", expanded=False):
    st.dataframe(df_temAmbiente[['ID Projeto','Nome','Coordenador','Gerente de Projeto',
                                 'UltimoStatus', 'Modelo Implantacao', 'Inicio Projeto',
                                 'Solicitacao do Foundation','DiasEntradaProjeto','Ambiente']])

with st.expander("Projetos com Foundation e ambiente criado, mas com pendência do cliente", expanded=False):
    st.dataframe(df_AtividadesClienteRealizada[['ID Projeto','Nome','Coordenador','Gerente de Projeto',
                                                'UltimoStatus', 'Modelo Implantacao', 'Data Cadastro Projeto',
                                                'DiasEntradaProjeto','Ultima Atividade Cliente',
                                                'Primeira Marcação do Cliente','Ultima Marcação do Cliente',
                                                'Ambiente']])

with st.expander("Projetos com Foundation Em Execução", expanded=False):
    colunas_exibidas_antiga = [
        'ID Projeto','Nome','Coordenador','Gerente de Projeto','PercentualFoundation','StatusFoundation',
        'UltimoStatus','Modelo Implantacao','Dias Cadadastro x Solicitacao Foundation',
        'Data Cadastro Projeto','Data Solicitacao Foundation',
        'Solicitacao Foundation x Primeira Marcação do Cliente','Primeira Marcação do Cliente',
        'Ultima Marcação do Cliente','Primeira Marcação do Analista',
        'Ultima Marcação do Cliente x Primeira Marcação do Analista',
        'Ultima Marcação do Analista','Analista','Ultima Atividade Analista'
    ]
    df_export_antiga = df_temfoundationExecucao[colunas_exibidas_antiga].sort_values(by='PercentualFoundation', ascending=False)
    st.dataframe(df_export_antiga)

    buffer_antiga = io.BytesIO()
    with pd.ExcelWriter(buffer_antiga, engine='xlsxwriter') as writer:
        df_export_antiga.to_excel(writer, index=False, sheet_name='Projetos Foundation')
    st.download_button("📥 Baixar Excel", buffer_antiga, file_name="Projetos_Foundation.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with st.expander("Projetos com Foundation Finalizados", expanded=False):
    st.dataframe(df_temfoundationFinalizado[['ID Projeto','Nome','Coordenador','Gerente de Projeto',
                                             'PercentualFoundation','UltimoStatus','Modelo Implantacao',
                                             'Data Cadastro Projeto','Data Solicitacao Foundation',
                                             'Dias Cadadastro x Solicitacao Foundation','Ultima Atividade Analista',
                                             'datUltimaMarcacao','Ambiente']])

with st.expander("Registros Demandas Abertas Foundation", expanded=False):
    colunas_exportar = [
        'ID_Projeto','Nome_Projeto','Gerente_Projeto','AberturaDemanda','Horas_Projeto','Status'
    ]
    df_export_demandas = df_demandas_mes[colunas_exportar].copy()
    st.dataframe(df_export_demandas)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_export_demandas.to_excel(writer, index=False, sheet_name='Demandas Abertas')
    st.download_button("📥 Baixar Excel", buffer, file_name="Demandas_Abertas_Foundation.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ------------------------------
# Gráficos Modernos
# ------------------------------
col1, col2 = st.columns(2)
col3, col4, col5 = st.columns(3)

fig1 = px.bar(
    projetos_por_mes_ano,
    x='mes_ano',
    y='total_projetos',
    text_auto=True,
    color="Modelo Implantacao",
    title='Qtde. Projetos por Mês e Ano',
    orientation='v',
    color_discrete_sequence=px.colors.qualitative.Pastel  # paleta qualitativa
)
fig1.update_layout(
    title_font=dict(size=20, family='Segoe UI', color='#2c3e50'),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis_title='Mês/Ano',
    yaxis_title='Total Projetos',
    font=dict(color='#2c3e50'),
)
fig1.update_traces(textfont_size=12, marker_line_width=0.5, marker_line_color='white', opacity=0.85)

fig2 = px.bar(
    df_agrupado,
    x='Mes',
    y='Total_Demandas',
    text_auto=True,
    title='Demandas Foundation (Cards)',
    orientation='v',
    color_discrete_sequence=px.colors.sequential.Cividis
)
fig2.update_layout(
    title_font=dict(size=20, family='Segoe UI', color='#2c3e50'),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis_title='Mês',
    yaxis_title='Total Demandas',
    font=dict(color='#2c3e50')
)
fig2.update_traces(textfont_size=12, marker_line_width=0.5, marker_line_color='white', opacity=0.85)

fig5 = px.pie(
    df_filtered,
    names='Modelo Implantacao',
    title='Modelo Venda',
    color_discrete_sequence=px.colors.sequential.Viridis
)
fig5.update_traces(textinfo='percent+label', pull=[0.05]*len(df_filtered))
fig5.update_layout(
    title_font=dict(size=18, family='Segoe UI', color='#2c3e50'),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)

# Renderizando gráficos
col1.plotly_chart(fig1, use_container_width=True)
col3.plotly_chart(fig2, use_container_width=True)
col5.plotly_chart(fig5, use_container_width=True)
