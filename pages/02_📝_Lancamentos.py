import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from services.provisioning_service import ProvisioningService
from data.referencias_manager import (
    carregar_centros_gasto,
    carregar_contas_contabeis,
    get_hierarquia_centro,
    get_ativos_unicos,
    MAPA_CLASSES,
    MESES_ORDEM
)
from utils_ui import setup_page, formatar_valor_brl, require_auth

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Gestão de Compromissos", "📝")
require_auth(module='lancamentos')

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

tab_novo, tab_import, tab_lista = st.tabs(["➕ Nova Provisão", "📥 Importação em Lote", "📋 Compromissos Ativos"])

# =============================================================================
# TAB: NOVA PROVISÃO
# =============================================================================
with tab_novo:
    if st.session_state.sucesso_prov:
        st.success(st.session_state.sucesso_prov)
        st.session_state.sucesso_prov = None

    with st.container():
        st.markdown('<div class="section-header"><span class="section-title">Cadastrar Obrigação</span></div>', unsafe_allow_html=True)
        
        # Formulário Aberto (Sem st.form para permitir interatividade/callbacks)
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
            st.markdown("**Localização & Centro**")
            
            # --- Filtro em Cascata para Centro de Custo ---
            
            # 1. Filtro de Regional (Se disponível)
            regionais = sorted(df_centros['regional'].dropna().unique().tolist()) if 'regional' in df_centros.columns else []
            sel_regional = st.selectbox("1. Regional", options=["Todas"] + regionais, index=0)
            
            # 2. Filtro de Base (Depende da Regional)
            df_bases_filtradas = df_centros.copy()
            if sel_regional != "Todas":
                df_bases_filtradas = df_bases_filtradas[df_bases_filtradas['regional'] == sel_regional]
                
            bases = sorted(df_bases_filtradas['base'].dropna().unique().tolist()) if 'base' in df_bases_filtradas.columns else []
            sel_base = st.selectbox("2. Base", options=["Todas"] + bases, index=0)
            
            # 3. Filtro de Centro (Depende da Base)
            df_centros_final = df_bases_filtradas.copy()
            if sel_base != "Todas":
                df_centros_final = df_centros_final[df_centros_final['base'] == sel_base]
            
            # Populando o Selectbox final
            opcoes_centros = []
            if not df_centros_final.empty:
                opcoes_centros = df_centros_final.sort_values(['codigo']).apply(lambda x: f"{x['codigo']} - {x['descricao']}", axis=1).tolist()
            
            centro_sel = st.selectbox("3. Centro de Custo", options=opcoes_centros, placeholder="Selecione o centro...", index=None)

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

        st.markdown("#### 📄 Dados Contratuais & Sistêmicos")
        col_c1, col_c2, col_c3 = st.columns(3)
        
        with col_c1:
            num_contrato = st.text_input("Número do Contrato (Opcional)", placeholder="Ex: CTR-2026/001")
        
        with col_c2:
            # O st.radio agora dispara rerun, atualizando o estado para o próximo render
            cadastrado_sis = st.radio("Cadastrado no Sistema (Oracle/Fusion)?", ["Não", "Sim"], horizontal=True, index=0)
        
        with col_c3:
            # Disabled atualizado dinamicamente
            num_registro = st.text_input("Número do Registro/RC/Pedido", placeholder="Obrigatório se cadastrado", disabled=(cadastrado_sis == "Não"))

        justificativa = st.text_area("Justificativa / Detalhes (OBZ)", placeholder="Por que este gasto é necessário?", height=100)

        st.markdown("---")
        if st.button("💾 Registrar Compromisso", type="primary", use_container_width=True):
            # Validação
            erros = []
            if not descricao: erros.append("Descrição obrigatória")
            if valor <= 0: erros.append("Informe o valor do compromisso (maior que zero)")
            if not centro_sel: erros.append("Centro de Custo obrigatório")
            if not conta_sel: erros.append("Conta Contábil obrigatória")
            if cadastrado_sis == "Sim" and not num_registro: erros.append("Número do Registro é obrigatório para item cadastrado")

            # Preparar dados de Regional/Base
            cod_centro_clean = centro_sel.split(' - ')[0] if centro_sel else ""
            reg_val = sel_regional if sel_regional != "Todas" else None
            base_val = sel_base if sel_base != "Todas" else None
            
            # Fallback: Se não selecionou (foi via Todas ou direto), tenta buscar na base
            if (not reg_val or not base_val) and not df_centros.empty and cod_centro_clean:
                match = df_centros[df_centros['codigo'] == cod_centro_clean]
                if not match.empty:
                    if not reg_val: reg_val = match.iloc[0].get('regional')
                    if not base_val: base_val = match.iloc[0].get('base')

            # Validação de Regional e Base (Obrigatórios)
            if not reg_val: erros.append("Regional é obrigatória (Selecione ou verifique o cadastro do Centro)")
            if not base_val: erros.append("Base é obrigatória (Selecione ou verifique o cadastro do Centro)")

            if erros:
                for e in erros: st.error(f"❌ {e}")
            else:
                try:
                    # FORÇA VALOR NEGATIVO (GASTO)
                    valor_final = -abs(valor)

                    dados = {
                        "descricao": f"{descricao} ({fornecedor})" if fornecedor else descricao,
                        "valor_estimado": valor_final,
                        "centro_gasto_codigo": cod_centro_clean,
                        "conta_contabil_codigo": conta_sel.split(' - ')[0],
                        "mes_competencia": mes,
                        "tipo_despesa": tipo_despesa,
                        "justificativa_obz": justificativa,
                        "usuario": st.session_state.get('username', 'Sistema'),
                        # Novos Campos
                        "numero_contrato": num_contrato,
                        "cadastrado_sistema": True if cadastrado_sis == "Sim" else False,
                        "numero_registro": num_registro,
                        # Novos campos de hierarquia
                        "regional": reg_val,
                        "base": base_val
                    }
                    prov_service.criar_provisao(dados)
                    st.session_state.sucesso_prov = "✅ Provisão registrada com sucesso!"
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# =============================================================================
# TAB: IMPORTAÇÃO EM LOTE
# =============================================================================
with tab_import:
    st.markdown('<div class="section-header"><span class="section-title">Importar Provisões em Lote</span></div>', unsafe_allow_html=True)
    
    col_dl, col_up = st.columns([1, 2])
    
    with col_dl:
        st.info("ℹ️ Baixe o modelo para preenchimento.")
        
        # Gerar Template
        df_template = pd.DataFrame({
            'descricao': ['Ex: Manutenção Preventiva'],
            'valor_estimado': [1500.00],
            'centro_gasto_codigo': ['01020504001'],
            'conta_contabil_codigo': ['3010101'],
            'mes_competencia': ['JAN'],
            'fornecedor': ['Fornecedor XYZ'],
            'tipo_despesa': ['Variavel'],
            'justificativa_obz': ['Contrato anual'],
            'numero_contrato': ['CTR-123'],
            'cadastrado_sistema': ['Sim'],
            'numero_registro': ['RC-999']
        })
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_template.to_excel(writer, index=False, sheet_name='Modelo')
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 Baixar Modelo Excel",
            data=processed_data,
            file_name="template_provisoes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col_up:
        uploaded_file = st.file_uploader("Carregar Arquivo Preenchido (Excel/CSV)", type=['xlsx', 'csv'])
        
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_import = pd.read_csv(uploaded_file)
            else:
                df_import = pd.read_excel(uploaded_file)
            
            st.markdown("#### Pré-visualização")
            st.dataframe(df_import.head(), use_container_width=True)
            
            if st.button("🚀 Processar Importação", type="primary"):
                # Converter para lista de dicts
                lista_dados = df_import.to_dict(orient='records')

                # --- ENRIQUECIMENTO AUTOMÁTICO (Regional, Base, Usuário, Valor) ---
                current_user = st.session_state.get('username', 'Importação em Lote')

                if not df_centros.empty and 'regional' in df_centros.columns:
                    for item in lista_dados:
                        try:
                            # 1. Atribuição de Usuário
                            item['usuario'] = current_user

                            # 2. Forçar Valor Negativo (Gasto)
                            val_raw = float(item.get('valor_estimado', 0))
                            item['valor_estimado'] = -abs(val_raw)

                            # 3. Normalizar código (pode vir como int do Excel)
                            cod_raw = str(item.get('centro_gasto_codigo', '')).strip()
                            if cod_raw.endswith('.0'): 
                                cod_raw = cod_raw[:-2]
                            cod_std = cod_raw.zfill(11)
                            
                            # Atualizar código normalizado no item também, é boa prática
                            item['centro_gasto_codigo'] = cod_std

                            # 4. Buscar na referência (Regional/Base)
                            match = df_centros[df_centros['codigo'] == cod_std]
                            if not match.empty:
                                item['regional'] = match.iloc[0]['regional']
                                item['base'] = match.iloc[0]['base']
                        except Exception:
                            continue # Se falhar o lookup, segue sem preencher ou com dados parciais
                
                # Barra de progresso (fake visual, pois processamento é rápido em lote)
                progress_text = "Importando registros..."
                my_bar = st.progress(0, text=progress_text)
                
                # Chamar serviço
                sucesso_count, erros = prov_service.criar_provisoes_em_lote(lista_dados)
                
                my_bar.progress(100, text="Finalizado!")
                
                if sucesso_count > 0:
                    st.success(f"✅ {sucesso_count} provisões importadas com sucesso!")
                
                if erros:
                    st.warning(f"⚠️ {len(erros)} registros falharam.")
                    with st.expander("Ver Detalhes dos Erros"):
                        for erro in erros:
                            st.write(erro)
                
                if sucesso_count > 0 and not erros:
                    st.balloons()
                    
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# =============================================================================
# TAB: LISTA
# =============================================================================
with tab_lista:
    st.markdown('<div class="section-header"><span class="section-title">Compromissos em Aberto</span></div>', unsafe_allow_html=True)
    
    # Prepara opções de Base
    bases_options = sorted(df_centros['base'].dropna().unique().tolist()) if 'base' in df_centros.columns else []

    col_f1, col_f2, col_f3, col_f4 = st.columns([1.5, 1.5, 1.5, 1])
    with col_f1:
        filtro_mes = st.selectbox("Filtrar Mês", ["Todos"] + MESES_ORDEM)
    with col_f2:
        filtro_base = st.selectbox("Filtrar Base", ["Todas"] + bases_options)
    with col_f3:
        filtro_status = st.selectbox("Status", ["TODOS", "PENDENTE", "REALIZADA", "CANCELADA"], index=1)
    
    lista = prov_service.listar_provisoes(
        status=None if filtro_status == "TODOS" else filtro_status,
        mes=None if filtro_mes == "Todos" else filtro_mes,
        base=None if filtro_base == "Todas" else filtro_base
    )

    if lista:
        df = pd.DataFrame(lista)
        df['Valor'] = df['valor_estimado'].apply(formatar_valor_brl)
        
        # --- EXPORTAR ---
        with col_f4:
            st.write("") # Spacer
            st.write("") 
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Provisões')
            
            st.download_button(
                label="📥 Exportar",
                data=output.getvalue(),
                file_name=f"provisoes_{filtro_mes}_{datetime.now().strftime('%d%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # GRID COM SELEÇÃO
        st.info("👆 Selecione uma linha na tabela para editar ou cancelar.")
        
        event = st.dataframe(
            df[['mes_competencia', 'base', 'regional', 'descricao', 'centro_gasto_codigo', 'status', 'numero_registro', 'Valor']],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "mes_competencia": st.column_config.TextColumn("Mês", width="small"),
                "base": st.column_config.TextColumn("Base", width="small"),
                "regional": st.column_config.TextColumn("Regional", width="small"),
                "descricao": "Descrição",
                "centro_gasto_codigo": "Centro",
                "status": st.column_config.TextColumn("Status", width="small"),
                "numero_registro": st.column_config.TextColumn("Nº Reg.", width="small"),
                "Valor": st.column_config.TextColumn("Valor", width="medium"),
            }
        )
        
        # Lógica de Seleção
        if event.selection.rows:
            idx = event.selection.rows[0]
            # O índice retornado corresponde ao DataFrame passado para st.dataframe
            # Como dataframes filtrados/ordenados no backend retornam nova lista, o índice é consistente com 'lista'/'df'
            item_atual = lista[idx]
            _id = item_atual['id']
            
            # --- ÁREA DE EDIÇÃO / AÇÃO ---
            st.markdown("---")
            # Ajuste visual para destacar a seleção
            st.markdown(f"#### ✏️ Gerenciar Item: {_id} - {item_atual['descricao']}")
            
            with st.expander("🛠️ Formulário de Edição", expanded=True):
                with st.form(key=f"edit_form_{_id}"):
                    col_e1, col_e2, col_e3 = st.columns(3)
                    
                    # Valor
                    val_atual = float(item_atual['valor_estimado'])
                    # Se for negativo (gasto), mostra absoluto para edição ou mantém negativo?
                    # Geralmente melhor manter a sinalética ou pedir positivo e inverter.
                    # Vamos mostrar como está no banco.
                    
                    novo_valor = col_e1.number_input("Valor (R$ - Negativo para Gasto)", value=val_atual, step=100.0)
                    novo_status = col_e2.selectbox("Status", ["PENDENTE", "REALIZADA", "CANCELADA"], index=["PENDENTE", "REALIZADA", "CANCELADA"].index(item_atual['status']))
                    novo_reg = col_e3.text_input("Nº Registro / RC", value=item_atual.get('numero_registro') or "")
                    
                    nova_desc = st.text_input("Descrição", value=item_atual['descricao'])
                    
                    chk_cadastrado = st.checkbox("Cadastrado no Sistema?", value=item_atual.get('cadastrado_sistema', False))

                    col_btn1, col_btn2 = st.columns([1, 4])
                    submit = col_btn1.form_submit_button("💾 Salvar Alterações", type="primary")
                    
                    if submit:
                        dados_upd = {
                            "valor_estimado": novo_valor,
                            "status": novo_status,
                            "numero_registro": novo_reg,
                            "descricao": nova_desc,
                            "cadastrado_sistema": chk_cadastrado
                        }
                        # Validação simples
                        if novo_status == "REALIZADA" and not novo_reg:
                            st.error("Para status REALIZADA, informe o Número de Registro.")
                        else:
                            prov_service.atualizar_provisao(_id, dados_upd)
                            st.success("Atualizado com sucesso!")
                            st.rerun()

            # Botão Cancelar separado do form
            if st.button("🗑️ Cancelar este Item (Definitivo)", key="bt_canc_sep"):
                    prov_service.cancelar_provisao(_id, "Cancelado via Interface")
                    st.success("Item cancelado.")
                    st.rerun()

    else:
        st.info("📭 Nenhum registro encontrado para os filtros selecionados.")
