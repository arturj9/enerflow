import streamlit as st
import pandas as pd
from databricks import sql
import altair as alt

# 1. Configuração da Página
st.set_page_config(
    page_title="Monitorização Inteligente de Energia: Xerém",
    page_icon="⚡",
    layout="wide"
)

# 2. Título e Contexto de Negócio
st.title("⚡ Monitorização Inteligente de Energia: Xerém Business Case")
st.markdown("""
Esta aplicação consome o nosso **Data Product** (`df_gold`) de forma desacoplada, cumprindo a estratégia de **DaaS (Data-as-a-Service)**.
Fornecemos aos Business Users acesso direto e interativo a insights valiosos sobre consumo de energia, temperatura e custos operacionais.
""")

# 3. Conexão DaaS (Só lê, não limpa dados!)
@st.cache_data(ttl=3600)
def load_data():
    try:
        conn = sql.connect(
            server_hostname=st.secrets["databricks"]["server_hostname"],
            http_path=st.secrets["databricks"]["http_path"],
            access_token=st.secrets["databricks"]["access_token"]
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT Data, Hora, Bandeira, TEMP_AR, val_cargaenergiahomwmed, Preco_BRL, (val_cargaenergiahomwmed * Preco_BRL) as Custo_Total FROM default.gold_energia")
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao Databricks: {e}")
        # Fallback atualizado para "Intermediaria"
        return pd.DataFrame({
            'Data': pd.date_range(start='2026-03-01', periods=12, freq='D'),
            'Bandeira': ['Verde', 'Intermediaria', 'Vermelha', 'Verde', 'Vermelha', 'Intermediaria', 'Verde', 'Vermelha', 'Vermelha', 'Intermediaria', 'Vermelha', 'Vermelha'],
            'val_cargaenergiahomwmed': [15000, 20000, 18000, 16000, 21000, 17500, 15500, 19000, 18500, 16500, 22000, 23000],
            'TEMP_AR': [25, 30, 28, 26, 31, 29, 24, 28, 27, 25, 32, 33],
            'Preco_BRL': [0.5, 0.9, 1.3, 0.5, 1.3, 0.9, 0.5, 1.3, 1.3, 0.9, 1.3, 1.3],
            'Custo_Total': [7500, 18000, 23400, 8000, 27300, 15750, 7750, 24700, 24050, 14850, 28600, 29900],
            'Hora': [8, 12, 18, 10, 19, 14, 9, 18, 20, 15, 18, 19]
        })

df_gold = load_data()

# --- SRE / PIPELINE STATUS (DINÂMICO E REAL) ---
st.sidebar.markdown("### 🛡️ Monitoramento SRE")

if not df_gold.empty:
    # Conta os nulos reais nas colunas críticas do DataFrame que acabou de ser carregado
    nulos_reais = df_gold[['TEMP_AR', 'val_cargaenergiahomwmed', 'Preco_BRL']].isnull().sum().sum()
    
    if nulos_reais == 0:
        st.sidebar.success("🟢 Status: System Healthy")
        st.sidebar.markdown(f"*(Auditoria Gold: {nulos_reais} Nulos Detectados)*")
    else:
        st.sidebar.error("🔴 Status: SLO Breach (Falha na Pipeline)")
        st.sidebar.markdown(f"*(Auditoria Gold: {nulos_reais} Nulos Detectados)*")
else:
    st.sidebar.warning("🟡 Status: Sistema Indisponível (Sem Dados)")

st.sidebar.divider()

if not df_gold.empty:
    # Tratamento de Datas para o Filtro
    df_gold['Data'] = pd.to_datetime(df_gold['Data'])
    min_date = df_gold['Data'].min().date()
    max_date = df_gold['Data'].max().date()

    # --- FILTROS LATERAIS ---
    st.sidebar.header("Filtros de Navegação")
    
    datas_selecionadas = st.sidebar.date_input("Intervalo de Data", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    if isinstance(datas_selecionadas, list) and len(datas_selecionadas) == 2:
        start_date, end_date = datas_selecionadas
        df_filtered = df_gold[(df_gold['Data'].dt.date >= start_date) & (df_gold['Data'].dt.date <= end_date)]
    else:
        df_filtered = df_gold

    if 'Bandeira' in df_gold.columns:
        bandeiras = sorted(df_gold['Bandeira'].dropna().unique().tolist())
        
        # Mapeamento corrigido para ler "Intermediaria" do Databricks
        def format_bandeira(b):
            cores = {'Verde': '🟢 Verde', 'Intermediaria': '🟡 Intermediária', 'Vermelha': '🔴 Vermelha'}
            # Se vier alguma variação (ex: intermediária com acento da Silver), trata também:
            if 'Intermedi' in b:
                return '🟡 Intermediária'
            return cores.get(b, b)

        bandeiras_selecionadas = st.sidebar.multiselect(
            "Bandeira Tarifária", 
            bandeiras, 
            default=bandeiras,
            format_func=format_bandeira
        )
        
        if bandeiras_selecionadas:
            df_filtered = df_filtered[df_filtered['Bandeira'].isin(bandeiras_selecionadas)]

    # --- KPIs PRINCIPAIS ---
    st.markdown("### 📈 Principais KPIs da Operação")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pico_carga = df_filtered['val_cargaenergiahomwmed'].max() if 'val_cargaenergiahomwmed' in df_filtered.columns else 0
        st.metric(label="Pico Máximo de Carga (MWmed)", value=f"{pico_carga:,.2f}")
        
    with col2:
        temp_max = df_filtered['TEMP_AR'].max() if 'TEMP_AR' in df_filtered.columns else 0
        st.metric(label="Pico de Temperatura (°C)", value=f"{temp_max:.1f} °C")
        
    with col3:
        custo_medio = df_filtered['Custo_Total'].mean() if 'Custo_Total' in df_filtered.columns else 0
        st.metric(label="Custo Médio Horário (BRL)", value=f"R$ {custo_medio:,.2f}")

    # --- VISUALIZAÇÕES E INSIGHTS ---
    st.divider()
    st.markdown("### 📊 Inteligência Analítica")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Temperatura vs. Consumo")
        st.markdown("Correlação direta: o consumo físico escala com o aumento térmico ambiente.")
        
        df_insight1 = df_filtered.copy()
        df_insight1['Temp_Graus'] = df_insight1['TEMP_AR'].round(0)
        consumo_por_temp = df_insight1.groupby('Temp_Graus')['val_cargaenergiahomwmed'].mean()
        
        st.line_chart(consumo_por_temp)
            
    with col_chart2:
        st.subheader("Custo Financeiro por Horário")
        st.markdown("Evidência do impacto tarifário real no Horário de Ponta (18h-20h).")
        
        custo_por_hora_bandeira = df_filtered.groupby(['Hora', 'Bandeira'])['Custo_Total'].mean().reset_index()
        
        # Gráfico atualizado para o domínio ['Verde', 'Intermediaria', 'Vermelha']
        grafico_barras = alt.Chart(custo_por_hora_bandeira).mark_bar().encode(
            x=alt.X('Hora:O', title='Hora do Dia (0-23)'),
            y=alt.Y('Custo_Total:Q', title='Custo Médio (BRL)'),
            color=alt.Color('Bandeira:N', 
                            scale=alt.Scale(
                                domain=['Verde', 'Intermediaria', 'Vermelha'],
                                range=['#2ecc71', '#f1c40f', '#e74c3c']
                            ),
                            legend=alt.Legend(title="Bandeira Ativa")
            ),
            tooltip=['Hora', 'Bandeira', 'Custo_Total']
        ).properties(height=350)
        
        st.altair_chart(grafico_barras, use_container_width=True)