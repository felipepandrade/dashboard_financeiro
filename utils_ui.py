import streamlit as st

# =============================================================================
# CORES & TEMA
# =============================================================================

CORES = {
    'orcado': '#3b82f6',       # Azul
    'realizado': '#10b981',    # Verde
    'desvio_neg': '#ef4444',   # Vermelho
    'desvio_pos': '#f59e0b',   # Amarelo/Laranja
    'neutro': '#6b7280',       # Cinza
    'background': '#0f172a',   # Slate escuro
    'card': '#1e293b',         # Slate
    'texto': '#f1f5f9',        # Slate claro
    'destaque': '#00d4aa',     # Cyan
    
    # Cores Semânticas Padrão
    'primary': '#3b82f6',      # Azul
    'success': '#10b981',      # Verde
    'warning': '#f59e0b',      # Laranja
    'danger': '#ef4444',       # Vermelho
    'info': '#0ea5e9',         # Azul claro
    
    # Elementos UI
    'card_bg': '#1e293b',
    'border': '#334155',
    'text_secondary': '#94a3b8'
}

def aplicar_estilo_premium():
    """Aplica o CSS global do tema Premium (Dark/Gradient)."""
    st.markdown("""
    <style>
        /* Tema escuro premium */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        }
        
        /* Cards de KPI */
        .kpi-card {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 1px solid #475569;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
        }
        
        .kpi-value {
            font-size: 32px;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 8px;
        }
        
        .kpi-label {
            font-size: 14px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Seções */
        .section-header {
            padding: 16px 0 8px 0;
            border-bottom: 2px solid #00d4aa;
            margin-bottom: 24px;
        }
        
        .section-title {
            font-size: 24px;
            font-weight: 600;
            color: #f1f5f9;
        }
        
        /* Tabelas */
        .dataframe {
            background: #1e293b !important;
        }
        
        /* Botões */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background: #0f172a;
        }

        /* Centralizar Logo (st.logo) */
        [data-testid="stLogo"] {
            width: 100%;
            justify-content: center;
            display: flex;
        }
        [data-testid="stLogo"] img {
            max-width: 200px !important; /* Forçar tamanho se necessário */
            width: 200px !important;
        }
    </style>
    """, unsafe_allow_html=True)

def setup_page(title: str, icon: str = "📊", layout: str = "wide"):
    """Configura cabeçalho e estilo da página."""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state="expanded"
    )
    aplicar_estilo_premium()
    
    # -------------------------------------------------------------------------
    # LOGO (Header)
    # -------------------------------------------------------------------------
    try:
        st.logo("logo_engie.png", icon_image="logo_engie.png")
    except:
        # Fallback se imagem não existir
        st.logo("https://img.icons8.com/color/48/data-configuration.png")
    
    # -------------------------------------------------------------------------
    # SIDEBAR GLOBAL (Configurações)
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### ⚙️ Configurações do Sistema")
        
        # Gestão de Chaves de API (Centralizada)
        if 'api_key' not in st.session_state:
            # Tentar carregar de variável de ambiente (Local Development)
            import os
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except: pass
            st.session_state['api_key'] = os.getenv("GEMINI_API_KEY", "")
            
        api_key_input = st.text_input(
            "🔑 Chave de API (IA)",
            value=st.session_state.get('api_key', ''),
            type="password",
            help="Insira sua chave Google Gemini ou OpenAI para habilitar os recursos de inteligência."
        )
        st.session_state['api_key'] = api_key_input
        
        # Provedor de IA
        if 'ai_provider' not in st.session_state:
            st.session_state['ai_provider'] = "Gemini (Google)"
            
        provider = st.selectbox(
            "🧠 Provedor de Inteligência",
            ["Gemini (Google)", "OpenAI (GPT-4)"],
            index=0 if "Gemini" in st.session_state['ai_provider'] else 1
        )
        st.session_state['ai_provider'] = provider
        
        # Indicador de Status
        if st.session_state['api_key']:
            st.success("IA Habilitada ✅")
        else:
            st.warning("IA Desabilitada ⚠️")
            
        st.divider()
        st.info("💡 Dica: Use a sidebar para navegar entre os módulos.")

def exibir_kpi_card(label: str, valor: str, delta: str = None, cor_delta: str = "neutral"):
    """Renderiza um card de KPI estilizado."""
    delta_html = ""
    if delta:
        delta_html = f"""<div class="kpi-delta {cor_delta}" style="font-size: 14px; margin-top: 8px; padding: 4px 8px; border-radius: 4px; display: inline-block; background: rgba(107, 114, 128, 0.2); color: #9ca3af;">{delta}</div>"""

    st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-value">{valor}</div>
    <div class="kpi-label">{label}</div>
    {delta_html}
</div>
""", unsafe_allow_html=True)

def formatar_valor_brl(valor: float, mostrar_simbolo: bool = True) -> str:
    """Formata float para BRL. O argumento mostrar_simbolo é mantido para compatibilidade."""
    if valor is None: return "R$ 0,00"
    msg = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return msg
