from utils_ui import setup_page, require_auth, formatar_valor_brl
from services.auth_service import AuthService
import streamlit as st

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Meu Perfil", "👤")
require_auth() # Acesso permitido a todos logados

st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #f1f5f9; font-size: 32px;">👤 Meu Perfil</h1>
    <p style="color: #94a3b8;">Gerencie suas informações de acesso</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# =============================================================================
# DADOS DO USUÁRIO
# =============================================================================

col_info, col_pwd = st.columns([1, 1])

with col_info:
    st.markdown("### 📋 Dados da Conta")
    
    st.markdown(f"**Nome:** {st.session_state.get('name', 'N/A')}")
    st.markdown(f"**Usuário (Login):** {st.session_state.get('username', 'N/A')}")
    
    role = st.session_state.get('user_role', 'viewer')
    st.markdown(f"**Nível de Acesso:** `{role.upper()}`")
    
    if role == 'admin':
        st.success("✅ Você tem privilégios totais de Administrador.")
    elif role == 'editor':
        st.info("ℹ️ Você pode visualizar e editar dados.")
    else:
        st.warning("⚠️ Você possui acesso apenas de visualização.")

with col_pwd:
    st.markdown("### 🔐 Alterar Minha Senha")
    
    with st.form("form_change_own_password", clear_on_submit=True):
        current_user = st.session_state.get('username')
        
        # Opcional: Pedir senha atual para segurança (AuthService precisaria suportar check sem login full)
        # Para simplificar na V1, permitimos troca direta se logado. 
        # Idealmente: check_password(current_user, old_pwd)
        
        st.caption("Defina sua nova senha de acesso.")
        
        new_pwd_1 = st.text_input("Nova Senha", type="password")
        new_pwd_2 = st.text_input("Confirmar Nova Senha", type="password")
        
        submit_change = st.form_submit_button("Atualizar Senha", type="primary")
        
        if submit_change:
            if not current_user:
                st.error("Erro de sessão. Faça login novamente.")
            elif new_pwd_1 != new_pwd_2:
                st.error("As novas senhas não coincidem.")
            elif len(new_pwd_1) < 4:
                 st.error("A senha deve ter no mínimo 4 caracteres.")
            else:
                success, msg = AuthService.update_password(current_user, new_pwd_1)
                if success:
                    st.success("Sua senha foi atualizada com sucesso!")
                else:
                    st.error(msg)

st.divider()
st.markdown("*Em caso de problemas com seu acesso, contate o administrador do sistema.*")
