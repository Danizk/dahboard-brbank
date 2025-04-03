import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import format_currency, format_percentage, load_kpis, load_performance, convert_df_to_csv # Importa funções

# Inicializa o estado da sessão se não existir
if 'exec_mode' not in st.session_state:
    st.session_state['exec_mode'] = False

# --- Carregar Dados Essenciais ---
df_kpis = load_kpis()
df_performance = load_performance()

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

    try:
        # --- Calcular e Adicionar Receita por Dia de Conversão ---
        if 'Receita Total (R$)' in df_performance.columns and 'Tempo Conversão (dias)' in df_performance.columns:
            # Evitar divisão por zero ou por NaN/infinito
            df_performance['Receita por Dia Conv (R$)'] = df_performance.apply(
                lambda row: row['Receita Total (R$)'] / row['Tempo Conversão (dias)']
                if pd.notna(row['Tempo Conversão (dias)']) and row['Tempo Conversão (dias)'] > 0 and pd.notna(row['Receita Total (R$)'])
                else pd.NA,
                axis=1
            )
            # Calcular média geral (ignorando NAs)
            media_receita_dia = df_performance['Receita por Dia Conv (R$)'].mean()
            st.metric("Receita Média por Dia de Conversão (Geral)", format_currency(media_receita_dia), help="Média de (Receita Total Vendedor / Tempo Médio Conversão Vendedor). Indica eficiência na geração de receita ao longo do tempo.")
        else:
            st.warning("Colunas 'Receita Total (R$)' ou 'Tempo Conversão (dias)' não encontradas para calcular Receita por Dia.")

        # --- Tabela de Performance ---
        st.subheader("Tabela Detalhada de Performance")
        # Seleciona e formata colunas para exibição
        df_display = df_performance.set_index('Vendedor').copy()
        cols_to_format_currency = ['Ticket Médio (R$)', 'Receita Total (R$)', 'Receita por Lead (R$)', 'Receita por Dia Conv (R$)']
        for col in cols_to_format_currency:
            if col in df_display.columns:
                 df_display[col] = df_display[col].map(format_currency)
        if 'Taxa Conversão (%)' in df_display.columns:
              df_display['Taxa Conversão (%)'] = df_display['Taxa Conversão (%)'].map(format_percentage)
        if 'Tempo Conversão (dias)' in df_display.columns:
            df_display['Tempo Conversão (dias)'] = df_display['Tempo Conversão (dias)'].map('{:.0f} dias'.format, na_action='ignore')

        st.dataframe(df_display) # Mostra a tabela formatada

        # Botão de Download
        csv_performance = convert_df_to_csv(df_performance) # Usa o DF original com números
        st.download_button(
           label="Download Tabela de Performance",
           data=csv_performance,
           file_name='performance_vendedores.csv',
           mime='text/csv',
        )
        st.markdown("---")

        # --- Gráficos de Performance (Ocultáveis no modo executivo) ---
        if not st.session_state.get('exec_mode', False):
            st.subheader("Análise Gráfica Individual")
            col_vend1, col_vend2 = st.columns(2)
            with col_vend1:
                fig_rev_vendedor = px.bar(df_performance, x='Vendedor', y='Receita Total (R$)', color='Vendedor', title='Receita Total Gerada', text_auto='.2s', labels={'Receita Total (R$)':'Receita (R$)'})
                fig_rev_vendedor.update_traces(textposition='outside')
                fig_rev_vendedor.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig_rev_vendedor, use_container_width=True)

                fig_leads_conv_vendedor = px.bar(df_performance, x='Vendedor', y='Leads Convertidos', color='Vendedor', title='Leads Convertidos', text_auto=True)
                fig_leads_conv_vendedor.update_traces(textposition='outside')
                fig_leads_conv_vendedor.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig_leads_conv_vendedor, use_container_width=True)

            with col_vend2:
                fig_tx_vendedor = px.bar(df_performance, x='Vendedor', y='Taxa Conversão (%)', color='Vendedor', title='Taxa de Conversão', text_auto='.1f', range_y=[0, df_performance['Taxa Conversão (%)'].max() * 1.15] if pd.notna(df_performance['Taxa Conversão (%)'].max()) else None)
                fig_tx_vendedor.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig_tx_vendedor.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig_tx_vendedor, use_container_width=True)

                fig_tempo_vendedor = px.bar(df_performance, x='Vendedor', y='Tempo Conversão (dias)', color='Vendedor', title='Tempo Médio de Conversão', text_auto='.0f')
                fig_tempo_vendedor.update_traces(texttemplate='%{text:.0f}d', textposition='outside')
                fig_tempo_vendedor.update_layout(showlegend=False, height=350)
                st.plotly_chart(fig_tempo_vendedor, use_container_width=True)
        else:
             st.info("Gráficos individuais ocultos no Modo Executivo.")

        st.markdown("---")
        # --- Ranking de Performance (Melhorado) ---
        st.subheader("📊 Ranking de Performance da Equipe")

        # Encontra o melhor e o pior para cada métrica (tratando NaNs)
        idx_max_tx_conv = df_performance['Taxa Conversão (%)'].idxmax() if pd.notna(df_performance['Taxa Conversão (%)'].max()) else None
        idx_min_tx_conv = df_performance['Taxa Conversão (%)'].idxmin() if pd.notna(df_performance['Taxa Conversão (%)'].min()) else None

        idx_max_receita = df_performance['Receita Total (R$)'].idxmax() if pd.notna(df_performance['Receita Total (R$)'].max()) else None
        idx_min_receita = df_performance['Receita Total (R$)'].idxmin() if pd.notna(df_performance['Receita Total (R$)'].min()) else None

        idx_max_ticket = df_performance['Ticket Médio (R$)'].idxmax() if pd.notna(df_performance['Ticket Médio (R$)'].max()) else None
        idx_min_ticket = df_performance['Ticket Médio (R$)'].idxmin() if pd.notna(df_performance['Ticket Médio (R$)'].min()) else None

        idx_min_tempo = df_performance['Tempo Conversão (dias)'].idxmin() if pd.notna(df_performance['Tempo Conversão (dias)'].min()) else None
        idx_max_tempo = df_performance['Tempo Conversão (dias)'].idxmax() if pd.notna(df_performance['Tempo Conversão (dias)'].max()) else None

        # Função auxiliar para exibir o ranking
        def display_rank(col, metric_name, best_idx, worst_idx, higher_is_better=True, format_func=None):
            if best_idx is not None:
                 best_val = df_performance.loc[best_idx, metric_name]
                 best_vend = df_performance.loc[best_idx, 'Vendedor']
                 best_text = format_func(best_val) if format_func else best_val
                 col.markdown(f"🏆 **Melhor {metric_name}:** {best_vend} ({best_text})")
            if worst_idx is not None:
                 worst_val = df_performance.loc[worst_idx, metric_name]
                 worst_vend = df_performance.loc[worst_idx, 'Vendedor']
                 worst_text = format_func(worst_val) if format_func else worst_val
                 col.markdown(f"⚠️ **Pior {metric_name}:** {worst_vend} ({worst_text})")

        ranking_col1, ranking_col2 = st.columns(2)
        with ranking_col1:
            st.markdown("**📈 Performance Positiva**")
            display_rank(ranking_col1, 'Taxa Conversão (%)', idx_max_tx_conv, idx_min_tx_conv, True, format_percentage)
            display_rank(ranking_col1, 'Receita Total (R$)', idx_max_receita, idx_min_receita, True, format_currency)
            display_rank(ranking_col1, 'Ticket Médio (R$)', idx_max_ticket, idx_min_ticket, True, format_currency)
            display_rank(ranking_col1, 'Tempo Conversão (dias)', idx_min_tempo, idx_max_tempo, False, lambda x: f"{x:.0f} dias") # Menor é melhor

        with ranking_col2:
            st.markdown("**📉 Pontos de Atenção**")
            # A função display_rank já mostra o pior, podemos adicionar outras métricas aqui se quiser
            st.markdown(f"*(O pior desempenho para cada métrica está listado à esquerda)*")
            # Exemplo: Adicionar Leads Recebidos
            # idx_max_leads = df_performance['Leads Recebidos'].idxmax() if pd.notna(df_performance['Leads Recebidos'].max()) else None
            # idx_min_leads = df_performance['Leads Recebidos'].idxmin() if pd.notna(df_performance['Leads Recebidos'].min()) else None
            # display_rank(ranking_col2, 'Leads Recebidos', idx_max_leads, idx_min_leads, True, lambda x: f"{x:,.0f}")


    except Exception as e:
        st.error(f"Ocorreu um erro ao exibir performance dos vendedores: {e}")
else:
    st.error("Arquivos kpis_gerais.csv ou performance_vendedores.csv não carregados. Página de Monetização não pode ser exibida.")
