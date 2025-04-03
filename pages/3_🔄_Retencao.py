import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Funções Auxiliares ---
# (Duplicadas ou importar de utils.py)
# ... (cole aqui as funções format_currency e format_percentage) ...
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


# --- Carregar Dados Essenciais ---
@st.cache_data
def load_retention_data():
    try:
        df_kpis = pd.read_csv('kpis_gerais.csv').set_index('Metrica')
        df_perda = pd.read_csv('motivos_perda.csv').set_index('Motivo')
        return df_kpis, df_perda
    except FileNotFoundError as e:
        st.error(f"Erro: Arquivo {e.filename} não encontrado.")
        return None, None
    except Exception as e:
        st.error(f"Erro ao carregar dados de retenção: {e}")
        return None, None

df_kpis, df_perda = load_retention_data()

# --- Conteúdo da Página ---
st.title("🔄 Retenção (Middle of Funnel)")
st.markdown("Análise da conversão de leads, tempo e motivos de perda.")
st.markdown("---")

if df_kpis is not None and df_perda is not None:
    st.subheader("Indicadores Chave de Retenção")
    col1, col2, col3, col4 = st.columns(4)
    try:
        col1.metric("Leads Cadastrados (CRM)", f"{int(df_kpis.loc['Leads Cadastrados no CRM', 'Valor']):,}")
        col2.metric("Leads Convertidos", f"{int(df_kpis.loc['Leads Convertidos', 'Valor']):,}")
        col3.metric("Leads Perdidos", f"{int(df_kpis.loc['Leads Perdidos', 'Valor']):,}")
        col4.metric("Tx. Conv. Leads → Clientes", format_percentage(df_kpis.loc['Taxa de Conversão Leads → Clientes (%)', 'Valor']))

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Tempo Médio Conversão", f"{int(df_kpis.loc['Tempo Médio para Conversão (dias)', 'Valor'])} dias", help="Tempo médio entre cadastro no CRM e conversão.")
        col6.metric("Leads Ativos (Follow-up)", f"{int(df_kpis.loc['Leads Ativos para Follow-up', 'Valor']):,}", help="Leads no CRM que ainda não converteram nem foram perdidos.")
        # Deixe col7 e col8 vazios ou adicione outros KPIs relevantes se tiver
        col7.empty()
        col8.empty()

    except KeyError as e:
        st.warning(f"Métrica não encontrada para Indicadores de Retenção: {e}")
    except ValueError as e:
        st.warning(f"Erro ao converter valor para Indicadores de Retenção: {e}")

    st.markdown("---")
    st.header("🚫 Motivos de Perda")

    col_perda1, col_perda2 = st.columns(2)

    with col_perda1:
        st.subheader("Volume Total por Motivo")
        try:
            df_perda_total = df_perda[['Total']].sort_values(by='Total', ascending=False)
            st.dataframe(df_perda_total)

            fig_perda_pie = px.pie(df_perda_total, names=df_perda_total.index, values='Total',
                                  title='Distribuição Geral dos Motivos de Perda', hole=0.3)
            fig_perda_pie.update_traces(textinfo='percent+label', textfont_size=14, marker=dict(line=dict(color='#000000', width=1)))
            st.plotly_chart(fig_perda_pie, use_container_width=True)
        except Exception as e:
            st.warning(f"Erro ao exibir motivos de perda totais: {e}")

    with col_perda2:
        st.subheader("Comparativo por Vendedor")
        try:
            df_perda_comp = df_perda.drop(columns=['Total']).reset_index()
            df_perda_melted = df_perda_comp.melt(id_vars='Motivo', var_name='Vendedor', value_name='Quantidade')

            fig_perda_vendedor = px.bar(df_perda_melted, x='Motivo', y='Quantidade', color='Vendedor',
                                        barmode='group', title='Motivos de Perda Detalhados por Vendedor',
                                        labels={'Quantidade':'Nº de Leads Perdidos'},
                                        category_orders={"Motivo": df_perda_total.index.tolist()}) # Usa a ordem do total
            fig_perda_vendedor.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_perda_vendedor, use_container_width=True)
        except Exception as e:
            st.warning(f"Erro ao exibir motivos de perda por vendedor: {e}")
else:
    st.warning("Não foi possível carregar os dados necessários para a página de Retenção.")
