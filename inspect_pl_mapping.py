
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

FILE_PATH = "Doc referencia/P&L - Dezembro_2025.xlsx"
xl = pd.ExcelFile(FILE_PATH)
df = xl.parse(xl.sheet_names[0], header=None)

print("Row 15 (Possible Header) Cols 0-25:")
print(df.iloc[15, 0:26].values)

print("\nRow 0 (Dates) Cols 0-25:")
print(df.iloc[0, 0:26].values)

print("\nRow 16 (Data Sample) Cols 0-25:")
print(df.iloc[16, 0:26].values)

# Check col 0 and 1 for non-nulls in data range
print("\nUnique values in Col 0 (Rows 16-50):")
print(df.iloc[16:50, 0].unique()) # Codes?

print("\nUnique values in Col 1 (Rows 16-50):")
print(df.iloc[16:50, 1].unique()) # Codes?
