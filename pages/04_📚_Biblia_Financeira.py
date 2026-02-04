"""
04_📚_Biblia_Financeira.py
==========================
Data Discovery e Visualização de Dados Mestres.
Permite explorar o Orçamento Base 2026, Histórico Realizado e Metadados (Centros/Contas).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from utils_ui import setup_page, exibir_kpi_card, formatar_valor_brl, CORES, require_auth
from data.referencias_manager import (
    carregar_orcamento_v1_2026,
    carregar_centros_gasto,
    carregar_contas_contabeis,
    MESES_ORDEM
)

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Bíblia Financeira - Dados Mestres", "📚")
require_auth(module='biblia')

st.markdown("""
<div class="section-header">
    <span class="section-title">📚 Bíblia Financeira</span>
    <p style="color: #94a3b8; font-size: 14px; margin-top: 5px;">
        Explorador de dados mestres, orçamento base e histórico financeiro.
    </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# CARREGAMENTO DE DADOS
# =============================================================================

@st.cache_data
def load_static_data():
    df_orc = carregar_orcamento_v1_2026()
    df_centros = carregar_centros_gasto()
    df_contas = carregar_contas_contabeis()
    return df_orc, df_centros, df_contas

def load_pl_from_db():
    """Carrega dados históricos (Realizado) do banco de dados Neon."""
    from database.models import get_session, LancamentoRealizado
    from datetime import datetime
    
    session = get_session()
    try:
        # Buscar apenas Realizado (ignora Budgets que são estáticos)
        query = session.query(LancamentoRealizado)
        # Opcional: Filtrar apenas anos fechados ou tudo
        dados = query.all()
        
        if not dados:
            return pd.DataFrame()
            
        # Converter para lista de dicts
        records = [d.to_dict() for d in dados]
        df = pd.DataFrame(records)
        
        if df.empty: return df
        
        # Adaptação para esquema do P&L (utils_financeiro)
        # Colunas esperadas: codigo_centro_gasto, centro_gasto_nome, conta_contabil, mes, tipo_valor, valor, ano, data
        
        # Mapeamento
        df['tipo_valor'] = 'Realizado' # Banco só guarda realizado
        # centro_gasto_nome vem de 'centro_gasto_descricao' ou 'regional/base'? 
        # No upload, vem do map. Aqui, temos descricao.
        # Vamos usar a descrição salva.
        if 'centro_gasto_descricao' in df.columns:
            df.rename(columns={'centro_gasto_descricao': 'centro_gasto_nome'}, inplace=True)
            
        # map meses number
        MESES_NUM = {'JAN':1, 'FEV':2, 'MAR':3, 'ABR':4, 'MAI':5, 'JUN':6, 
                     'JUL':7, 'AGO':8, 'SET':9, 'OUT':10, 'NOV':11, 'DEZ':12}
        
        df['mes_num'] = df['mes'].map(MESES_NUM)
        
        # Criar data
        def make_date(row):
            try:
                return datetime(row['ano'], row['mes_num'], 1)
            except:
                return None
        
        df['data'] = df.apply(make_date, axis=1)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar histórico do banco: {e}")
        return pd.DataFrame()
    finally:
        session.close()

df_orc_base, df_centros_base, df_contas_base = load_static_data()

df_orc_base, df_centros_base, df_contas_base = load_static_data()

# =============================================================================
# UNIFICAÇÃO DE DADOS (DB + Session)
# =============================================================================

@st.cache_data(ttl=600, show_spinner="Carregando histórico unificado...")
def get_unified_history():
    """Retorna DF unificado do Banco (2024/25) e Session (Upload Atual)."""
    # 1. Carrega do Banco
    df_db = load_pl_from_db()
    if not df_db.empty:
        df_db['origem_dado'] = 'Banco de Dados (Persistido)'
    
    return df_db

# 1. Dados Persistidos
pl_df_db = get_unified_history()

# 2. Dados da Sessão (Uploads recentes)
pl_df_session = st.session_state.get('pl_df')
if pl_df_session is not None and not pl_df_session.empty:
    pl_df_session = pl_df_session.copy()
    pl_df_session['origem_dado'] = 'Sessão Atual (Upload)'

# 3. Merge Inteligente
# Prioridade: Sessão > Banco (para anos que coincidem, assumimos que o upload é mais novo)
# Mas o usuário pediu para carregar 2024/2025 no banco. Se ele subir 2025 de novo, usa sessão.
if pl_df_session is not None and not pl_df_session.empty:
    if not pl_df_db.empty:
        # Se temos ambos, concatenamos.
        # Estratégia simples: Concatenar tudo. O filtro de ano resolverá a visualização.
        # (Opcional: Remover do DB se ano existir na sessão? Por enquanto, mantemos tudo)
        # Melhor: Se ano X está na sessão, remove X do DB para não duplicar na visualização.
        
        anos_sessao = pl_df_session['ano'].unique()
        df_db_filtered = pl_df_db[~pl_df_db['ano'].isin(anos_sessao)]
        
        pl_df_final = pd.concat([df_db_filtered, pl_df_session], ignore_index=True)
    else:
        pl_df_final = pl_df_session
else:
    pl_df_final = pl_df_db

# Salvar no contexto local para visualização
df_hist_view = pl_df_final


# =============================================================================
# TABS PRINCIPAIS
# =============================================================================

tab_orc, tab_hist, tab_meta = st.tabs([
    "💰 Orçamento Base 2026",
    "🕰️ Histórico Realizado",
    "🗂️ Metadados (Estrutura)"
])

# -----------------------------------------------------------------------------
# ABA 1: ORÇAMENTO BASE 2026
# -----------------------------------------------------------------------------
with tab_orc:
    st.markdown("### Orçamento Aprovado (V1) - 2026")
    
    if not df_orc_base.empty:
        # KPIs Rápidos
        cols_orc = [c for c in df_orc_base.columns if c in ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ']]
        if not cols_orc:
             # Tentar mapear se estiverem como jan/26 etc
             # Mas referencias_manager diz que retorna jan/26 a dez/26 ou JAN..DEZ?
             # Docstring diz: "Valores mensais: jan/26 a dez/26"
             # Vamos verificar as colunas
             cols_orc = [c for c in df_orc_base.columns if any(m.lower() in c.lower() for m in MESES_ORDEM)]
        
        total_orc = df_orc_base[cols_orc].sum().sum()
        total_linhas = len(df_orc_base)
        centros_unicos = df_orc_base['CENTRO DE GASTO'].nunique() if 'CENTRO DE GASTO' in df_orc_base.columns else 0
        
        c1, c2, c3 = st.columns(3)
        with c1: exibir_kpi_card("Total Orçado 2026", formatar_valor_brl(total_orc), "Base V1")
        with c2: exibir_kpi_card("Itens de Custo", str(total_linhas), "Linhas Orçamentárias")
        with c3: exibir_kpi_card("Centros de Custo", str(centros_unicos), "Com Orçamento")
        
        st.divider()
        
        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            search_term = st.text_input("🔍 Buscar (Centro, Conta, Fornecedor, Descrição)", "")
        with col_f2:
            ver_detalhe_mes = st.toggle("Ver abertura mensal", value=False)
            
        # Filtragem
        df_show = df_orc_base.copy()
        if search_term:
            s = search_term.lower()
            mask = df_show.astype(str).apply(lambda x: x.str.lower().str.contains(s)).any(axis=1)
            df_show = df_show[mask]
        
        if not ver_detalhe_mes:
            # Esconder meses individuais para limpar a vista
            cols_to_hide = [c for c in cols_orc]
            df_show['Total Anual'] = df_show[cols_to_hide].sum(axis=1)
            # Reordenar: Dados cadastrais + Total
            cols_cadastrais = [c for c in df_show.columns if c not in cols_to_hide and c != 'Total Anual']
            df_show = df_show[cols_cadastrais + ['Total Anual']]
            
            # Formatação
            st.dataframe(
                df_show.style.format({'Total Anual': 'R$ {:,.2f}'}),
                use_container_width=True,
                height=500
            )
        else:
            st.dataframe(df_show, use_container_width=True, height=500)
            
    else:
        st.error("Base de orçamento 2026 não encontrada ou vazia.")

# -----------------------------------------------------------------------------
# ABA 2: HISTÓRICO REALIZADO
# -----------------------------------------------------------------------------
with tab_hist:
    st.markdown("### 🕰️ Histórico Realizado (P&L)")
    
    
    if df_hist_view is not None and not df_hist_view.empty:
        # Filtro de Ano
        anos_disponiveis = sorted(df_hist_view['ano'].unique().tolist()) if 'ano' in df_hist_view.columns else []
        anos_selecionados = st.multiselect("📅 Filtrar Anos", anos_disponiveis, default=anos_disponiveis)
        
        if anos_selecionados:
            df_table = df_hist_view[df_hist_view['ano'].isin(anos_selecionados)]
        else:
            df_table = df_hist_view
            
        # Resumo KPI
        # Conta combinações únicas de Ano+Mes para refletir total de meses carregados (ex: 12 de 2024 + 12 de 2025 = 24)
        meses_hist = df_table[['ano', 'mes']].drop_duplicates().shape[0] if {'ano', 'mes'}.issubset(df_table.columns) else 0
        total_hist = df_table.query("tipo_valor == 'Realizado'")['valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        with c1: exibir_kpi_card("Total Realizado", formatar_valor_brl(total_hist), f"Anos: {anos_selecionados}")
        with c2: exibir_kpi_card("Meses Carregados", str(meses_hist), "Meses Fechados")
        with c3: exibir_kpi_card("Registros", f"{len(df_table):,}", "Linhas P&L")
        
        st.divider()
        
        st.dataframe(df_table, use_container_width=True, height=500)
        
    else:
        st.warning("⚠️ Nenhum histórico carregado na sessão.")
        st.markdown("""
        Para visualizar o histórico:
        1. Vá para a página **Home** 🏠
        2. Faça upload do arquivo de **P&L (Realizado)** selecionando o ano correto.
        3. Você pode carregar múltiplos anos (ex: 2024, 2025, 2026) sequencialmente.
        4. Retorne a esta aba para conferir os dados consolidados.
        """)

# -----------------------------------------------------------------------------
# ABA 3: METADADOS (ESTRUTURA)
# -----------------------------------------------------------------------------
with tab_meta:
    sub_tab1, sub_tab2 = st.tabs(["🏢 Centros de Custo", "🧾 Plano de Contas"])
    
    with sub_tab1:
        st.markdown(f"**Total de Centros:** {len(df_centros_base)}")
        st.dataframe(df_centros_base, use_container_width=True, height=600)
        
    with sub_tab2:
        st.markdown(f"**Total de Contas:** {len(df_contas_base)}")
        st.dataframe(df_contas_base, use_container_width=True, height=600)

