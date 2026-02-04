
import sys
import os
import streamlit as st

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import get_session, LancamentoRealizado, get_engine
from sqlalchemy import extract, text

def verify_data():
    print("--- DIAGNOSTICO DE DADOS ---")
    
    # 1. Check Config
    db_url = os.getenv("DATABASE_URL")
    print(f"Env DATABASE_URL: {'[SET]' if db_url else '[NOT SET]'}")
    
    if not db_url:
        # Try secrets mock
        try:
             if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
                 print("Streamlit Secrets: [FOUND]")
             else:
                 print("Streamlit Secrets: [NOT FOUND]")
        except:
             pass
             
    # 2. Check Connection
    try:
        engine = get_engine()
        print(f"Engine Dialect: {engine.dialect.name}")
        
        with engine.connect() as conn:
            print("Connection Successful!")
            
            # Check Table
            try:
                result = conn.execute(text("SELECT count(*) FROM lancamentos_realizados WHERE ano = 2026"))
                count = result.scalar()
                print(f"Total entries for 2026: {count}")
                
                 # Check Total Realized Value
                result_val = conn.execute(text("SELECT sum(valor) FROM lancamentos_realizados WHERE ano = 2026"))
                total_val = result_val.scalar()
                print(f"Total Value for 2026: {total_val}")

            except Exception as e:
                print(f"Query Failed: {e}")
                
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    verify_data()
