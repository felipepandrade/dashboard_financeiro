
import sys
import os

# Adiciona o diretório raiz ao path para encontrar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, get_engine
from services.auth_service import AuthService

def update_schema():
    print("Conectando ao banco de dados...")
    engine = get_engine()
    
    # Cria as tabelas que ainda não existem
    print("Criando tabelas novas...")
    Base.metadata.create_all(engine)
    print("Schema atualizado!")
    
    # Cria admin se necessário
    print("Verificando usuario admin...")
    AuthService.create_initial_admin()

if __name__ == "__main__":
    update_schema()
