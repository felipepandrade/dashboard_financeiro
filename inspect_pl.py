
import pandas as pd

FILE_PATH = "Doc referencia/P&L - Dezembro_2025.xlsx"

try:
    xl = pd.ExcelFile(FILE_PATH)
    print(f"Abas encontradas: {xl.sheet_names}")
    
    # Ler primeira aba para ver colunas
    df = xl.parse(xl.sheet_names[0])
    print(f"\nColunas da primeira aba ({xl.sheet_names[0]}):")
    print(df.columns.tolist())
    
    print("\nPrimeiras 3 linhas:")
    print(df.head(3).to_string())
    
except Exception as e:
    print(f"Erro ao ler Excel: {e}")
