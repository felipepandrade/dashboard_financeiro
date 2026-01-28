"""
03_📈_Acompanhamento.py
=======================
Página de acompanhamento orçamentário - Comparativo Orçado x Realizado.

Esta página oferece:
- Visão geral do ano com KPIs
- Comparativo mensal com gráficos
- Análise por centro de custo
- Análise por conta contábil
- Drill-down por ativo (hierarquia)
- Exportação de relatórios

Autor: Sistema Orçamentário 2026
Data: Janeiro/2026
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.comparador import (
    get_comparativo_mensal,
    get_comparativo_por_centro,
    get_comparativo_por_conta,
    get_drill_down_ativo,
    get_kpis_gerais,
    get_top_desvios,
    get_resumo_por_ativo,
    MESES_ORDEM
)

from data.referencias_manager import (
    get_ativos_unicos,
    carregar_centros_gasto,
    ATIVOS_SEM_HIERARQUIA
)

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Acompanhamento Orçamentário - 2026",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# PALETA DE CORES
# =============================================================================

CORES = {
    'orcado': '#3b82f6',       # Azul
    'realizado': '#10b981',    # Verde
    'desvio_neg': '#ef4444',   # Vermelho
    'desvio_pos': '#f59e0b',   # Amarelo/Laranja
    'neutro': '#6b7280',       # Cinza
    'background': '#0f172a',   # Slate escuro
    'card': '#1e293b',         # Slate
    'texto': '#f1f5f9',        # Slate claro
    'destaque': '#00d4aa'      # Cyan
}

# =============================================================================
# CSS CUSTOMIZADO
# =============================================================================

st.markdown("""
<style>
    /* Tema escuro premium */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Cards de KPI */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        border: 1px solid #475569;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    
    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 8px;
    }
    
    .kpi-label {
        font-size: 14px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .kpi-delta {
        font-size: 14px;
        margin-top: 8px;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
    }
    
    .kpi-delta.positive {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    
    .kpi-delta.negative {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    
    .kpi-delta.neutral {
        background: rgba(107, 114, 128, 0.2);
        color: #9ca3af;
    }
    
    /* Seções */
    .section-header {
        padding: 16px 0 8px 0;
        border-bottom: 2px solid #00d4aa;
        margin-bottom: 24px;
    }
    
    .section-title {
        font-size: 24px;
        font-weight: 600;
        color: #f1f5f9;
    }
    
    /* Tabelas */
    .dataframe {
        background: #1e293b !important;
    }
    
    /* Alertas customizados */
    .alert-info {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin: 16px 0;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #b45309 0%, #f59e0b 100%);
        color: white;
        padding: 16px;
        border-radius: 12px;
        margin: 16px 0;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #0f172a;
    }
    
    /* Métricas do Streamlit */
    [data-testid="stMetricValue"] {
        font-size: 28px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def formatar_valor_brl(valor: float, resumido: bool = False) -> str:
    """Formata valor em reais."""
    if valor is None:
        return "R$ 0,00"
    
    if resumido and abs(valor) >= 1_000_000:
        return f"R$ {valor/1_000_000:,.1f}M".replace(",", "X").replace(".", ",").replace("X", ".")
    elif resumido and abs(valor) >= 1_000:
        return f"R$ {valor/1_000:,.1f}K".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor: float) -> str:
    """Formata valor como percentual."""
    if valor is None:
        return "0,0%"
    return f"{valor:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def get_cor_desvio(desvio_pct: float) -> str:
    """Retorna cor baseada no desvio."""
    if abs(desvio_pct) <= 5:
        return CORES['neutro']
    elif desvio_pct > 0:
        return CORES['desvio_pos']  # Acima do orçado
    else:
        return CORES['realizado']  # Abaixo do orçado (economia)


def criar_grafico_comparativo_mensal(df: pd.DataFrame) -> go.Figure:
    """Cria gráfico de barras comparativo mensal."""
    
    fig = go.Figure()
    
    # Barras de orçado
    fig.add_trace(go.Bar(
        name='Orçado',
        x=df['mes'],
        y=df['orcado'],
        marker_color=CORES['orcado'],
        text=[formatar_valor_brl(v, True) for v in df['orcado']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Orçado: %{y:,.2f}<extra></extra>'
    ))
    
    # Barras de realizado
    fig.add_trace(go.Bar(
        name='Realizado',
        x=df['mes'],
        y=df['realizado'],
        marker_color=CORES['realizado'],
        text=[formatar_valor_brl(v, True) for v in df['realizado']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Realizado: %{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=CORES['texto']),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor='#475569'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#334155',
            showline=False,
            tickformat=',.0f'
        )
    )
    
    return fig


def criar_grafico_desvio_mensal(df: pd.DataFrame) -> go.Figure:
    """Cria gráfico de linha com desvio percentual."""
    
    cores_desvio = [get_cor_desvio(d) for d in df['desvio_pct']]
    
    fig = go.Figure()
    
    # Área de referência (±5%)
    fig.add_hrect(y0=-5, y1=5, fillcolor="rgba(107,114,128,0.1)", line_width=0)
    
    # Linha zero
    fig.add_hline(y=0, line_dash="dash", line_color="#475569", line_width=1)
    
    # Barras de desvio
    fig.add_trace(go.Bar(
        x=df['mes'],
        y=df['desvio_pct'],
        marker_color=cores_desvio,
        text=[f"{d:+.1f}%" for d in df['desvio_pct']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Desvio: %{y:+.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title='Desvio Percentual por Mês',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=CORES['texto']),
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
        height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=True,
            gridcolor='#334155',
            title='Desvio (%)',
            ticksuffix='%'
        )
    )
    
    return fig


def criar_treemap_ativos(df: pd.DataFrame) -> go.Figure:
    """Cria treemap de custos por ativo."""
    
    if df.empty:
        return go.Figure()
    
    # Preparar dados
    df = df[df['realizado'] != 0].copy()
    
    if df.empty:
        return go.Figure()
    
    # Cores baseadas no desvio
    df['cor'] = df['desvio_pct'].apply(
        lambda x: '#10b981' if x < -5 else ('#ef4444' if x > 5 else '#6b7280')
    )
    
    fig = px.treemap(
        df,
        path=['ativo'],
        values='realizado',
        color='desvio_pct',
        color_continuous_scale=['#10b981', '#6b7280', '#ef4444'],
        color_continuous_midpoint=0,
        custom_data=['orcado', 'desvio', 'desvio_pct', 'qtd_centros']
    )
    
    fig.update_traces(
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Realizado: R$ %{value:,.2f}<br>'
            'Orçado: R$ %{customdata[0]:,.2f}<br>'
            'Desvio: %{customdata[2]:+.1f}%<br>'
            'Centros: %{customdata[3]}'
            '<extra></extra>'
        ),
        textinfo='label+value',
        texttemplate='<b>%{label}</b><br>R$ %{value:,.0f}'
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=CORES['texto']),
        margin=dict(l=10, r=10, t=10, b=10),
        height=400,
        coloraxis_showscale=False
    )
    
    return fig


def criar_heatmap_desvios(df: pd.DataFrame) -> go.Figure:
    """Cria heatmap de desvios por centro de custo."""
    
    if df.empty or len(df) == 0:
        return go.Figure()
    
    # Limitar a 20 centros
    df = df.head(20)
    
    # Criar labels
    labels = [f"{row['centro_gasto_codigo'][:8]}... ({row['ativo']})" 
              for _, row in df.iterrows()]
    
    fig = go.Figure(data=go.Heatmap(
        z=[df['desvio_pct'].tolist()],
        x=labels,
        colorscale=[
            [0, '#10b981'],
            [0.5, '#6b7280'],
            [1, '#ef4444']
        ],
        zmid=0,
        text=[[f"{d:+.1f}%" for d in df['desvio_pct']]],
        texttemplate='%{text}',
        textfont={"size": 10},
        hovertemplate='%{x}<br>Desvio: %{z:+.1f}%<extra></extra>',
        showscale=True,
        colorbar=dict(
            title='Desvio %',
            ticksuffix='%'
        )
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=CORES['texto']),
        margin=dict(l=20, r=20, t=20, b=100),
        height=150,
        xaxis=dict(tickangle=45)
    )
    
    return fig


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

# Título
st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #f1f5f9; font-size: 36px; margin-bottom: 8px;">
        📈 Acompanhamento Orçamentário
    </h1>
    <p style="color: #94a3b8; font-size: 16px;">
        Comparativo Orçado x Realizado | Exercício 2026
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# KPIs GERAIS
# =============================================================================

kpis = get_kpis_gerais(2026)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{formatar_valor_brl(kpis['total_orcado'], True)}</div>
        <div class="kpi-label">Total Orçado</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{formatar_valor_brl(kpis['total_realizado'], True)}</div>
        <div class="kpi-label">Total Realizado</div>
        <div class="kpi-delta {'positive' if kpis['desvio'] > 0 else 'negative' if kpis['desvio'] < 0 else 'neutral'}">
            {formatar_valor_brl(kpis['desvio'], True)} ({kpis['desvio_pct']:+.1f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    execucao_cor = 'positive' if kpis['execucao_pct'] > 100 else 'neutral'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{kpis['execucao_pct']:.1f}%</div>
        <div class="kpi-label">Execução Orçamentária</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{kpis['meses_com_dados']}/12</div>
        <div class="kpi-label">Meses com Lançamentos</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# TABS PRINCIPAIS
# =============================================================================

tab_mensal, tab_centro, tab_conta, tab_ativo = st.tabs([
    "📅 Visão Mensal",
    "🏢 Por Centro de Custo",
    "📊 Por Conta Contábil",
    "🔍 Drill-down por Ativo"
])

# =============================================================================
# TAB: VISÃO MENSAL
# =============================================================================

with tab_mensal:
    st.markdown('<div class="section-header"><span class="section-title">Comparativo Mensal</span></div>', unsafe_allow_html=True)
    
    # Obter dados
    df_mensal = get_comparativo_mensal(2026)
    
    if not df_mensal.empty:
        # Gráfico de barras
        fig_barras = criar_grafico_comparativo_mensal(df_mensal)
        st.plotly_chart(fig_barras, use_container_width=True)
        
        # Gráfico de desvio
        fig_desvio = criar_grafico_desvio_mensal(df_mensal)
        st.plotly_chart(fig_desvio, use_container_width=True)
        
        # Tabela detalhada
        st.markdown("#### 📋 Tabela Detalhada")
        
        df_display = df_mensal.copy()
        df_display['Orçado'] = df_display['orcado'].apply(formatar_valor_brl)
        df_display['Realizado'] = df_display['realizado'].apply(formatar_valor_brl)
        df_display['Desvio'] = df_display['desvio'].apply(formatar_valor_brl)
        df_display['Desvio %'] = df_display['desvio_pct'].apply(lambda x: f"{x:+.1f}%")
        
        st.dataframe(
            df_display[['mes', 'Orçado', 'Realizado', 'Desvio', 'Desvio %']],
            hide_index=True,
            use_container_width=True,
            column_config={
                'mes': st.column_config.TextColumn('Mês', width='small')
            }
        )
    else:
        st.info("📭 Nenhum dado disponível para comparação mensal.")

# =============================================================================
# TAB: POR CENTRO DE CUSTO
# =============================================================================

with tab_centro:
    st.markdown('<div class="section-header"><span class="section-title">Análise por Centro de Custo</span></div>', unsafe_allow_html=True)
    
    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        mes_filtro = st.selectbox(
            "Mês",
            options=['Todos'] + MESES_ORDEM,
            key="filtro_mes_centro"
        )
    with col_f2:
        df_centros = carregar_centros_gasto()
        ativos_lista = ['Todos'] + sorted(df_centros['ativo'].unique().tolist()) if not df_centros.empty else ['Todos']
        ativo_filtro = st.selectbox(
            "Ativo",
            options=ativos_lista,
            key="filtro_ativo_centro"
        )
    
    # Obter dados
    mes_param = None if mes_filtro == 'Todos' else mes_filtro
    df_centro = get_comparativo_por_centro(mes_param, 2026)
    
    # Filtrar por ativo
    if ativo_filtro != 'Todos' and not df_centro.empty:
        df_centro = df_centro[df_centro['ativo'] == ativo_filtro]
    
    if not df_centro.empty:
        # Heatmap de desvios
        st.markdown("#### 🌡️ Heatmap de Desvios (Top 20)")
        fig_heat = criar_heatmap_desvios(df_centro)
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # Estatísticas
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            total_centros = len(df_centro)
            st.metric("Total de Centros", total_centros)
        with col_s2:
            centros_acima = (df_centro['desvio_pct'] > 5).sum()
            st.metric("Acima do Orçado (>5%)", centros_acima, delta=f"{centros_acima/total_centros*100:.0f}%" if total_centros > 0 else "0%")
        with col_s3:
            centros_abaixo = (df_centro['desvio_pct'] < -5).sum()
            st.metric("Abaixo do Orçado (<-5%)", centros_abaixo, delta=f"{centros_abaixo/total_centros*100:.0f}%" if total_centros > 0 else "0%")
        
        # Tabela
        st.markdown("#### 📋 Detalhamento por Centro")
        
        df_display = df_centro.copy()
        df_display['Orçado'] = df_display['orcado'].apply(formatar_valor_brl)
        df_display['Realizado'] = df_display['realizado'].apply(formatar_valor_brl)
        df_display['Desvio'] = df_display['desvio'].apply(formatar_valor_brl)
        df_display['Desvio %'] = df_display['desvio_pct'].apply(lambda x: f"{x:+.1f}%")
        
        st.dataframe(
            df_display[['centro_gasto_codigo', 'ativo', 'Orçado', 'Realizado', 'Desvio', 'Desvio %']],
            hide_index=True,
            use_container_width=True,
            height=400
        )
        
        # Exportar
        if st.button("📥 Exportar CSV", key="export_centro"):
            csv = df_centro.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "⬇️ Baixar",
                data=csv,
                file_name=f"comparativo_centro_{mes_filtro}_{datetime.now():%Y%m%d}.csv",
                mime="text/csv"
            )
    else:
        st.info("📭 Nenhum dado disponível para os filtros selecionados.")

# =============================================================================
# TAB: POR CONTA CONTÁBIL
# =============================================================================

with tab_conta:
    st.markdown('<div class="section-header"><span class="section-title">Análise por Conta Contábil</span></div>', unsafe_allow_html=True)
    
    # Filtro
    mes_filtro_conta = st.selectbox(
        "Mês",
        options=['Todos'] + MESES_ORDEM,
        key="filtro_mes_conta"
    )
    
    mes_param = None if mes_filtro_conta == 'Todos' else mes_filtro_conta
    df_conta = get_comparativo_por_conta(mes_param, 2026)
    
    if not df_conta.empty:
        # Top 10 por valor realizado
        st.markdown("#### 🏆 Top 10 Contas por Valor Realizado")
        
        df_top10 = df_conta.head(10)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Orçado',
            y=df_top10['descricao'].str[:40] + '...',
            x=df_top10['orcado'],
            orientation='h',
            marker_color=CORES['orcado']
        ))
        
        fig.add_trace(go.Bar(
            name='Realizado',
            y=df_top10['descricao'].str[:40] + '...',
            x=df_top10['realizado'],
            orientation='h',
            marker_color=CORES['realizado']
        ))
        
        fig.update_layout(
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=CORES['texto']),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=20, r=20, t=40, b=20),
            height=400,
            xaxis=dict(showgrid=True, gridcolor='#334155'),
            yaxis=dict(showgrid=False, autorange='reversed')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela completa
        st.markdown("#### 📋 Todas as Contas")
        
        df_display = df_conta.copy()
        df_display['Orçado'] = df_display['orcado'].apply(formatar_valor_brl)
        df_display['Realizado'] = df_display['realizado'].apply(formatar_valor_brl)
        df_display['Desvio'] = df_display['desvio'].apply(formatar_valor_brl)
        df_display['Desvio %'] = df_display['desvio_pct'].apply(lambda x: f"{x:+.1f}%")
        
        st.dataframe(
            df_display[['conta_contabil_codigo', 'descricao', 'Orçado', 'Realizado', 'Desvio', 'Desvio %']],
            hide_index=True,
            use_container_width=True,
            height=400
        )
    else:
        st.info("📭 Nenhum dado disponível para o mês selecionado.")

# =============================================================================
# TAB: DRILL-DOWN POR ATIVO
# =============================================================================

with tab_ativo:
    st.markdown('<div class="section-header"><span class="section-title">Drill-down por Ativo</span></div>', unsafe_allow_html=True)
    
    # Resumo por ativo
    df_resumo = get_resumo_por_ativo(None, 2026)
    
    if not df_resumo.empty:
        # Treemap
        st.markdown("#### 🗺️ Distribuição de Custos por Ativo")
        fig_tree = criar_treemap_ativos(df_resumo)
        st.plotly_chart(fig_tree, use_container_width=True)
        
        # Tabela resumo
        st.markdown("#### 📊 Resumo por Ativo")
        
        df_display = df_resumo.copy()
        df_display['Orçado'] = df_display['orcado'].apply(formatar_valor_brl)
        df_display['Realizado'] = df_display['realizado'].apply(formatar_valor_brl)
        df_display['Desvio'] = df_display['desvio'].apply(formatar_valor_brl)
        df_display['Desvio %'] = df_display['desvio_pct'].apply(lambda x: f"{x:+.1f}%")
        df_display['Hierarquia'] = df_display['sem_hierarquia'].apply(lambda x: '⚠️ Sem hierarquia' if x else '✅ Com hierarquia')
        
        st.dataframe(
            df_display[['ativo', 'qtd_centros', 'Orçado', 'Realizado', 'Desvio', 'Desvio %', 'Hierarquia']],
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("---")
        
        # Drill-down específico
        st.markdown("#### 🔎 Explorar Ativo Específico")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            ativo_drill = st.selectbox(
                "Selecione o Ativo",
                options=df_resumo['ativo'].tolist(),
                key="drill_ativo"
            )
        with col_d2:
            mes_drill = st.selectbox(
                "Mês",
                options=['Todos'] + MESES_ORDEM,
                key="drill_mes"
            )
        
        if ativo_drill:
            mes_param = None if mes_drill == 'Todos' else mes_drill
            df_drill = get_drill_down_ativo(ativo_drill, mes_param, 2026)
            
            if not df_drill.empty:
                is_sem_hier = ativo_drill in ATIVOS_SEM_HIERARQUIA
                
                if is_sem_hier:
                    st.warning(f"⚠️ O ativo **{ativo_drill}** não segue a lógica de hierarquia pai-filho.")
                
                # Mostrar centros
                st.markdown(f"##### Centros de Custo - {ativo_drill}")
                
                df_display = df_drill.copy()
                df_display['Centro'] = df_display.apply(
                    lambda r: f"{'└── ' if r['classe'] != '0' else ''}{r['centro_gasto_codigo']}",
                    axis=1
                )
                df_display['Descrição'] = df_display['descricao']
                df_display['Classe'] = df_display['classe_nome']
                df_display['Orçado'] = df_display['orcado'].apply(formatar_valor_brl)
                df_display['Realizado'] = df_display['realizado'].apply(formatar_valor_brl)
                df_display['Desvio %'] = df_display['desvio_pct'].apply(lambda x: f"{x:+.1f}%")
                
                st.dataframe(
                    df_display[['Centro', 'Descrição', 'Classe', 'Orçado', 'Realizado', 'Desvio %']],
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info(f"📭 Nenhum dado disponível para o ativo {ativo_drill}.")
    else:
        st.info("📭 Nenhum dado disponível para análise por ativo.")

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("### 📈 Acompanhamento 2026")
    st.markdown("---")
    
    # Status
    st.markdown("#### 📊 Status Geral")
    
    if kpis['status_geral'] == 'normal':
        st.success("✅ Execução dentro do esperado (±5%)")
    elif kpis['status_geral'] == 'acima':
        st.warning("⚠️ Execução acima do orçado")
    elif kpis['status_geral'] == 'abaixo':
        st.info("📉 Execução abaixo do orçado")
    else:
        st.info("📭 Sem dados suficientes")
    
    st.markdown("---")
    
    # Top desvios
    st.markdown("#### 🔥 Top 5 Desvios")
    
    df_top = get_top_desvios(5, None, 2026)
    
    if not df_top.empty:
        for _, row in df_top.iterrows():
            cor = '🔴' if row['desvio'] > 0 else '🟢'
            st.markdown(f"{cor} **{row['ativo']}**: {row['desvio_pct']:+.1f}%")
    else:
        st.caption("Nenhum desvio registrado")
    
    st.markdown("---")
    
    # Legenda
    st.markdown("#### 📋 Legenda de Cores")
    st.markdown("""
    - 🔵 **Azul**: Valor orçado
    - 🟢 **Verde**: Valor realizado / Economia
    - 🔴 **Vermelho**: Acima do orçado
    - ⚪ **Cinza**: Dentro da tolerância (±5%)
    """)
    
    st.markdown("---")
    st.caption("Dashboard Financeiro BASEAL © 2026")
