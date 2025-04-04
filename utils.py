import streamlit as st
import pandas as pd

# --- Funções de Formatação (Mantidas como no original) ---
# Obs: A lógica de limpeza dentro destas funções pode ser redundante ou
# até problemática se as funções de carregamento já fornecerem números limpos.
# Considere simplificá-las se encontrar problemas ou para maior clareza.
def format_currency(value):
    try:
        # Tenta limpar e converter caso receba string, ou converte direto se for número
        if isinstance(value, (int, float)):
             numeric_value = float(value)
        else:
            # Lógica original de limpeza (pode ser frágil)
            numeric_string = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], str(value)))
            # Tenta tratar milhares com '.' e decimal com ','
            if isinstance(numeric_string, str):
                 # Remove pontos de milhar (todos menos o último se houver vírgula)
                 if ',' in numeric_string:
                      parts = numeric_string.split(',')
                      integer_part = parts[0].replace('.', '')
                      numeric_string = f"{integer_part}.{parts[1]}" if len(parts) > 1 else integer_part
                 else: # Se não há vírgula, remove todos os pontos (arriscado se for decimal)
                      # Melhor assumir que ponto é decimal se não há vírgula
                      pass # Mantém o ponto como está
            numeric_value = float(numeric_string)

        # Formatação BR
        return f"R$ {numeric_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError, AttributeError):
        return "N/A" # Retorna N/A se não for número válido

def format_percentage(value):
    try:
       # Tenta limpar e converter caso receba string, ou converte direto se for número
        if isinstance(value, (int, float)):
             numeric_value = float(value)
        else:
            # Lógica original de limpeza (similar à de format_currency, pode ser frágil)
            numeric_string = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], str(value)))
            if isinstance(numeric_string, str):
                 if ',' in numeric_string:
                      parts = numeric_string.split(',')
                      integer_part = parts[0].replace('.', '')
                      numeric_string = f"{integer_part}.{parts[1]}" if len(parts) > 1 else integer_part
                 else:
                      pass # Mantém o ponto como está (assumindo ser decimal)
            numeric_value = float(numeric_string)

        # Formatação Percentual (talvez queira usar vírgula como decimal aqui também?)
        # return f"{numeric_value:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".") # Exemplo com vírgula
        return f"{numeric_value:.2f}%" # Original com ponto
    except (ValueError, TypeError, AttributeError):
        return "N/A"

# --- Funções de Carregamento de Dados (Corrigidas e com Cache) ---
@st.cache_data
def load_kpis():
    try:
        df = pd.read_csv('kpis_gerais.csv').set_index('Metrica')
        # --- CORREÇÃO ---
        # Converte a coluna 'Valor' diretamente para numérico.
        # Assume que o CSV usa '.' como decimal e não contém outros caracteres (R$, %).
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce') # Erros viram NaN

        # Opcional: Adiciona um aviso se houver falha na conversão
        if df['Valor'].isnull().any():
            st.warning("Atenção: Alguns valores na coluna 'Valor' do kpis_gerais.csv não puderam ser convertidos para número e foram definidos como Nulos (NaN).")

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
        nan_warning = False # Flag para aviso
        for col in cols_to_convert_midia:
            if col in df.columns:
                # --- CORREÇÃO ---
                # Tenta converter diretamente para numérico
                original_type = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if df[col].isnull().any() and 'object' in str(original_type):
                     nan_warning = True # Marca se houve NaN após tentar converter de objeto/string

        # Opcional: Aviso único se alguma conversão falhou
        if nan_warning:
             st.warning(f"Atenção: Pelo menos uma coluna em midia_canais.csv ({', '.join(cols_to_convert_midia)}) continha valores não numéricos que foram definidos como Nulos (NaN).")

        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo midia_canais.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar midia_canais.csv: {e}")
        return None

@st.cache_data
def load_performance():
    try:
        df = pd.read_csv('performance_vendedores.csv')
        # Esta função já usava pd.to_numeric diretamente, o que é geralmente correto
        # se os dados no CSV estiverem em formato numérico padrão.
        cols_to_num = ['Leads Recebidos', 'Leads Convertidos', 'Leads Perdidos', 'Taxa Conversão (%)', 'Ticket Médio (R$)', 'Receita Total (R$)', 'Receita por Lead (R$)', 'Tempo Conversão (dias)']
        nan_warning = False
        for col in cols_to_num:
            if col in df.columns:
                original_type = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce') # Erros viram NaN
                if df[col].isnull().any() and 'object' in str(original_type):
                    nan_warning = True

        if nan_warning:
             st.warning(f"Atenção: Pelo menos uma coluna em performance_vendedores.csv continha valores não numéricos que foram definidos como Nulos (NaN).")

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
        df = pd.read_csv('motivos_perda.csv').set_index('Motivo')
         # Esta função também já usava pd.to_numeric diretamente.
        cols_to_num = ['A', 'B', 'C', 'D', 'E', 'Total']
        nan_warning = False
        for col in cols_to_num:
            if col in df.columns:
                original_type = df[col].dtype
                df[col] = pd.to_numeric(df[col], errors='coerce') # Erros viram NaN
                if df[col].isnull().any() and 'object' in str(original_type):
                     nan_warning = True

        if nan_warning:
             st.warning(f"Atenção: Pelo menos uma coluna em motivos_perda.csv ({', '.join(cols_to_num)}) continha valores não numéricos que foram definidos como Nulos (NaN).")

        return df
    except FileNotFoundError:
        st.error("Erro Crítico: Arquivo motivos_perda.csv não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar motivos_perda.csv: {e}")
        return None

# --- Função para Download de DataFrame como CSV (Mantida como no original) ---
@st.cache_data # Cacheia a conversão para não refazer toda hora
def convert_df_to_csv(df_to_convert):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    # Garante que o índice seja incluído se ele tiver nome (como 'Motivo' ou 'Metrica')
    include_index = df_to_convert.index.name is not None
    return df_to_convert.to_csv(index=include_index).encode('utf-8-sig') # Usa utf-8-sig para melhor compatibilidade Excel

# --- O restante do seu código Streamlit viria aqui ---
# Exemplo:
# st.title("Dashboard BR Bank")
# kpis_df = load_kpis()
# if kpis_df is not None:
#     st.metric("Receita Total", format_currency(kpis_df.loc['Receita Total (R$)','Valor']))
#     # ... exibir outros kpis ...
