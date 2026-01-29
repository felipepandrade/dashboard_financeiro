"""
01_📊_Analise_Financeira.py
============================
Módulo principal de análise financeira (Refatorado para UI Premium).
"""

import pandas as pd
import streamlit as st
import plotly.express as px

from utils_financeiro import (
    gerar_estatisticas_orcamento,
    exportar_orcamento_csv,
    ValidadorDados,
    gerar_analise_ia,
    get_ai_chat_response,
    plot_heatmap_desvios,
    plot_stl_decomposition,
    MESES_ORDEM,
    criar_interface_forecasting_simples
)
from utils_ui import (
    setup_page,
    exibir_kpi_card,
    formatar_valor_brl,
    CORES
)

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Análise Financeira", "📊")

# =============================================================================
# VERIFICAR DADOS NA SESSÃO
# =============================================================================

pl_df = st.session_state.get('pl_df')
razao_df = st.session_state.get('razao_df')
df_orc_proc = st.session_state.get('df_orc_proc')
api_key = st.session_state.get('api_key', '')
ai_provider = st.session_state.get('ai_provider', 'Gemini (Google)')

if pl_df is None and df_orc_proc is None:
    st.warning("⚠️ **Nenhum dado carregado.**")
    st.info("👈 Retorne à página inicial (Home) para fazer o upload dos arquivos.")
    st.stop()

# Status rápido com Cards Premium
col_st1, col_st2, col_st3 = st.columns(3)
with col_st1:
    exibir_kpi_card(
        "Dados P&L", 
        f"{len(pl_df):,} linhas" if pl_df is not None else "N/A", 
        "Registros Contábeis"
    )
with col_st2:
    exibir_kpi_card(
        "Dados Razão", 
        f"{len(razao_df):,} linhas" if razao_df is not None else "N/A", 
        "Detalhe por Fornecedor"
    )
with col_st3:
    exibir_kpi_card(
        "Dados Orçamento", 
        f"{len(df_orc_proc):,} linhas" if df_orc_proc is not None else "N/A", 
        "Base Orçamentária"
    )

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# ABAS PRINCIPAIS
# =============================================================================

tabs = st.tabs([
    "📈 Análise Financeira (P&L)",
    "💼 Acompanhamento Orçamentário",
    "✓ Qualidade de Dados",
    "📊 Previsão Financeira"
])

# -----------------------------------------------------------------------------
# ABA 1: Análise Financeira (P&L)
# -----------------------------------------------------------------------------

with tabs[0]:
    st.markdown('<div class="section-header"><span class="section-title">Análise de Performance (P&L)</span></div>', unsafe_allow_html=True)
    
    if pl_df is not None and not pl_df.empty:
        
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
        
        if ultimo_mes_realizado:
            st.info(f"📅 **Último mês realizado:** {ultimo_mes_realizado} ({numero_meses_passados} meses acumulados)")
        
        # FILTROS
        with st.container():
            st.markdown("#### 🔍 Filtros de Análise")
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
        
        st.divider()
        
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
        
        # SUB-ABAS
        tab_custos, tab_dre = st.tabs(["💰 Análise de Custos", "📋 DRE"])
        
        with tab_custos:
            sub_tabs = st.tabs([
                "📊 Dashboard", "💵 Despesas Detalhadas", "🏢 Fornecedores",
                "📈 Visualizações", "🔍 Análise com IA"
            ])
            
            with sub_tabs[0]:  # Dashboard
                st.markdown(f"### {centro_custo_selecionado}")
                st.caption(f"Conta: {conta_contabil_selecionada} | Período: {periodo_selecionado}")
                
                total_realizado = df_custos_filtrado.query("tipo_valor == 'Realizado'")['valor'].sum()
                total_budget = df_custos_filtrado.query("tipo_valor == 'Budget V3'")['valor'].sum()
                total_budget_v1 = df_custos_filtrado.query("tipo_valor == 'Budget V1'")['valor'].sum()
                variacao = ((total_realizado - total_budget) / total_budget * 100) if total_budget != 0 else 0
                
                # KPIs com visual premium
                col1, col2, col3, col4 = st.columns(4)
                with col1: exibir_kpi_card("Realizado", formatar_valor_brl(total_realizado), "Total Gasto")
                with col2: exibir_kpi_card("Budget V3", formatar_valor_brl(total_budget), "Meta Vigente")
                with col3: exibir_kpi_card("Budget V1", formatar_valor_brl(total_budget_v1), "Meta Inicial")
                
                # Card de variação com cor condicional
                cor_var = CORES['success'] if variacao <= 0 else CORES['danger']
                delta_sym = "▼" if variacao <= 0 else "▲"
                with col4: 
                    st.markdown(f"""
<div style="background-color: {CORES['card_bg']}; padding: 20px; border-radius: 12px; border: 1px solid {CORES['border']};">
    <div style="color: {CORES['text_secondary']}; font-size: 14px;">Variação V3</div>
    <div style="font-size: 24px; font-weight: bold; color: {cor_var};">{delta_sym} {abs(variacao):.2f}%</div>
    <div style="color: {CORES['text_secondary']}; font-size: 12px;">vs Meta</div>
</div>
""", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Gráficos
                if periodo_selecionado == 'YTD (Acumulado do Ano)':
                    df_grafico = df_custos_filtrado.groupby(['mes', 'tipo_valor'])['valor'].sum().reset_index()
                    df_grafico['mes'] = pd.Categorical(df_grafico['mes'], categories=MESES_ORDEM, ordered=True)
                    df_grafico = df_grafico.sort_values('mes')
                    fig = px.line(
                        df_grafico, x='mes', y='valor', color='tipo_valor',
                        markers=True,
                        title=f"Evolução Mensal",
                        labels={'valor': 'Valor (R$)', 'mes': 'Mês', 'tipo_valor': 'Versão'},
                        color_discrete_map={
                            'Realizado': CORES['primary'],
                            'Budget V1': CORES['warning'],
                            'Budget V3': CORES['success'],
                            'LY - Actual': CORES['danger']
                        }
                    )
                else:
                    df_grafico = df_custos_filtrado.groupby('tipo_valor')['valor'].sum().reset_index()
                    fig = px.bar(
                        df_grafico, x='tipo_valor', y='valor', color='tipo_valor',
                        title=f"Comparativo no Mês de {periodo_selecionado}",
                        labels={'valor': 'Valor (R$)', 'tipo_valor': 'Versão'},
                        text_auto='.2s',
                        color_discrete_map={
                            'Realizado': CORES['primary'],
                            'Budget V1': CORES['warning'],
                            'Budget V3': CORES['success'],
                            'LY - Actual': CORES['danger']
                        }
                    )
                
                fig.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            
            with sub_tabs[1]:  # Despesas Detalhadas
                st.subheader("💵 Detalhamento de Despesas")
                summary_pivot = df_custos_filtrado.pivot_table(
                    values='valor',
                    index='tipo_valor',
                    columns='mes',
                    aggfunc='sum',
                    fill_value=0
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
            
            with sub_tabs[2]:  # Fornecedores
                st.subheader("🏢 Análise por Fornecedor")
                if not razao_filtrado.empty:
                    top_fornecedores = razao_filtrado.groupby('fornecedor')['valor'].sum().nlargest(10).reset_index()
                    fig_fornec = px.bar(
                        top_fornecedores, x='valor', y='fornecedor', orientation='h',
                        title="Top 10 Fornecedores", labels={'valor': 'Valor (R$)', 'fornecedor': 'Fornecedor'},
                        text_auto='.2s', color='valor', color_continuous_scale='Blues'
                    )
                    fig_fornec.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
                    st.plotly_chart(fig_fornec, use_container_width=True)
                    
                    st.markdown("#### Detalhes dos Lançamentos")
                    fornecedor_sel = st.selectbox("Filtrar Fornecedor:", ['Todos'] + sorted(razao_filtrado['fornecedor'].dropna().unique().tolist()))
                    df_f = razao_filtrado if fornecedor_sel == 'Todos' else razao_filtrado[razao_filtrado['fornecedor'] == fornecedor_sel]
                    st.dataframe(df_f, use_container_width=True)
                else:
                    st.info("Dados de Razão não disponíveis.")
            
            with sub_tabs[3]:  # Visualizações
                st.subheader("📈 Visualizações Avançadas")
                df_treemap = df_custos_filtrado.query("tipo_valor == 'Realizado' and valor > 0")
                if not df_treemap.empty:
                    fig_tm = px.treemap(
                        df_treemap, path=[px.Constant("Total"), 'centro_gasto_nome', 'conta_contabil'],
                        values='valor', title='Hierarquia de Custos (Realizado)', color='valor', color_continuous_scale='RdYlGn_r'
                    )
                    fig_tm.update_layout(template="plotly_dark")
                    st.plotly_chart(fig_tm, use_container_width=True)
                
                if not pl_df.empty and 'data' in pl_df.columns:
                    try:
                        fig_stl = plot_stl_decomposition(pl_df, 'data', 'valor')
                        fig_stl.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_stl, use_container_width=True)
                    except: pass
            
            with sub_tabs[4]:  # IA
                st.subheader("🤖 Assistente de Análise Financeira")
                
                if api_key:
                    st.success(f"Conectado: {ai_provider}")
                    user_q = st.text_area("Pergunte à IA sobre os dados:", placeholder="Ex: Onde posso reduzir custos?")
                    if st.button("Enviar Pergunta"):
                        if user_q:
                            resumo = df_custos_filtrado.groupby(['tipo_valor', 'mes'])['valor'].sum().reset_index()
                            msgs = [{"role": "system", "content": "Analista financeiro sênior."}, {"role": "user", "content": f"Dados:\n{resumo.to_string()}\n\nPergunta: {user_q}"}]
                            resp = get_ai_chat_response(msgs, api_key, ai_provider)
                            st.markdown(resp)
                else:
                    st.warning("Configure a API Key na Home para usar IA.")

        with tab_dre:
            st.markdown("### Demonstrativo de Resultados (DRE)")
            if not df_financeiro.empty:
                ordem_dre = ["Gross Sales - Basic Services", "Gross Sales - Eventual Services", "Sales tax - Basic", "Sales tax - Eventual", "Net Revenue", "Cost of Sales", "Gross profit", "Gross margin (%)"]
                df_financeiro['conta_contabil'] = pd.Categorical(df_financeiro['conta_contabil'], categories=ordem_dre, ordered=True)
                pivot_dre = df_financeiro.query("tipo_valor == 'Realizado'").pivot_table(values='valor', index='conta_contabil', columns='mes', aggfunc='sum').reindex(columns=MESES_ORDEM).fillna(0)
                st.dataframe(pivot_dre.style.format("R$ {:,.2f}"), use_container_width=True)
            else:
                st.info("Dados de DRE indisponíveis.")
    
    else:
        st.info("Carregue o P&L na Home.")

# -----------------------------------------------------------------------------
# ABA 2: Acompanhamento Orçamentário
# -----------------------------------------------------------------------------

with tabs[1]:
    st.markdown('<div class="section-header"><span class="section-title">Acompanhamento Orçamentário</span></div>', unsafe_allow_html=True)
    
    if df_orc_proc is not None and not df_orc_proc.empty:
        stats = gerar_estatisticas_orcamento(df_orc_proc)
        col1, col2, col3, col4 = st.columns(4)
        with col1: exibir_kpi_card("Total Previsto", formatar_valor_brl(stats['total_previsto']), "Budget Global")
        with col2: exibir_kpi_card("Total Realizado", formatar_valor_brl(stats['total_realizado']), "Executado")
        with col3: exibir_kpi_card("% Execução", f"{stats['percentual_execucao']:.1f}%", "Real / Prev")
        with col4: exibir_kpi_card("Desvios Críticos", str(stats['desvios_criticos']), "Alertas > 20%")
        
        st.divider()
        st.subheader("🗺️ Heatmap de Desvios (Real vs Previsto)")
        fig_heat = plot_heatmap_desvios(df_orc_proc)
        fig_heat.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_heat, use_container_width=True)
        
        st.divider()
        st.subheader("📋 Evolução por Base Operacional")
        base_sel = st.selectbox("Base:", ['Todas'] + sorted(df_orc_proc['base_operacional'].unique().tolist()))
        df_base = df_orc_proc if base_sel == 'Todas' else df_orc_proc[df_orc_proc['base_operacional'] == base_sel]
        
        resumo_base = df_base.groupby('mes').agg({'previsto': 'sum', 'realizado': 'sum'}).reset_index()
        resumo_base['mes'] = pd.Categorical(resumo_base['mes'], categories=MESES_ORDEM, ordered=True)
        resumo_base = resumo_base.sort_values('mes')
        
        fig_evol = px.line(resumo_base, x='mes', y=['previsto', 'realizado'], markers=True, title=f"Evolução - {base_sel}", color_discrete_map={'previsto': CORES['warning'], 'realizado': CORES['primary']})
        fig_evol.update_layout(template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_evol, use_container_width=True)
    else:
        st.info("Carregue o Orçamento na Home.")

# -----------------------------------------------------------------------------
# ABA 3: Qualidade de Dados
# -----------------------------------------------------------------------------

with tabs[2]:
    st.markdown('<div class="section-header"><span class="section-title">Auditoria e Qualidade</span></div>', unsafe_allow_html=True)
    
    if df_orc_proc is not None:
        validador = ValidadorDados()
        st.subheader("✅ Validação de Schema (Pandera)")
        valido, _, rel = validador.validar_orcamento(df_orc_proc.copy(), lazy=True)
        
        if valido:
            st.success(f"Dados Validados: {rel['linhas_validas']:,} registros OK.")
        else:
            st.error(f"Falha na Validação: {rel['linhas_com_erro']:,} registros com erro.")
            if rel['erros']: st.dataframe(pd.DataFrame(rel['erros']), use_container_width=True)
        
        st.divider()
        st.subheader("📊 Estatísticas Descritivas")
        rel_q = validador.gerar_relatorio_qualidade(df_orc_proc.copy())
        st.dataframe(pd.DataFrame(rel_q['colunas']).T, use_container_width=True)

# -----------------------------------------------------------------------------
# ABA 4: Previsão Financeira
# -----------------------------------------------------------------------------

with tabs[3]:
    st.markdown('<div class="section-header"><span class="section-title">Forecasting & Projeções</span></div>', unsafe_allow_html=True)
    if pl_df is not None:
        criar_interface_forecasting_simples()
    else:
        st.info("Necessário P&L carregado para gerar previsões.")

# =============================================================================
# RODAPÉ
# =============================================================================

st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {CORES['text_secondary']}; font-size: 12px;">
    Análise Financeira Avançada • Baseal 2026
</div>
""", unsafe_allow_html=True)
