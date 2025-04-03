import streamlit as st
import pandas as pd

# --- Funções de Formatação (Mantidas como antes) ---
def format_currency(value):
    try:
        numeric_string = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], str(value)))
        # Lógica aprimorada para lidar com . como milhar e , como decimal OU o contrário
        if ',' in numeric_string and '.' in numeric_string:
            if numeric_string.rfind(',') > numeric_string.rfind('.'): # Formato pt-BR: 1.234,56
                 numeric_string = numeric_string.replace('.', '', numeric_string.count('.') -1).replace(',', '.')
            # else: Formato en-US 1,234.56 - já estaria quase correto, só remover vírgula
        numeric_string = numeric_string.replace(',', '') # Remove separador de milhar se for vírgula

        numeric_value = float(numeric_string)
        # Formatação BR
        return f"R$ {numeric_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError, AttributeError):
        return "N/A"

def format_percentage(value):
    try:
        # Converte para float e formata, não precisa de limpeza complexa se a leitura estiver correta
        numeric_value = float(value)
        return f"{numeric_value:.2f}%"
    except (ValueError, TypeError, AttributeError):
        return "N/A"

# --- Funções de Carregamento de Dados (Cache aplicado aqui) ---
@st.cache_data
def load_kpis():
    try:
        df = pd.read_csv('kpis_gerais.csv').set_index('Metrica')
        # --- LÓGICA DE LIMPEZA CORRIGIDA ---
        # Remove R$, % e espaços. Trata , como separador de milhar (remove). Preserva . como decimal.
        df['Valor'] = pd.to_numeric(
            df['Valor'].astype(str).str.replace('R$', '', regex=False)
                                  .str.replace('%', '', regex=False)
                                  .str.replace('.', '', regex=False) # Remove separador de milhar pt-BR
                                  .str.replace(',', '.', regex=False) # Troca decimal pt-BR para .
                                  .str.strip(), # Remove espaços extras
            errors='coerce' # Erros viram NaN
        )
        # --- FIM DA LÓGICA CORRIGIDA ---
        if df['Valor'].isnull().any():
             st.warning("Aviso: Alguns valores em kpis_gerais.csv não puderam ser convertidos para número após limpeza.")
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo kpis_gerais.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar kpis_gerais.csv: {e}")
        return None

@st.cache_data
def load_midia(): # Mantida como antes, parece ok
    try:
        df = pd.read_csv('midia_canais.csv').set_index('Metrica')
        cols_to_convert_midia = ['MetaAds', 'GoogleAds', 'Total']
        for col in cols_to_convert_midia:
             if col in df.columns and df[col].dtype == 'object':
                  df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip()
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
def load_performance(): # Mantida como antes, parece ok
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
def load_perda(): # Mantida como antes, parece ok
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
   include_index = df_to_convert.index.name is not None
   return df_to_convert.to_csv(index=include_index).encode('utf-8-sig')
