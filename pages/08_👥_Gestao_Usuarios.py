from utils_ui import setup_page, require_auth
from services.auth_service import AuthService
import streamlit as st
import pandas as pd
import json

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Gerenciamento de Usuários", "👥")
require_auth("admin")

st.markdown("""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="color: #f1f5f9; font-size: 32px;">👥 Painel Administrativo</h1>
    <p style="color: #94a3b8;">Gerenciamento de Usuários e Permissões (RBAC)</p>
</div>
""", unsafe_allow_html=True)

# Lista completa de módulos
modulos_disponiveis = [
    "analise_financeira",
    "lancamentos",
    "acompanhamento",
    "biblia",
    "controle",
    "previsao",
    "dados"
]

# =============================================================================
# ESTADO E TABS
# =============================================================================

tab_lista, tab_novo = st.tabs(["📋 Usuários e Permissões", "➕ Cadastrar Novo Usuário"])

# =============================================================================
# TAB 1: LISTAR E EDITAR
# =============================================================================
with tab_lista:
    users = AuthService.list_users()
    
    if users:
        df = pd.DataFrame(users)
        
        # Parse permissions for display
        def format_perms(p):
            try:
                d = json.loads(p)
                return ", ".join([f"{k}:{v}" for k,v in d.items()])
            except:
                return ""
        
        df['perms_display'] = df['permissions'].apply(format_perms)
        
        with st.container():
            st.markdown("### 📋 Lista de Usuários")
            st.dataframe(
                df[['id', 'username', 'name', 'role', 'perms_display', 'created_at']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "username": "Login",
                    "name": "Nome Completo",
                    "role": st.column_config.TextColumn("Global Role", width="small"),
                    "perms_display": "Permissões Específicas",
                    "created_at": "Data Criação"
                }
            )
        
        st.divider()
        st.markdown("### 🛠️ Ações e Edição")
        
        col_sel, col_act = st.columns([1, 2])
        
        with col_sel:
            user_options = [f"{u['username']}" for u in users]
            selected_username = st.selectbox("Selecione o Usuário:", options=["Selecione..."] + user_options)
        
        if selected_username and selected_username != "Selecione...":
            # Obter dados atuais do usuário selecionado
            current_user_data = next(u for u in users if u['username'] == selected_username)
            current_perms = json.loads(current_user_data.get('permissions', '{}'))
            
            with col_act:
                # =================================================================
                # PAINEL DE EDIÇÃO (NOVA FEATURE)
                # =================================================================
                with st.expander("📝 Editar Dados e Permissões", expanded=True):
                    with st.form("form_edit_user"):
                        st.subheader(f"Editando: {current_user_data['name']}")
                        
                        e_name = st.text_input("Nome Completo", value=current_user_data['name'])
                        e_role = st.selectbox("Role Global", ["viewer", "editor", "admin"], 
                                            index=["viewer", "editor", "admin"].index(current_user_data['role']))
                        
                        st.markdown("**Permissões Granulares por Módulo**")
                        st.caption("Defina permissões específicas que sobrescrevem a role global (exceto Admin).")
                        
                        new_perms = {}
                        cols = st.columns(2)
                        for i, mod in enumerate(modulos_disponiveis):
                            col = cols[i % 2]
                            # Existing val
                            val = current_perms.get(mod, "default")
                            options = ["default", "viewer", "editor", "admin"]
                            idx = options.index(val) if val in options else 0
                            
                            sel = col.selectbox(f"Módulo: {mod}", options, index=idx, key=f"sel_{mod}")
                            if sel != "default":
                                new_perms[mod] = sel
                        
                        st.markdown("---")
                        btn_update = st.form_submit_button("💾 Salvar Alterações", type="primary")
                        
                        if btn_update:
                            success, msg = AuthService.update_user(
                                selected_username, 
                                name=e_name, 
                                role=e_role, 
                                permissions=new_perms
                            )
                            if success:
                                st.success("Dados atualizados com sucesso!")
                                st.rerun()
                            else:
                                st.error(msg)

                # Ações Antigas
                with st.expander("🔑 Redefinir Senha"):
                    with st.form("form_reset_password"):
                        new_pwd_1 = st.text_input("Nova Senha", type="password")
                        new_pwd_2 = st.text_input("Confirmar", type="password")
                        if st.form_submit_button("Alterar Senha"):
                            if new_pwd_1 == new_pwd_2 and new_pwd_1:
                                success, msg = AuthService.update_password(selected_username, new_pwd_1)
                                if success: st.success("Senha alterada!")
                                else: st.error(msg)
                            else:
                                st.error("Senhas inválidas.")

                with st.expander("🗑️ Excluir Usuário"):
                    if st.button("Excluir Permanentemente"):
                         if selected_username == st.session_state.get('username'):
                            st.error("Não pode excluir a si mesmo.")
                         else:
                            AuthService.delete_user(selected_username)
                            st.rerun()

# =============================================================================
# TAB 2: NOVO USUÁRIO
# =============================================================================
with tab_novo:
    st.markdown("### 🆕 Cadastro (Simples)")
    with st.form("form_new_user", clear_on_submit=True):
        c1, c2 = st.columns(2)
        u = c1.text_input("Usuário")
        n = c1.text_input("Nome")
        r = c1.selectbox("Role Inicial", ["viewer", "editor", "admin"])
        p1 = c2.text_input("Senha", type="password")
        p2 = c2.text_input("Confirmar", type="password")
        
        if st.form_submit_button("Criar Usuário"):
            if p1 == p2 and u and p1:
                success, msg = AuthService.create_user(u, p1, n, r)
                if success: st.success("Criado! Vá para a aba 'Lista' para configurar permissões finas.")
                else: st.error(msg)
            else:
                st.error("Preencha corretamente.")
