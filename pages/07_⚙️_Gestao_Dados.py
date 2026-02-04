"""
06_⚙️_Gestao_Dados.py
======================
Módulo de Gestão de Dados e Schema.
Permite visualizar, editar e excluir registros do banco de dados,
além de fornecer interface para evoluções de schema (colunas novas).
"""

import streamlit as st
import pandas as pd
from sqlalchemy import text
import sys
import os

# Adicionar root ao path se necessário
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.models import get_session, LancamentoRealizado, Provisao, Remanejamento, ForecastCenario, DATABASE_PATH
from utils_ui import setup_page, CORES, require_auth

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

setup_page("Gestão de Dados", "⚙️")
require_auth("admin", module='dados')

if 'admin_mode' not in st.session_state:
    st.session_state['admin_mode'] = False

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

from sqlalchemy import inspect

def get_table_names():
    """Retorna lista de tabelas do banco (Compatível Postgres/SQLite)."""
    session = get_session()
    try:
        inspector = inspect(session.bind)
        return inspector.get_table_names()
    except Exception as e:
        st.error(f"Erro ao listar tabelas: {e}")
        return []
    finally:
        session.close()

# ... (rest of code)



def load_data(table_name):
    """Carrega dados de uma tabela."""
    session = get_session()
    try:
        # Cuidado aqui: SQL Injection evitado pois values vem de lista fixa get_table_names()
        # Mas para garantir, usamos pandas read_sql com session.bind
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(text(query), session.bind)
        return df
    except Exception as e:
        st.error(f"Erro ao ler tabela: {e}")
        return pd.DataFrame()
    finally:
        session.close()

def run_migration_add_column(table, column, col_type):
    """Executa comando alembic ou SQL direto para adicionar coluna."""
    # Para simplicidade via UI, usamos SQL direto (ALTER TABLE)
    # Alembic é ideal para versionamento em arquivos, mas aqui o usuário quer agilidade "on the fly".
    # Podemos registrar isso criando uma migration alembic programaticamente se quisermos ser puristas,
    # mas um ALTER TABLE ADD COLUMN direto funciona no SQLite.
    
    session = get_session()
    try:
        # Mapeamento tipos
        type_map = {
            "Texto": "TEXT",
            "Inteiro": "INTEGER",
            "Decimal": "REAL",
            "Data": "DATETIME"
        }
        sql_type = type_map.get(col_type, "TEXT")
        
        cmd = f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"
        session.execute(text(cmd))
        session.commit()
        return True, "Coluna adicionada com sucesso!"
    except Exception as e:
        return False, str(e)
    finally:
        session.close()

# =============================================================================
# INTERFACE
# =============================================================================

st.markdown("### ⚙️ Gestão de Banco de Dados")

tab_dados, tab_schema = st.tabs(["📝 Editar Dados", "🔧 Estrutura (Schema)"])

# -----------------------------------------------------------------------------
# ABA 1: DADOS (CRUD)
# -----------------------------------------------------------------------------
with tab_dados:
    st.info("💡 Edite dados diretamente na tabela. Pressione 'Enter' para confirmar a célula e depois 'Salvar Alterações'.")
    
    tabelas = get_table_names()
    tabela_sel = st.selectbox("Selecione a Tabela:", tabelas)
    
    if tabela_sel:
        # Carregar dados
        if f'df_{tabela_sel}' not in st.session_state:
            st.session_state[f'df_{tabela_sel}'] = load_data(tabela_sel)
            
        df = st.session_state[f'df_{tabela_sel}']
        
        # Editor de Dados
        edited_df = st.data_editor(
            df,
            num_rows="dynamic", # Permite adicionar/remover
            use_container_width=True,
            key=f"editor_{tabela_sel}"
        )
        
        col_actions = st.columns([1, 4])
        if col_actions[0].button("💾 Salvar Alterações"):
            # Lógica de salvar é complexa pois data_editor retorna o estado final
            # O ideal é detectar diffs.
            # Implementação simplificada: Truncate e Insert All (PERIGOSO PARA GRANDES DADOS)
            # Implementação Segura: Usar library ou lógica de diff.
            
            # Vamos usar uma abordagem de upsert baseada no ID se existir, ou insert.
            # Como data_editor não retorna o que foi deletado facilmente sem comparar sessions...
            # Para este MVP, vamos alertar o usuário.
            
            try:
                session = get_session()
                # 1. Transformar DF editado em dicts
                records = edited_df.to_dict('records')
                
                # 2. Bulk Insert/Replace é arriscado.
                # Vamos iterar e fazer merge. 
                # SQLite tem REPLACE INTO mas deleta e cria novo ID.
                
                # Melhor estratégia segura para este contexto "Admin":
                # Salvar o DF inteiro sobrescrevendo a tabela (se tabela nao for gigante).
                # tabelas financeiras mensais costumam ter < 10k linhas, aceitável.
                
                edited_df.to_sql(tabela_sel, session.bind, if_exists='replace', index=False)
                
                st.success("Dados salvos com sucesso!")
                st.session_state[f'df_{tabela_sel}'] = edited_df # Atualiza cache
                session.close()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# -----------------------------------------------------------------------------
# ABA 2: SCHEMA (EVOLUÇÃO)
# -----------------------------------------------------------------------------
with tab_schema:
    st.warning("⚠️ Cuidado: Alterações de estrutura afetam todo o sistema.")
    
    col_sch1, col_sch2 = st.columns(2)
    
    with col_sch1:
        st.subheader("Adicionar Nova Coluna")
        tabela_target = st.selectbox("Tabela Alvo:", tabelas, key="schema_table")
        nova_coluna = st.text_input("Nome da Nova Coluna (sem espaços):", placeholder="ex: centro_custo_secundario")
        tipo_coluna = st.selectbox("Tipo de Dado:", ["Texto", "Inteiro", "Decimal", "Data"])
        
        if st.button("Adicionar Coluna"):
            if not nova_coluna:
                st.error("Nome da coluna obrigatório.")
            else:
                sucesso, msg = run_migration_add_column(tabela_target, nova_coluna, tipo_coluna)
                if sucesso:
                    st.success(msg)
                    st.balloons()
                    # Limpar cache para recarregar com nova coluna
                    if f'df_{tabela_target}' in st.session_state:
                        del st.session_state[f'df_{tabela_target}']
                else:
                    st.error(f"Erro: {msg}")
                    
    with col_sch2:
        st.subheader("Status do Banco")
        
        # Detecção de tipo de banco para exibir info adequada
        session = get_session()
        is_sqlite = 'sqlite' in str(session.bind.url)
        session.close()
        
        if is_sqlite:
            st.text(f"Arquivo: {DATABASE_PATH}")
            try:
                size_kb = os.path.getsize(DATABASE_PATH) / 1024
                st.metric("Tamanho do Arquivo", f"{size_kb:.2f} KB")
            except:
                st.warning("Arquivo local não encontrado.")
        else:
            st.info("☁️ Conectado ao Neon (Postgres)")
            st.caption("Gerenciado via Cloud")

# =============================================================================
# RODAPÉ
# =============================================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {CORES['text_secondary']}; font-size: 12px;">
    Módulo Administrativo • Baseal 2026
</div>
""", unsafe_allow_html=True)
