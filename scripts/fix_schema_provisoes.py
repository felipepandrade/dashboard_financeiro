import sys
import os
from sqlalchemy import text, inspect

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.models import get_session, get_engine

def fix_provisoes_schema():
    print("🔧 Iniciando Reparo de Schema: Tabela 'provisoes'...")
    session = get_session()
    engine = get_engine()
    
    try:
        # 1. Verificar colunas atuais
        insp = inspect(engine)
        cols = [c['name'] for c in insp.get_columns('provisoes')]
        pk_constraint = insp.get_pk_constraint('provisoes')
        
        print(f"📋 Colunas detectadas: {cols}")
        print(f"🔑 PK atual: {pk_constraint}")

        # Se não tem PK ou sequence, vamos consertar.
        # Postgres specific commands
        
        commands = [
            # 1. Garantir que ID é Not Null
            "ALTER TABLE provisoes ALTER COLUMN id SET NOT NULL;",
            
            # 2. Criar sequence se não existir (ou ignorar erro)
            "CREATE SEQUENCE IF NOT EXISTS provisoes_id_seq;",
            
            # 3. Vincular sequence ao ID (se já não estiver)
            "ALTER TABLE provisoes ALTER COLUMN id SET DEFAULT nextval('provisoes_id_seq');",
            
            # 4. Sincronizar sequence com o maior ID atual
            "SELECT setval('provisoes_id_seq', COALESCE((SELECT MAX(id) FROM provisoes), 0) + 1, false);",
            
            # 5. Restaurar PK Constraint (apenas se não detectou corretamente)
            # drop primeiro para garantir
            "ALTER TABLE provisoes DROP CONSTRAINT IF EXISTS provisoes_pkey;",
            "ALTER TABLE provisoes ADD PRIMARY KEY (id);"
        ]
        
        for cmd in commands:
            print(f"🚀 Executando: {cmd}")
            try:
                session.execute(text(cmd))
                session.commit()
            except Exception as e:
                print(f"⚠️ Aviso (pode ser normal): {e}")
                session.rollback()
                
        print("✅ Processo de reparo concluído!")
        
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    fix_provisoes_schema()
