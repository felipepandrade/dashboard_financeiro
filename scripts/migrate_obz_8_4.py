
import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/database/lancamentos_2026.db")

def migrate_obz():
    if not DATABASE_PATH.exists():
        print(f"Banco de dados não encontrado em {DATABASE_PATH}")
        return

    print(f"Conectando ao banco: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Criar Tabela OBZ
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS obz_justificativas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        centro_gasto_codigo VARCHAR(11) NOT NULL,
        pacote VARCHAR(100) NOT NULL,
        descricao TEXT NOT NULL,
        valor_orcado REAL NOT NULL,
        classificacao VARCHAR(20) NOT NULL,
        usuario_responsavel VARCHAR(100),
        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        print("Criando tabela obz_justificativas...")
        cursor.execute(create_table_sql)
        
        # Criar índice para performance de filtro por centro
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_obz_centro ON obz_justificativas(centro_gasto_codigo);")
        
        print("Tabela obz_justificativas criada com sucesso.")
    except Exception as e:
        print(f"Erro ao criar tabela: {e}")

    conn.commit()
    conn.close()
    print("Migração concluída.")

if __name__ == "__main__":
    migrate_obz()
