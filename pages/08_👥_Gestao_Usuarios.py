from utils_ui import setup_page, require_auth
from services.auth_service import AuthService
import streamlit as st
import pandas as pd

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Gerenciamento de Usuários", "👥")
require_auth("admin")

st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #f1f5f9; font-size: 32px;">👥 Painel Administrativo</h1>
    <p style="color: #94a3b8;">Gerenciamento de Usuários e Acessos (RBAC)</p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# ESTADO E TABS
# =============================================================================

tab_lista, tab_novo = st.tabs(["📋 Usuários Cadastrados", "➕ Cadastrar Novo Usuário"])

# =============================================================================
# TAB 1: LISTAR USUÁRIOS
# =============================================================================
with tab_lista:
    users = AuthService.list_users()
    
    if users:
        df = pd.DataFrame(users)
        
        with st.container():
            st.markdown("### 📋 Lista de Usuários")
            st.dataframe(
                df[['id', 'username', 'name', 'role', 'created_at']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "username": "Login",
                    "name": "Nome Completo",
                    "role": st.column_config.TextColumn("Permissão", width="small"),
                    "created_at": "Data Criação"
                }
            )
        
        st.divider()
        st.markdown("### 🛠️ Ações de Usuário")
        
        col_sel, col_act = st.columns([1, 2])
        
        with col_sel:
            # Lista de usuários para seleção (Logicamente não exibe senha)
            # Formato: "username - nome"
            user_options = [f"{u['username']}" for u in users]
            selected_username = st.selectbox("Selecione o Usuário para Alterar:", options=["Selecione..."] + user_options)
        
        if selected_username and selected_username != "Selecione...":
            with col_act:
                # Painel de Ações
                st.info(f"Usuário Selecionado: **{selected_username}**")
                
                with st.expander("🔑 Redefinir Senha (Admin Reset)"):
                    with st.form("form_reset_password"):
                        new_pwd_1 = st.text_input("Nova Senha", type="password")
                        new_pwd_2 = st.text_input("Confirmar Nova Senha", type="password")
                        btn_reset = st.form_submit_button("Redefinir Senha")
                        
                        if btn_reset:
                            if new_pwd_1 != new_pwd_2:
                                st.error("As senhas não coincidem.")
                            elif not new_pwd_1:
                                st.error("A senha não pode estar vazia.")
                            else:
                                success, msg = AuthService.update_password(selected_username, new_pwd_1)
                                if success:
                                    st.success(f"Senha de {selected_username} redefinida com sucesso!")
                                else:
                                    st.error(msg)
                
                with st.expander("🗑️ Excluir Usuário"):
                    st.warning("Ação Irreversível! O usuário será removido permanentemente.")
                    if st.button("Confirmar Exclusão do Usuário", type="primary"):
                        if selected_username == st.session_state.get('username'):
                            st.error("Você não pode excluir a si mesmo.")
                        else:
                            success, msg = AuthService.delete_user(selected_username)
                            if success:
                                st.success(f"Usuário {selected_username} removido!")
                                st.rerun()
                            else:
                                st.error(msg)

# =============================================================================
# TAB 2: NOVO USUÁRIO
# =============================================================================
with tab_novo:
    st.markdown("### 🆕 Cadastro de Usuário")
    st.info("Crie novos acessos para a plataforma. Defina a função (Role) corretamente.")
    
    with st.form("form_new_user", clear_on_submit=True):
        col_n1, col_n2 = st.columns(2)
        
        with col_n1:
            new_username = st.text_input("Login (Usuário)", placeholder="ex: joao.silva")
            new_name = st.text_input("Nome Completo", placeholder="ex: João Silva")
            new_role = st.selectbox("Perfil de Acesso (Role)", ["viewer", "editor", "admin"])
            
        with col_n2:
            st.markdown("**🔐 Definição de Senha Inicial**")
            n_pwd = st.text_input("Senha", type="password")
            n_pwd_conf = st.text_input("Confirmar Senha", type="password")
            
        st.markdown("---")
        submitted_new = st.form_submit_button("✅ Criar Usuário", type="primary", use_container_width=True)
        
        if submitted_new:
            # Validações
            errors = []
            if not new_username: errors.append("Username obrigatório")
            if not new_name: errors.append("Nome obrigatório")
            if not n_pwd: errors.append("Senha obrigatória")
            if n_pwd != n_pwd_conf: errors.append("Senhas não conferem")
            
            if errors:
                for e in errors: st.error(f"❌ {e}")
            else:
                success, msg = AuthService.create_user(new_username, n_pwd, new_name, new_role)
                if success:
                    st.success(f"Usuário {new_username} criado com sucesso!")
                    st.balloons()
                else:
                    st.error(msg)
