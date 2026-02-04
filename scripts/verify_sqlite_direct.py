
import sqlite3
import os

DB_PATH = r"c:\Aplicativos Desenvolvidos\dashboard_financeiro\data\database\lancamentos_2026.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("--- Checking Table: lancamentos_realizados ---")
        try:
            # Check count for 2026
            cursor.execute("SELECT count(*) FROM lancamentos_realizados WHERE ano = 2026")
            count = cursor.fetchone()[0]
            print(f"Total entries for 2026: {count}")
            
            if count > 0:
                # Group by month
                cursor.execute("SELECT mes, count(*) FROM lancamentos_realizados WHERE ano = 2026 GROUP BY mes")
                rows = cursor.fetchall()
                print("Entries by month:", dict(rows))
            else:
                print("No entries found for 2026.")
                
        except sqlite3.OperationalError as e:
            print(f"Query Error (table might not exist): {e}")
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            print("Tables:", [r[0] for r in cursor.fetchall()])

        conn.close()
        
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    check_db()
