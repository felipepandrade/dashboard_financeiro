
import pandas as pd

FILE_PATH = "Doc referencia/P&L - Dezembro_2025.xlsx"
xl = pd.ExcelFile(FILE_PATH)
df = xl.parse(xl.sheet_names[0], header=None) # Read without header to see raw grid

print("Linhas 10 a 20:")
print(df.iloc[10:21].to_string())
