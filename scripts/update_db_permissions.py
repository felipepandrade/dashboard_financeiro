"""
Script to add 'permissions' column to users table if it doesn't exist.
Run manually: python scripts/update_db_permissions.py
"""
import sys
import os
from sqlalchemy import text, inspect

# Adiciona diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import get_engine

def update_schema():
    print("Verificando schema do banco de dados...")
    engine = get_engine()
    inspector = inspect(engine)
    
    columns = [c['name'] for c in inspector.get_columns('users')]
    
    if 'permissions' not in columns:
        print("Coluna 'permissions' não encontrada. Adicionando...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN permissions TEXT DEFAULT '{}'"))
            conn.commit()
        print("Coluna 'permissions' adicionada com sucesso!")
    else:
        print("Coluna 'permissions' já existe.")

if __name__ == "__main__":
    update_schema()
