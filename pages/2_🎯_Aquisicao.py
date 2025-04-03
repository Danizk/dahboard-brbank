import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# Importa funções e garante que o estado da sessão exista
from utils import format_currency, format_percentage, load_kpis, load_midia

# Inicializa o estado da sessão se não existir (para o filtro)
if 'channel_filter' not in st.session_state:
    st.session_state['channel_filter'] = 'Todos'
if 'exec_mode' not in st.session_state: # Garante que existe para a lógica de ocultar
    st.session_state['exec_mode'] = False

# --- Carregar Dados ---
df_kpis = load_kpis()
df_midia = load_midia()

# --- Conteúdo da Página ---
st.title("🎯 Aquisição (Top of Funnel)")
st.markdown("Análise do funil inicial e performance dos canais de mídia paga.")
st.markdown("---")

# --- Filtro de Canal na Barra Lateral ---
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros de Aquisição")
channel_options = ['Todos', 'GoogleAds', 'MetaAds']
st.session_state['channel_filter'] = st.sidebar.radio(
    "Selecionar Canal de Mídia:",
    options=channel_options,
    key='channel_select', # Chave única para o widget
    index=channel_options.index(st.session_state['channel_filter']) # Mantém a seleção anterior
)

# --- Lógica Principal ---
if df_kpis is not None and df_midia is not None:
    col_acq1, col_acq2 = st.columns(2)

    # --- Coluna 1: Funil Geral e Taxas ---
    with col_acq1:
        st.subheader("Funil de Aquisição Geral")
        try:
            required_metrics = ['Impressões dos Anúncios', 'Visitantes no site', 'Cliques no Anúncio', 'Leads Cadastrados no CRM', 'Leads Convertidos']
            if all(metric in df_kpis.index for metric in required_metrics):
                funnel_data = {
                    'Etapa': ['Impressões', 'Visitantes', 'Cliques', 'Leads CRM', 'Clientes (Vendas)'],
                    'Valor': [
                        int(df_kpis.loc['Impressões dos Anúncios', 'Valor']),
                        int(df_kpis.loc['Visitantes no site', 'Valor']),
                        int(df_kpis.loc['Cliques no Anúncio', 'Valor']),
                        int(df_kpis.loc['Leads Cadastrados no CRM', 'Valor']),
                        int(df_kpis.loc['Leads Convertidos', 'Valor'])
                    ]
                }
                df_funnel = pd.DataFrame(funnel_data)
                df_funnel = df_funnel[df_funnel['Valor'].notna() & df_funnel['Valor'] > 0] # Remove etapas sem valor

                if not df_funnel.empty:
                    fig_funnel = go.Figure(go.Funnel(
                        y = df_funnel['Etapa'], x = df_funnel['Valor'],
                        textposition = "inside", textinfo = "value+percent previous",
                        opacity = 0.75, marker = {"color": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"][0:len(df_funnel)]}, # Ajusta cores
                        connector = {"line": {"color": "silver", "dash": "dot", "width": 2}}))
                    fig_funnel.update_layout(title_text="Visualização do Funil", margin=dict(t=50, l=0, r=0, b=0), height=400)
                    st.plotly_chart(fig_funnel, use_container_width=True)
                else:
                    st.warning("Não há dados válidos para exibir o funil.")

                # Exibir taxas de conversão chave
                st.metric("Tx. Conv. Visitantes → Leads CRM", format_percentage(df_kpis.loc['Taxa de Conversão Visitantes → Leads (%)', 'Valor']), help="Percentual de visitantes do site que se cadastraram no CRM.")
                st.metric("Tx. Conv. Leads → Clientes", format_percentage(df_kpis.loc['Taxa de Conversão Leads → Clientes (%)', 'Valor']), help="Percentual de Leads no CRM que se tornaram clientes.")
            else:
                 st.warning("Métricas necessárias para o funil não encontradas em kpis_gerais.csv.")
        except Exception as e:
            st.warning(f"Erro ao gerar funil ou métricas de conversão: {e}")

    # --- Coluna 2: Performance por Canal (com filtro e modo executivo) ---
    with col_acq2:
        st.subheader(f"Performance por Canal ({st.session_state['channel_filter']})")

        # Seleciona a(s) coluna(s) com base no filtro
        if st.session_state['channel_filter'] == 'Todos':
            selected_cols = ['GoogleAds', 'MetaAds'] # Para gráficos comparativos
            display_col = 'Total' # Para métricas totais
        else:
            selected_cols = [st.session_state['channel_filter']]
            display_col = st.session_state['channel_filter']

        try:
            # Mostra KPIs gerais do canal selecionado (ou total)
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            kpi_col1.metric("Impressões", f"{int(df_midia.loc['Impressões', display_col]):,}" if pd.notna(df_midia.loc['Impressões', display_col]) else "N/A")
            kpi_col2.metric("Cliques", f"{int(df_midia.loc['Cliques', display_col]):,}" if pd.notna(df_midia.loc['Cliques', display_col]) else "N/A")
            kpi_col3.metric("Custo Total", format_currency(df_midia.loc['Custo de Tráfego Pago (R$)', display_col]))

            kpi_col4, kpi_col5, kpi_col6 = st.columns(3)
            kpi_col4.metric("Leads Captados (Ads)", f"{int(df_midia.loc['Leads Captados', display_col]):,}" if pd.notna(df_midia.loc['Leads Captados', display_col]) else "N/A")
            kpi_col5.metric("CPA (Custo por Lead Ads)", format_currency(df_midia.loc['CPA (R$)', display_col]))
            kpi_col6.metric("CTR (%)", format_percentage(df_midia.loc['CTR (%)', display_col]))

            # --- Gráficos (Ocultáveis no modo executivo) ---
            if not st.session_state.get('exec_mode', False):
                st.markdown("---")
                st.subheader("Análise Comparativa Detalhada")

                df_midia_plot = df_midia.loc[['Custo de Tráfego Pago (R$)', 'CPA (R$)', 'CTR (%)'], selected_cols].copy() # Pega só colunas selecionadas
                df_midia_plot.dropna(inplace=True) # Remove linhas/colunas com NaN para evitar erro no melt

                if not df_midia_plot.empty:
                     df_melted = df_midia_plot.reset_index().melt(id_vars='Metrica', var_name='Canal', value_name='Valor')

                     # Gráfico CPA por Canal (Novo) - Mostra se filtro = Todos
                     if st.session_state['channel_filter'] == 'Todos':
                         df_cpa_plot = df_melted[df_melted['Metrica'] == 'CPA (R$)']
                         fig_midia_cpa = px.bar(df_cpa_plot, x='Canal', y='Valor', color='Canal', title='CPA por Canal', text='Valor', labels={'Valor':'CPA (R$)'})
                         fig_midia_cpa.update_traces(texttemplate='%{text:,.2f}', textposition='outside')
                         fig_midia_cpa.update_layout(showlegend=False, height=350)
                         st.plotly_chart(fig_midia_cpa, use_container_width=True)

                     # Gráfico Custo por Canal
                     df_cost_plot = df_melted[df_melted['Metrica'] == 'Custo de Tráfego Pago (R$)']
                     fig_midia_cost = px.bar(df_cost_plot, x='Canal', y='Valor', color='Canal', title='Custo Total por Canal', text='Valor', labels={'Valor':'Custo (R$)'})
                     fig_midia_cost.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
                     fig_midia_cost.update_layout(showlegend=False, height=350)
                     st.plotly_chart(fig_midia_cost, use_container_width=True)

                     # Gráfico CTR por Canal
                     df_ctr_plot = df_melted[df_melted['Metrica'] == 'CTR (%)']
                     fig_midia_ctr = px.bar(df_ctr_plot, x='Canal', y='Valor', color='Canal', title='CTR por Canal', text='Valor', labels={'Valor':'CTR (%)'})
                     fig_midia_ctr.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                     fig_midia_ctr.update_layout(showlegend=False, height=350)
                     st.plotly_chart(fig_midia_ctr, use_container_width=True)
                else:
                     st.info("Não há dados suficientes para os gráficos detalhados com o filtro atual.")

        except KeyError as e:
            st.error(f"Erro: Métrica não encontrada nos arquivos de dados: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro ao exibir dados do canal: {e}")
else:
    st.error("Arquivos kpis_gerais.csv ou midia_canais.csv não carregados. Página de Aquisição não pode ser exibida.")
