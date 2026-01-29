import streamlit as st
import pandas as pd
from datetime import datetime
from services.provisioning_service import ProvisioningService
from data.referencias_manager import (
    carregar_centros_gasto,
    carregar_contas_contabeis,
    get_hierarquia_centro,
    get_ativos_unicos,
    MAPA_CLASSES,
    MESES_ORDEM
)
from utils_ui import setup_page, formatar_valor_brl

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Gestão de Compromissos", "📝")

st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #f1f5f9; font-size: 36px; margin-bottom: 8px;">
        📝 Registro de Compromissos
    </h1>
    <p style="color: #94a3b8; font-size: 16px;">
        Gestão de Provisões e Obrigações Financeiras (IAS 37)
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Serviços e Dados
try:
    prov_service = ProvisioningService()
    df_centros = carregar_centros_gasto()
    df_contas = carregar_contas_contabeis()
except Exception as e:
    st.error(f"Erro ao inicializar serviços: {e}")
    st.stop()

# Inicializar Session State
if 'sucesso_prov' not in st.session_state:
    st.session_state.sucesso_prov = None

# =============================================================================
# UI HELPER: HIERARQUIA
# =============================================================================

def exibir_hierarquia_card(hierarquia):
    if not hierarquia.get('encontrado'):
        return

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%); border-left: 4px solid #00d4aa; padding: 16px; border-radius: 8px; margin-top: 20px;">
        <div style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">Hierarquia do Centro</div>
        <div style="color: white; font-weight: bold; margin-top: 4px;">{hierarquia.get('codigo')} - {hierarquia.get('descricao')}</div>
        <div style="color: #cbd5e1; font-size: 14px; margin-top: 4px;">
            🏢 Ativo: <span style="color: #00d4aa;">{hierarquia.get('ativo')}</span>
             • Pai: {hierarquia.get('codigo_pai')}
        </div>
        <div style="color: #94a3b8; font-size: 12px; margin-top: 8px;">
            {hierarquia.get('classe')} - {hierarquia.get('classe_nome')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# TABS
# =============================================================================

tab_novo, tab_lista = st.tabs(["➕ Nova Provisão", "📋 Compromissos Ativos"])

# =============================================================================
# TAB: NOVA PROVISÃO
# =============================================================================
with tab_novo:
    if st.session_state.sucesso_prov:
        st.success(st.session_state.sucesso_prov)
        st.session_state.sucesso_prov = None

    with st.container():
        st.markdown('<div class="section-header"><span class="section-title">Cadastrar Obrigação</span></div>', unsafe_allow_html=True)
        
        with st.form("form_provisao", clear_on_submit=True):
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                descricao = st.text_input("Descrição do Compromisso", placeholder="Ex: Manutenção Preventiva Compressores")
                fornecedor = st.text_input("Fornecedor (Opcional)", placeholder="Razão Social ou Nome")
            
            with col_a2:
                valor = st.number_input("Valor Estimado (R$)", min_value=0.0, step=100.0, format="%.2f")
                tipo_despesa = st.selectbox("Classificação", ["Variavel", "Fixa", "Emergencial"])

            st.markdown("#### 📅 Competência e Alocação")
            col_b1, col_b2, col_b3 = st.columns(3)
            
            with col_b1:
                mes = st.selectbox("Mês Competência", MESES_ORDEM)
            
            with col_b2:
                # Selectbox inteligente para centros
                opcoes_centros = []
                if not df_centros.empty:
                    opcoes_centros = df_centros.apply(lambda x: f"{x['codigo']} - {x['descricao']}", axis=1).tolist()
                
                centro_sel = st.selectbox("Centro de Custo", options=opcoes_centros, placeholder="Selecione...", index=None)

            with col_b3:
                # Selectbox inteligente para contas
                opcoes_contas = []
                if not df_contas.empty:
                    opcoes_contas = df_contas.apply(lambda x: f"{x['codigo']} - {x['descricao']}", axis=1).tolist()
                    
                conta_sel = st.selectbox("Conta Contábil", options=opcoes_contas, placeholder="Selecione...", index=None)

            # Hierarquia Preview
            if centro_sel:
                cod_centro = centro_sel.split(' - ')[0]
                h = get_hierarquia_centro(cod_centro, df_centros)
                exibir_hierarquia_card(h)

            justificativa = st.text_area("Justificativa / Detalhes (OBZ)", placeholder="Por que este gasto é necessário?", height=100)

            st.markdown("---")
            if st.form_submit_button("💾 Registrar Compromisso", type="primary", use_container_width=True):
                # Validação
                erros = []
                if not descricao: erros.append("Descrição obrigatória")
                if valor <= 0: erros.append("Valor deve ser maior que zero")
                if not centro_sel: erros.append("Centro de Custo obrigatório")
                if not conta_sel: erros.append("Conta Contábil obrigatória")

                if erros:
                    for e in erros: st.error(f"❌ {e}")
                else:
                    try:
                        dados = {
                            "descricao": f"{descricao} ({fornecedor})" if fornecedor else descricao,
                            "valor_estimado": valor,
                            "centro_gasto_codigo": centro_sel.split(' - ')[0],
                            "conta_contabil_codigo": conta_sel.split(' - ')[0],
                            "mes_competencia": mes,
                            "tipo_despesa": tipo_despesa,
                            "justificativa_obz": justificativa,
                            "usuario": "Sistema" 
                        }
                        prov_service.criar_provisao(dados)
                        st.session_state.sucesso_prov = "✅ Provisão registrada com sucesso!"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

# =============================================================================
# TAB: LISA
# =============================================================================
with tab_lista:
    st.markdown('<div class="section-header"><span class="section-title">Compromissos em Aberto</span></div>', unsafe_allow_html=True)
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_mes = st.selectbox("Filtrar Mês", ["Todos"] + MESES_ORDEM)
    with col_f2:
        filtro_status = st.selectbox("Status", ["TODOS", "PENDENTE", "REALIZADA", "CANCELADA"], index=1)

    lista = prov_service.listar_provisoes(
        status=None if filtro_status == "TODOS" else filtro_status,
        mes=None if filtro_mes == "Todos" else filtro_mes
    )

    if lista:
        df = pd.DataFrame(lista)
        
        # Formatação para exibição
        df['Valor'] = df['valor_estimado'].apply(formatar_valor_brl)
        
        st.dataframe(
            df[['id', 'mes_competencia', 'descricao', 'centro_gasto_codigo', 'status', 'Valor']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("#", width="small"),
                "mes_competencia": st.column_config.TextColumn("Mês", width="small"),
                "descricao": "Descrição",
                "centro_gasto_codigo": "Centro",
                "status": st.column_config.TextColumn("Status", width="small"),
                "Valor": st.column_config.TextColumn("Valor", width="medium"),
            }
        )
        
        # Ações Rápidas
        st.markdown("#### ⚡ Ações Rápidas")
        col_act1, col_act2 = st.columns(2)
        
        pendentes = [p for p in lista if p['status'] == 'PENDENTE']
        opcoes_pendentes = [f"{p['id']} - {p['descricao']}" for p in pendentes]
        
        with col_act1:
            if opcoes_pendentes:
                sel_canc = st.selectbox("Cancelar Item", opcoes_pendentes, key="sel_canc")
                motivo = st.text_input("Motivo Cancelamento")
                if st.button("🗑️ Cancelar"):
                    if motivo:
                        pid = int(sel_canc.split(' - ')[0])
                        prov_service.cancelar_provisao(pid, motivo)
                        st.success("Cancelado!")
                        st.rerun()
                    else:
                        st.warning("Motivo obrigatório")
        
        with col_act2:
            st.info("ℹ️ Para conciliar com realizado, aguarde a carga do P&L.")

    else:
        st.info("📭 Nenhum registro encontrado.")
