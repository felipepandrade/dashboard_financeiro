
import pandas as pd
import sys

# Forçar encoding utf-8 no stdout para evitar erro no Windows
sys.stdout.reconfigure(encoding='utf-8')

FILE_PATH = "Doc referencia/P&L - Dezembro_2025.xlsx"
xl = pd.ExcelFile(FILE_PATH)
df = xl.parse(xl.sheet_names[0], header=None)

print("--- ANALISE DE CABEÇALHO ---")
# Row 0: Dates
# Row 3: Metrics? (Actual, Budget)? Let's check row 3 or 4
print("Linha 0 (Datas):")
for i, val in enumerate(df.iloc[0]):
    if pd.notna(val):
        print(f"Col {i}: {val}")

print("\nLinha 3:") # Checking for metric names
for i, val in enumerate(df.iloc[3]):
    if pd.notna(val):
        print(f"Col {i}: {val}")
        
print("\n--- ANALISE DE DADOS (Esq) ---")
# Print first 5 cols of rows 15-20 (Assuming header ends before 15)
for idx, row in df.iloc[15:21, 0:5].iterrows():
    print(f"Row {idx}: {row.tolist()}")
