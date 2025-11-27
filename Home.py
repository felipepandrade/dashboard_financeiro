"""
Home.py
=======
Página inicial do Sistema de Controle Financeiro.
Responsável pelo upload de arquivos e configuração de chaves de API.
"""

import streamlit as st
import pandas as pd
from utils_financeiro import (
    processar_pl_baseal,
    processar_razao_gastos,
    processar_acompanhamento_orcamento_completo
)

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Sistema Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
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
        
        /* Buttons */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
            background: linear-gradient(90deg, #4F8BF9 0%, #9B5DE5 100%);
            border: none;
            color: white;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(79, 139, 249, 0.4);
        }
        
        /* File Uploader */
        .stFileUploader {
            background-color: #161924;
            border-radius: 10px;
            padding: 15px;
            border: 1px dashed #4F8BF9;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #161924;
            border-right: 1px solid #2E3245;
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
        
        .hero-text {
            font-size: 1.2rem;
            color: #B0B3C5;
            line-height: 1.6;
        }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# TÍTULO E INTRODUÇÃO
# =============================================================================

col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("logo_engie.png", width=100)
with col_title:
    st.title("Sistema de Controle Financeiro e Orçamentário")
    st.markdown("### Gerência de O&M de Gasodutos")

st.markdown("---")

col_intro, col_status = st.columns([2, 1])

with col_intro:
    st.markdown("""
    <div class="card">
        <h3>Bem-vindo ao Sistema Financeiro</h3>
        <p class="hero-text">
            Uma plataforma avançada para análise, controle e previsão financeira.
            Utilize o poder da Inteligência Artificial para obter insights estratégicos sobre seus dados de O&M.
        </p>
        <ul>
            <li>📊 <b>Análise de P&L</b>: Comparativo detalhado Realizado vs Budget</li>
            <li>💼 <b>Controle Orçamentário</b>: Monitoramento por base operacional</li>
            <li>📈 <b>Previsão Financeira</b>: Projeções com extrapolação linear e médias móveis</li>
            <li>✓ <b>Auditoria Automática</b>: Validação de qualidade de dados</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# CONFIGURAÇÃO DE API
# =============================================================================

with st.sidebar:
    # Logo ENGIE
    st.image("logo_engie.png", use_column_width=True)
    st.markdown("---")
    st.header("⚙ Configurações")
    
    st.subheader("🔐 Chaves de API (IA)")
    provider = st.selectbox("Provedor de IA", ["Gemini (Google)", "OpenAI (GPT-4)"])
    
    api_key = st.text_input(
        "API Key", 
        type="password", 
        help="Insira sua chave de API para habilitar recursos de IA."
    )
    
    if api_key:
        st.session_state['api_key'] = api_key
        st.session_state['ai_provider'] = provider
        st.success("Chave de API configurada!")
    else:
        st.warning("IA desabilitada (sem chave).")
    
    st.markdown("---")
    st.info("Desenvolvido para análise gerencial.")

# =============================================================================
# UPLOAD DE ARQUIVOS
# =============================================================================

st.subheader("📂 Carregamento de Dados")

col_pl, col_orc = st.columns(2)

# --- Upload P&L ---
with col_pl:
    st.markdown("### 1. Arquivo de P&L (Baseal)")
    file_pl = st.file_uploader("Selecione o arquivo Excel (P&L)", type=['xlsx'], key='upload_pl')
    
    if file_pl:
        if 'pl_file_hash' not in st.session_state or st.session_state.pl_file_hash != file_pl.file_id:
            with st.spinner("Processando P&L e Razão..."):
                # Processar P&L
                df_pl = processar_pl_baseal(file_pl)
                
                # Processar Razão (assumindo que está no mesmo arquivo, conforme prática comum, ou tentar ler)
                # O código original sugere que pode ser o mesmo arquivo ou separado.
                # Vamos tentar ler a aba Razão do mesmo arquivo.
                df_razao = processar_razao_gastos(file_pl)
                
                if not df_pl.empty:
                    st.session_state['pl_df'] = df_pl
                    st.session_state['razao_df'] = df_razao
                    st.session_state['pl_file_hash'] = file_pl.file_id
                    st.success(f"✅ P&L carregado: {len(df_pl)} registros")
                    if not df_razao.empty:
                        st.success(f"✅ Razão carregado: {len(df_razao)} registros")
                else:
                    st.error("Falha ao processar P&L.")
        else:
            st.success("✅ Arquivo já processado.")

# --- Upload Orçamento ---
with col_orc:
    st.markdown("### 2. Arquivo de Orçamento")
    file_orc = st.file_uploader("Selecione o arquivo Excel (Orçamento)", type=['xlsx'], key='upload_orc')
    
    ano_ref = st.number_input("Ano de Referência", min_value=2020, max_value=2030, value=2025)
    
    if file_orc:
        if 'orc_file_hash' not in st.session_state or st.session_state.orc_file_hash != file_orc.file_id:
            with st.spinner("Processando Orçamento..."):
                df_orc = processar_acompanhamento_orcamento_completo(file_orc, ano_ref)
                
                if not df_orc.empty:
                    st.session_state['df_orc_proc'] = df_orc
                    st.session_state['processed_orc_year'] = ano_ref
                    st.session_state['orc_file_hash'] = file_orc.file_id
                    st.success(f"✅ Orçamento carregado: {len(df_orc)} registros")
                else:
                    st.error("Falha ao processar Orçamento.")
        else:
            st.success("✅ Arquivo já processado.")

# =============================================================================
# STATUS DO SISTEMA
# =============================================================================

st.markdown("---")

with col_status:
    st.markdown("### ▪ Status do Sistema")
    
    pl_ok = 'pl_df' in st.session_state and st.session_state.pl_df is not None
    orc_ok = 'df_orc_proc' in st.session_state and st.session_state.df_orc_proc is not None
    
    if pl_ok:
        st.success("✅ Dados Financeiros (P&L) Prontos")
    else:
        st.warning("⚠️ Aguardando P&L")
        
    if orc_ok:
        st.success("✅ Dados Orçamentários Prontos")
    else:
        st.warning("⚠️ Aguardando Orçamento")
    
    if pl_ok or orc_ok:
        st.markdown("### ➡ Vá para a página de **Análise Financeira** no menu lateral.")
        if st.button("Ir para Análise Financeira"):
            st.switch_page("pages/01_📊_Analise_Financeira.py")

