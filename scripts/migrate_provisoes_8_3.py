
import sqlite3
from pathlib import Path

# Caminho do banco (ajuste conforme necessário baseado na estrutura do projeto)
# O script será rodado da raiz do projeto, então o caminho relativo deve funcionar
DATABASE_PATH = Path("data/database/lancamentos_2026.db")

def migrate():
    if not DATABASE_PATH.exists():
        print(f"Banco de dados não encontrado em {DATABASE_PATH}")
        return

    print(f"Conectando ao banco: {DATABASE_PATH}")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Colunas para adicionar
    colunas = [
        ("numero_contrato", "VARCHAR(50)"),
        ("cadastrado_sistema", "BOOLEAN DEFAULT 0"),
        ("numero_registro", "VARCHAR(50)")
    ]
    
    for nome_col, tipo_col in colunas:
        try:
            print(f"Adicionando coluna {nome_col}...")
            cursor.execute(f"ALTER TABLE provisoes ADD COLUMN {nome_col} {tipo_col}")
            print(f"Coluna {nome_col} adicionada com sucesso.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Coluna {nome_col} já existe.")
            else:
                print(f"Erro ao adicionar {nome_col}: {e}")

    conn.commit()
    conn.close()
    print("Migração concluída.")

if __name__ == "__main__":
    migrate()
