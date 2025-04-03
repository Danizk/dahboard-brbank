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
def load_monetization_data():
    try:
        df_kpis = pd.read_csv('kpis_gerais.csv').set_index('Metrica')
        df_performance = pd.read_csv('performance_vendedores.csv')
        return df_kpis, df_performance
    except FileNotFoundError as e:
        st.error(f"Erro: Arquivo {e.filename} não encontrado.")
        return None, None
    except Exception as e:
        st.error(f"Erro ao carregar dados de monetização: {e}")
        return None, None

df_kpis, df_performance = load_monetization_data()

# --- Conteúdo da Página ---
st.title("💰 Monetização (Bottom of Funnel)")
st.markdown("Resultados financeiros e análise da performance da equipe de vendas.")
st.markdown("---")

if df_kpis is not None and df_performance is not None:
    st.subheader("Resultados Financeiros Chave")
    col1, col2, col3, col4 = st.columns(4)
    try:
        col1.metric("Receita Total", format_currency(df_kpis.loc['Receita Total (R$)', 'Valor']))
        col2.metric("Lucro Líquido", format_currency(df_kpis.loc['Lucro Líquido (R$)', 'Valor']))
        col3.metric("Ticket Médio por Cliente", format_currency(df_kpis.loc['Ticket Médio (R$)', 'Valor']))
        col4.metric("LTV (proxy)", format_currency(df_kpis.loc['LTV (R$)', 'Valor']))
    except KeyError as e:
        st.warning(f"Métrica não encontrada para Resultados Financeiros: {e}")

    st.markdown("---")
    st.header("🏆 Performance da Equipe de Vendas")

    st.dataframe(df_performance.set_index('Vendedor')) # Mostra tabela completa

    # Gráficos de Performance
    col_vend1, col_vend2 = st.columns(2)
    try:
        with col_vend1:
            fig_rev_vendedor = px.bar(df_performance, x='Vendedor', y='Receita Total (R$)', color='Vendedor', title='Receita Total Gerada', text='Receita Total (R$)', labels={'Receita Total (R$)':'Receita (R$)'})
            fig_rev_vendedor.update_traces(texttemplate='%{text:,.2s}', textposition='outside')
            fig_rev_vendedor.update_layout(showlegend=False)
            st.plotly_chart(fig_rev_vendedor, use_container_width=True)

            fig_leads_conv_vendedor = px.bar(df_performance, x='Vendedor', y='Leads Convertidos', color='Vendedor', title='Leads Convertidos', text='Leads Convertidos')
            fig_leads_conv_vendedor.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_leads_conv_vendedor.update_layout(showlegend=False)
            st.plotly_chart(fig_leads_conv_vendedor, use_container_width=True)

        with col_vend2:
            fig_tx_vendedor = px.bar(df_performance, x='Vendedor', y='Taxa Conversão (%)', color='Vendedor', title='Taxa de Conversão', text='Taxa Conversão (%)', range_y=[0, df_performance['Taxa Conversão (%)'].max() * 1.15])
            fig_tx_vendedor.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_tx_vendedor.update_layout(showlegend=False)
            st.plotly_chart(fig_tx_vendedor, use_container_width=True)

            fig_tempo_vendedor = px.bar(df_performance, x='Vendedor', y='Tempo Conversão (dias)', color='Vendedor', title='Tempo Médio de Conversão', text='Tempo Conversão (dias)')
            fig_tempo_vendedor.update_traces(texttemplate='%{text:.0f}d', textposition='outside')
            fig_tempo_vendedor.update_layout(showlegend=False)
            st.plotly_chart(fig_tempo_vendedor, use_container_width=True)

        # Ranking de Performance (Conforme Proposta)
        st.subheader("📊 Ranking de Performance")
        ranking_col1, ranking_col2 = st.columns(2)
        with ranking_col1:
            st.markdown("**Melhor Performance**")
            st.write(f"📈 **Taxa de Conversão:** {df_performance.loc[df_performance['Taxa Conversão (%)'].idxmax()]['Vendedor']} ({df_performance['Taxa Conversão (%)'].max():.2f}%)")
            st.write(f"💰 **Receita Total:** {df_performance.loc[df_performance['Receita Total (R$)'].idxmax()]['Vendedor']} ({format_currency(df_performance['Receita Total (R$)'].max())})")
            st.write(f"🎟️ **Ticket Médio:** {df_performance.loc[df_performance['Ticket Médio (R$)'].idxmax()]['Vendedor']} ({format_currency(df_performance['Ticket Médio (R$)'].max())})")
            st.write(f"⏱️ **Tempo de Conversão (Mais Rápido):** {df_performance.loc[df_performance['Tempo Conversão (dias)'].idxmin()]['Vendedor']} ({df_performance['Tempo Conversão (dias)'].min()} dias)")

        with ranking_col2:
            st.markdown("**Pior Performance**")
            st.write(f"📉 **Taxa de Conversão:** {df_performance.loc[df_performance['Taxa Conversão (%)'].idxmin()]['Vendedor']} ({df_performance['Taxa Conversão (%)'].min():.2f}%)")
            st.write(f"💸 **Receita Total:** {df_performance.loc[df_performance['Receita Total (R$)'].idxmin()]['Vendedor']} ({format_currency(df_performance['Receita Total (R$)'].min())})")
            st.write(f"🎟️ **Ticket Médio:** {df_performance.loc[df_performance['Ticket Médio (R$)'].idxmin()]['Vendedor']} ({format_currency(df_performance['Ticket Médio (R$)'].min())})")
            st.write(f"⏳ **Tempo de Conversão (Mais Lento):** {df_performance.loc[df_performance['Tempo Conversão (dias)'].idxmax()]['Vendedor']} ({df_performance['Tempo Conversão (dias)'].max()} dias)")

    except Exception as e:
        st.warning(f"Erro ao exibir performance dos vendedores: {e}")
else:
    st.warning("Não foi possível carregar os dados necessários para a página de Monetização.")
