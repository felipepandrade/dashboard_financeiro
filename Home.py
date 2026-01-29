import streamlit as st
import pandas as pd
from pathlib import Path
from utils_financeiro import (
    verificar_status_dados,
    processar_upload_pl,
    get_resumo_importacao
)
from utils_ui import setup_page, exibir_kpi_card, formatar_valor_brl

# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================

setup_page("Home - Baseal Planejamento", "🏠")

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div style="text-align: center; padding: 40px 0;">
    <h1 style="color: #f1f5f9; font-size: 42px; font-weight: 800; margin-bottom: 12px;">
        🚀 Dashboard Financeiro 2026
    </h1>
    <p style="color: #94a3b8; font-size: 18px; max_width: 600px; margin: 0 auto;">
        Sistema integrado de planejamento, controle orçamentário e acompanhamento de resultados.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# STATUS DO SISTEMA
# =============================================================================

status = verificar_status_dados()

col1, col2, col3 = st.columns(3)

with col1:
    cor_orc = "✅" if status['orcamento_ok'] else "❌"
    exibir_kpi_card(
        "Status Orçamento 2026", 
        f"{cor_orc} Carregado" if status['orcamento_ok'] else "Pendente",
        f"{status['orcamento_linhas']} registros"
    )

with col2:
    cor_pl = "✅" if status['pl_ok'] else "⚠️"
    exibir_kpi_card(
        "Dados Realizados (P&L)",
        f"{cor_pl} Atualizado", 
        f"Última carga: {status['pl_data']}" if status['pl_data'] else "Sem dados"
    )

with col3:
    exibir_kpi_card(
        "Mês de Fechamento",
        status['mes_atual'] if status['mes_atual'] else "N/D",
        "Referência Atual"
    )

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# AÇÕES PRINCIPAIS (UPLOAD P&L)
# =============================================================================

st.markdown('<div class="section-header"><span class="section-title">📥 Carga de Dados (Fechamento)</span></div>', unsafe_allow_html=True)

col_upload, col_info = st.columns([1, 1])

with col_upload:
    st.info("ℹ️ Utilize esta área para carregar o **P&L Oficial** (Razão/Balancete) exportado do ERP para conciliação mensal.")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo de P&L (Excel/CSV)", 
        type=['xlsx', 'xls', 'csv'],
        key="upload_pl"
    )
    
    if uploaded_file:
        with st.spinner("Processando P&L..."):
            sucesso, msg, detalhes = processar_upload_pl(uploaded_file)
            
            if sucesso:
                st.success(f"✅ {msg}")
                st.json(detalhes)
                st.balloons()
            else:
                st.error(f"❌ {msg}")

with col_info:
    
    resumo = get_resumo_importacao()
    if resumo:
        st.markdown("#### 📊 Última Importação")
        st.write(resumo)
    
    # Visualizador de Orçamento
    dados_orcamento = st.session_state.get('df_orc_proc')
    if dados_orcamento is not None:
        with st.expander("🔍 Visualizar Dados Orçamentários (2026)", expanded=False):
            st.dataframe(dados_orcamento, use_container_width=True)
            st.caption(f"Total de registros: {len(dados_orcamento)}")

# =============================================================================
# RODAPÉ
# =============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 12px;">
    Dashboard Financeiro v2.0 • Baseal 2026 • Desenvolvido com Streamlit & Python
</div>
""", unsafe_allow_html=True)
