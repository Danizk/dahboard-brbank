import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# Importa funções de utils.py (certifique-se que utils.py está na raiz)
from utils import format_currency, format_percentage, load_kpis

# --- Configuração da Página ---
st.set_page_config(
    page_title="BR Bank - Visão Geral",
    page_icon="🏠",
    layout="wide"
)

# --- Barra Lateral (com Toggle Modo Executivo) ---
st.sidebar.header("Configurações de Exibição")
if 'exec_mode' not in st.session_state:
    st.session_state['exec_mode'] = False
st.session_state['exec_mode'] = st.sidebar.toggle(
    "Modo Executivo Simplificado",
    value=st.session_state.get('exec_mode', False),
    help="Oculta detalhes e gráficos secundários nas outras páginas para uma visão de alto nível."
)
st.sidebar.markdown("---")

# --- Carregar Dados ---
df_kpis = load_kpis()

# --- Constantes ---
META_FATURAMENTO_ANUAL = 30000000
MESES_PERIODO_ATUAL = 6 # Set/22 a Fev/23

# --- Conteúdo da Página ---
st.title("🏠 Resumo Executivo | BR Bank")
st.markdown(f"Visão Geral dos Indicadores Chave (Período: Set/22 a Fev/23)")
st.markdown("---")

if df_kpis is not None:
    try:
        # --- Extração e Validação de Valores Chave ---
        receita_total_valor = df_kpis.loc['Receita Total (R$)', 'Valor'] if 'Receita Total (R$)' in df_kpis.index else None
        lucro_liquido_valor = df_kpis.loc['Lucro Líquido (R$)', 'Valor'] if 'Lucro Líquido (R$)' in df_kpis.index else None
        margem_liquida_valor = df_kpis.loc['Margem Líquida (%)', 'Valor'] if 'Margem Líquida (%))' in df_kpis.index else None
        roas_valor = df_kpis.loc['ROAS (%)', 'Valor'] if 'ROAS (%)' in df_kpis.index else None
        leads_convertidos_valor = df_kpis.loc['Leads Convertidos', 'Valor'] if 'Leads Convertidos' in df_kpis.index else None
        ticket_medio_valor = df_kpis.loc['Ticket Médio (R$)', 'Valor'] if 'Ticket Médio (R$)' in df_kpis.index else None
        ltv_valor = df_kpis.loc['LTV (R$)', 'Valor'] if 'LTV (R$)' in df_kpis.index else None
        cac_valor = df_kpis.loc['CPA - Custo por Aquisição (R$)', 'Valor'] if 'CPA - Custo por Aquisição (R$)' in df_kpis.index else None

        # --- Seção: Crescimento e Metas ---
        st.subheader("📈 Crescimento e Metas")
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)

        col_g1.metric("Receita Total (Período)",
                      format_currency(receita_total_valor),
                      help="Receita total acumulada nos 6 meses (Set/22-Fev/23). Como estamos em relação à meta?")

        if pd.notna(receita_total_valor):
            gap_meta = META_FATURAMENTO_ANUAL - receita_total_valor
            projecao_anual = (receita_total_valor / MESES_PERIODO_ATUAL) * 12 if MESES_PERIODO_ATUAL > 0 else 0
            col_g2.metric("Gap para Meta Anual",
                          format_currency(gap_meta),
                          help=f"Quanto falta para atingir a meta anual de {format_currency(META_FATURAMENTO_ANUAL)}?")
            col_g3.metric("Projeção Anual (Linear)",
                          format_currency(projecao_anual),
                          help=f"Estimativa de receita anual baseada na média dos últimos {MESES_PERIODO_ATUAL} meses. Estamos no ritmo?")
        else:
            col_g2.metric("Gap para Meta Anual", "N/A", help="Necessário valor da Receita Total.")
            col_g3.metric("Projeção Anual (Linear)", "N/A", help="Necessário valor da Receita Total.")

        col_g4.metric("Leads Convertidos",
                      f"{int(leads_convertidos_valor):,}" if pd.notna(leads_convertidos_valor) else "N/A",
                      help="Volume total de clientes que contrataram empréstimos no período. É suficiente para a meta?")

        # --- Gráfico Velocímetro ---
        if pd.notna(receita_total_valor):
            st.markdown("##### Progresso da Receita vs Meta Anual")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = receita_total_valor,
                number = {'prefix': "R$", 'valueformat': ',.0f'},
                domain = {'x': [0, 1], 'y': [0, 1]},
                # title = {'text': "Receita Acumulada (Set/22-Fev/23)", 'font': {'size': 16}}, # Título opcional
                gauge = {
                    'axis': {'range': [0, META_FATURAMENTO_ANUAL], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "#4682B4"}, # SteelBlue - Tom azul médio
                    'bgcolor': "white",
                    'borderwidth': 1,
                    'bordercolor': "gray",
                    'steps': [ # Escala de Azul Pastel (claro -> escuro) com transparência
                        {'range': [0, META_FATURAMENTO_ANUAL * 0.5], 'color': 'rgba(173, 216, 230, 0.5)'}, # LightBlue 50%
                        {'range': [META_FATURAMENTO_ANUAL * 0.5, META_FATURAMENTO_ANUAL * 0.8], 'color': 'rgba(135, 206, 250, 0.6)'}, # LightSkyBlue 60%
                        {'range': [META_FATURAMENTO_ANUAL * 0.8, META_FATURAMENTO_ANUAL], 'color': 'rgba(70, 130, 180, 0.7)'} # SteelBlue 70%
                        ],
                    'threshold': {
                        'line': {'color': "orange", 'width': 4}, # Linha laranja para projeção
                        'thickness': 0.75,
                        'value': projecao_anual if pd.notna(projecao_anual) else 0
                        }
                    }
                ))
            fig_gauge.update_layout(height=250, margin=dict(t=10, b=10, l=30, r=30)) # Ajuste de margem e altura
            st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.info("Gráfico de progresso não disponível (Receita Total ausente).")

        st.markdown("---")
        # --- Seção: Lucratividade e Eficiência ---
        st.subheader("💰 Lucratividade e Eficiência")
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)

        col_e1.metric("Lucro Líquido (Período)",
                      format_currency(lucro_liquido_valor),
                      help="O crescimento da receita está sendo lucrativo? (Receita Total - Custo de Tráfego Pago)")
        col_e2.metric("Margem Líquida (%)",
                      format_percentage(margem_liquida_valor),
                      help="Qual a % de lucro sobre a receita? (Lucro Líquido / Receita Total)")
        col_e3.metric("ROAS (%)",
                      format_percentage(roas_valor),
                      help="Qual o retorno sobre o investimento em Ads? Está valendo a pena?")
        col_e4.metric("CAC (proxy Custo Ads)",
                      format_currency(cac_valor),
                      help="Quanto custa adquirir um lead pelos anúncios? (Custo Ads / Leads Captados Ads)")

        # --- Cálculo e Exibição LTV/CAC Ratio ---
        st.markdown("##### Eficiência de Aquisição vs Valor do Cliente")
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("LTV (proxy)",
                     format_currency(ltv_valor),
                     help="Qual o valor médio gerado por cliente? (Receita Total / Leads Convertidos)")
        col_r2.metric("CAC (proxy Custo Ads)",
                      format_currency(cac_valor),
                      help="Custo médio para adquirir um lead via Ads.")

        ltv_cac_ratio = None
        if pd.notna(ltv_valor) and pd.notna(cac_valor) and cac_valor > 0:
            ltv_cac_ratio = ltv_valor / cac_valor
            col_r3.metric("LTV / CAC Ratio",
                          f"{ltv_cac_ratio:.1f}x",
                          help="Relação LTV/CAC. Um valor > 3x geralmente indica aquisição saudável e escalável.")
            # Adicionar um pequeno comentário interpretativo (opcional)
            if ltv_cac_ratio < 3:
                 st.caption(f"⚠️ A relação LTV/CAC de {ltv_cac_ratio:.1f}x sugere atenção à eficiência dos custos de aquisição ou necessidade de aumentar o LTV.")
            else:
                 st.caption(f"✅ A relação LTV/CAC de {ltv_cac_ratio:.1f}x indica uma aquisição saudável.")

        else:
            col_r3.metric("LTV / CAC Ratio", "N/A", help="Não foi possível calcular (LTV ou CAC ausente/inválido).")


    except KeyError as e:
        st.error(f"Erro: Métrica essencial não encontrada para o Resumo Executivo: {e}. Verifique kpis_gerais.csv.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar os dados do Resumo Executivo: {e}")

else:
    st.error("Arquivo kpis_gerais.csv não carregado. KPIs não podem ser exibidos.")

# --- Rodapé ---
st.caption(f"Última atualização do código: {pd.to_datetime('today').strftime('%d/%m/%Y %H:%M')}")
