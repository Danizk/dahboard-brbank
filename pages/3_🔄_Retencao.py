import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import format_currency, format_percentage, load_kpis, load_perda, convert_df_to_csv # Importa funções

# Inicializa o estado da sessão se não existir
if 'exec_mode' not in st.session_state:
    st.session_state['exec_mode'] = False

# --- Carregar Dados ---
df_kpis = load_kpis()
df_perda = load_perda()

# --- Conteúdo da Página ---
st.title("🔄 Retenção (Middle of Funnel)")
st.markdown("Análise da conversão de leads, tempo e motivos de perda.")
st.markdown("---")

if df_kpis is not None and df_perda is not None:
    st.subheader("Indicadores Chave de Retenção")
    col1, col2, col3, col4 = st.columns(4)
    try:
        # KPIs Gerais de Retenção
        col1.metric("Leads Cadastrados (CRM)", f"{int(df_kpis.loc['Leads Cadastrados no CRM', 'Valor']):,}" if pd.notna(df_kpis.loc['Leads Cadastrados no CRM', 'Valor']) else "N/A")
        col2.metric("Leads Convertidos", f"{int(df_kpis.loc['Leads Convertidos', 'Valor']):,}" if pd.notna(df_kpis.loc['Leads Convertidos', 'Valor']) else "N/A")
        col3.metric("Leads Perdidos", f"{int(df_kpis.loc['Leads Perdidos', 'Valor']):,}" if pd.notna(df_kpis.loc['Leads Perdidos', 'Valor']) else "N/A")
        col4.metric("Tx. Conv. Leads → Clientes", format_percentage(df_kpis.loc['Taxa de Conversão Leads → Clientes (%)', 'Valor']))

        col5, col6, col7 = st.columns(3) # Ajustado para 3 colunas
        col5.metric("Tempo Médio Conversão", f"{int(df_kpis.loc['Tempo Médio para Conversão (dias)', 'Valor'])} dias" if pd.notna(df_kpis.loc['Tempo Médio para Conversão (dias)', 'Valor']) else "N/A", help="Tempo médio entre cadastro no CRM e conversão.")
        col6.metric("Leads Ativos (Follow-up)", f"{int(df_kpis.loc['Leads Ativos para Follow-up', 'Valor']):,}" if pd.notna(df_kpis.loc['Leads Ativos para Follow-up', 'Valor']) else "N/A", help="Leads no CRM que ainda não converteram nem foram marcados como perdidos.")

        # --- Cálculo e Exibição do Potencial de Receita Leads Ativos ---
        try:
            leads_ativos = df_kpis.loc['Leads Ativos para Follow-up', 'Valor']
            tx_conv_hist = df_kpis.loc['Taxa de Conversão Leads → Clientes (%)', 'Valor'] / 100 # Converter % para decimal
            ticket_medio = df_kpis.loc['Ticket Médio (R$)', 'Valor']

            if pd.notna(leads_ativos) and pd.notna(tx_conv_hist) and pd.notna(ticket_medio):
                potencial_receita = leads_ativos * tx_conv_hist * ticket_medio
                col7.metric("Potencial Receita Leads Ativos", format_currency(potencial_receita), help="Estimativa: Leads Ativos * Tx. Conv. Histórica * Ticket Médio.")
            else:
                 col7.metric("Potencial Receita Leads Ativos", "N/A", help="Não foi possível calcular. Verifique os dados de origem.")
        except Exception as e_potencial:
            col7.metric("Potencial Receita Leads Ativos", "Erro", help=f"Erro no cálculo: {e_potencial}")

    except KeyError as e:
        st.warning(f"Métrica não encontrada para Indicadores de Retenção: {e}")
    except Exception as e:
        st.warning(f"Erro ao converter valor para Indicadores de Retenção: {e}")

    st.markdown("---")
    st.header("🚫 Motivos de Perda")

    # --- Alerta Visual Motivo Principal ---
    try:
        motivo_principal = "Não retornou contato"
        if motivo_principal in df_perda.index and 'Total' in df_perda.columns:
            total_perdas = df_perda['Total'].sum()
            perdas_motivo_principal = df_perda.loc[motivo_principal, 'Total']
            if pd.notna(total_perdas) and total_perdas > 0 and pd.notna(perdas_motivo_principal):
                percentual_motivo_principal = (perdas_motivo_principal / total_perdas)
                if percentual_motivo_principal > 0.7: # Limiar de 70%
                    st.warning(f"⚠️ Atenção: '{motivo_principal}' representa {percentual_motivo_principal:.1%} das perdas totais. Otimizar follow-up é crucial!")
    except Exception as e_alerta:
         st.error(f"Não foi possível gerar alerta de motivo de perda: {e_alerta}")


    col_perda1, col_perda2 = st.columns(2)

    with col_perda1:
        st.subheader("Volume Total por Motivo")
        try:
            df_perda_total = df_perda[['Total']].sort_values(by='Total', ascending=False).dropna()
            if not df_perda_total.empty:
                st.dataframe(df_perda_total.style.format('{:,.0f}'))

                # Botão de Download para Motivos de Perda Totais
                csv_perda_total = convert_df_to_csv(df_perda_total.reset_index())
                st.download_button(
                   label="Download Tabela de Perdas (Total)",
                   data=csv_perda_total,
                   file_name='motivos_perda_total.csv',
                   mime='text/csv',
                )

                # Gráfico de Pizza dos Motivos Totais (Ocultável no modo executivo)
                if not st.session_state.get('exec_mode', False):
                    fig_perda_pie = px.pie(df_perda_total, names=df_perda_total.index, values='Total',
                                          title='Distribuição Geral dos Motivos de Perda', hole=0.3)
                    fig_perda_pie.update_traces(textinfo='percent+label', textfont_size=14, marker=dict(line=dict(color='#000000', width=1)))
                    st.plotly_chart(fig_perda_pie, use_container_width=True)
            else:
                 st.info("Não há dados válidos para exibir a tabela/gráfico de perdas totais.")

        except Exception as e:
            st.warning(f"Erro ao exibir motivos de perda totais: {e}")

    with col_perda2:
        st.subheader("Comparativo por Vendedor")
        # (Ocultável no modo executivo)
        if not st.session_state.get('exec_mode', False):
            try:
                df_perda_comp = df_perda.drop(columns=['Total'], errors='ignore').reset_index() # Remove total e reseta indice
                df_perda_melted = df_perda_comp.melt(id_vars='Motivo', var_name='Vendedor', value_name='Quantidade').dropna(subset=['Quantidade'])

                if not df_perda_melted.empty:
                    fig_perda_vendedor = px.bar(df_perda_melted, x='Motivo', y='Quantidade', color='Vendedor',
                                                barmode='group', title='Motivos de Perda Detalhados por Vendedor',
                                                labels={'Quantidade':'Nº de Leads Perdidos'},
                                                category_orders={"Motivo": df_perda_total.index.tolist()}) # Usa a ordem do total
                    fig_perda_vendedor.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_perda_vendedor, use_container_width=True)
                else:
                    st.info("Não há dados válidos para exibir o comparativo por vendedor.")

            except Exception as e:
                st.warning(f"Erro ao exibir motivos de perda por vendedor: {e}")
        else:
            st.info("Gráfico comparativo por vendedor oculto no Modo Executivo.")

else:
    st.error("Arquivos kpis_gerais.csv ou motivos_perda.csv não carregados. Página de Retenção não pode ser exibida.")
