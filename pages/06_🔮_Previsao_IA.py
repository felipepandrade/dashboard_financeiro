"""
04_🔮_Previsao_IA.py
====================
Módulo de Inteligência e Previsão (Features A & C).
Inclui Forecasting Automático e AI Board of Directors.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.forecast_service import ForecastService
from services.ai_board import AIBoard
from services.provisioning_service import ProvisioningService
from data.comparador import get_comparativo_mensal, get_realizado_agregado_por_mes

from utils_ui import setup_page, require_auth

# Configuração da Página
setup_page("Previsão e Inteligência - 2026", "🔮")
require_auth(module='previsao')

# CSS Personalizado Adicional (específico desta página)
st.markdown("""
    <style>
        .board-card {
            background-color: #1E2130;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #2E3245;
            margin-bottom: 10px;
        }
        .persona-title {
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        .cfo { color: #4F8BF9; border-left: 4px solid #4F8BF9; }
        .controller { color: #F59E0B; border-left: 4px solid #F59E0B; }
        .auditor { color: #EF4444; border-left: 4px solid #EF4444; }
        .analyst { color: #10B981; border-left: 4px solid #10B981; }
        .chairman { color: #A78BFA; border: 2px solid #A78BFA; background-color: #2D2B55; }
    </style>
""", unsafe_allow_html=True)

st.title("🔮 Inteligência e Previsão")
st.markdown("---")

# Verificar Chaves de API
if 'api_key' not in st.session_state or not st.session_state['api_key']:
    st.warning("⚠️ **IA Desabilitada:** Insira sua chave de API na Barra Lateral (Sidebar) para habilitar os recursos de inteligência.")
    # Não vamos parar (stop), permitindo ver o Forecast matemático, mas desabilitando o Board.
else:
    st.caption("✅ Inteligência Artificial Ativa")

# Serviços
forecast_service = ForecastService()
prov_service = ProvisioningService()
ai_board = AIBoard(st.session_state['api_key'], st.session_state.get('ai_provider', 'Gemini (Google)'))

tabs = st.tabs(["🤖 AI Board Advisor", "📈 Previsão de Fechamento (Forecast)"])

# =============================================================================
# ABA 1: AI BOARD ADVISOR
# =============================================================================
with tabs[0]:
    st.header("Conselho Consultivo de IA")
    st.markdown("Receba insights holísticos do nosso board de especialistas digitais.")
    
    col_input, col_board = st.columns([1, 2])
    
    with col_input:
        st.markdown("### 💬 Consulta")
        user_query = st.text_area(
            "O que você deseja saber?",
            height=150,
            placeholder="Ex: Como está nosso desempenho em G&A? Há riscos de estourar o orçamento anual?"
        )
        
        btn_consultar = st.button("Convocar Reunião do Board", type="primary")
        
        if btn_consultar and user_query:
            with st.spinner("🤖 O Board está deliberando... (Consultando CFO, Controller e Auditor)"):
                try:
                    resultado = ai_board.realizar_reuniao_board(user_query)
                    st.session_state['board_result'] = resultado
                except Exception as e:
                    st.error(f"Erro na reunião: {e}")

    with col_board:
        if 'board_result' in st.session_state:
            res = st.session_state['board_result']
            opinioes = res.get('opinioes', {})
            sintese = res.get('sintese', '')
            
            # Síntese do Chairman
            st.markdown(f"""
            <div class="board-card chairman">
                <div class="persona-title">🏛️ CHAIRMAN (SÍNTESE)</div>
                {sintese}
            </div>
            """, unsafe_allow_html=True)
            
            # Opiniões dos Membros
            col_cfo, col_ctrl = st.columns(2)
            
            with col_cfo:
                with st.expander("💼 CFO (Estratégia)", expanded=True):
                    st.markdown(f"<div class='cfo'>{opinioes.get('CFO', 'Em silêncio...')}</div>", unsafe_allow_html=True)
                
                with st.expander("📉 ANALYST (Previsão)", expanded=False):
                    st.markdown(f"<div class='analyst'>{opinioes.get('Analyst', 'Calculando...')}</div>", unsafe_allow_html=True)

            with col_ctrl:
                with st.expander("⚙️ CONTROLLER (Operação)", expanded=True):
                    st.markdown(f"<div class='controller'>{opinioes.get('Controller', 'Em silêncio...')}</div>", unsafe_allow_html=True)
                
                with st.expander("🔍 AUDITOR (Risco)", expanded=False):
                    st.markdown(f"<div class='auditor'>{opinioes.get('Auditor', 'Auditando...')}</div>", unsafe_allow_html=True)
        else:
            st.info("👈 Faça uma pergunta para iniciar a reunião.")

# =============================================================================
# ABA 2: FORECAST
# =============================================================================
with tabs[1]:
    st.header("Projeção de Fechamento Anual (Forecast)")
    
    col_config, col_grafico = st.columns([1, 3])
    
    with col_config:
        st.subheader("⚙️ Gerar Cenário")
        metodo = st.selectbox("Método de Projeção", ["hybrid", "linear", "sma"], 
                            format_func=lambda x: {
                                "hybrid": "Híbrido (Tendência + Sazonalidade)",
                                "linear": "Regressão Linear",
                                "sma": "Média Móvel Simples"
                            }[x])
        
        if st.button("Gerar Novo Forecast"):
            with st.spinner("Processando histórico e projetando..."):
                try:
                    # Carregar dados REAIS do banco
                    df_realizado = get_comparativo_mensal(2026)
                    
                    if df_realizado.empty:
                        st.error("Sem dados realizados para projeção.")
                    else:
                        # Adaptar dataframe para o serviço
                        # O serviço espera: ['data_ref', 'valor', 'conta_contabil_codigo', 'centro_gasto_codigo']
                        # O get_comparativo_mensal retorna ['mes', 'orcado', 'realizado', ...] agrupado por mes
                        # Preciso dos dados detalhados.
                        
                        # Vou usar uma query direta aqui para simplificar ou um novo metodo no comparador
                        # Por enquanto, vou usar o DF agregado e "explodir" ou melhor:
                        # Usar get_realizado_agregado_por_mes que retorna logs brutos?
                        # Não, preciso de granularidade de conta.
                        
                        # Mock temporário: Usar os dados realizados existentes
                        # Vou criar um adapter rápido
                        data_adapter = df_realizado.copy()
                        MESES_MAP_FIX = {m: i+1 for i, m in enumerate(['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'])}
                        data_adapter['month_num_temp'] = data_adapter['mes'].map(MESES_MAP_FIX)
                        data_adapter['data_ref'] = data_adapter.apply(lambda x: pd.Timestamp(year=2026, month=x['month_num_temp'], day=1), axis=1)
                        data_adapter['valor'] = data_adapter['realizado']
                        # Falta conta contabil... O forecast service precisa de conta.
                        # Vou pedir para o usuário: "Forecast Global" por enquanto (Soma tudo)
                        
                        # TODO: Implementar forecast detalhado na V2
                        st.info("⚠️ Nesta versão, o Forecast é calculado sobre o Total Consolidado.")
                        
                        nome_cenario = f"Manual {metodo} - {pd.Timestamp.now().strftime('%H:%M')}"
                        
                        # Simplificação: Passa um DF "fake" que representa o total como uma única conta
                        df_total = data_adapter.groupby('mes').agg({'realizado': 'sum'}).reset_index()
                        df_total['conta_contabil_codigo'] = 'TOTAL'
                        df_total['centro_gasto_codigo'] = 'CONSOLIDADO'
                        df_total['valor'] = df_total['realizado']
                        
                        # Ajustando data
                        meses_map = {m: i+1 for i, m in enumerate(['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'])}
                        df_total['month_num'] = df_total['mes'].map(meses_map)
                        df_total['data_ref'] = df_total.apply(lambda x: pd.Timestamp(year=2026, month=x['month_num'], day=1), axis=1)
                        
                        id_cenario = forecast_service.criar_cenario_automatico(df_total, nome=nome_cenario, metodo=metodo)
                        st.success(f"Cenário {id_cenario} criado!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Erro ao gerar: {str(e)}")

    with col_grafico:
        cenarios = forecast_service.listar_cenarios()
        if cenarios:
            cenario_sel = st.selectbox("Visualizar Cenário", cenarios, format_func=lambda x: f"{x['nome']} ({x['data_criacao']})")
            
            if cenario_sel:
                df_forecast = forecast_service.get_dados_cenario(cenario_sel['id'])
                
                # Gráfico
                fig = go.Figure()
                
                # Realizado
                df_real = get_comparativo_mensal(2026)
                fig.add_trace(go.Bar(name='Realizado', x=df_real['mes'], y=df_real['realizado'], marker_color='#059669'))
                
                # Provisões (Compromissado - Synergy Feature)
                saldos_prov = prov_service.get_saldo_provisoes_por_mes()
                # Mapear para lista ordenada pelos meses
                # Importar MESES_ORDEM localmente ou definir
                MESES_ORDEM = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                vals_prov = [saldos_prov.get(m, 0.0) for m in MESES_ORDEM]
                
                fig.add_trace(go.Bar(
                    name='Compromissado (Provisões)', 
                    x=MESES_ORDEM, 
                    y=vals_prov, 
                    marker_color='#F59E0B',
                    opacity=0.6,
                    hoverinfo='y+name'
                ))
                
                # Previsto
                # Forecast geralmente cobre meses futuros.
                fig.add_trace(go.Bar(name='Forecast (Tendência)', x=df_forecast['mes'], y=df_forecast['valor_previsto'], marker_color='#A78BFA'))
                
                # Budget (Linha)
                fig.add_trace(go.Scatter(name='Budget Plan', x=df_real['mes'], y=df_real['orcado'], mode='lines', line=dict(color='#4F8BF9', width=3)))
                
                fig.update_layout(barmode='overlay') # Sobrepor barras para melhor comparação
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de Dados
                st.dataframe(df_forecast)
                
        else:
            st.info("Nenhum cenário de forecast gerado ainda.")
