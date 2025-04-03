import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import format_currency, format_percentage, load_kpis, load_midia # Importa funções

# Define paleta de cores Azul Pastel
azul_pastel_palette = ['#E1F5FE', '#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6'] # Do mais claro ao mais escuro
funnel_colors = azul_pastel_palette[::-1] # Inverte para funil (mais escuro no topo)
channel_color_map = {'GoogleAds': azul_pastel_palette[3], 'MetaAds': azul_pastel_palette[1]} # Tons diferentes de azul

# Inicializa estados da sessão se não existirem
if 'channel_filter' not in st.session_state:
    st.session_state['channel_filter'] = 'Todos'
if 'exec_mode' not in st.session_state:
    st.session_state['exec_mode'] = False

# --- Carregar Dados ---
df_kpis = load_kpis()
df_midia = load_midia()

# --- Conteúdo da Página ---
st.title("🎯 Aquisição (Top of Funnel)")
st.markdown("Análise do funil inicial e performance dos canais de mídia paga.")
st.markdown("---")

# --- Filtro de Canal na Barra Lateral ---
current_channel_filter = st.session_state.get('channel_filter', 'Todos')
if current_channel_filter not in ['Todos', 'GoogleAds', 'MetaAds']:
    current_channel_filter = 'Todos'
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros de Aquisição")
channel_options = ['Todos', 'GoogleAds', 'MetaAds']
selected_channel = st.sidebar.radio(
    "Selecionar Canal de Mídia:",
    options=channel_options,
    key='channel_select_aquisicao', # Chave única
    index=channel_options.index(current_channel_filter)
)
st.session_state['channel_filter'] = selected_channel

# --- Lógica Principal ---
if df_kpis is not None and df_midia is not None:
    col_acq1, col_acq2 = st.columns([2,3])

    # --- Coluna 1: Funil Geral e Taxas ---
    with col_acq1:
        st.subheader("Funil de Aquisição Geral")
        try:
            required_kpis_funnel = ['Impressões dos Anúncios', 'Visitantes no site', 'Cliques no Anúncio', 'Leads Cadastrados no CRM', 'Leads Convertidos']
            if all(kpi in df_kpis.index for kpi in required_kpis_funnel):
                funnel_data = {
                    'Etapa': ['Impressões', 'Visitantes', 'Cliques', 'Leads CRM', 'Clientes (Vendas)'],
                    'Valor': [ df_kpis.loc[kpi, 'Valor'] for kpi in required_kpis_funnel ]
                }
                df_funnel = pd.DataFrame(funnel_data).dropna(subset=['Valor'])
                df_funnel = df_funnel[df_funnel['Valor'] > 0]
                df_funnel['Valor'] = df_funnel['Valor'].astype(int)

                if not df_funnel.empty:
                    # Atualiza cores do funil
                    fig_funnel = go.Figure(go.Funnel(
                        y = df_funnel['Etapa'], x = df_funnel['Valor'],
                        textposition = "inside", textinfo = "value+percent previous",
                        opacity = 0.8, marker = {"color": funnel_colors[0:len(df_funnel)]}, # Usa paleta azul pastel
                        connector = {"line": {"color": "silver", "dash": "dot", "width": 2}}))
                    fig_funnel.update_layout(title_text="Visualização do Funil", margin=dict(t=50, l=0, r=0, b=0), height=400)
                    st.plotly_chart(fig_funnel, use_container_width=True)
                else:
                    st.warning("Não há dados válidos para exibir o funil.")

                # Exibir taxas de conversão chave
                st.metric("Tx. Conv. Visitantes → Leads (%)", format_percentage(df_kpis.loc['Taxa de Conversão Visitantes → Leads (%)', 'Valor']), help="Percentual de visitantes do site que se cadastraram no CRM.")
                st.metric("Tx. Conv. Leads → Clientes (%)", format_percentage(df_kpis.loc['Taxa de Conversão Leads → Clientes (%)', 'Valor']), help="Percentual de Leads no CRM que se tornaram clientes.")
            else:
                missing_kpis = [kpi for kpi in required_kpis_funnel if kpi not in df_kpis.index]
                st.warning(f"Métricas necessárias para o funil não encontradas: {', '.join(missing_kpis)}. Verifique kpis_gerais.csv.")
        except Exception as e:
            st.warning(f"Erro ao gerar funil ou métricas de conversão: {e}")

    # --- Coluna 2: Performance por Canal ---
    with col_acq2:
        st.subheader(f"Performance por Canal ({st.session_state['channel_filter']})")

        if st.session_state['channel_filter'] == 'Todos':
            selected_cols_plot = ['GoogleAds', 'MetaAds']
            display_col_kpi = 'Total'
        else:
            selected_cols_plot = [st.session_state['channel_filter']]
            display_col_kpi = st.session_state['channel_filter']

        try:
            # Mostra KPIs gerais
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            kpi_col1.metric("Impressões", f"{int(df_midia.loc['Impressões', display_col_kpi]):,}" if pd.notna(df_midia.loc['Impressões', display_col_kpi]) else "N/A")
            kpi_col2.metric("Cliques", f"{int(df_midia.loc['Cliques', display_col_kpi]):,}" if pd.notna(df_midia.loc['Cliques', display_col_kpi]) else "N/A")
            kpi_col3.metric("Custo Total", format_currency(df_midia.loc['Custo de Tráfego Pago (R$)', display_col_kpi]))

            kpi_col4, kpi_col5, kpi_col6 = st.columns(3)
            kpi_col4.metric("Leads Captados (Ads)", f"{int(df_midia.loc['Leads Captados', display_col_kpi]):,}" if pd.notna(df_midia.loc['Leads Captados', display_col_kpi]) else "N/A")
            kpi_col5.metric("CPA (Custo por Lead Ads)", format_currency(df_midia.loc['CPA (R$)', display_col_kpi]))
            kpi_col6.metric("CTR (%)", format_percentage(df_midia.loc['CTR (%)', display_col_kpi]))

            # --- Gráficos (Ocultáveis no modo executivo) ---
            if not st.session_state.get('exec_mode', False):
                st.markdown("---")
                st.subheader("Análise Comparativa Detalhada por Canal")

                df_midia_plot = df_midia.loc[['Custo de Tráfego Pago (R$)', 'CPA (R$)', 'CTR (%)']].copy()
                df_midia_plot_filtered = df_midia_plot[selected_cols_plot].dropna(axis=1, how='all').dropna(axis=0, how='any')

                if not df_midia_plot_filtered.empty:
                     df_melted = df_midia_plot_filtered.reset_index().melt(id_vars='Metrica', var_name='Canal', value_name='Valor')

                     # Gráfico CPA por Canal (Cores Atualizadas)
                     if st.session_state['channel_filter'] == 'Todos' and 'CPA (R$)' in df_midia_plot_filtered.index:
                         df_cpa_plot = df_melted[df_melted['Metrica'] == 'CPA (R$)']
                         if not df_cpa_plot.empty:
                             fig_midia_cpa = px.bar(df_cpa_plot, x='Canal', y='Valor', color='Canal',
                                                    title='CPA por Canal', text='Valor', labels={'Valor':'CPA (R$)'},
                                                    color_discrete_map=channel_color_map) # Aplica cores azul pastel
                             fig_midia_cpa.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
                             fig_midia_cpa.update_layout(showlegend=False, height=350, yaxis_title="CPA (R$)")
                             st.plotly_chart(fig_midia_cpa, use_container_width=True)

                     # Gráfico Custo por Canal (Cores Atualizadas)
                     if 'Custo de Tráfego Pago (R$)' in df_midia_plot_filtered.index:
                         df_cost_plot = df_melted[df_melted['Metrica'] == 'Custo de Tráfego Pago (R$)']
                         if not df_cost_plot.empty:
                              fig_midia_cost = px.bar(df_cost_plot, x='Canal', y='Valor', color='Canal',
                                                      title='Custo Total por Canal', text='Valor', labels={'Valor':'Custo (R$)'},
                                                      color_discrete_map=channel_color_map) # Aplica cores azul pastel
                              fig_midia_cost.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
                              fig_midia_cost.update_layout(showlegend=False, height=350, yaxis_title="Custo (R$)")
                              st.plotly_chart(fig_midia_cost, use_container_width=True)

                     # Gráfico CTR por Canal (Cores Atualizadas)
                     if 'CTR (%)' in df_midia_plot_filtered.index:
                         df_ctr_plot = df_melted[df_melted['Metrica'] == 'CTR (%)']
                         if not df_ctr_plot.empty:
                             fig_midia_ctr = px.bar(df_ctr_plot, x='Canal', y='Valor', color='Canal',
                                                    title='CTR por Canal', text='Valor', labels={'Valor':'CTR (%)'},
                                                    color_discrete_map=channel_color_map) # Aplica cores azul pastel
                             fig_midia_ctr.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
                             fig_midia_ctr.update_layout(showlegend=False, height=350, yaxis_title="CTR (%)")
                             st.plotly_chart(fig_midia_ctr, use_container_width=True)
                else:
                     st.info("Não há dados comparativos suficientes para os gráficos detalhados com o filtro atual.")
            else:
                 st.info("Detalhes comparativos ocultos no Modo Executivo.")
        except KeyError as e:
            st.error(f"Erro: Métrica de mídia não encontrada: {e}. Verifique midia_canais.csv.")
        except Exception as e:
            st.error(f"Ocorreu um erro ao exibir dados do canal: {e}")
else:
    st.error("Arquivos kpis_gerais.csv ou midia_canais.csv não carregados. Página de Aquisição não pode ser exibida.")
