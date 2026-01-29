"""
05_🧱_Controle_Orcamentario.py
==============================
Módulo de Controle Orçamentário (Features B, D, E).
Gestão de Provisões, Remanejamentos e Justificativas (OBZ).
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from services.provisioning_service import ProvisioningService
from services.budget_control import BudgetControlService
from data.referencias_manager import carregar_centros_gasto
from database.models import get_session, LancamentoRealizado
from utils_financeiro import MESES_ORDEM

st.set_page_config(
    page_title="Controle Orçamentário",
    page_icon="🧱",
    layout="wide"
)

st.title("🧱 Controle e Governança Orçamentária")
st.markdown("---")

# Serviços
prov_service = ProvisioningService()
budget_service = BudgetControlService()

# Carregar Referências
df_centros = carregar_centros_gasto()
lista_centros = df_centros['codigo'].unique().tolist() if not df_centros.empty else []
lista_centros_fmt = [f"{c} - {df_centros[df_centros['codigo']==c]['descricao'].iloc[0]}" for c in lista_centros]
map_centro_desc = {c: desc for c, desc in zip(lista_centros, lista_centros_fmt)}

tabs = st.tabs(["📋 Gestão de Provisões (Feature B)", "🔄 Remanejamentos (Feature D)", "🛡️ Justificativa OBZ (Feature E)"])

# =============================================================================
# ABA 1: GESTÃO DE PROVISÕES (FEATURE B)
# =============================================================================
with tabs[0]:
    st.header("Gestão de Provisões e Passivos (IAS 37)")
    st.caption("Registre despesas estimadas (obrigações presentes) e concilie quando realizadas.")
    
    col_form, col_list = st.columns([1, 3])
    
    with col_form:
        st.subheader("Nova Provisão")
        with st.form("form_provisao"):
            desc_prov = st.text_input("Descrição da Obrigação")
            valor_prov = st.number_input("Valor Estimado (R$)", min_value=0.0, format="%.2f")
            centro_prov = st.selectbox("Centro de Custo", lista_centros, format_func=lambda x: map_centro_desc.get(x, x))
            conta_prov = st.text_input("Conta Contábil (Código)") # Ideal seria dropdown
            mes_prov = st.selectbox("Mês Competência", MESES_ORDEM)
            tipo_despesa = st.selectbox("Tipo", ["Variavel", "Fixa", "Emergencial"])
            justif_prov = st.text_area("Justificativa")
            
            if st.form_submit_button("Registrar Provisão"):
                try:
                    prov_service.criar_provisao({
                        "descricao": desc_prov,
                        "valor_estimado": valor_prov,
                        "centro_gasto_codigo": centro_prov,
                        "conta_contabil_codigo": conta_prov,
                        "mes_competencia": mes_prov,
                        "tipo_despesa": tipo_despesa,
                        "justificativa_obz": justif_prov,
                        "usuario": "UsuarioAtual" # Mock
                    })
                    st.success("Provisão registrada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    with col_list:
        st.subheader("Provisões Ativas")
        
        filtro_status = st.selectbox("Status", ["TODOS", "PENDENTE", "REALIZADA", "CANCELADA"], index=1)
        
        lista_prov = prov_service.listar_provisoes(status=None if filtro_status=="TODOS" else filtro_status)
        
        if lista_prov:
            df_prov = pd.DataFrame(lista_prov)
            st.dataframe(
                df_prov[['id', 'descricao', 'valor_estimado', 'mes_competencia', 'status', 'centro_gasto_codigo']],
                use_container_width=True
            )
            
            # Ação de Conciliação
            st.divider()
            col_conciliacao, col_cancel = st.columns(2)
            
            with col_conciliacao:
                st.markdown("#### 🔗 Conciliar Provisão")
                prov_id_sel = st.selectbox("Selecione ID para Conciliar", [p['id'] for p in lista_prov if p['status']=='PENDENTE'])
                
                if prov_id_sel:
                    # Buscar lançamentos candidatos (mesmo mês e centro)
                    prov_selecionada = next(p for p in lista_prov if p['id'] == prov_id_sel)
                    
                    # Buscar no banco (query simples)
                    session = get_session()
                    candidatos = session.query(LancamentoRealizado).filter(
                        LancamentoRealizado.mes == prov_selecionada['mes_competencia'],
                        LancamentoRealizado.centro_gasto_codigo == prov_selecionada['centro_gasto_codigo']
                    ).all()
                    session.close()
                    
                    opcoes_lanc = [f"{l.id} | R$ {l.valor} | {l.fornecedor}" for l in candidatos]
                    lanc_sel_str = st.selectbox("Vincular ao Lançamento Recente:", ["Selecione..."] + opcoes_lanc)
                    
                    if st.button("Confirmar Conciliação") and lanc_sel_str != "Selecione...":
                        lanc_id = int(lanc_sel_str.split('|')[0].strip())
                        try:
                            prov_service.conciliar_provisao(prov_id_sel, lanc_id)
                            st.success(f"Provisão {prov_id_sel} conciliada com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

            with col_cancel:
                st.markdown("#### 🗑️ Reverter/Cancelar")
                prov_id_cancel = st.selectbox("Selecione ID para Cancelar", [p['id'] for p in lista_prov if p['status']=='PENDENTE'], key='cancel_sel')
                motivo_cancel = st.text_input("Motivo do Cancelamento")
                
                if st.button("Cancelar Provisão"):
                    if motivo_cancel:
                        prov_service.cancelar_provisao(prov_id_cancel, motivo_cancel)
                        st.success("Cancelado.")
                        st.rerun()
                    else:
                        st.warning("Informe o motivo.")
        else:
            st.info("Nenhuma provisão encontrada.")

# =============================================================================
# ABA 2: REMANEJAMENTOS (FEATURE D)
# =============================================================================
with tabs[1]:
    st.header("Remanejamento Orçamentário")
    st.caption("Solicite e aprove transferências de saldo entre centros de custo.")
    
    col_req, col_hist = st.columns([1, 2])
    
    with col_req:
        st.subheader("Solicitar Transferência")
        with st.form("form_remanejamento"):
            origem = st.selectbox("Centro Origem", lista_centros, format_func=lambda x: map_centro_desc.get(x, x), key='orig')
            destino = st.selectbox("Centro Destino", lista_centros, format_func=lambda x: map_centro_desc.get(x, x), key='dest')
            valor_transf = st.number_input("Valor (R$)", min_value=0.0)
            mes_transf = st.selectbox("Mês Referência", MESES_ORDEM, key='mes_transf')
            justif_transf = st.text_area("Justificativa Econômica")
            
            if st.form_submit_button("Solicitar Aprovação"):
                if origem == destino:
                    st.error("Origem e Destino devem ser diferentes.")
                else:
                    try:
                        budget_service.solicitar_remanejamento({
                            "centro_origem": origem,
                            "centro_destino": destino,
                            "valor": valor_transf,
                            "mes": mes_transf,
                            "justificativa": justif_transf,
                            "solicitante": "UsuarioAtual"
                        })
                        st.success("Solicitação enviada para workflow!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with col_hist:
        st.subheader("Histórico de Solicitações")
        reqs = budget_service.listar_remanejamentos()
        
        if reqs:
            df_reqs = pd.DataFrame(reqs)
            
            # Workflow Mock
            st.dataframe(df_reqs[['id', 'origem', 'destino', 'valor', 'status', 'justificativa']], use_container_width=True)
            
            st.markdown("#### 👮 Área de Aprovação")
            pendentes = [r for r in reqs if r['status'] == 'SOLICITADO']
            
            if pendentes:
                req_aprovar = st.selectbox("Selecione Solicitação Pendente", [f"{r['id']} - R$ {r['valor']} ({r['origem']}->{r['destino']})" for r in pendentes])
                id_aprov = int(req_aprovar.split('-')[0].strip())
                
                col_yes, col_no = st.columns(2)
                if col_yes.button("✅ APROVAR"):
                    budget_service.aprovar_remanejamento(id_aprov, "Admin")
                    st.balloons()
                    st.rerun()
                
                if col_no.button("❌ REJEITAR"):
                    budget_service.rejeitar_remanejamento(id_aprov, "Admin (Motivo Genérico)")
                    st.rerun()
            else:
                st.success("Nenhuma solicitação pendente.")
        else:
            st.info("Nenhum histórico.")

# =============================================================================
# ABA 3: JUSTIFICATIVA OBZ (FEATURE E)
# =============================================================================
with tabs[2]:
    st.header("Justificativa Base Zero (OBZ Light)")
    st.markdown("""
    Nesta visualização, analise os gastos históricos e classifique-os por essencialidade. 
    O objetivo é eliminar desperdícios e garantir que cada centavo gere valor.
    """)
    
    st.info("🚧 Em construção: Esta funcionalidade será integrada aos dados de P&L históricos na próxima iteração.")
    
    # Mock visual
    st.subheader("Matriz de Essencialidade")
    df_mock = pd.DataFrame({
        "Pacote": ["Viagens", "Treinamento", "Software", "Eventos"],
        "Valor Orçado (Base Histórica)": [50000, 20000, 15000, 10000], 
        "Justificativa": ["Necessário visita técnica", "Upskilling equipe", "Licença obrigatória", "Team building"],
        "Score Essencialidade": ["Alto", "Médio", "Crítico", "Baixo"]
    })
    st.dataframe(df_mock, use_container_width=True)
