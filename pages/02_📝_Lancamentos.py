"""
02_📝_Lancamentos.py
====================
Página de lançamentos de valores realizados mensais.

Esta página permite:
- Cadastrar novos lançamentos de custos realizados
- Visualizar e editar lançamentos existentes
- Validar centros de custo e contas contábeis contra bases de referência
- Exibir hierarquia pai-filho dos centros de custo

Autor: Sistema Orçamentário 2026
Data: Janeiro/2026
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.referencias_manager import (
    carregar_centros_gasto,
    carregar_contas_contabeis,
    get_hierarquia_centro,
    buscar_centros_gasto,
    buscar_contas_contabeis,
    validar_centro_gasto,
    validar_conta_contabil,
    get_ativos_unicos,
    MAPA_CLASSES,
    MESES_ORDEM
)

from database.crud import (
    criar_lancamento,
    listar_lancamentos,
    obter_lancamento,
    atualizar_lancamento,
    deletar_lancamento,
    obter_estatisticas_gerais
)

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Lançamentos - Sistema Orçamentário 2026",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# ESTILOS CSS
# =============================================================================

st.markdown("""
<style>
    /* Card de hierarquia */
    .hierarchy-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        margin: 10px 0;
        border-left: 4px solid #00d4aa;
    }
    
    .hierarchy-title {
        font-size: 14px;
        color: #afd4f2;
        margin-bottom: 8px;
    }
    
    .hierarchy-item {
        padding: 5px 0;
        font-size: 14px;
    }
    
    .hierarchy-item strong {
        color: #00d4aa;
    }
    
    /* Botão de ação */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Mensagem de sucesso */
    .success-msg {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Card de estatísticas */
    .stat-card {
        background: #f8fafc;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #1e3a5f;
    }
    
    .stat-label {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

@st.cache_data(ttl=60)
def carregar_dados_dropdowns():
    """Carrega dados para os dropdowns de seleção."""
    df_centros = carregar_centros_gasto()
    df_contas = carregar_contas_contabeis()
    
    # Preparar opções de centros
    if not df_centros.empty:
        df_centros['opcao'] = df_centros.apply(
            lambda row: f"{row['codigo']} - {row['descricao']} ({row['ativo']})",
            axis=1
        )
    
    # Preparar opções de contas
    if not df_contas.empty:
        df_contas['opcao'] = df_contas.apply(
            lambda row: f"{row['codigo']} - {row['descricao']}",
            axis=1
        )
    
    return df_centros, df_contas


def formatar_valor_brl(valor: float) -> str:
    """Formata valor em reais."""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def exibir_hierarquia(hierarquia: dict):
    """Exibe card de hierarquia do centro de custo."""
    if not hierarquia.get('encontrado', False):
        st.warning(f"⚠️ {hierarquia.get('erro', 'Centro não encontrado')}")
        return
    
    # Determinar tipo de centro
    is_sem_hierarquia = hierarquia.get('is_sem_hierarquia', False)
    is_cos = hierarquia.get('is_cos', False)
    is_ga = hierarquia.get('is_ga', False)
    
    # Definir label do tipo de custo
    if is_cos:
        tipo_custo = '<span style="color: #fbbf24;"> (Custo Administrativo)</span>'
    elif is_ga:
        tipo_custo = '<span style="color: #f59e0b;"> (Custo de Suporte)</span>'
    else:
        tipo_custo = ''
    
    # Nota sobre hierarquia
    if is_sem_hierarquia:
        nota_hierarquia = '<div class="hierarchy-item" style="color: #fbbf24; font-size: 12px;">⚠️ Este centro NÃO segue a lógica de hierarquia pai-filho</div>'
    else:
        nota_hierarquia = f'<div class="hierarchy-item" style="color: #afd4f2; font-size: 12px;">{hierarquia.get("filhos_count", 0)} centros filhos no mesmo ativo pai</div>'
    
    st.markdown(f"""
    <div class="hierarchy-card">
        <div class="hierarchy-title">📊 Hierarquia do Centro de Custo</div>
        <div class="hierarchy-item">
            <strong>Ativo:</strong> {hierarquia.get('ativo', 'N/A')}
            {tipo_custo}
        </div>
        <div class="hierarchy-item">
            <strong>Pai:</strong> {hierarquia.get('codigo_pai', 'N/A')}000 - {hierarquia.get('pai_descricao', 'N/A')}
        </div>
        <div class="hierarchy-item">
            <strong>Classe:</strong> {hierarquia.get('classe', 'N/A')} - {hierarquia.get('classe_nome', 'N/A')}
        </div>
        <div class="hierarchy-item">
            <strong>Centro:</strong> {hierarquia.get('codigo', 'N/A')} - {hierarquia.get('descricao', 'N/A')}
        </div>
        {nota_hierarquia}
    </div>
    """, unsafe_allow_html=True)


def exibir_estatisticas():
    """Exibe estatísticas gerais dos lançamentos."""
    stats = obter_estatisticas_gerais(2026)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📝 Total de Lançamentos",
            value=stats['total_lancamentos']
        )
    
    with col2:
        st.metric(
            label="💰 Valor Total",
            value=formatar_valor_brl(stats['total_valor'])
        )
    
    with col3:
        st.metric(
            label="📅 Meses com Dados",
            value=f"{stats['meses_com_dados']}/12"
        )
    
    with col4:
        st.metric(
            label="🏢 Centros Utilizados",
            value=stats['centros_utilizados']
        )


# =============================================================================
# INICIALIZAÇÃO DO SESSION STATE
# =============================================================================

if 'lancamento_sucesso' not in st.session_state:
    st.session_state.lancamento_sucesso = None

if 'centro_selecionado' not in st.session_state:
    st.session_state.centro_selecionado = None

if 'modo_edicao' not in st.session_state:
    st.session_state.modo_edicao = False

if 'lancamento_editando' not in st.session_state:
    st.session_state.lancamento_editando = None


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

# Título
st.title("📝 Lançamentos Realizados")
st.markdown("---")

# Estatísticas
exibir_estatisticas()
st.markdown("---")

# Carregar dados dos dropdowns
df_centros, df_contas = carregar_dados_dropdowns()

# Tabs principais
tab_novo, tab_lista, tab_importar = st.tabs([
    "➕ Novo Lançamento", 
    "📋 Lançamentos do Mês",
    "📥 Importar Excel"
])


# =============================================================================
# TAB: NOVO LANÇAMENTO
# =============================================================================

with tab_novo:
    st.subheader("Cadastrar Novo Lançamento")
    
    # Mensagem de sucesso
    if st.session_state.lancamento_sucesso:
        st.success(st.session_state.lancamento_sucesso)
        st.session_state.lancamento_sucesso = None
    
    # Formulário
    with st.form("form_lancamento", clear_on_submit=True):
        
        # Linha 1: Período
        col1, col2 = st.columns(2)
        with col1:
            mes_selecionado = st.selectbox(
                "📅 Mês",
                options=MESES_ORDEM,
                index=0,
                help="Selecione o mês do lançamento"
            )
        with col2:
            ano_selecionado = st.selectbox(
                "📆 Ano",
                options=[2026, 2025],
                index=0,
                help="Selecione o ano do lançamento"
            )
        
        st.markdown("---")
        
        # Linha 2: Centro de Custo
        st.markdown("#### 🏢 Centro de Custo")
        
        # Filtros de centro de custo
        col_filtro1, col_filtro2 = st.columns(2)
        with col_filtro1:
            ativos_disponiveis = ['Todos'] + get_ativos_unicos(df_centros)
            filtro_ativo = st.selectbox(
                "Filtrar por Ativo",
                options=ativos_disponiveis,
                index=0
            )
        with col_filtro2:
            classes_disponiveis = ['Todas'] + list(MAPA_CLASSES.values())
            filtro_classe = st.selectbox(
                "Filtrar por Classe",
                options=classes_disponiveis,
                index=0
            )
        
        # Aplicar filtros
        df_centros_filtrado = df_centros.copy()
        if filtro_ativo != 'Todos':
            df_centros_filtrado = df_centros_filtrado[df_centros_filtrado['ativo'] == filtro_ativo]
        if filtro_classe != 'Todas':
            df_centros_filtrado = df_centros_filtrado[df_centros_filtrado['classe_nome'] == filtro_classe]
        
        # Dropdown de centros
        opcoes_centros = df_centros_filtrado['opcao'].tolist() if not df_centros_filtrado.empty else []
        
        centro_selecionado = st.selectbox(
            "Selecione o Centro de Custo",
            options=opcoes_centros,
            index=None,
            placeholder="🔍 Digite para buscar entre os centros de custo...",
            help="Selecione o centro de custo onde o lançamento será registrado"
        )
        
        # Exibir hierarquia se selecionou centro
        if centro_selecionado:
            codigo_centro = centro_selecionado.split(' - ')[0]
            hierarquia = get_hierarquia_centro(codigo_centro, df_centros)
            exibir_hierarquia(hierarquia)
        
        st.markdown("---")
        
        # Linha 3: Conta Contábil
        st.markdown("#### 📊 Conta Contábil")
        
        opcoes_contas = df_contas['opcao'].tolist() if not df_contas.empty else []
        
        conta_selecionada = st.selectbox(
            "Selecione a Conta Contábil",
            options=opcoes_contas,
            index=None,
            placeholder="🔍 Digite para buscar entre as contas contábeis...",
            help="Selecione a conta contábil do lançamento"
        )
        
        st.markdown("---")
        
        # Linha 4: Detalhes do lançamento
        st.markdown("#### 📋 Detalhes do Lançamento")
        
        col_det1, col_det2 = st.columns(2)
        with col_det1:
            fornecedor = st.text_input(
                "Fornecedor",
                placeholder="Nome do fornecedor (opcional)",
                help="Informe o nome do fornecedor, se aplicável"
            )
        with col_det2:
            valor = st.number_input(
                "Valor (R$)",
                value=0.00,
                step=100.00,
                format="%.2f",
                help="Valores negativos representam custos/despesas"
            )
        
        descricao = st.text_area(
            "Descrição",
            placeholder="Descrição do lançamento...",
            height=100,
            help="Descreva o motivo ou detalhe do lançamento"
        )
        
        observacoes = st.text_area(
            "Observações",
            placeholder="Observações adicionais (opcional)...",
            height=80
        )
        
        st.markdown("---")
        
        # Botões
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        with col_btn1:
            submitted = st.form_submit_button(
                "💾 Salvar Lançamento",
                type="primary",
                use_container_width=True
            )
        with col_btn2:
            limpar = st.form_submit_button(
                "🔄 Limpar",
                use_container_width=True
            )
        
        # Processar submissão
        if submitted:
            # Validações
            erros = []
            
            if not centro_selecionado:
                erros.append("Selecione um centro de custo")
            
            if not conta_selecionada:
                erros.append("Selecione uma conta contábil")
            
            if valor == 0:
                erros.append("Informe um valor diferente de zero")
            
            if erros:
                for erro in erros:
                    st.error(f"❌ {erro}")
            else:
                # Extrair dados selecionados
                codigo_centro = centro_selecionado.split(' - ')[0]
                hierarquia = get_hierarquia_centro(codigo_centro, df_centros)
                
                codigo_conta = conta_selecionada.split(' - ')[0]
                descricao_conta = conta_selecionada.split(' - ', 1)[1] if ' - ' in conta_selecionada else ''
                
                # Montar dados do lançamento
                dados = {
                    'ano': ano_selecionado,
                    'mes': mes_selecionado,
                    'centro_gasto_codigo': hierarquia['codigo'],
                    'centro_gasto_pai': hierarquia['codigo_pai'],
                    'centro_gasto_classe': hierarquia['classe'],
                    'centro_gasto_classe_nome': hierarquia['classe_nome'],
                    'centro_gasto_descricao': hierarquia['descricao'],
                    'ativo': hierarquia['ativo'],
                    'is_cos': hierarquia.get('is_cos', False),
                    'is_ga': hierarquia.get('is_ga', False),
                    'is_sem_hierarquia': hierarquia.get('is_sem_hierarquia', False),
                    'conta_contabil_codigo': codigo_conta,
                    'conta_contabil_descricao': descricao_conta,
                    'fornecedor': fornecedor,
                    'descricao': descricao,
                    'valor': valor,
                    'usuario': 'usuario_sistema',
                    'observacoes': observacoes
                }
                
                # Criar lançamento
                sucesso, id_lancamento, mensagem = criar_lancamento(dados)
                
                if sucesso:
                    st.session_state.lancamento_sucesso = f"✅ {mensagem}"
                    st.rerun()
                else:
                    st.error(f"❌ {mensagem}")


# =============================================================================
# TAB: LISTA DE LANÇAMENTOS
# =============================================================================

with tab_lista:
    st.subheader("Lançamentos do Período")
    
    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        mes_filtro = st.selectbox(
            "Mês",
            options=['Todos'] + MESES_ORDEM,
            key="filtro_mes_lista"
        )
    with col_f2:
        ano_filtro = st.selectbox(
            "Ano",
            options=[2026, 2025],
            key="filtro_ano_lista"
        )
    with col_f3:
        ativo_filtro = st.selectbox(
            "Ativo",
            options=['Todos'] + get_ativos_unicos(df_centros),
            key="filtro_ativo_lista"
        )
    
    # Buscar lançamentos
    filtro_mes = None if mes_filtro == 'Todos' else mes_filtro
    filtro_ativo_val = None if ativo_filtro == 'Todos' else ativo_filtro
    
    lancamentos = listar_lancamentos(
        ano=ano_filtro,
        mes=filtro_mes,
        ativo=filtro_ativo_val
    )
    
    if lancamentos:
        # Converter para DataFrame
        df_lancamentos = pd.DataFrame(lancamentos)
        
        # Formatar colunas
        df_display = df_lancamentos[[
            'id', 'mes', 'centro_gasto_codigo', 'ativo', 
            'centro_gasto_classe_nome', 'conta_contabil_codigo',
            'fornecedor', 'valor', 'descricao'
        ]].copy()
        
        df_display.columns = [
            'ID', 'Mês', 'Centro', 'Ativo', 
            'Classe', 'Conta',
            'Fornecedor', 'Valor', 'Descrição'
        ]
        
        # Formatar valor
        df_display['Valor'] = df_display['Valor'].apply(formatar_valor_brl)
        
        # Total
        total = sum(l['valor'] for l in lancamentos)
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.info(f"📊 **{len(lancamentos)}** lançamentos encontrados")
        with col_info2:
            st.info(f"💰 **Total:** {formatar_valor_brl(total)}")
        
        # Tabela
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Mês": st.column_config.TextColumn("Mês", width="small"),
                "Centro": st.column_config.TextColumn("Centro", width="medium"),
                "Ativo": st.column_config.TextColumn("Ativo", width="small"),
                "Classe": st.column_config.TextColumn("Classe", width="medium"),
                "Conta": st.column_config.TextColumn("Conta", width="medium"),
                "Fornecedor": st.column_config.TextColumn("Fornecedor", width="medium"),
                "Valor": st.column_config.TextColumn("Valor", width="medium"),
                "Descrição": st.column_config.TextColumn("Descrição", width="large")
            }
        )
        
        # Ações
        st.markdown("---")
        st.markdown("#### 🔧 Ações")
        
        col_acao1, col_acao2 = st.columns(2)
        
        with col_acao1:
            id_deletar = st.number_input(
                "ID do lançamento para deletar",
                min_value=1,
                step=1,
                key="id_deletar"
            )
            if st.button("🗑️ Deletar Lançamento", type="secondary"):
                sucesso, msg = deletar_lancamento(int(id_deletar))
                if sucesso:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        
        with col_acao2:
            # Exportar
            if st.button("📥 Exportar para Excel"):
                df_export = pd.DataFrame(lancamentos)
                csv = df_export.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="⬇️ Baixar CSV",
                    data=csv,
                    file_name=f"lancamentos_{mes_filtro}_{ano_filtro}.csv",
                    mime="text/csv"
                )
    else:
        st.info("📭 Nenhum lançamento encontrado para os filtros selecionados.")
        st.markdown("""
        **Dicas:**
        - Verifique os filtros de mês e ano
        - Cadastre novos lançamentos na aba "Novo Lançamento"
        """)


# =============================================================================
# TAB: IMPORTAR EXCEL
# =============================================================================

with tab_importar:
    st.subheader("Importar Lançamentos via Excel")
    
    st.info("""
    📋 **Formato esperado do arquivo:**
    - Colunas obrigatórias: `mes`, `centro_gasto_codigo`, `conta_contabil_codigo`, `valor`
    - Colunas opcionais: `fornecedor`, `descricao`, `observacoes`
    """)
    
    # Template
    st.markdown("#### 📥 Baixar Template")
    
    template_data = {
        'mes': ['JAN', 'JAN', 'FEV'],
        'centro_gasto_codigo': ['01021027102', '01021027401', '01021027501'],
        'conta_contabil_codigo': ['4120101001', '4130102001', '4120101001'],
        'valor': [-15000.00, -8500.00, -12000.00],
        'fornecedor': ['Fornecedor A', 'Fornecedor B', ''],
        'descricao': ['Manutenção preventiva', 'Serviços gerais', 'Material de consumo'],
        'observacoes': ['', 'Urgente', '']
    }
    df_template = pd.DataFrame(template_data)
    
    csv_template = df_template.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="⬇️ Baixar Template Excel",
        data=csv_template,
        file_name="template_lancamentos.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # Upload
    st.markdown("#### 📤 Upload de Arquivo")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo Excel ou CSV",
        type=['xlsx', 'xls', 'csv'],
        help="O arquivo deve seguir o formato do template"
    )
    
    if uploaded_file:
        try:
            # Ler arquivo
            if uploaded_file.name.endswith('.csv'):
                df_import = pd.read_csv(uploaded_file)
            else:
                df_import = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Arquivo carregado: {len(df_import)} linhas")
            
            # Preview
            st.dataframe(df_import.head(10), use_container_width=True)
            
            # Validar
            colunas_obrigatorias = ['mes', 'centro_gasto_codigo', 'conta_contabil_codigo', 'valor']
            colunas_faltantes = [c for c in colunas_obrigatorias if c not in df_import.columns]
            
            if colunas_faltantes:
                st.error(f"❌ Colunas obrigatórias faltantes: {', '.join(colunas_faltantes)}")
            else:
                # Ano para importação
                ano_import = st.selectbox("Ano para importação", options=[2026, 2025], key="ano_import")
                
                if st.button("📥 Importar Lançamentos", type="primary"):
                    from database.crud import criar_lancamentos_lote
                    
                    # Preparar dados
                    lista_dados = []
                    for _, row in df_import.iterrows():
                        codigo_centro = str(row['centro_gasto_codigo']).zfill(11)
                        hierarquia = get_hierarquia_centro(codigo_centro, df_centros)
                        
                        dados = {
                            'ano': ano_import,
                            'mes': str(row['mes']).upper(),
                            'centro_gasto_codigo': codigo_centro,
                            'centro_gasto_pai': hierarquia.get('codigo_pai', codigo_centro[:8]),
                            'centro_gasto_classe': hierarquia.get('classe', '0'),
                            'centro_gasto_classe_nome': hierarquia.get('classe_nome', 'Desconhecido'),
                            'centro_gasto_descricao': hierarquia.get('descricao', ''),
                            'ativo': hierarquia.get('ativo', ''),
                            'is_cos': hierarquia.get('is_cos', False),
                            'is_ga': hierarquia.get('is_ga', False),
                            'is_sem_hierarquia': hierarquia.get('is_sem_hierarquia', False),
                            'conta_contabil_codigo': str(row['conta_contabil_codigo']),
                            'conta_contabil_descricao': '',
                            'fornecedor': row.get('fornecedor', '') or '',
                            'descricao': row.get('descricao', '') or '',
                            'valor': float(row['valor']),
                            'usuario': 'importacao',
                            'observacoes': row.get('observacoes', '') or ''
                        }
                        lista_dados.append(dados)
                    
                    # Importar
                    criados, erros, msgs = criar_lancamentos_lote(lista_dados)
                    
                    if criados > 0:
                        st.success(f"✅ {criados} lançamentos importados com sucesso!")
                    
                    if erros > 0:
                        st.warning(f"⚠️ {erros} erros durante a importação")
                        for msg in msgs[:5]:
                            st.error(msg)
                    
                    st.rerun()
                    
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("### 📊 Sistema Orçamentário 2026")
    st.markdown("---")
    
    # Status das referências
    st.markdown("#### 📁 Bases de Referência")
    
    from data.referencias_manager import get_status_referencias
    status = get_status_referencias()
    
    if status['orcamento_ok']:
        st.success(f"✅ Orçamento: {status['orcamento_count']} itens")
    else:
        st.error("❌ Orçamento não carregado")
    
    if status['centros_ok']:
        st.success(f"✅ Centros: {status['centros_count']} itens")
    else:
        st.error("❌ Centros não carregados")
    
    if status['contas_ok']:
        st.success(f"✅ Contas: {status['contas_count']} itens")
    else:
        st.error("❌ Contas não carregadas")
    
    st.markdown("---")
    
    # Legenda de classes
    st.markdown("#### 📋 Classes de Ativos")
    
    for codigo, nome in MAPA_CLASSES.items():
        st.markdown(f"**{codigo}** - {nome}")
    
    st.markdown("---")
    st.caption("Dashboard Financeiro BASEAL © 2026")
