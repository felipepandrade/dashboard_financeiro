
import bcrypt
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
    def check_permission(required_role: str) -> bool:
        """
        Verifica se o usuário atual tem permissão baseada em hierarquia de roles.
        Hierarquia: admin > editor > viewer
        """
        if 'user_role' not in st.session_state or not st.session_state['user_role']:
            return False
            
        current_role = st.session_state['user_role']
        
        # Mapa de níveis de acesso
        levels = {
            'admin': 3,
            'editor': 2,
            'viewer': 1
        }
        
        user_level = levels.get(current_role, 0)
        required_level = levels.get(required_role, 99) # Se role desconhecida, bloqueia
        
        return user_level >= required_level

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
                role=role
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
            
            # Impedir auto-deleção do user logado (opcional, mas boa prática de UI) ou admin principal
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
