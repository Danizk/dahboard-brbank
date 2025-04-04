import streamlit as st
import pandas as pd
import re

# --- Funções de Formatação (Ultra-Simplificadas) ---
def format_currency(value):
    try:
        # Tenta formatar direto, assumindo que 'value' já é numérico após load_kpis
        return f"R$ {float(value):,.2f}"
    except:
        return "N/A" # Retorna N/A se não conseguir formatar

def format_percentage(value):
    try:
        # Tenta formatar direto, assumindo que 'value' já é numérico após load_kpis
        return f"{float(value):.2f}%"
    except:
        return "N/A"

# --- Funções de Carregamento de Dados (Ultra-Simplificadas) ---
@st.cache_data
def load_kpis():
    try:
        # Leitura direta, especificando decimal e tentando inferir índice corretamente
        df = pd.read_csv('kpis_gerais.csv', decimal='.')
        # Verifica se 'Métrica' existe antes de definir como índice
        if 'Métrica' in df.columns:
             df = df.set_index('Métrica')
        elif 'Metrica' in df.columns: # Fallback caso o cabeçalho mude
             df = df.set_index('Metrica')
        else:
             st.error("Coluna 'Métrica' ou 'Metrica' não encontrada em kpis_gerais.csv!")
             return None

        # Tenta converter 'Valor' para numérico, removendo APENAS R$ e % se presentes
        # Esta é uma tentativa mais segura se os números já estiverem quase limpos no CSV
        df['Valor'] = df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce')

        if df['Valor'].isnull().any():
             st.warning("Aviso Simplificado: Alguns valores em kpis_gerais.csv não são numéricos.")
        return df
    except FileNotFoundError:
        st.error("Erro Simplificado: Arquivo kpis_gerais.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro Simplificado ao carregar kpis_gerais.csv: {e}")
        return None

# Mantem as outras funções de load como estavam na última versão funcional do código
@st.cache_data
def load_midia():
    try:
        df = pd.read_csv('midia_canais.csv').set_index('Metrica') # Assume 'Metrica' aqui
        cols_to_convert_midia = ['MetaAds', 'GoogleAds', 'Total']
        for col in cols_to_convert_midia:
             if col in df.columns:
                  df[f'{col}_Limp'] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
                  df[col] = pd.to_numeric(df[f'{col}_Limp'], errors='coerce')
                  df = df.drop(columns=[f'{col}_Limp'])
        return df
    except FileNotFoundError: st.error("Erro Crítico: Arquivo midia_canais.csv não encontrado."); return None
    except KeyError as e: st.error(f"Erro Crítico: Coluna 'Metrica' não encontrada em midia_canais.csv."); return None
    except Exception as e: st.error(f"Erro ao carregar midia_canais.csv: {e}"); return None

@st.cache_data
def load_performance():
    try:
        df = pd.read_csv('performance_vendedores.csv')
        cols_to_num = ['Leads Recebidos', 'Leads Convertidos', 'Leads Perdidos', 'Taxa Conversão (%)', 'Ticket Médio (R$)', 'Receita Total (R$)', 'Receita por Lead (R$)', 'Tempo Conversão (dias)']
        for col in cols_to_num:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except FileNotFoundError: st.error("Erro Crítico: Arquivo performance_vendedores.csv não encontrado."); return None
    except Exception as e: st.error(f"Erro ao carregar performance_vendedores.csv: {e}"); return None

@st.cache_data
def load_perda():
    try:
        df = pd.read_csv('motivos_perda.csv').set_index('Motivo') # Assume 'Motivo'
        cols_to_num = ['A', 'B', 'C', 'D', 'E', 'Total']
        for col in cols_to_num:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except FileNotFoundError: st.error("Erro Crítico: Arquivo motivos_perda.csv não encontrado."); return None
    except KeyError as e: st.error(f"Erro Crítico: Coluna 'Motivo' não encontrada em motivos_perda.csv."); return None
    except Exception as e: st.error(f"Erro ao carregar motivos_perda.csv: {e}"); return None

@st.cache_data
def convert_df_to_csv(df_to_convert):
   include_index = df_to_convert.index.name is not None
   return df_to_convert.to_csv(index=include_index).encode('utf-8-sig')
