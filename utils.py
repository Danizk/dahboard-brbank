import streamlit as st
import pandas as pd
import re # Importar regex para limpeza mais robusta

# --- Funções de Formatação (Mantidas como antes) ---
def format_currency(value):
    try:
        if isinstance(value, (int, float)): numeric_value = float(value)
        else:
            numeric_string = re.sub(r'[^\d,.]', '', str(value))
            if ',' in numeric_string and '.' in numeric_string:
                if numeric_string.rfind(',') > numeric_string.rfind('.'):
                    numeric_string = numeric_string.replace('.', '').replace(',', '.')
            numeric_string = numeric_string.replace(',', '')
            numeric_value = float(numeric_string)
        return f"R$ {numeric_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError, AttributeError): return "N/A"

def format_percentage(value):
    try:
        numeric_value = float(value)
        return f"{numeric_value:.2f}%"
    except (ValueError, TypeError, AttributeError): return "N/A"

# --- Funções de Carregamento de Dados (Cache aplicado) ---
@st.cache_data
def load_kpis():
    try:
        # --- CORREÇÃO APLICADA AQUI ---
        # Usa 'Métrica' com acento no set_index
        df = pd.read_csv('kpis_gerais.csv').set_index('Métrica')
        # --- FIM DA CORREÇÃO ---

        df['Valor_Limp'] = df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
        df['Valor'] = pd.to_numeric(df['Valor_Limp'], errors='coerce')
        df = df.drop(columns=['Valor_Limp'])

        if df['Valor'].isnull().any():
             st.warning("Aviso: Alguns valores em kpis_gerais.csv não puderam ser convertidos para número.")
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo kpis_gerais.csv não encontrado.")
        return None
    # Captura o erro específico de coluna não encontrada
    except KeyError as e:
         st.error(f"Erro Crítico ao processar kpis_gerais.csv: Coluna esperada não encontrada: {e}. Verifique o cabeçalho do CSV.")
         return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar kpis_gerais.csv: {e}")
        return None

@st.cache_data
def load_midia():
    try:
        df = pd.read_csv('midia_canais.csv').set_index('Metrica') # Assume que aqui é 'Metrica' sem acento
        cols_to_convert_midia = ['MetaAds', 'GoogleAds', 'Total']
        for col in cols_to_convert_midia:
             if col in df.columns:
                  df[f'{col}_Limp'] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
                  df[col] = pd.to_numeric(df[f'{col}_Limp'], errors='coerce')
                  df = df.drop(columns=[f'{col}_Limp'])
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo midia_canais.csv não encontrado.")
        return None
    except KeyError as e:
         st.error(f"Erro Crítico ao processar midia_canais.csv: Coluna 'Metrica' não encontrada para índice. Verifique o cabeçalho do CSV.")
         return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar midia_canais.csv: {e}")
        return None

@st.cache_data
def load_performance():
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
    try:
         # --- CORREÇÃO APLICADA AQUI ---
         # Usa 'Motivo' com acento no set_index, assumindo que o CSV também tem acento
        df = pd.read_csv('motivos_perda.csv').set_index('Motivo')
        # --- FIM DA CORREÇÃO ---
        cols_to_num = ['A', 'B', 'C', 'D', 'E', 'Total']
        for col in cols_to_num:
            if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo motivos_perda.csv não encontrado.")
        return None
    # Captura erro específico de coluna não encontrada
    except KeyError as e:
         st.error(f"Erro Crítico ao processar motivos_perda.csv: Coluna esperada ('Motivo'?) não encontrada para índice: {e}. Verifique o cabeçalho do CSV.")
         return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar motivos_perda.csv: {e}")
        return None

# --- Função para Download de DataFrame como CSV ---
@st.cache_data
def convert_df_to_csv(df_to_convert):
   include_index = df_to_convert.index.name is not None
   return df_to_convert.to_csv(index=include_index).encode('utf-8-sig')
