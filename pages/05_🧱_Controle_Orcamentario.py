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
# =============================================================================
# ABA 2: JUSTIFICATIVA OBZ (FEATURE E)
# =============================================================================
with tab_obz:
    st.markdown('<div class="section-header"><span class="section-title">🛡️ Justificativa Base Zero (OBZ)</span></div>', unsafe_allow_html=True)
    
    # Seletor de Centro para OBZ (pode ser diferente do remanejamento)
    col_sel_obz, col_info_obz = st.columns([1, 2])
    with col_sel_obz:
        centro_obz = st.selectbox("Selecione o Centro de Custo", lista_centros, format_func=lambda x: map_centro_desc.get(x, x), key='centro_obz')
    
    if centro_obz:
        # 1. Integração com Detalhes Operacionais (Lançamentos)
        with st.expander("🔎 Detalhes Operacionais (Provisões Lançadas)", expanded=False):
            detalhes = budget_service.get_detalhes_operacionais(centro_obz)
            if detalhes:
                df_det = pd.DataFrame(detalhes)
                df_det['Valor'] = df_det['valor'].apply(formatar_valor_brl)
                st.dataframe(
                    df_det[['descricao', 'Valor', 'justificativa_item', 'tipo']],
                    use_container_width=True,
                    column_config={
                        "descricao": "Item / Fornecedor",
                        "justificativa_item": "Justificativa Operacional (Lançamentos)",
                        "tipo": st.column_config.TextColumn("Tipo", width="small"),
                        "Valor": st.column_config.TextColumn("Valor", width="small"),
                    }
                )
                total_op = df_det['valor'].sum()
                st.caption(f"Total Operacional Lançado: {formatar_valor_brl(total_op)}")
            else:
                st.info("Nenhuma provisão lançada para este centro.")

        st.markdown("---")

        # 2. Gerenciamento de Pacotes OBZ
        col_form_obz, col_view_obz = st.columns([1, 2])
        
        with col_form_obz:
            st.markdown("#### 📦 Novo Pacote de Decisão")
            with st.form("form_obz_pack", clear_on_submit=True):
                pacote_nome = st.text_input("Nome do Pacote", placeholder="Ex: Viagens, TI, Consultoria")
                valor_pack = st.number_input("Valor Orçado (R$)", min_value=0.0, step=1000.0, format="%.2f")
                classificacao = st.selectbox("Classificação / Criticidade", [
                    "Obrigatório (Legal/Compliance)", 
                    "Estratégico (Crescimento)", 
                    "Necessário (Operação)", 
                    "Desejável (Melhoria)"
                ])
                desc_pack = st.text_area("Defesa do Pacote", placeholder="Justifique a necessidade deste pacote baseando-se nos detalhes operacionais...", height=150)
                
                resp = st.text_input("Responsável", value="Gestor Atual")
                
                if st.form_submit_button("Salvar Pacote", type="primary", use_container_width=True):
                    if not pacote_nome or valor_pack <= 0 or not desc_pack:
                        st.error("Preencha todos os campos obrigatórios.")
                    else:
                        budget_service.salvar_justificativa_obz({
                            "centro_gasto_codigo": centro_obz,
                            "pacote": pacote_nome,
                            "valor_orcado": valor_pack,
                            "classificacao": classificacao,
                            "descricao": desc_pack,
                            "usuario_responsavel": resp
                        })
                        st.success("Pacote salvo com sucesso!")
                        st.rerun()

        with col_view_obz:
            st.markdown("#### 📊 Matriz de Essencialidade")
            
            # Listar Pacotes
            pacotes = budget_service.listar_justificativas_obz(centro_obz)
            
            if pacotes:
                df_packs = pd.DataFrame(pacotes)
                
                # Gráfico de Dispersão (Matriz)
                import plotly.express as px
                
                # Mapear cores para classificação
                color_map = {
                    "Obrigatório (Legal/Compliance)": "#ef4444", # Red
                    "Estratégico (Crescimento)": "#3b82f6", # Blue
                    "Necessário (Operação)": "#f59e0b", # Amber
                    "Desejável (Melhoria)": "#10b981"  # Emerald
                }
                
                fig = px.scatter(
                    df_packs, 
                    x="valor_orcado", 
                    y="classificacao", 
                    size="valor_orcado", 
                    color="classificacao",
                    hover_data=["pacote", "descricao"],
                    color_discrete_map=color_map,
                    title="Matriz Valor x Criticidade",
                    labels={"valor_orcado": "Valor Orçado", "classificacao": "Criticidade"}
                )
                fig.update_layout(height=350, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela Resumo
                st.markdown("#### Pacotes Cadastrados")
                for p in pacotes:
                    with st.expander(f"📦 {p['pacote']} - {formatar_valor_brl(p['valor_orcado'])} ({p['classificacao']})"):
                        st.write(p['descricao'])
                        st.caption(f"Responsável: {p['usuario_responsavel']} | Atualizado em: {p['data_atualizacao']}")
            else:
                st.info("Nenhum pacote cadastrado para este centro.")
    else:
        st.warning("Selecione um Centro de Custo para iniciar a justificativa OBZ.")

