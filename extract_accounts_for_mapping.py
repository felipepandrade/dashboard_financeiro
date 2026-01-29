import pandas as pd
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

# Import utils (suppress streamlit warnings if possible, but they go to stderr usually)
try:
    from utils_financeiro import processar_pl_baseal
    from data.referencias_manager import carregar_contas_contabeis
except ImportError as e:
    print(f"Error importing utils: {e}")
    sys.exit(1)

def main():
    print(">>> Extracting Accounts for Mapping...")
    
    # 1. Source: P&L Accounts (English)
    pl_path = "Doc referencia/P&L - Dezembro_2025.xlsx"
    if not os.path.exists(pl_path):
        print(f"File not found: {pl_path}")
        return

    try:
        with open(pl_path, "rb") as f:
            df_pl = processar_pl_baseal(f)
        
        if df_pl.empty:
            print("P&L DataFrame is empty.")
            return
            
        pl_accounts = sorted(df_pl['conta_contabil'].dropna().unique().astype(str))
        print(f"Found {len(pl_accounts)} unique accounts in P&L.")
        
    except Exception as e:
        print(f"Error reading P&L: {e}")
        return

    # 2. Target: System Accounts (Portuguese)
    try:
        df_sys = carregar_contas_contabeis()
        if df_sys.empty:
            print("System Accounts DataFrame is empty.")
            return
            
        # Create list of strings "CODE | DESC" for easy reading
        sys_accounts = []
        for _, row in df_sys.iterrows():
            sys_accounts.append(f"{row['codigo']} | {row['descricao']}")
            
        print(f"Found {len(sys_accounts)} unique accounts in System Reference.")
        
    except Exception as e:
        print(f"Error reading System Accounts: {e}")
        return

    # 3. Save to file for AI analysis (Agent will read this file)
    output_file = "temp_accounts_extraction.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"--- SOURCE ACCOUNTS (P&L - English) ---\n")
        for acc in pl_accounts:
            f.write(f"{acc}\n")
            
        f.write(f"\n--- TARGET ACCOUNTS (SYSTEM - Portuguese) ---\n")
        for acc in sys_accounts:
            f.write(f"{acc}\n")
            
    print(f"Extraction saved to {output_file}")

if __name__ == "__main__":
    main()
