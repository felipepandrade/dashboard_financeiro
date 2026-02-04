import streamlit as st
import time
from services.auth_service import AuthService

# =============================================================================
# CONTROLE DE ACESSO (Login)
# =============================================================================

def require_auth(required_role: str = None, module: str = None):
    """
    Verifica se o usuário está autenticado e tem permissão.
    
    Args:
        required_role: Role mínima (viewer, editor, admin)
        module: Nome do módulo para permissão granular (opcional)
    """
    
    # 1. Verifica se já está logado
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        
    if not st.session_state['authenticated']:
        render_login_screen()
        st.stop() # Impede que o resto da página carregue
        
    # 2. Verifica permissão (RBAC + Granular)
    if required_role:
        # Passa 'module' como 'module_key'
        if not AuthService.check_permission(required_role, module_key=module):
            st.error(f"⛔ Acesso Negado: Você não tem permissão de nível '{required_role.upper()}' para acessar este módulo.")
            st.stop()
            
    # 3. Sidebar com Infos do Usuário
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"**👤 Usuário:** {st.session_state.get('name', 'User')}")
        
        role = st.session_state.get('user_role', 'viewer')
        st.markdown(f"**🔑 Perfil Global:** {role.upper()}")
        
        if st.button("🚪 Sair (Logout)"):
            keys_to_clear = ['authenticated', 'user_role', 'username', 'name', 'user_permissions']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

def render_login_screen():
    """Renderiza a tela de login."""
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background: #1e293b;
            border-radius: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #334155;
            text-align: center;
        }
        .login-title {
            color: #f1f5f9;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .login-subtitle {
            color: #94a3b8;
            font-size: 14px;
            margin-bottom: 24px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="font-size: 60px;">🔐</h1>
            <h2 style="color: #f1f5f9;">Acesso Restrito</h2>
            <p style="color: #94a3b8;">Sistema de Gestão Financeira v2.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Usuário", placeholder="admin")
            password = st.text_input("Senha", type="password", placeholder="••••••")
            
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.warning("⚠️ Preencha todos os campos.")
                else:
                    user = AuthService.verify_user(username, password)
                    if user:
                        st.session_state['authenticated'] = True
                        st.session_state['username'] = user.username
                        st.session_state['name'] = user.name
                        st.session_state['user_role'] = user.role
                        st.session_state['user_permissions'] = user.permissions # Load permissions
                        st.success(f"Bem-vindo, {user.name}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos.")


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
    from database.models import init_db
    
    # Garantir que o banco de dados (tabelas) exista (Executa apenas 1x devido ao cache)
    try:
        init_db()
        from services.auth_service import AuthService
        AuthService.create_initial_admin()
    except Exception as e:
        st.error(f"Erro Crítico ao conectar no Banco de Dados: {e}")
        
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
            st.session_state['ai_provider'] = "Gemini 3 Pro"
            
        provider = st.selectbox(
            "🧠 Provedor de Inteligência",
            ["Gemini 3 Pro", "Gemini 3 Flash"],
            index=0 if "Pro" in st.session_state['ai_provider'] else 1
        )
        st.session_state['ai_provider'] = provider
        
        # Indicador de Status
        if st.session_state['api_key']:
            st.success("IA Habilitada ✅")
        else:
            st.warning("IA Desabilitada ⚠️")
            
        st.divider()
        
        # Monitoramento de Conexão de Banco de Dados (Verificação de Segurança)
        st.markdown("### 🛢️ Status do Banco de Dados")
        try:
            from database.models import get_engine
            engine = get_engine()
            url_str = str(engine.url)
            
            if "postgresql" in url_str:
                st.success("🟢 Conectado: Neon (Postgres)")
                st.caption(f"Host: ...{url_str.split('@')[1].split(':')[0][-15:]}") # Mostra parte do host para confirmar
            else:
                st.warning("🟡 Conectado: SQLite (Local)")
                st.caption("Armazenamento local temporário")
                
        except Exception as e:
            st.error(f"🔴 Erro de Conexão: {str(e)[:20]}...")

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
