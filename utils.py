import streamlit as st
import pandas as pd

# --- Funções de Formatação ---
def format_currency(value):
    """Formata um valor numérico para moeda brasileira (R$ XXX.XXX,XX)."""
    try:
        numeric_string = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], str(value)))
        numeric_string = numeric_string.replace('.', '', numeric_string.count('.') - 1).replace(',', '.') if isinstance(numeric_string, str) else str(value)
        numeric_value = float(numeric_string)
        return f"R$ {numeric_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError, AttributeError):
        return "N/A"

def format_percentage(value):
    """Formata um valor numérico para porcentagem (XX.XX%)."""
    try:
        numeric_string = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], str(value)))
        numeric_string = numeric_string.replace('.', '', numeric_string.count('.') - 1).replace(',', '.') if isinstance(numeric_string, str) else str(value)
        numeric_value = float(numeric_string)
        return f"{numeric_value:.2f}%"
    except (ValueError, TypeError, AttributeError):
        return "N/A"

# --- Funções de Carregamento de Dados ---
@st.cache_data
def load_kpis():
    """Carrega e processa o arquivo kpis_gerais.csv."""
    try:
        df = pd.read_csv('kpis_gerais.csv').set_index('Metrica')
        df['Valor'] = pd.to_numeric(
            df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace('%', '', regex=False).str.replace(',', '.', regex=False),
            errors='coerce'
        )
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo kpis_gerais.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar kpis_gerais.csv: {e}")
        return None

@st.cache_data
def load_midia():
    """Carrega e processa o arquivo midia_canais.csv."""
    try:
        df = pd.read_csv('midia_canais.csv').set_index('Metrica')
        cols_to_convert_midia = ['MetaAds', 'GoogleAds', 'Total']
        for col in cols_to_convert_midia:
            if col in df.columns and df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo midia_canais.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar midia_canais.csv: {e}")
        return None

@st.cache_data
def load_performance():
    """Carrega e processa o arquivo performance_vendedores.csv."""
    try:
        df = pd.read_csv('performance_vendedores.csv')
        cols_to_num = ['Leads Recebidos', 'Leads Convertidos', 'Leads Perdidos', 'Taxa Conversão (%)', 'Ticket Médio (R$)', 'Receita Total (R$)', 'Receita por Lead (R$)', 'Tempo Conversão (dias)']
        for col in cols_to_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo performance_vendedores.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar performance_vendedores.csv: {e}")
        return None

@st.cache_data
def load_perda():
    """Carrega e processa o arquivo motivos_perda.csv."""
    try:
        df = pd.read_csv('motivos_perda.csv').set_index('Motivo')
        cols_to_num = ['A', 'B', 'C', 'D', 'E', 'Total']
        for col in cols_to_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo motivos_perda.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar motivos_perda.csv: {e}")
        return None

# --- Função para Download de DataFrame como CSV ---
@st.cache_data
def convert_df_to_csv(df_to_convert):
    """Converte um DataFrame para CSV e prepara para download."""
    include_index = df_to_convert.index.name is not None
    return df_to_convert.to_csv(index=include_index).encode('utf-8-sig')
