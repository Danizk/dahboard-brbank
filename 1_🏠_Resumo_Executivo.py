import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import format_currency, format_percentage, load_kpis, convert_df_to_csv # Importa funções do utils.py

# --- Configuração da Página ---
st.set_page_config(
    page_title="BR Bank - Visão Geral",
    page_icon="🏠",
    layout="wide"
)

# --- Barra Lateral ---
st.sidebar.header("Configurações de Exibição")
# Adiciona o Toggle "Modo Executivo" e guarda no estado da sessão
# Inicializa o estado se não existir
if 'exec_mode' not in st.session_state:
    st.session_state['exec_mode'] = False

st.session_state['exec_mode'] = st.sidebar.toggle(
    "Modo Executivo Simplificado",
    value=st.session_state['exec_mode'], # Usa o valor atual do estado
    help="Oculta detalhes e gráficos secundários para uma visão de alto nível."
)
st.sidebar.markdown("---") # Linha separadora na sidebar

# --- Carregar Dados ---
df_kpis = load_kpis()

# --- Constantes ---
META_FATURAMENTO_ANUAL = 30000000
MESES_PERIODO_ATUAL = 6 # Set/22 a Fev/23

# --- Conteúdo da Página ---
st.title("🏠 Resumo Executivo | BR Bank")
st.markdown(f"Visão Geral dos Indicadores Chave (Período: Set/22 a Fev/23)")
st.markdown("---")

if df_kpis is not None:
    try:
        # Extrai valor numérico da Receita Total (já convertido em load_kpis)
        receita_total_valor = df_kpis.loc['Receita Total (R$)', 'Valor']

        if pd.notna(receita_total_valor):
            # Calcula Gap e Projeção
            gap_meta = META_FATURAMENTO_ANUAL - receita_total_valor
            projecao_anual = (receita_total_valor / MESES_PERIODO_ATUAL) * 12 if MESES_PERIODO_ATUAL > 0 else 0

            # --- KPIs Principais ---
            st.subheader("📈 Performance Financeira e Operacional")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Receita Total (Período)", format_currency(receita_total_valor), help="Faturamento total nos 6 meses analisados (Set/22-Fev/23).")
            col2.metric("Lucro Líquido (Período)", format_currency(df_kpis.loc['Lucro Líquido (R$)', 'Valor']), help="Receita Total - Custo de Tráfego Pago.")
            col3.metric("Margem Líquida (%)", format_percentage(df_kpis.loc['Margem Líquida (%)', 'Valor']), help="Lucro Líquido / Receita Total.")
            col4.metric("ROAS (%)", format_percentage(df_kpis.loc['ROAS (%)', 'Valor']), help="(Receita Gerada por Ads / Custo de Ads) * 100%")

            # --- KPIs Operacionais (Visíveis mesmo no modo executivo)---
            col5, col6, col7, col8 = st.columns(4)
            col5.metric("Leads Convertidos", f"{int(df_kpis.loc['Leads Convertidos', 'Valor']):,}" if pd.notna(df_kpis.loc['Leads Convertidos', 'Valor']) else "N/A", help="Número total de empréstimos contratados no período.")
            col6.metric("Ticket Médio", format_currency(df_kpis.loc['Ticket Médio (R$)', 'Valor']), help="Receita Total / Leads Convertidos.")
            col7.metric("LTV (proxy)", format_currency(df_kpis.loc['LTV (R$)', 'Valor']), help="Valor médio do cliente (igual ao Ticket Médio neste caso).")
            col8.metric("CAC (proxy Custo Ads)", format_currency(df_kpis.loc['CPA - Custo por Aquisição (R$)', 'Valor']), help="Custo por Aquisição (Custo de Ads / Leads Captados por Ads).")

            st.markdown("---")
            # --- Meta e Projeção ---
            st.subheader("🎯 Meta Anual (R$ 30 Milhões)")
            col_meta1, col_meta2, col_meta3 = st.columns(3)
            col_meta1.metric("Meta Anual", format_currency(META_FATURAMENTO_ANUAL))
            col_meta2.metric("Gap para Meta", format_currency(gap_meta), help="Quanto falta para atingir a meta anual de R$ 30M.")
            col_meta3.metric("Projeção Anual (Linear)", format_currency(projecao_anual), help=f"Estimativa anual baseada na média dos últimos {MESES_PERIODO_ATUAL} meses.")

            # --- Gráfico Velocímetro ---
            # (Pode ser escondido no modo executivo se desejar, mas como é visual e alto nível, pode ficar)
            # if not st.session_state.get('exec_mode', False): # Descomente esta linha se quiser esconder no modo exec
            st.subheader("🌡️ Progresso da Receita vs Meta Anual")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = receita_total_valor,
                number = {'prefix': "R$", 'valueformat': ',.0f'}, # Formato sem centavos
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Receita Acumulada (Set/22-Fev/23)", 'font': {'size': 18}},
                gauge = {
                    'axis': {'range': [0, META_FATURAMENTO_ANUAL], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "#1f77b4"},
                    'bgcolor': "white",
                    'borderwidth': 1,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, META_FATURAMENTO_ANUAL * 0.5], 'color': 'rgba(255, 0, 0, 0.1)'},
                        {'range': [META_FATURAMENTO_ANUAL * 0.5, META_FATURAMENTO_ANUAL * 0.8], 'color': 'rgba(255, 255, 0, 0.1)'},
                        {'range': [META_FATURAMENTO_ANUAL * 0.8, META_FATURAMENTO_ANUAL], 'color': 'rgba(0, 128, 0, 0.1)'} # Verde
                        ],
                    'threshold': {
                        'line': {'color': "orange", 'width': 4},
                        'thickness': 0.75,
                        'value': projecao_anual
                        }
                    }
                ))
            fig_gauge.update_layout(height=300, margin=dict(t=30, b=10, l=10, r=10)) # Ajuste de margem
            st.plotly_chart(fig_gauge, use_container_width=True)

        else:
            st.warning("Não foi possível exibir metas/projeção pois o valor da Receita Total ('Receita Total (R$)') está ausente ou inválido no arquivo kpis_gerais.csv.")

    except KeyError as e:
        st.error(f"Erro: Métrica essencial não encontrada no arquivo kpis_gerais.csv: {e}. Verifique o arquivo.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar os dados do Resumo Executivo: {e}")

else:
    st.error("Arquivo kpis_gerais.csv não carregado. KPIs não podem ser exibidos.")

st.caption(f"Última atualização do código: {pd.to_datetime('today').strftime('%d/%m/%Y %H:%M')}")
