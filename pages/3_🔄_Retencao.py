import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import format_currency, format_percentage, load_kpis, load_perda, convert_df_to_csv

# Paleta azul pastel para vendedores
azul_pastel_palette = ['#E1F5FE', '#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6']
seller_color_map = {'A': azul_pastel_palette[0], 'B': azul_pastel_palette[1], 'C': azul_pastel_palette[2], 'D': azul_pastel_palette[3], 'E': azul_pastel_palette[4]}
pie_color_sequence = px.colors.sequential.Blues_r

# Inicializa estado da sessão
if 'exec_mode' not in st.session_state:
    st.session_state['exec_mode'] = False

# --- Carregar Dados ---
df_kpis = load_kpis()
df_perda = load_perda()

# --- Página ---
st.title("🔄 Retenção (Middle of Funnel)")
st.markdown("Análise da conversão de leads, tempo e motivos de perda.")
st.markdown("---")

if df_kpis is not None and df_perda is not None:
    st.subheader("Indicadores Chave de Retenção")
    col1, col2, col3, col4 = st.columns(4)
    try:
        col1.metric("Leads Cadastrados (CRM)", f"{int(df_kpis.loc[df_kpis['Métrica'] == 'Leads Cadastrados no CRM', 'Valor'].values[0]):,}")
        col2.metric("Leads Convertidos", f"{int(df_kpis.loc[df_kpis['Métrica'] == 'Leads Convertidos', 'Valor'].values[0]):,}")
        col3.metric("Leads Perdidos", f"{int(df_kpis.loc[df_kpis['Métrica'] == 'Leads Perdidos', 'Valor'].values[0]):,}")
        col4.metric("Tx. Conv. Leads → Clientes", f"{df_kpis.loc[df_kpis['Métrica'] == 'Taxa de Conversão Leads → Clientes', 'Valor'].values[0]:.2f}%", help="Leads Convertidos / Leads Cadastrados")

        col5, col6, col7 = st.columns(3)
        col5.metric("Tempo Médio Conversão", f"{int(df_kpis.loc[df_kpis['Métrica'] == 'Tempo Médio para Conversão', 'Valor'].values[0])} dias")
        col6.metric("Leads Ativos (Follow-up)", f"{int(df_kpis.loc[df_kpis['Métrica'] == 'Leads Ativos para Follow-up', 'Valor'].values[0]):,}")

        # Potencial de Receita
        leads_ativos = df_kpis.loc[df_kpis['Métrica'] == 'Leads Ativos para Follow-up', 'Valor'].values[0]
        tx_conv_hist_pct = df_kpis.loc[df_kpis['Métrica'] == 'Taxa de Conversão Leads → Clientes', 'Valor'].values[0]
        ticket_medio = df_kpis.loc[df_kpis['Métrica'] == 'Ticket Médio por Cliente', 'Valor'].values[0]

        if all(pd.notna([leads_ativos, tx_conv_hist_pct, ticket_medio])):
            potencial_receita = leads_ativos * (tx_conv_hist_pct / 100.0) * ticket_medio
            col7.metric("Potencial Receita Leads Ativos", format_currency(potencial_receita), help="Leads Ativos * Tx. Conversão Histórica * Ticket Médio")
        else:
            col7.metric("Potencial Receita Leads Ativos", "N/A")

    except Exception as e:
        st.warning(f"Erro ao carregar indicadores: {e}")

    st.markdown("---")
    st.header("🚫 Motivos de Perda")

    # Alerta motivo principal
    try:
        motivo_principal = "Não retornou contato"
        if motivo_principal in df_perda.index and 'Total' in df_perda.columns:
            total_perdas = df_perda['Total'].sum()
            qtd_principal = df_perda.loc[motivo_principal, 'Total']
            percentual = qtd_principal / total_perdas if total_perdas > 0 else 0

            if percentual > 0.7:
                st.warning(f"⚠️ '{motivo_principal}' representa {percentual:.1%} das perdas. Otimize follow-up!")

    except Exception as e:
        st.error(f"Erro no alerta de motivo principal: {e}")

    if not st.session_state.get('exec_mode', False):
        col_perda1, col_perda2 = st.columns(2)

        # Total por motivo
        with col_perda1:
            st.subheader("Volume Total por Motivo")
            try:
                df_total = df_perda[['Total']].dropna().sort_values(by='Total', ascending=False)
                st.dataframe(df_total.astype(int))

                df_download = df_total.reset_index().rename(columns={"index": "Motivo"})
                csv = convert_df_to_csv(df_download)
                st.download_button("📥 Baixar CSV", data=csv, file_name="motivos_perda_total.csv", mime="text/csv")

                fig = px.pie(df_download, names='Motivo', values='Total', hole=0.3, color_discrete_sequence=pie_color_sequence)
                fig.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.warning(f"Erro ao exibir motivos de perda: {e}")

        # Comparativo por vendedor
        with col_perda2:
            st.subheader("Comparativo por Vendedor")
            try:
                df_vend = df_perda.drop(columns='Total', errors='ignore').reset_index().rename(columns={"index": "Motivo"})
                df_melt = df_vend.melt(id_vars='Motivo', var_name='Vendedor', value_name='Quantidade').dropna()
                df_melt['Quantidade'] = df_melt['Quantidade'].astype(int)

                fig = px.bar(df_melt, x='Motivo', y='Quantidade', color='Vendedor', barmode='group',
                             color_discrete_map=seller_color_map,
                             title='Motivos de Perda por Vendedor',
                             labels={'Quantidade': 'Leads Perdidos'})
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Erro ao exibir comparativo por vendedor: {e}")
    else:
        st.info("Modo executivo ativado. Detalhes ocultos.")
else:
    st.error("❌ Arquivo kpis_gerais.csv ou motivos_perda.csv não carregado.")
