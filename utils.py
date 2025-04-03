import streamlit as st
import pandas as pd
import re # Importar regex para limpeza mais robusta

# --- Funções de Formatação (Mantidas) ---
def format_currency(value):
    try:
        # Tenta converter para float primeiro, se já for numérico
        if isinstance(value, (int, float)):
            numeric_value = float(value)
        else:
            # Limpeza robusta: remove tudo exceto dígitos, ponto e vírgula
            # Substitui vírgula decimal por ponto
            numeric_string = re.sub(r'[^\d,.]', '', str(value))
            # Trata caso pt-BR (milhar com ponto, decimal com vírgula)
            if ',' in numeric_string and '.' in numeric_string:
                if numeric_string.rfind(',') > numeric_string.rfind('.'):
                    numeric_string = numeric_string.replace('.', '').replace(',', '.')
                else: # Assume formato com vírgula de milhar e ponto decimal
                     numeric_string = numeric_string.replace(',', '')
            else: # Se só tem vírgula, assume que é decimal
                 numeric_string = numeric_string.replace(',', '.')

            numeric_value = float(numeric_string)

        # Formatação BR
        return f"R$ {numeric_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError, AttributeError):
        return "N/A"

def format_percentage(value):
    try:
        numeric_value = float(value) # Converte direto, a leitura deve estar correta agora
        return f"{numeric_value:.2f}%"
    except (ValueError, TypeError, AttributeError):
        return "N/A"

# --- Funções de Carregamento de Dados (Cache aplicado) ---
@st.cache_data
def load_kpis():
    try:
        df = pd.read_csv('kpis_gerais.csv').set_index('Metrica')

        # --- LÓGICA DE LIMPEZA CORRIGIDA E SIMPLIFICADA ---
        # Remove R$, %, e espaços em branco das bordas.
        # Assume que o separador decimal no CSV é '.' e não há separador de milhar,
        # ou que o separador de milhar é ',' (que será ignorado pelo to_numeric padrão).
        df['Valor_Limp'] = df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
        # Converte para numérico, tratando erros. A função pd.to_numeric lida bem com '.' como decimal.
        df['Valor'] = pd.to_numeric(df['Valor_Limp'], errors='coerce')
        df = df.drop(columns=['Valor_Limp']) # Remove coluna auxiliar
        # --- FIM DA LÓGICA CORRIGIDA ---

        if df['Valor'].isnull().any():
             st.warning("Aviso: Alguns valores em kpis_gerais.csv não puderam ser convertidos para número.")
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo kpis_gerais.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar kpis_gerais.csv: {e}")
        return None

@st.cache_data
def load_midia():
    try:
        df = pd.read_csv('midia_canais.csv').set_index('Metrica')
        cols_to_convert_midia = ['MetaAds', 'GoogleAds', 'Total']
        for col in cols_to_convert_midia:
             if col in df.columns:
                  # --- LÓGICA DE LIMPEZA CORRIGIDA E SIMPLIFICADA ---
                  df[f'{col}_Limp'] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
                  df[col] = pd.to_numeric(df[f'{col}_Limp'], errors='coerce')
                  df = df.drop(columns=[f'{col}_Limp'])
                  # --- FIM DA LÓGICA CORRIGIDA ---
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo midia_canais.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar midia_canais.csv: {e}")
        return None

@st.cache_data
def load_performance(): # Mantida como antes, conversão numérica parece ok
    try:
        df = pd.read_csv('performance_vendedores.csv')
        cols_to_num = ['Leads Recebidos', 'Leads Convertidos', 'Leads Perdidos', 'Taxa Conversão (%)', 'Ticket Médio (R$)', 'Receita Total (R$)', 'Receita por Lead (R$)', 'Tempo Conversão (dias)']
        for col in cols_to_num:
            if col in df.columns:
                 # Tenta converter direto, se falhar vira NaN
                 df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo performance_vendedores.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar performance_vendedores.csv: {e}")
        return None

@st.cache_data
def load_perda(): # Mantida como antes, conversão numérica parece ok
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

# --- Função para Download de DataFrame como CSV (Mantida) ---
@st.cache_data
def convert_df_to_csv(df_to_convert):
   include_index = df_to_convert.index.name is not None
   return df_to_convert.to_csv(index=include_index).encode('utf-8-sig')
