import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# Importa funções do utils.py (necessário ter utils.py na raiz do projeto)
from utils import format_currency, format_percentage, load_kpis, load_performance, convert_df_to_csv

# --- Paleta de Cores Azul Pastel para Vendedores ---
# (Certifique-se que os nomes A, B, C, D, E correspondem aos seus dados)
azul_pastel_palette = ['#E1F5FE', '#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6'] # Do mais claro ao mais escuro
seller_color_map = {'A': azul_pastel_palette[0], 'B': azul_pastel_palette[1], 'C': azul_pastel_palette[2], 'D': azul_pastel_palette[3], 'E': azul_pastel_palette[4]}

# --- Inicialização do Estado da Sessão (Modo Executivo) ---
if 'exec_mode' not in st.session_state:
    st.session_state['exec_mode'] = False

# --- Carregar Dados Essenciais ---
df_kpis = load_kpis()
df_performance = load_performance()

# --- Conteúdo da Página ---
st.title("💰 Monetização (Bottom of Funnel)")
st.markdown("Resultados financeiros e análise da performance da equipe de vendas.")
st.markdown("---")

# Verifica se os dataframes foram carregados corretamente
if df_kpis is not None and df_performance is not None:
    st.subheader("Resultados Financeiros Chave")
    col1, col2, col3, col4 = st.columns(4)
    try:
        # Exibe KPIs financeiros com formatação segura
        col1.metric("Receita Total", format_currency(df_kpis.loc['Receita Total (R$)', 'Valor']))
        col2.metric("Lucro Líquido", format_currency(df_kpis.loc['Lucro Líquido (R$)', 'Valor']))
        col3.metric("Ticket Médio por Cliente", format_currency(df_kpis.loc['Ticket Médio (R$)', 'Valor']))
        col4.metric("LTV (proxy)", format_currency(df_kpis.loc['LTV (R$)', 'Valor']))
    except KeyError as e:
        st.warning(f"Métrica financeira não encontrada: {e}. Verifique kpis_gerais.csv.")
    except Exception as e:
        st.error(f"Erro ao exibir KPIs financeiros: {e}")


    st.markdown("---")
    st.header("🏆 Performance da Equipe de Vendas")

    try:
        # Cria cópia para não alterar o dataframe cacheado
        df_performance_processed = df_performance.copy()

        # --- Calcular e Adicionar Receita por Dia de Conversão ---
        receita_dia_col = 'Receita por Dia Conv (R$)'
        if 'Receita Total (R$)' in df_performance_processed.columns and 'Tempo Conversão (dias)' in df_performance_processed.columns:
            df_performance_processed[receita_dia_col] = df_performance_processed.apply(
                lambda row: row['Receita Total (R$)'] / row['Tempo Conversão (dias)']
                if pd.notna(row['Tempo Conversão (dias)']) and row['Tempo Conversão (dias)'] > 0 and pd.notna(row['Receita Total (R$)'])
                else pd.NA, # Usa pd.NA para valores indeterminados
                axis=1
            )
            # Calcula média ignorando erros/NAs
            media_receita_dia = pd.to_numeric(df_performance_processed[receita_dia_col], errors='coerce').mean()
            st.metric("Receita Média por Dia de Conversão (Geral)", format_currency(media_receita_dia), help="Média (Receita Total Vendedor / Tempo Médio Conversão Vendedor). Eficiência da receita no tempo.")
        else:
            st.warning("Colunas 'Receita Total (R$)' ou 'Tempo Conversão (dias)' não encontradas para calcular Receita por Dia.")
            receita_dia_col = None # Flag para não formatar/usar depois

        # --- Tabela de Performance (Ocultável no modo executivo) ---
        if not st.session_state.get('exec_mode', False):
            st.subheader("Tabela Detalhada de Performance")
            # Cria cópia para formatar exibição sem alterar o df_performance_processed original
            df_display = df_performance_processed.set_index('Vendedor').copy()

            # Formatação segura para exibição
            cols_to_format_currency = ['Ticket Médio (R$)', 'Receita Total (R$)', 'Receita por Lead (R$)', receita_dia_col]
            cols_to_format_currency = [col for col in cols_to_format_currency if col is not None and col in df_display.columns]
            for col in cols_to_format_currency:
                 df_display[col] = df_display[col].map(format_currency) # format_currency já retorna 'N/A' em caso de erro
            if 'Taxa Conversão (%)' in df_display.columns:
                  df_display['Taxa Conversão (%)'] = df_display['Taxa Conversão (%)'].map(format_percentage)
            if 'Tempo Conversão (dias)' in df_display.columns:
                # Formata apenas se for número, senão mantém como está (pode ser NA)
                df_display['Tempo Conversão (dias)'] = df_display['Tempo Conversão (dias)'].apply(lambda x: f"{x:.0f} dias" if pd.notna(x) else 'N/A')

            st.dataframe(df_display, use_container_width=True)

            # Botão de Download (Usa df_performance_processed com números)
            try:
                 csv_performance_download = convert_df_to_csv(df_performance_processed)
                 st.download_button(
                    label="Download Tabela de Performance", data=csv_performance_download,
                    file_name='performance_vendedores_detalhada.csv', mime='text/csv', key='download-performance'
                 )
            except Exception as e_download:
                 st.error(f"Erro ao preparar dados para download: {e_download}")

            st.markdown("---")
        # else: # Comentado para evitar mensagem desnecessária quando tabela está oculta
             # st.info("Tabela detalhada oculta no Modo Executivo.")

        # --- Gráficos de Performance (Ocultáveis no modo executivo) ---
        if not st.session_state.get('exec_mode', False):
            st.subheader("Análise Gráfica Individual")
            # Garante que temos dados para plotar
            if not df_performance_processed.empty:
                col_vend1, col_vend2 = st.columns(2)
                with col_vend1:
                    # Gráfico de Receita (Cores Atualizadas)
                    if 'Receita Total (R$)' in df_performance_processed.columns:
                        fig_rev_vendedor = px.bar(df_performance_processed, x='Vendedor', y='Receita Total (R$)', color='Vendedor', title='Receita Total Gerada', text_auto='.2s', labels={'Receita Total (R$)':'Receita (R$)'},
                                                  color_discrete_map=seller_color_map) # << COR AZUL PASTEL APLICADA
                        fig_rev_vendedor.update_traces(textposition='outside')
                        fig_rev_vendedor.update_layout(showlegend=False, height=350)
                        st.plotly_chart(fig_rev_vendedor, use_container_width=True)

                    # Gráfico Leads Convertidos (Cores Atualizadas)
                    if 'Leads Convertidos' in df_performance_processed.columns:
                        fig_leads_conv_vendedor = px.bar(df_performance_processed, x='Vendedor', y='Leads Convertidos', color='Vendedor', title='Leads Convertidos', text_auto=True,
                                                         color_discrete_map=seller_color_map) # << COR AZUL PASTEL APLICADA
                        fig_leads_conv_vendedor.update_traces(textposition='outside')
                        fig_leads_conv_vendedor.update_layout(showlegend=False, height=350)
                        st.plotly_chart(fig_leads_conv_vendedor, use_container_width=True)

                with col_vend2:
                     # Gráfico Taxa Conversão (Cores Atualizadas)
                     if 'Taxa Conversão (%)' in df_performance_processed.columns:
                        y_range_max = df_performance_processed['Taxa Conversão (%)'].max() * 1.15 if pd.notna(df_performance_processed['Taxa Conversão (%)'].max()) else None
                        fig_tx_vendedor = px.bar(df_performance_processed, x='Vendedor', y='Taxa Conversão (%)', color='Vendedor', title='Taxa de Conversão', text_auto='.1f', range_y=[0, y_range_max],
                                                 color_discrete_map=seller_color_map) # << COR AZUL PASTEL APLICADA
                        fig_tx_vendedor.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                        fig_tx_vendedor.update_layout(showlegend=False, height=350)
                        st.plotly_chart(fig_tx_vendedor, use_container_width=True)

                     # Gráfico Tempo Médio Conversão (Cores Atualizadas)
                     if 'Tempo Conversão (dias)' in df_performance_processed.columns:
                        fig_tempo_vendedor = px.bar(df_performance_processed, x='Vendedor', y='Tempo Conversão (dias)', color='Vendedor', title='Tempo Médio de Conversão', text_auto='.0f',
                                                    color_discrete_map=seller_color_map) # << COR AZUL PASTEL APLICADA
                        fig_tempo_vendedor.update_traces(texttemplate='%{text:.0f}d', textposition='outside')
                        fig_tempo_vendedor.update_layout(showlegend=False, height=350)
                        st.plotly_chart(fig_tempo_vendedor, use_container_width=True)
            else:
                 st.warning("Não há dados de performance para exibir os gráficos.")
        # else: # Comentado para evitar mensagem desnecessária
        #      st.info("Gráficos individuais ocultos no Modo Executivo.")

        st.markdown("---")
        # --- Ranking de Performance (Melhorado Visualmente) ---
        st.subheader("📊 Ranking de Performance da Equipe")

        # Função auxiliar para obter dados do ranking com segurança
        def get_rank_data(df, col, id_func, format_func=None):
             # Verifica se a coluna existe e não está toda NaN
             if col not in df.columns or df[col].isnull().all(): return "N/A", "N/A"
             # Aplica idxmin/idxmax nos não-NaN e obtém o índice original
             valid_series = df[col].dropna()
             if valid_series.empty: return "N/A", "N/A"
             idx = id_func(valid_series)
             # Se idx for retornado e existir no DataFrame original...
             if pd.notna(idx) and idx in df.index:
                 val = df.loc[idx, col]
                 vend = df.loc[idx, 'Vendedor']
                 text = format_func(val) if format_func and pd.notna(val) else (str(int(val)) if pd.notna(val) else "N/A") # Formata ou converte pra string
                 return vend, text
             return "N/A", "N/A"


        # Obtem dados para o ranking (com tratamento de erro mais robusto)
        best_tx_vend, best_tx_val = get_rank_data(df_performance_processed, 'Taxa Conversão (%)', pd.Series.idxmax, format_percentage)
        worst_tx_vend, worst_tx_val = get_rank_data(df_performance_processed, 'Taxa Conversão (%)', pd.Series.idxmin, format_percentage)
        best_rec_vend, best_rec_val = get_rank_data(df_performance_processed, 'Receita Total (R$)', pd.Series.idxmax, format_currency)
        worst_rec_vend, worst_rec_val = get_rank_data(df_performance_processed, 'Receita Total (R$)', pd.Series.idxmin, format_currency)
        best_tk_vend, best_tk_val = get_rank_data(df_performance_processed, 'Ticket Médio (R$)', pd.Series.idxmax, format_currency)
        worst_tk_vend, worst_tk_val = get_rank_data(df_performance_processed, 'Ticket Médio (R$)', pd.Series.idxmin, format_currency)
        best_tm_vend, best_tm_val = get_rank_data(df_performance_processed, 'Tempo Conversão (dias)', pd.Series.idxmin, lambda x: f"{x:.0f} dias")
        worst_tm_vend, worst_tm_val = get_rank_data(df_performance_processed, 'Tempo Conversão (dias)', pd.Series.idxmax, lambda x: f"{x:.0f} dias")

        # Exibição melhorada com colunas e expander
        ranking_col1, ranking_col2 = st.columns(2)
        with ranking_col1:
            with st.expander("🏆 Melhores Performances", expanded=True):
                st.markdown(f"**Taxa Conversão:** {best_tx_vend} ({best_tx_val})")
                st.markdown(f"**Receita Total:** {best_rec_vend} ({best_rec_val})")
                st.markdown(f"**Ticket Médio:** {best_tk_vend} ({best_tk_val})")
                st.markdown(f"**Tempo Médio Conv. (Mais Rápido):** {best_tm_vend} ({best_tm_val})")
        with ranking_col2:
             with st.expander("⚠️ Pontos de Atenção", expanded=True):
                st.markdown(f"**Taxa Conversão:** {worst_tx_vend} ({worst_tx_val})")
                st.markdown(f"**Receita Total:** {worst_rec_vend} ({worst_rec_val})")
                st.markdown(f"**Ticket Médio:** {worst_tk_vend} ({worst_tk_val})")
                st.markdown(f"**Tempo Médio Conv. (Mais Lento):** {worst_tm_vend} ({worst_tm_val})")

    except Exception as e:
        st.error(f"Ocorreu um erro ao exibir performance dos vendedores: {e}")
else:
    st.error("Arquivos kpis_gerais.csv ou performance_vendedores.csv não carregados. Página de Monetização não pode ser exibida.")
