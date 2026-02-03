
import bcrypt
import json
from sqlalchemy.orm import Session
from database.models import User, get_session
import streamlit as st

class AuthService:
    """
    Serviço para gerenciamento de autenticação e usuários.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Gera o hash da senha usando bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        """Verifica se a senha corresponde ao hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def verify_user(username: str, password: str) -> User:
        """
        Verifica credenciais e retorna o usuário se válido.
        Retorna None se inválido.
        """
        session = get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            
            if user and AuthService.check_password(password, user.password_hash):
                return user
            return None
        finally:
            session.close()

    @staticmethod
    def create_initial_admin():
        """Cria o usuário admin padrão se não existir nenhum usuário."""
        session = get_session()
        try:
            if session.query(User).count() == 0:
                print("Nenhum usuario encontrado. Criando admin padrao...")
                hashed = AuthService.hash_password("admin123")
                admin = User(
                    username="admin",
                    password_hash=hashed,
                    name="Administrador do Sistema",
                    role="admin"
                )
                session.add(admin)
                session.commit()
                print("Usuario 'admin' criado com sucesso!")
        except Exception as e:
            print(f"Erro ao criar admin inicial: {e}")
        finally:
            session.close()

    @staticmethod
    def check_permission(required_role: str, module_key: str = None) -> bool:
        """
        Verifica se o usuário atual tem permissão.
        1. Se module_key for informado, checa a permissão específica naquele módulo (JSON).
           Se não houver definição específica, fallback para a role global.
        2. Se apenas required_role for informado, checa a role global.
        
        Hierarquia: admin > editor > viewer
        """
        if 'user_role' not in st.session_state or not st.session_state['user_role']:
            return False
            
        current_role = st.session_state['user_role']
        
        # Mapa de níveis de acesso
        levels = {
            'admin': 3,
            'editor': 2,
            'viewer': 1,
            'none': 0
        }
        
        # Nível global do usuário
        user_global_level = levels.get(current_role, 0)
        
        # 1. Super-Admin Global tem acesso a tudo (exceto se explicitamente bloqueado? Não, admin é deus)
        if user_global_level >= 3:
            return True
        
        # 2. Verifica permissão específica do módulo, se solicitada
        if module_key:
            permissions_json = st.session_state.get('user_permissions', '{}') # Use chave correta da sessão
            try:
                if isinstance(permissions_json, str):
                    permissions = json.loads(permissions_json)
                else:
                    permissions = permissions_json if isinstance(permissions_json, dict) else {}
                
                module_role = permissions.get(module_key)
                
                # Se houver uma definição específica para o módulo, usa ela
                if module_role:
                    user_module_level = levels.get(module_role, 0)
                    required_level = levels.get(required_role, 99)
                    return user_module_level >= required_level
                    
            except Exception:
                pass # Ignora erro de parse, usa global
        
        # Fallback: Validação pela Role Global
        required_level = levels.get(required_role, 99)
        return user_global_level >= required_level

    # =========================================================================
    # USER MANAGEMENT METHODS (CRUD)
    # =========================================================================

    @staticmethod
    def list_users() -> list:
        """Lista todos os usuários cadastrados (sem campos sensíveis)."""
        session = get_session()
        try:
            users = session.query(User).all()
            return [u.to_dict() for u in users]
        finally:
            session.close()

    @staticmethod
    def create_user(username, password, name, role):
        """Cria um novo usuário."""
        session = get_session()
        try:
            if session.query(User).filter(User.username == username).first():
                return False, "Usuário já existe"
            
            hashed = AuthService.hash_password(password)
            new_user = User(
                username=username,
                password_hash=hashed,
                name=name,
                role=role,
                permissions='{}' # Default empty JSON
            )
            session.add(new_user)
            session.commit()
            return True, "Usuário criado com sucesso!"
        except Exception as e:
            return False, f"Erro ao criar usuário: {e}"
        finally:
            session.close()

    @staticmethod
    def delete_user(username):
        """Remove um usuário pelo username."""
        session = get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False, "Usuário não encontrado"
            
            if username == 'admin':
                 return False, "Não é possível remover o super-admin."

            session.delete(user)
            session.commit()
            return True, "Usuário removido com sucesso!"
        except Exception as e:
            return False, f"Erro ao remover: {e}"
        finally:
            session.close()

    @staticmethod
    def update_password(username, new_password):
        """Atualiza a senha de um usuário."""
        session = get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False, "Usuário não encontrado"
            
            user.password_hash = AuthService.hash_password(new_password)
            session.commit()
            return True, "Senha atualizada com sucesso!"
        except Exception as e:
            return False, f"Erro ao atualizar senha: {e}"
        finally:
            session.close()

    @staticmethod
    def update_user(username, name=None, role=None, permissions=None):
        """Atualiza dados cadastrais e permissões de um usuário."""
        session = get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if not user:
                return False, "Usuário não encontrado"
            
            if username == 'admin' and role != 'admin':
                return False, "Não é possível rebaixar o super-admin."

            if name: user.name = name
            if role: user.role = role
            
            if permissions is not None:
                if isinstance(permissions, dict):
                    user.permissions = json.dumps(permissions)
                else:
                    user.permissions = str(permissions)

            session.commit()
            return True, "Dados atualizados com sucesso!"
        except Exception as e:
            return False, f"Erro ao atualizar dados: {e}"
        finally:
            session.close()
