"""
01_📊_Analise_Financeira.py
============================
Módulo principal de análise financeira (Multi-Page).

Esta página é detectada automaticamente pelo Streamlit através da pasta pages/.
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

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

st.set_page_config(
    layout="wide",
    page_title="Análise Financeira",
    page_icon="📊"
)

st.markdown("""
    <style>
        /* Global Settings */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        /* Premium Dark Theme Adjustments */
        .stApp {
            background-color: #0E1117;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #FAFAFA;
            font-weight: 700;
        }
        
        h1 {
            color: #4F8BF9;
            padding-bottom: 10px;
        }
        
        /* Cards */
        .css-1r6slb0, .css-12w0qpk {
            background-color: #1E2130;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid #2E3245;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 24px;
            color: #4F8BF9;
        }
        
        /* Custom Classes */
        .card {
            background-color: #1E2130;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #2E3245;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# CABEÇALHO
# =============================================================================

st.title("📊 Módulo de Análise Financeira")
st.markdown("Visão completa da performance orçamentária, custos, resultados e projeções futuras.")
st.markdown("---")

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

# Status rápido
col_st1, col_st2, col_st3 = st.columns(3)
with col_st1:
    st.metric("📊 P&L", f"{len(pl_df):,} linhas" if pl_df is not None else "Não carregado")
with col_st2:
    st.metric("📝 Razão", f"{len(razao_df):,} linhas" if razao_df is not None else "Não carregado")
with col_st3:
    st.metric("💰 Orçamento", f"{len(df_orc_proc):,} linhas" if df_orc_proc is not None else "Não carregado")

st.markdown("---")

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
        
        st.info(f"📅 **Último mês realizado detectado:** {ultimo_mes_realizado} ({numero_meses_passados} meses acumulados)")
        st.divider()
        
        # FILTROS
        st.subheader("🔍 Filtros de Análise")
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
                st.header(f"Dashboard: {centro_custo_selecionado} | {conta_contabil_selecionada}")
                st.caption(f"Período: {periodo_selecionado}")
                
                total_realizado = df_custos_filtrado.query("tipo_valor == 'Realizado'")['valor'].sum()
                total_budget = df_custos_filtrado.query("tipo_valor == 'Budget V3'")['valor'].sum()
                total_budget_v1 = df_custos_filtrado.query("tipo_valor == 'Budget V1'")['valor'].sum()
                variacao = ((total_realizado - total_budget) / total_budget * 100) if total_budget != 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💰 Realizado", f"R$ {total_realizado:,.2f}")
                col2.metric("🎯 Budget V3", f"R$ {total_budget:,.2f}")
                col3.metric("📊 Budget V1", f"R$ {total_budget_v1:,.2f}")
                col4.metric("📈 Variação V3", f"{variacao:.2f}%", delta=f"{variacao:.2f}%")
                
                st.divider()
                
                st.subheader("📈 Evolução Temporal")
                
                if periodo_selecionado == 'YTD (Acumulado do Ano)':
                    df_grafico = df_custos_filtrado.groupby(['mes', 'tipo_valor'])['valor'].sum().reset_index()
                    df_grafico['mes'] = pd.Categorical(df_grafico['mes'], categories=MESES_ORDEM, ordered=True)
                    df_grafico = df_grafico.sort_values('mes')
                    fig = px.line(
                        df_grafico, x='mes', y='valor', color='tipo_valor',
                        markers=True,
                        title=f"Evolução Mensal: {centro_custo_selecionado} | {conta_contabil_selecionada}",
                        labels={'valor': 'Valor (R$)', 'mes': 'Mês', 'tipo_valor': 'Versão'},
                        color_discrete_map={
                            'Realizado': '#1f77b4',
                            'Budget V1': '#ff7f0e',
                            'Budget V3': '#2ca02c',
                            'LY - Actual': '#d62728'
                        }
                    )
                else:
                    df_grafico = df_custos_filtrado.groupby('tipo_valor')['valor'].sum().reset_index()
                    fig = px.bar(
                        df_grafico, x='tipo_valor', y='valor', color='tipo_valor',
                        title=f"Comparativo no Mês de {periodo_selecionado}",
                        labels={'valor': 'Valor (R$)', 'tipo_valor': 'Versão'},
                        text_auto='.2s'
                    )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with sub_tabs[1]:  # Despesas Detalhadas
                st.header("💵 Análise Detalhada de Despesas")
                
                st.subheader("📊 Resumo Mensal Consolidado")
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
                    st.info("Nenhum dado disponível para o filtro selecionado.")
                
                st.divider()
                st.subheader("🔍 Performance por Conta Contábil")
                
                tipos_disponiveis = df_custos_filtrado['tipo_valor'].unique().tolist()
                tipos_selecionados = st.multiselect(
                    "Selecione os Tipos de Valor:",
                    options=tipos_disponiveis,
                    default=tipos_disponiveis
                )
                
                if tipos_selecionados:
                    df_detalhada = df_custos_filtrado[df_custos_filtrado['tipo_valor'].isin(tipos_selecionados)].copy()
                    
                    df_detalhada['mes'] = pd.Categorical(df_detalhada['mes'], categories=MESES_ORDEM, ordered=True)
                    
                    df_pivot = df_detalhada.pivot_table(
                        index=['conta_contabil', 'tipo_valor'],
                        columns='mes',
                        values='valor',
                        aggfunc='sum'
                    ).fillna(0)
                    
                    df_pivot = df_pivot.sort_index(level='conta_contabil')
                    
                    if not df_pivot.empty:
                        st.dataframe(df_pivot.style.format("R$ {:,.2f}"), use_container_width=True)
                    else:
                        st.info("Nenhum dado disponível para os tipos selecionados.")
                    
                    st.divider()
                    
                    # Top Agressores
                    st.subheader("🎯 Top Agressores (Maiores Desvios)")
                    top_n = st.slider("Número de agressores:", 3, 20, 5, key='top_agressores')
                    
                    df_pivot_desvio = df_custos_filtrado[
                        df_custos_filtrado['tipo_valor'].isin(['Realizado', 'Budget V3'])
                    ].pivot_table(
                        index='conta_contabil',
                        columns='tipo_valor',
                        values='valor',
                        aggfunc='sum'
                    ).fillna(0)
                    
                    if 'Realizado' in df_pivot_desvio.columns and 'Budget V3' in df_pivot_desvio.columns:
                        df_pivot_desvio['Desvio (R$)'] = df_pivot_desvio['Realizado'] - df_pivot_desvio['Budget V3']
                        df_pivot_desvio['Desvio (%)'] = (df_pivot_desvio['Desvio (R$)'] / df_pivot_desvio['Budget V3'] * 100).replace([float('inf'), -float('inf')], 0)
                        df_pivot_desvio['Desvio (Absoluto)'] = df_pivot_desvio['Desvio (R$)'].abs()
                        
                        df_agressores = df_pivot_desvio.sort_values(by='Desvio (Absoluto)', ascending=False).head(top_n)
                        
                        if not df_agressores.empty:
                            df_agressores_melted = df_agressores.reset_index().melt(
                                id_vars='conta_contabil',
                                value_vars=['Realizado', 'Budget V3'],
                                var_name='Tipo',
                                value_name='Valor'
                            )
                            
                            fig_agressores = px.bar(
                                df_agressores_melted,
                                x='conta_contabil',
                                y='Valor',
                                color='Tipo',
                                barmode='group',
                                title=f"Top {top_n} Agressores - Realizado vs Budget V3",
                                text_auto='.2s',
                                color_discrete_map={'Realizado': '#1f77b4', 'Budget V3': '#2ca02c'}
                            )
                            fig_agressores.update_xaxes(tickangle=-45)
                            st.plotly_chart(fig_agressores, use_container_width=True)
                            
                            st.dataframe(
                                df_agressores[['Realizado', 'Budget V3', 'Desvio (R$)', 'Desvio (%)']].style.format({
                                    'Realizado': 'R$ {:,.2f}',
                                    'Budget V3': 'R$ {:,.2f}',
                                    'Desvio (R$)': 'R$ {:,.2f}',
                                    'Desvio (%)': '{:.2f}%'
                                }),
                                use_container_width=True
                            )
                        else:
                            st.info("Nenhum agressor identificado.")
                    else:
                        st.info("Dados de Realizado ou Budget V3 não disponíveis para comparação.")
            
            with sub_tabs[2]:  # Fornecedores
                st.header("🏢 Análise por Fornecedor")
                
                if not razao_filtrado.empty:
                    st.subheader("📊 Top 10 Fornecedores")
                    top_fornecedores = razao_filtrado.groupby('fornecedor')['valor'].sum().nlargest(10).reset_index()
                    
                    fig_fornec = px.bar(
                        top_fornecedores,
                        x='valor',
                        y='fornecedor',
                        orientation='h',
                        title="Top 10 Fornecedores por Valor Total",
                        labels={'valor': 'Valor (R$)', 'fornecedor': 'Fornecedor'},
                        text_auto='.2s',
                        color='valor',
                        color_continuous_scale='Blues'
                    )
                    fig_fornec.update_layout(showlegend=False)
                    st.plotly_chart(fig_fornec, use_container_width=True)
                    
                    st.divider()
                    st.subheader("📋 Detalhes dos Lançamentos por Fornecedor")
                    
                    fornecedor_selecionado = st.selectbox(
                        "Selecione um fornecedor:",
                        ['Todos'] + sorted(razao_filtrado['fornecedor'].dropna().unique().tolist())
                    )
                    
                    if fornecedor_selecionado != 'Todos':
                        razao_detalhado = razao_filtrado[razao_filtrado['fornecedor'] == fornecedor_selecionado]
                    else:
                        razao_detalhado = razao_filtrado
                    
                    st.dataframe(razao_detalhado, use_container_width=True)
                    
                    # Exportar
                    csv_razao = razao_detalhado.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Baixar Dados de Fornecedores (CSV)",
                        csv_razao,
                        f"fornecedores_{fornecedor_selecionado}.csv",
                        "text/csv"
                    )
                else:
                    st.info("Dados de Razão (Fornecedores) não disponíveis.")
            
            with sub_tabs[3]:  # Visualizações
                st.header("📈 Visualizações Avançadas")
                
                st.subheader("🗺️ Estrutura de Custos (Treemap)")
                df_treemap = df_custos_filtrado.query("tipo_valor == 'Realizado' and valor > 0")
                if not df_treemap.empty:
                    fig_treemap = px.treemap(
                        df_treemap,
                        path=[px.Constant("Total"), 'centro_gasto_nome', 'conta_contabil'],
                        values='valor',
                        title='Composição Hierárquica dos Custos Realizados',
                        color='valor',
                        color_continuous_scale='RdYlGn_r'
                    )
                    st.plotly_chart(fig_treemap, use_container_width=True)
                else:
                    st.info("Nenhum dado disponível para o Treemap.")
                
                st.divider()
                st.subheader("📉 Decomposição Temporal (STL)")
                st.caption("Análise de tendência, sazonalidade e resíduos")
                
                if not pl_df.empty and 'data' in pl_df.columns:
                    try:
                        fig_stl = plot_stl_decomposition(pl_df, 'data', 'valor')
                        st.plotly_chart(fig_stl, use_container_width=True)
                    except Exception as e:
                        st.error(f"Erro ao gerar decomposição STL: {e}")
                else:
                    st.info("Dados insuficientes para decomposição temporal.")
            
            with sub_tabs[4]:  # IA
                st.header("🔍 Análise com Inteligência Artificial")
                
                if not api_key:
                    st.warning("⚠️ **Configure a chave de API na página inicial para usar análises com IA.**")
                else:
                    st.success(f"✅ Conectado ao provedor: **{ai_provider}**")
                
                st.markdown("---")
                
                if st.button("🚀 Gerar Análise Financeira com IA", type="primary"):
                    if not api_key:
                        st.error("❌ Configure a chave de API na página inicial.")
                    else:
                        with st.spinner("🤖 Analisando dados com IA..."):
                            contexto = f"""
                            Centro de Custo: {centro_custo_selecionado}
                            Conta Contábil: {conta_contabil_selecionada}
                            Período: {periodo_selecionado}
                            Total Realizado: R$ {total_realizado:,.2f}
                            Total Budget: R$ {total_budget:,.2f}
                            Variação: {variacao:.2f}%
                            """
                            analise = gerar_analise_ia(df_custos_filtrado, api_key, ai_provider, contexto)
                            st.markdown("### 📊 Análise Gerada")
                            st.markdown(analise)
                
                st.markdown("---")
                st.subheader("💬 Chat com IA sobre seus dados")
                
                user_question = st.text_area(
                    "Faça uma pergunta sobre os dados financeiros:",
                    placeholder="Ex: Quais são as maiores oportunidades de redução de custos?",
                    height=100
                )
                
                if st.button("💡 Enviar Pergunta"):
                    if not api_key:
                        st.error("❌ Configure a chave de API na página inicial.")
                    elif not user_question:
                        st.warning("⚠️ Digite uma pergunta primeiro.")
                    else:
                        with st.spinner("🤖 Consultando IA..."):
                            # Preparar contexto
                            resumo_dados = df_custos_filtrado.groupby(['tipo_valor', 'mes'])['valor'].sum().reset_index()
                            
                            messages = [
                                {"role": "system", "content": "Você é um analista financeiro sênior especializado em O&M de gasodutos."},
                                {"role": "user", "content": f"""
                                Contexto dos dados:
                                {resumo_dados.to_string()}
                                
                                Pergunta do usuário: {user_question}
                                """}
                            ]
                            
                            resposta = get_ai_chat_response(messages, api_key, ai_provider)
                            st.markdown("### 💬 Resposta da IA")
                            st.markdown(resposta)
        
        with tab_dre:
            st.header("📋 Demonstrativo de Resultados (DRE)")
            
            if not df_financeiro.empty:
                ordem_dre = [
                    "Gross Sales - Basic Services",
                    "Gross Sales - Eventual Services",
                    "Sales tax - Basic",
                    "Sales tax - Eventual",
                    "Net Revenue",
                    "Cost of Sales",
                    "Gross profit",
                    "Gross margin (%)"
                ]
                
                df_financeiro['conta_contabil'] = pd.Categorical(
                    df_financeiro['conta_contabil'],
                    categories=ordem_dre,
                    ordered=True
                )
                df_financeiro = df_financeiro.sort_values('conta_contabil')
                
                st.subheader("💰 DRE - Realizados")
                pivot_dre = df_financeiro.query("tipo_valor == 'Realizado'").pivot_table(
                    values='valor',
                    index='conta_contabil',
                    columns='mes',
                    aggfunc='sum'
                ).reindex(columns=MESES_ORDEM).fillna(0)
                
                if ultimo_mes_realizado and numero_meses_passados > 0:
                    pivot_dre['YTD'] = pivot_dre.loc[:, MESES_ORDEM[:numero_meses_passados]].sum(axis=1)
                
                st.dataframe(pivot_dre.style.format("R$ {:,.2f}"), use_container_width=True)
                
                st.divider()
                
                st.subheader("📊 DRE - Budget V3")
                pivot_dre_budget = df_financeiro.query("tipo_valor == 'Budget V3'").pivot_table(
                    values='valor',
                    index='conta_contabil',
                    columns='mes',
                    aggfunc='sum'
                ).reindex(columns=MESES_ORDEM).fillna(0)
                
                if ultimo_mes_realizado and numero_meses_passados > 0:
                    pivot_dre_budget['YTD'] = pivot_dre_budget.loc[:, MESES_ORDEM[:numero_meses_passados]].sum(axis=1)
                
                st.dataframe(pivot_dre_budget.style.format("R$ {:,.2f}"), use_container_width=True)
                
                # Visualização comparativa
                st.divider()
                st.subheader("📈 Comparativo DRE: Realizado vs Budget")
                
                # Selecionar contas principais
                contas_principais = ['Net Revenue', 'Cost of Sales', 'Gross profit']
                df_dre_comp = df_financeiro[df_financeiro['conta_contabil'].isin(contas_principais)]
                
                df_dre_comp_group = df_dre_comp.pivot_table(
                    values='valor',
                    index='conta_contabil',
                    columns='tipo_valor',
                    aggfunc='sum'
                ).reset_index()
                
                if not df_dre_comp_group.empty:
                    df_dre_melted = df_dre_comp_group.melt(
                        id_vars='conta_contabil',
                        var_name='Tipo',
                        value_name='Valor'
                    )
                    
                    fig_dre = px.bar(
                        df_dre_melted,
                        x='conta_contabil',
                        y='Valor',
                        color='Tipo',
                        barmode='group',
                        title='Comparativo DRE: Principais Contas',
                        text_auto='.2s'
                    )
                    st.plotly_chart(fig_dre, use_container_width=True)
            else:
                st.info("Dados de DRE não disponíveis.")
    
    else:
        st.info("📊 Carregue os dados de P&L na página inicial para visualizar esta análise.")

# -----------------------------------------------------------------------------
# ABA 2: Acompanhamento Orçamentário
# -----------------------------------------------------------------------------

with tabs[1]:
    st.header("📊 Acompanhamento Orçamentário")
    
    if df_orc_proc is not None and not df_orc_proc.empty:
        
        ano_ref = st.session_state.get('processed_orc_year', 2025)
        st.subheader(f"📅 Análise Orçamentária - Ano {ano_ref}")
        
        stats = gerar_estatisticas_orcamento(df_orc_proc)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Total Previsto", f"R$ {stats['total_previsto']:,.2f}")
        col2.metric("✅ Total Realizado", f"R$ {stats['total_realizado']:,.2f}")
        col3.metric("📊 % Execução", f"{stats['percentual_execucao']:.1f}%")
        col4.metric("⚠️ Desvios Críticos", stats['desvios_criticos'])
        
        st.divider()
        
        st.subheader("🗺️ Heatmap de Desvios Orçamentários")
        st.caption("Visualização de desvios (Realizado - Previsto) por Base Operacional e Mês")
        
        fig_heat = plot_heatmap_desvios(df_orc_proc)
        st.plotly_chart(fig_heat, use_container_width=True)
        
        st.divider()
        
        st.subheader("📋 Análise Detalhada por Base")
        
        base_selecionada = st.selectbox(
            "Selecione uma Base Operacional:",
            ['Todas'] + sorted(df_orc_proc['base_operacional'].unique().tolist())
        )
        
        if base_selecionada != 'Todas':
            df_base = df_orc_proc[df_orc_proc['base_operacional'] == base_selecionada]
        else:
            df_base = df_orc_proc
        
        # Resumo da base
        resumo_base = df_base.groupby('mes').agg({
            'previsto': 'sum',
            'realizado': 'sum',
            'diferenca': 'sum'
        }).reset_index()
        
        resumo_base['mes'] = pd.Categorical(resumo_base['mes'], categories=MESES_ORDEM, ordered=True)
        resumo_base = resumo_base.sort_values('mes')
        
        fig_base = px.line(
            resumo_base,
            x='mes',
            y=['previsto', 'realizado'],
            markers=True,
            title=f"Evolução Orçamentária - {base_selecionada}",
            labels={'value': 'Valor (R$)', 'variable': 'Tipo', 'mes': 'Mês'}
        )
        st.plotly_chart(fig_base, use_container_width=True)
        
        st.dataframe(resumo_base.style.format({
            'previsto': 'R$ {:,.2f}',
            'realizado': 'R$ {:,.2f}',
            'diferenca': 'R$ {:,.2f}'
        }), use_container_width=True)
        
        st.divider()
        
        csv_orc = exportar_orcamento_csv(df_orc_proc)
        st.download_button(
            "📥 Baixar Orçamento Completo (CSV)",
            csv_orc,
            f"orcamento_{ano_ref}.csv",
            "text/csv",
            key='download_orc'
        )
    
    else:
        st.info("📊 Carregue os dados de Orçamento na página inicial para visualizar esta análise.")

# -----------------------------------------------------------------------------
# ABA 3: Qualidade de Dados
# -----------------------------------------------------------------------------

with tabs[2]:
    st.header("🔬 Validação de Qualidade de Dados")
    
    if df_orc_proc is not None and not df_orc_proc.empty:
        validador = ValidadorDados()
        
        st.subheader("✅ Validação de Schema (Pandera)")
        
        with st.spinner("Validando schema..."):
            valido, df_val, rel = validador.validar_orcamento(df_orc_proc.copy(), lazy=True)
        
        if valido:
            st.success(f"✅ **Schema válido!** {rel['linhas_validas']:,} linhas aprovadas")
        else:
            st.error(f"❌ **Schema inválido!** {rel['linhas_com_erro']:,} linhas com erros")
            
            if rel['erros']:
                st.subheader("📋 Erros Detectados")
                df_erros = pd.DataFrame(rel['erros'])
                st.dataframe(df_erros, use_container_width=True)
        
        st.divider()
        
        st.subheader("📊 Relatório de Qualidade dos Dados")
        
        rel_q = validador.gerar_relatorio_qualidade(df_orc_proc.copy())
        
        st.metric("Total de Linhas", rel_q['total_linhas'])
        st.metric("Total de Colunas", rel_q['total_colunas'])
        
        st.markdown("---")
        
        st.subheader("📈 Estatísticas por Coluna")
        df_stats = pd.DataFrame(rel_q['colunas']).T
        
        cols_display = ['tipo', 'valores_nulos', 'percentual_nulos', 'valores_unicos', 'media', 'min', 'max']
        df_stats_display = df_stats[[c for c in cols_display if c in df_stats.columns]]
        
        st.dataframe(df_stats_display, use_container_width=True)
        
        # Visualizar nulos
        st.divider()
        st.subheader("🔍 Análise de Valores Nulos")
        
        df_nulos = df_stats[['valores_nulos', 'percentual_nulos']].sort_values('percentual_nulos', ascending=False).head(10)
        
        if not df_nulos.empty and df_nulos['valores_nulos'].sum() > 0:
            fig_nulos = px.bar(
                df_nulos.reset_index(),
                x='index',
                y='percentual_nulos',
                title='Top 10 Colunas com Valores Nulos',
                labels={'index': 'Coluna', 'percentual_nulos': '% Nulos'},
                text_auto='.2f'
            )
            fig_nulos.update_xaxes(tickangle=-45)
            st.plotly_chart(fig_nulos, use_container_width=True)
        else:
            st.success("✅ Nenhum valor nulo detectado!")
    
    elif pl_df is not None and not pl_df.empty:
        st.info("Validação de P&L não implementada nesta versão. Foco em Orçamento.")
    
    else:
        st.info("📊 Carregue os dados de Orçamento na página inicial para validar.")

# -----------------------------------------------------------------------------
# ABA 4: Previsão Financeira (Modelo Matemático)
# -----------------------------------------------------------------------------

with tabs[3]:
    st.header("📈 Previsão Financeira")
    
    if pl_df is not None and not pl_df.empty:
        criar_interface_forecasting_simples()
    else:
        st.info("📊 Carregue os dados de P&L na página inicial para utilizar o modelo de previsão.")

# =============================================================================
# RODAPÉ
# =============================================================================

st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.caption("📦 **Versão:** 2.0.1")
with col_f2:
    st.caption("📊 **Página:** Análise Financeira")
with col_f3:
    st.caption("📅 **Nov 2025**")
