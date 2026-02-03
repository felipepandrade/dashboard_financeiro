
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Adicionar raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from database.models import Base, get_engine

# Configuração SQLite (Origem)
SQLITE_PATH = Path(__file__).parent.parent / "data" / "database" / "lancamentos_2026.db"
SQLITE_URL = f"sqlite:///{SQLITE_PATH}"

# Configuração Postgres (Destino - via .env ou models.py)
# Nota: get_engine() já pega o Postgres se o .env estiver carregado
# Mas queremos forçar duas conexões distintas aqui.

def migrate_data():
    print("🚀 Iniciando migração SQLite -> Postgres...")
    
    # 1. Conectar na Origem (SQLite)
    print(f"📂 Lendo SQLite: {SQLITE_PATH}")
    engine_sqlite = create_engine(SQLITE_URL)
    SessionSQLite = sessionmaker(bind=engine_sqlite)
    session_sqlite = SessionSQLite()
    
    # 2. Conectar no Destino (Postgres)
    # Vamos usar o get_engine() que já deve estar configurado com a URL do .env
    engine_pg = get_engine()
    
    if "sqlite" in str(engine_pg.url):
        print("❌ ERRO: O engine de destino parece ser SQLite.")
        print("Certifique-se de que o arquivo .env contém a DATABASE_URL do Neon.")
        return

    print(f"☁️  Conectado no Postgres: {engine_pg.url.host}")
    
    # 3. Criar Tabelas no Postgres (Schema)
    print("🏗️  Criando tabelas no Postgres...")
    Base.metadata.create_all(engine_pg)
    
    # 4. Migrar Dados
    SessionPG = sessionmaker(bind=engine_pg)
    session_pg = SessionPG()
    
    inspector = inspect(engine_sqlite)
    tables = inspector.get_table_names()
    
    for table_name in tables:
        # Pular tabela de migração do alembic por enquanto
        if table_name == 'alembic_version':
            continue
            
        print(f"📦 Migrando tabela: {table_name}...")
        
        # Ler dados do SQLite cru
        try:
            with engine_sqlite.connect() as conn_sqlite:
                rows = conn_sqlite.execute(text(f"SELECT * FROM {table_name}")).fetchall()
                
            if not rows:
                print(f"   ⚠️ Tabela vazia. Pulando.")
                continue
                
            print(f"   Found {len(rows)} rows.")
            
            # Pegar o modelo SQLAlchemy correspondente pelo Table Name
            # (Isso é um jeito dinâmico simples)
            TargetModel = None
            for mapper in Base.registry.mappers:
                if mapper.persist_selectable.name == table_name:
                    TargetModel = mapper.class_
                    break
            
            if not TargetModel:
                print(f"   ⚠️ Modelo não encontrado para tabela {table_name}. Pulando (talvez seja tabela auxiliar).")
                continue

            # Inserir no Postgres
            # Limpar tabela destino antes? (Opcional, aqui vamos assumir banco novo vazio)
            # session_pg.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            
            count = 0
            for row in rows:
                # Converter row (tuple) para dict baseada nas colunas
                # Precisamos mapear colunas... O jeito mais fácil é usar pandas para intermediar ou mapear manual
                # Vamos usar dict comprehension com keys do result set
                
                # SQLAlchemy Rows tem _mapping nos novos, ou keys() nos velhos
                row_dict = dict(row._mapping)
                
                # Criar objeto
                obj = TargetModel(**row_dict)
                session_pg.add(obj)
                count += 1
            
            session_pg.commit()
            print(f"   ✅ {count} registros inseridos com sucesso.")
            
        except Exception as e:
            print(f"   ❌ Erro ao migrar tabela {table_name}: {e}")
            session_pg.rollback()

    print("\n✨ Migração Concluída!")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv() # Garantir que carrega o .env
    migrate_data()
