import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Configuração da Página (só precisa estar no script principal) ---
st.set_page_config(
    page_title="BR Bank - Visão Geral",
    page_icon="🏠",
    layout="wide"
)

# --- Funções Auxiliares ---
# (Duplicadas aqui para manter a página independente, poderiam ir para utils.py)
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
@st.cache_data # Cacheia o resultado da função
def load_kpis():
    try:
        df_kpis = pd.read_csv('kpis_gerais.csv')
        df_kpis = df_kpis.set_index('Metrica')
        return df_kpis
    except FileNotFoundError:
        st.error("Erro: Arquivo kpis_gerais.csv não encontrado.")
        return None # Retorna None se o arquivo não for encontrado
    except Exception as e:
        st.error(f"Erro ao carregar kpis_gerais.csv: {e}")
        return None

df_kpis = load_kpis()

# --- Conteúdo da Página ---
st.title("🏠 Resumo Executivo | BR Bank")
st.markdown("Visão Geral dos Indicadores Chave (Set/22 a Fev/23)")
st.markdown("---")

if df_kpis is not None: # Verifica se os dados foram carregados
    st.header("📈 Performance Financeira e Operacional")

    # Usar .loc para buscar valores pelo índice 'Metrica' e aplicar formatação
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Total", format_currency(df_kpis.loc['Receita Total (R$)', 'Valor']), help="Faturamento total no período.")
    col2.metric("Lucro Líquido", format_currency(df_kpis.loc['Lucro Líquido (R$)', 'Valor']), help="Receita Total - Custo de Tráfego Pago. (Outros custos não incluídos).")
    col3.metric("Margem Líquida", format_percentage(df_kpis.loc['Margem Líquida (%)', 'Valor']), help="Lucro Líquido / Receita Total.")
    col4.metric("ROAS", format_percentage(df_kpis.loc['ROAS (%)', 'Valor']), help="(Receita Gerada por Ads / Custo de Ads) * 100%")

    st.markdown("---") # Linha separadora

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Leads Convertidos", f"{int(df_kpis.loc['Leads Convertidos', 'Valor']):,}", help="Número total de empréstimos contratados no período.")
    col6.metric("Ticket Médio", format_currency(df_kpis.loc['Ticket Médio (R$)', 'Valor']), help="Receita Total / Leads Convertidos.")
    col7.metric("LTV (proxy)", format_currency(df_kpis.loc['LTV (R$)', 'Valor']), help="Valor médio do cliente (neste caso, igual ao Ticket Médio pois é um produto único).")
    col8.metric("CAC (proxy)", format_currency(df_kpis.loc['CPA - Custo por Aquisição (R$)', 'Valor']), help="Custo por Aquisição (Custo de Ads / Leads Captados por Ads). Considera apenas custo de mídia.")

    # Poderia adicionar aqui a projeção vs meta se tivesse os dados
    # st.header("🎯 Meta de Faturamento (R$ 30M até Dez/23)")
    # Adicionar gráfico de progresso ou projeção aqui...

else:
    st.warning("Não foi possível carregar os dados de KPIs para exibir o resumo.")

st.caption(f"Data da última atualização: {pd.to_datetime('today').strftime('%d/%m/%Y')}")
