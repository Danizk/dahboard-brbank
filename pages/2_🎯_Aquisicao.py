import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Funções Auxiliares ---
# (Duplicadas ou importar de utils.py)
def format_currency(value):
    try:
        numeric_string = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], str(value)))
        numeric_string = numeric_string.replace('.', '', numeric_string.count('.') -1).replace(',', '.')
        return f"R$ {float(numeric_string):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value

def format_percentage(value):
    try:
        numeric_string = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], str(value)))
        numeric_string = numeric_string.replace('.', '', numeric_string.count('.') -1).replace(',', '.')
        return f"{float(numeric_string):.2f}%"
    except (ValueError, TypeError):
        return value

# --- Carregar Dados Essenciais para esta página ---
@st.cache_data
def load_acquisition_data():
    try:
        df_kpis = pd.read_csv('kpis_gerais.csv').set_index('Metrica')
        df_midia = pd.read_csv('midia_canais.csv').set_index('Metrica')
        return df_kpis, df_midia
    except FileNotFoundError as e:
        st.error(f"Erro: Arquivo {e.filename} não encontrado.")
        return None, None
    except Exception as e:
        st.error(f"Erro ao carregar dados de aquisição: {e}")
        return None, None

df_kpis, df_midia = load_acquisition_data()

# --- Conteúdo da Página ---
st.title("🎯 Aquisição (Top of Funnel)")
st.markdown("Análise do funil inicial e performance dos canais de mídia paga.")
st.markdown("---")

if df_kpis is not None and df_midia is not None: # Verifica se ambos foram carregados
    col_acq1, col_acq2 = st.columns(2)

    with col_acq1:
        st.subheader("Funil de Aquisição Geral")
        try:
            # Adiciona checagem se as métricas existem antes de acessá-las
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

                fig_funnel = go.Figure(go.Funnel(
                    y = df_funnel['Etapa'],
                    x = df_funnel['Valor'],
                    textposition = "inside", textinfo = "value+percent previous",
                    opacity = 0.75, marker = {"color": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]},
                    connector = {"line": {"color": "silver", "dash": "dot", "width": 2}}))
                fig_funnel.update_layout(title_text="Visualização do Funil", margin=dict(t=50, l=0, r=0, b=0))
                st.plotly_chart(fig_funnel, use_container_width=True)

                st.metric("Tx. Conv. Visitantes → Leads CRM", format_percentage(df_kpis.loc['Taxa de Conversão Visitantes → Leads (%)', 'Valor']), help="Percentual de visitantes do site que se cadastraram no CRM.")
                st.metric("Tx. Conv. Leads → Clientes", format_percentage(df_kpis.loc['Taxa de Conversão Leads → Clientes (%)', 'Valor']), help="Percentual de Leads no CRM que se tornaram clientes.")
            else:
                st.warning("Algumas métricas necessárias para o funil não foram encontradas em kpis_gerais.csv.")

        except KeyError as e:
            st.warning(f"Métrica não encontrada para o funil: {e}")
        except ValueError as e:
             st.warning(f"Erro ao converter valor para o funil: {e}")


    with col_acq2:
        st.subheader("Performance por Canal de Mídia")
        st.dataframe(df_midia) # Mostra a tabela de mídia

        try:
            df_midia_plot = df_midia.copy()
            if 'Total' in df_midia_plot.columns:
                 df_midia_plot = df_midia_plot.drop(columns=['Total'])

            cols_to_convert_midia = ['MetaAds', 'GoogleAds']
            for col in cols_to_convert_midia:
                if df_midia_plot[col].dtype == 'object':
                    df_midia_plot[col] = df_midia_plot[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
                df_midia_plot[col] = pd.to_numeric(df_midia_plot[col], errors='coerce')

            # Gráfico Custo
            df_cost_plot = df_midia_plot.loc[['Custo de Tráfego Pago (R$)']].reset_index().melt(id_vars='Metrica', var_name='Canal', value_name='Custo')
            fig_midia_cost = px.bar(df_cost_plot, x='Canal', y='Custo', color='Canal', title='Custo Total por Canal', text='Custo', labels={'Custo':'Custo (R$)'})
            fig_midia_cost.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
            fig_midia_cost.update_layout(showlegend=False)
            st.plotly_chart(fig_midia_cost, use_container_width=True)

            # Gráfico CPA
            df_cpa_plot = df_midia_plot.loc[['CPA (R$)']].reset_index().melt(id_vars='Metrica', var_name='Canal', value_name='CPA')
            fig_midia_cpa = px.bar(df_cpa_plot, x='Canal', y='CPA', color='Canal', title='CPA por Canal', text='CPA', labels={'CPA':'CPA (R$)'})
            fig_midia_cpa.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
            fig_midia_cpa.update_layout(showlegend=False)
            st.plotly_chart(fig_midia_cpa, use_container_width=True)

            # Gráfico CTR
            df_ctr_plot = df_midia_plot.loc[['CTR (%)']].reset_index().melt(id_vars='Metrica', var_name='Canal', value_name='CTR')
            fig_midia_ctr = px.bar(df_ctr_plot, x='Canal', y='CTR', color='Canal', title='CTR por Canal', text='CTR', labels={'CTR':'CTR (%)'})
            fig_midia_ctr.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_midia_ctr.update_layout(showlegend=False)
            st.plotly_chart(fig_midia_ctr, use_container_width=True)

        except KeyError as e:
            st.warning(f"Métrica não encontrada para gráficos de mídia: {e}")
        except Exception as e:
            st.warning(f"Erro ao gerar gráficos de mídia: {e}")

else:
    st.warning("Não foi possível carregar os dados necessários para a página de Aquisição.")
