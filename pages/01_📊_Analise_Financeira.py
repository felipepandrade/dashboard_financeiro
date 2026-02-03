"""
01_📊_Analise_Financeira.py
============================
Módulo principal de análise financeira (Refatorado para UI Premium).
Foco: P&L e Razão de Gastos.
Estrutura: Executivo | Analítico | Estratégico
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils_financeiro import (
    gerar_analise_ia,
    get_ai_chat_response,
    plot_robust_forecast,
    MESES_ORDEM
)
from utils_ui import (
    setup_page,
    exibir_kpi_card,
    formatar_valor_brl,
    CORES,
    require_auth
)

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Análise Financeira", "📊")
require_auth(module='analise_financeira')

# =============================================================================
# VERIFICAR DADOS NA SESSÃO
# =============================================================================

pl_df = st.session_state.get('pl_df')
razao_df = st.session_state.get('razao_df')
api_key = st.session_state.get('api_key', '')
ai_provider = st.session_state.get('ai_provider', 'Gemini (Google)')

if pl_df is None:
    st.warning("⚠️ **Nenhum dado de P&L carregado.**")
    st.info("👈 Retorne à página inicial (Home) para fazer o upload dos arquivos.")
    # Exibe status do Razão se houver, mas bloqueia análise
    if razao_df is not None:
        st.info(f"ℹ️ Razão de Gastos carregado: {len(razao_df)} registros.")
    st.stop()

# =============================================================================
# PROCESSAMENTO INICIAL
# =============================================================================

# Separar custos e financeiro
df_custos = pl_df[pl_df['codigo_centro_gasto'] != 0].copy()
df_financeiro = pl_df[pl_df['codigo_centro_gasto'] == 0].copy()

# Calcular último mês realizado
ultimo_mes_realizado = None
if not df_custos.empty:
    dados_realizados = df_custos.query("tipo_valor == 'Realizado' and valor != 0")
    if not dados_realizados.empty:
        dados_realizados['mes_num'] = pd.Categorical(
            dados_realizados['mes'],
            categories=MESES_ORDEM,
            ordered=True
        ).codes
        ultimo_mes_realizado = dados_realizados.loc[dados_realizados['mes_num'].idxmax(), 'mes']

numero_meses_passados = MESES_ORDEM.index(ultimo_mes_realizado) + 1 if ultimo_mes_realizado else 0

# =============================================================================
# HEADER & FILTROS GLOBAIS
# =============================================================================

st.markdown('<div class="section-header"><span class="section-title">Análise de Performance (Overview)</span></div>', unsafe_allow_html=True)

with st.expander("🔍 Filtros Globais", expanded=False):
    col1_filter, col2_filter, col3_filter = st.columns(3)
    
    with col1_filter:
        lista_centros_custo = ['Visão Geral (Consolidado)'] + sorted(df_custos['centro_gasto_nome'].dropna().unique().tolist())
        centro_custo_selecionado = st.selectbox("Centro de Custo", lista_centros_custo)
    
    with col2_filter:
        lista_contas_contabeis = ['Visão Geral (Consolidado)'] + sorted(df_custos['conta_contabil'].unique().tolist())
        conta_contabil_selecionada = st.selectbox("Conta Contábil", lista_contas_contabeis)
    
    with col3_filter:
        opcoes_periodo = ['YTD (Acumulado do Ano)'] + MESES_ORDEM
        periodo_selecionado = st.selectbox("Período", opcoes_periodo)

# FILTRAGEM
df_custos_filtrado = df_custos.copy()
razao_filtrado = razao_df.copy() if razao_df is not None else pd.DataFrame()

# Filtro Centro de Custo
if centro_custo_selecionado != 'Visão Geral (Consolidado)':
    df_custos_filtrado = df_custos_filtrado[df_custos_filtrado['centro_gasto_nome'] == centro_custo_selecionado]
    if not razao_filtrado.empty and 'centro_gasto_nome' in razao_filtrado.columns:
        razao_filtrado = razao_filtrado[razao_filtrado['centro_gasto_nome'] == centro_custo_selecionado]

# Filtro Conta Contábil
if conta_contabil_selecionada != 'Visão Geral (Consolidado)':
    df_custos_filtrado = df_custos_filtrado[df_custos_filtrado['conta_contabil'] == conta_contabil_selecionada]

# Filtro Período
if periodo_selecionado == 'YTD (Acumulado do Ano)':
    meses_a_analisar = MESES_ORDEM[:numero_meses_passados]
    df_custos_filtrado = df_custos_filtrado[df_custos_filtrado['mes'].isin(meses_a_analisar)]
    if not razao_filtrado.empty and 'mes' in razao_filtrado.columns:
        razao_filtrado = razao_filtrado[razao_filtrado['mes'].isin(meses_a_analisar)]
else:
    df_custos_filtrado = df_custos_filtrado[df_custos_filtrado['mes'] == periodo_selecionado]
    if not razao_filtrado.empty and 'mes' in razao_filtrado.columns:
        razao_filtrado = razao_filtrado[razao_filtrado['mes'] == periodo_selecionado]

# =============================================================================
# ESTRUTURA DE ABAS PRINCIPAIS
# =============================================================================

tab_executivo, tab_analitico, tab_estrategico, tab_dre = st.tabs([
    "🏛️ Executivo", "🔍 Analítico", "🤖 Estratégico", "📋 DRE"
])

# =============================================================================
# ABA 1: EXECUTIVO (C-LEVEL)
# =============================================================================
with tab_executivo:
    st.markdown("### Visão Executiva")
    
    # 1. KPIs Principais
    total_realizado = df_custos_filtrado.query("tipo_valor == 'Realizado'")['valor'].sum()
    total_budget = df_custos_filtrado.query("tipo_valor == 'Budget V3'")['valor'].sum()
    variacao_abs = total_realizado - total_budget
    # Variação %: (Realizado - Budget) / |Budget| para manter sinal correto
    variacao_perc = (variacao_abs / abs(total_budget) * 100) if total_budget != 0 else 0
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1: exibir_kpi_card("Realizado", formatar_valor_brl(total_realizado), "Total Gasto")
    with col_kpi2: exibir_kpi_card("Budget V3", formatar_valor_brl(total_budget), "Meta Vigente")
    with col_kpi3:
        # Lógica de cor: Gasto maior que Budget (Var positiva em módulo de despesa negativa?)
        # P&L Despesas são Negativas. Realizado (-120) < Budget (-100). (Real - Budg) = -20.
        # Se for receita, Positivo.
        # Vamos assumir "Custo" como magnitude absoluta para facilitar o usuário executivo.
        
        abs_real = abs(total_realizado)
        abs_budg = abs(total_budget)
        diff_abs = abs_real - abs_budg
        perc_diff_abs = (diff_abs / abs_budg * 100) if abs_budg != 0 else 0
        
        cor_delta_kpi = "danger" if diff_abs > 0 else "success" # Gastou mais (danger) ou menos (success)
        exibir_kpi_card("Variação (Abs)", formatar_valor_brl(diff_abs), f"{perc_diff_abs:+.1f}%", cor_delta_kpi)
    
    with col_kpi4:
         # Gauge Chart - Consumo do Budget (Usando Absolutos)
        percentual_consumido = (abs(total_realizado) / abs(total_budget) * 100) if abs(total_budget) > 0 else 0
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = percentual_consumido,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "% do Budget"},
            number = {'suffix': "%"},
            gauge = {
                'axis': {'range': [None, max(120, percentual_consumido)], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': CORES['primary']},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 90], 'color': 'rgba(16, 185, 129, 0.3)'},
                    {'range': [90, 100], 'color': 'rgba(245, 158, 11, 0.3)'},
                    {'range': [100, max(120, percentual_consumido)], 'color': 'rgba(239, 68, 68, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            }
        ))
        fig_gauge.update_layout(height=140, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Gráfico de Tendência (Smoothed)
    st.subheader("Tendência de Gastos (YTD - Absoluto)")
    df_trend = df_custos.copy() 
    
    if centro_custo_selecionado != 'Visão Geral (Consolidado)':
        df_trend = df_trend[df_trend['centro_gasto_nome'] == centro_custo_selecionado]
        
    df_trend_group = df_trend.groupby(['mes', 'tipo_valor'])['valor'].sum().reset_index()
    # Filtrar apenas meses realizados e ordenados ou budget
    df_trend_group = df_trend_group[df_trend_group['tipo_valor'].isin(['Realizado', 'Budget V3'])]
    df_trend_group['mes'] = pd.Categorical(df_trend_group['mes'], categories=MESES_ORDEM, ordered=True)
    df_trend_group = df_trend_group.sort_values('mes')
    
    # Converter para absoluto para melhor visualização em gráfico de área
    df_trend_group['valor_abs'] = df_trend_group['valor'].abs()
    
    fig_trend = px.area(
        df_trend_group, x='mes', y='valor_abs', color='tipo_valor',
        line_shape='spline',
        title="Volume de Gastos (Absoluto)",
        labels={'valor_abs': 'Valor (R$ Absoluto)', 'mes': 'Mês'},
        color_discrete_map={'Realizado': CORES['primary'], 'Budget V3': CORES['warning']}
    )
    fig_trend.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_trend, use_container_width=True)

# =============================================================================
# ABA 2: ANALÍTICO (MANAGER)
# =============================================================================
with tab_analitico:
    sub_tabs_analise = st.tabs(["💰 Detalhamento", "🏢 Fornecedores", "🗺️ Visão Hierárquica"])
    
    with sub_tabs_analise[0]: # Detalhamento
        st.subheader("Detalhamento de Despesas")
        
        # Tabela 1: Resumo Mensal
        summary_pivot = df_custos_filtrado.pivot_table(
            values='valor', index='tipo_valor', columns='mes', aggfunc='sum', fill_value=0
        ).reindex(columns=MESES_ORDEM).dropna(axis=1, how='all').fillna(0)
        
        if not summary_pivot.empty:
            summary_pivot['Total'] = summary_pivot.sum(axis=1)
            st.dataframe(summary_pivot.style.format("R$ {:,.2f}"), use_container_width=True)
        else:
            st.info("Nenhum dado disponível.")
            
        st.markdown("#### Performance por Conta Contábil")
        tipos_disponiveis = df_custos_filtrado['tipo_valor'].unique().tolist()
        tipos_selecionados = st.multiselect("Tipos de Valor:", tipos_disponiveis, default=tipos_disponiveis)
        
        if tipos_selecionados:
            df_detalhada = df_custos_filtrado[df_custos_filtrado['tipo_valor'].isin(tipos_selecionados)].copy()
            df_detalhada['mes'] = pd.Categorical(df_detalhada['mes'], categories=MESES_ORDEM, ordered=True)
            df_pivot = df_detalhada.pivot_table(index=['conta_contabil', 'tipo_valor'], columns='mes', values='valor', aggfunc='sum').fillna(0)
            st.dataframe(df_pivot.style.format("R$ {:,.2f}"), use_container_width=True)

    with sub_tabs_analise[1]: # Fornecedores
        st.subheader("Análise por Fornecedor (Razão)")
        if not razao_filtrado.empty:
            # Trabalhando com absolutos para ranking de fornecedores (quem gastou mais)
            df_forn_calc = razao_filtrado.copy()
            df_forn_calc['valor_abs'] = df_forn_calc['valor'].abs()
            
            df_fornecedores = df_forn_calc.groupby('fornecedor')['valor_abs'].sum().reset_index()
            if not df_fornecedores.empty:
                top_fornecedores = df_fornecedores.nlargest(10, 'valor_abs')
                fig_fornec = px.bar(
                    top_fornecedores, x='valor_abs', y='fornecedor', orientation='h',
                    title="Top 10 Fornecedores (Volume de Gasto)", 
                    labels={'valor_abs': 'Valor Total (R$)', 'fornecedor': 'Fornecedor'},
                    text_auto='.2s', color='valor_abs', color_continuous_scale='Blues'
                )
                fig_fornec.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
                st.plotly_chart(fig_fornec, use_container_width=True)
                
                st.markdown("#### Detalhes dos Lançamentos")
                fornecedor_sel = st.selectbox("Filtrar Fornecedor:", ['Todos'] + sorted(razao_filtrado['fornecedor'].dropna().unique().tolist()))
                df_f = razao_filtrado if fornecedor_sel == 'Todos' else razao_filtrado[razao_filtrado['fornecedor'] == fornecedor_sel]
                cols_exibir = [c for c in ['data', 'mes', 'fornecedor', 'valor', 'historico', 'centro_gasto_nome'] if c in df_f.columns]
                st.dataframe(df_f[cols_exibir], use_container_width=True)
            else:
                st.info("Nenhum lançamento relevante.")
        else:
             st.warning("⚠️ Dados de Razão não disponíveis para este filtro.")
    
    with sub_tabs_analise[2]: # Visualizações (Treemap)
        st.subheader("Mapa de Custos (Treemap)")
        # Treemap com valores absolutos para visualização de área
        df_treemap = df_custos_filtrado.query("tipo_valor == 'Realizado'")
        if not df_treemap.empty:
            df_treemap['valor_abs'] = df_treemap['valor'].abs()
            df_treemap = df_treemap[df_treemap['valor_abs'] > 0] # Filtrar zeros
            
            fig_tm = px.treemap(
                df_treemap, path=[px.Constant("Total"), 'centro_gasto_nome', 'conta_contabil'],
                values='valor_abs', title='Hierarquia de Custos (Realizado Absoluto)', color='valor_abs', color_continuous_scale='RdYlGn_r'
            )
            fig_tm.update_layout(template="plotly_dark")
            st.plotly_chart(fig_tm, use_container_width=True)
        else:
            st.info("Sem dados para exibir Treemap.")

# =============================================================================
# ABA 3: ESTRATÉGICO (Forecast + IA)
# =============================================================================
with tab_estrategico:
    st.subheader("🤖 Inteligência & Previsões")
    
    col_ia1, col_ia2 = st.columns([1, 2])
    
    with col_ia1:
        st.markdown("#### Assistente Virtual")
        if api_key:
            st.success(f"Conectado: {ai_provider}")
            user_q = st.text_area("Pergunte à IA:", placeholder="Onde posso reduzir custos?", height=150)
            if st.button("Enviar Pergunta"):
                if user_q:
                    resumo = df_custos_filtrado.groupby(['tipo_valor', 'mes'])['valor'].sum().reset_index()
                    msgs = [{"role": "system", "content": "Analista financeiro sênior. Responda curto e direto."}, 
                            {"role": "user", "content": f"Dados:\n{resumo.to_string()}\n\nPergunta: {user_q}"}]
                    with st.spinner("Analisando..."):
                        resp = get_ai_chat_response(msgs, api_key, ai_provider)
                    st.markdown(f"**Resposta:**\n{resp}")
        else:
            st.warning("IA Desabilitada: Configure a Chave de API na Sidebar.")
            
    with col_ia2:
        st.markdown("#### Previsão de Tendência (Linear)")
        # Tenta usar a nova função robusta
        if not pl_df.empty and 'data' in pl_df.columns:
            try:
                # Filtrar para ter apenas realizado consolidado para previsão
                df_forecast = df_custos.query("tipo_valor == 'Realizado'").groupby('data')['valor'].sum().reset_index()
                
                # Usar plot_robust_forecast
                fig_forecast = plot_robust_forecast(df_forecast, 'data', 'valor', periods=3)
                
                if fig_forecast:
                     fig_forecast.update_layout(height=400, template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                     st.plotly_chart(fig_forecast, use_container_width=True)
                else:
                    st.info("Dados insuficientes para gerar projeção (necessário histórico mínimo).")
            except Exception as e:
                st.error(f"Não foi possível gerar previsão: {e}")

# =============================================================================
# ABA 4: DRE (Formatada)
# =============================================================================
with tab_dre:
    st.markdown("### Demonstrativo de Resultados (DRE)")
    if not df_financeiro.empty:
        ordem_dre = ["Gross Sales - Basic Services", "Gross Sales - Eventual Services", "Sales tax - Basic", "Sales tax - Eventual", "Net Revenue", "Cost of Sales", "Gross profit", "Gross margin (%)"]
        df_financeiro['conta_contabil'] = pd.Categorical(df_financeiro['conta_contabil'], categories=ordem_dre, ordered=True)
        pivot_dre = df_financeiro.query("tipo_valor == 'Realizado'").pivot_table(values='valor', index='conta_contabil', columns='mes', aggfunc='sum').reindex(columns=MESES_ORDEM).fillna(0)
        
        # Formatação Condicional
        def formatar_dre(val, row_name):
            if "%" in row_name:
                return f"{val*100:.1f}%"
            return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        # Aplicar formatação pandas Styler linha a linha é complexo, 
        # vamos formatar o dataframe como string para exibição
        df_display = pivot_dre.copy()
        for idx in df_display.index:
            for col in df_display.columns:
                val = df_display.loc[idx, col]
                df_display.loc[idx, col] = formatar_dre(val, idx)
                
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Dados de DRE indisponíveis neste arquivo ou filtro.")

# =============================================================================
# RODAPÉ
# =============================================================================

st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {CORES['text_secondary']}; font-size: 12px;">
    Análise Financeira Avançada v2.1 • Baseal 2026
</div>
""", unsafe_allow_html=True)
