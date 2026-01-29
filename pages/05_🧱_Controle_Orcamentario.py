import streamlit as st
import pandas as pd
from datetime import datetime
from services.budget_control import BudgetControlService
from data.referencias_manager import carregar_centros_gasto, MESES_ORDEM
from utils_ui import setup_page, formatar_valor_brl

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Controle Orçamentário", "🧱")

st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #f1f5f9; font-size: 36px; margin-bottom: 8px;">
        🧱 Governança Orçamentária
    </h1>
    <p style="color: #94a3b8; font-size: 16px;">
        Gestão de Remanejamentos (Transposições) e Justificativas de Base Zero
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Serviços
try:
    budget_service = BudgetControlService()
    df_centros = carregar_centros_gasto()
    
    # Preparar listas para dropdowns
    lista_centros = []
    map_centro_desc = {}
    if not df_centros.empty:
        lista_centros = df_centros['codigo'].unique().tolist()
        for idx, row in df_centros.iterrows():
             map_centro_desc[row['codigo']] = f"{row['codigo']} - {row['descricao']}"
except Exception as e:
    st.error(f"Erro ao inicializar serviços: {e}")
    st.stop()

# =============================================================================
# TABS
# =============================================================================

tab_remanejamento, tab_obz = st.tabs(["🔄 Solicitar Remanejamento", "🛡️ Justificativa OBZ"])

# =============================================================================
# ABA 1: REMANEJAMENTOS (FEATURE D)
# =============================================================================
with tab_remanejamento:
    st.markdown('<div class="section-header"><span class="section-title">Transferências de Saldo</span></div>', unsafe_allow_html=True)
    
    col_req, col_hist = st.columns([1, 2])
    
    with col_req:
        st.markdown("#### 📝 Nova Solicitação")
        st.info("Utilize para transferir saldo disponível entre centros de custo.")
        
        with st.form("form_remanejamento", clear_on_submit=True):
            origem = st.selectbox("Centro Origem (De)", lista_centros, format_func=lambda x: map_centro_desc.get(x, x), key='orig')
            destino = st.selectbox("Centro Destino (Para)", lista_centros, format_func=lambda x: map_centro_desc.get(x, x), key='dest')
            
            valor_transf = st.number_input("Valor (R$)", min_value=0.0, step=1000.0, format="%.2f")
            mes_transf = st.selectbox("Mês de Referência", MESES_ORDEM, key='mes_transf')
            
            justif_transf = st.text_area("Justificativa Técnica/Econômica", placeholder="Motivo da transferência...")
            
            submitted = st.form_submit_button("🚀 Enviar Solicitação", type="primary", use_container_width=True)
            
            if submitted:
                if origem == destino:
                    st.error("❌ Origem e Destino devem ser diferentes.")
                elif valor_transf <= 0:
                    st.error("❌ Valor deve ser maior que zero.")
                elif not justif_transf:
                    st.error("❌ Justificativa obrigatória.")
                else:
                    try:
                        budget_service.solicitar_remanejamento({
                            "centro_origem": origem,
                            "centro_destino": destino,
                            "valor": valor_transf,
                            "mes": mes_transf,
                            "justificativa": justif_transf,
                            "solicitante": "UsuarioAtual" # Implementar auth real futuramente
                        })
                        st.success("✅ Solicitação enviada para aprovação!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao processar: {e}")

    with col_hist:
        st.markdown("#### 📜 Histórico & Aprovações")
        reqs = budget_service.listar_remanejamentos()
        
        if reqs:
            df_reqs = pd.DataFrame(reqs)
            
            # Formatar para exibição
            df_reqs['Valor'] = df_reqs['valor'].apply(formatar_valor_brl)
            
            st.dataframe(
                df_reqs[['id', 'origem', 'destino', 'Valor', 'status', 'justificativa']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("#", width="small"),
                    "origem": "Origem",
                    "destino": "Destino",
                    "Valor": "Valor",
                    "status": st.column_config.TextColumn("Status", width="small"),
                    "justificativa": "Justificativa"
                }
            )
            
            # Área de Aprovação (Simulação de Admin)
            st.markdown("---")
            st.markdown("#### 👮 Painel do Aprovador")
            
            pendentes = [r for r in reqs if r['status'] == 'SOLICITADO']
            
            if pendentes:
                col_aprov1, col_aprov2 = st.columns([2, 1])
                
                with col_aprov1:
                    req_aprovar = st.selectbox(
                        "Selecione Solicitação Pendente", 
                        [f"{r['id']} - {formatar_valor_brl(r['valor'])} ({r['origem']} -> {r['destino']})" for r in pendentes]
                    )
                
                if req_aprovar:
                    id_aprov = int(req_aprovar.split(' - ')[0])
                    
                    with col_aprov2:
                        st.markdown("<br>", unsafe_allow_html=True) # Espaçamento
                        col_y, col_n = st.columns(2)
                        if col_y.button("✅ Aprovar", use_container_width=True):
                            budget_service.aprovar_remanejamento(id_aprov, "Admin")
                            st.success(f"Solicitação {id_aprov} aprovada!")
                            st.rerun()
                        
                        if col_n.button("❌ Rejeitar", use_container_width=True):
                            budget_service.rejeitar_remanejamento(id_aprov, "Rejeitado pelo Admin")
                            st.rerun()
            else:
                st.success("✅ Nenhuma solicitação pendente de análise.")
        else:
            st.info("📭 Nenhum histórico de remanejamentos encontrado.")

# =============================================================================
# ABA 2: JUSTIFICATIVA OBZ (FEATURE E)
# =============================================================================
with tab_obz:
    st.markdown('<div class="section-header"><span class="section-title">Justificativa Base Zero (OBZ)</span></div>', unsafe_allow_html=True)
    
    col_obz1, col_obz2 = st.columns([1, 1])
    
    with col_obz1:
        st.markdown("""
        <div style="background-color: #1e293b; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b;">
            <h4 style="color: #f59e0b; margin-top: 0;">🎯 Metodologia OBZ</h4>
            <p>Nesta seção, você deve justificar a necessidade e essencialidade de pacotes de gastos específicos, 
            classificando-os conforme sua criticidade para a operação.</p>
            <p>O objetivo é eliminar desperdícios e garantir alocação eficiente de recursos.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_obz2:
        st.info("🚧 Funcionalidade em desenvolvimento para a Fase 2 (Integração com P&L Histórico).")

    # Mock Visual
    st.markdown("#### Prévia da Matriz de Essencialidade")
    
    df_mock = pd.DataFrame({
        "Pacote de Gastos": ["Viagens Corporativas", "Treinamento Técnico", "Licenças de Software", "Confraternizações"],
        "Valor Orçado 2026": [50000, 20000, 15000, 10000],
        "Classificação OBZ": ["Necessário / Não Crítico", "Estratégico / Crítico", "Obrigatório / Legal", "Desejável"],
        "Ação Recomendada": ["Reduzir 20%", "Manter", "Renegociar", "Cortar"]
    })
    
    df_mock['Valor Orçado 2026'] = df_mock['Valor Orçado 2026'].apply(formatar_valor_brl)
    
    st.dataframe(df_mock, use_container_width=True)

