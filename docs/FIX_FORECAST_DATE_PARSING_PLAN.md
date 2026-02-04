# Fix Forecast Date Parsing Plan

## Problem

`ValueError: time data "FEV/2026" doesn't match format "%b/%Y"` in `pages/06_🔮_Previsao_IA.py` due to locale mismatch.

## Solution

Replace `pd.to_datetime(..., format='%b/%Y')` with explicit dictionary mapping for months.

### Changes

In `pages/06_🔮_Previsao_IA.py`:

- Remove line 162.
- Ensure lines 179-181 (which already implement robust logic) cover the requirements or are moved up if `data_adapter` needs the date early.
- Actually, looking at the code, line 162 modifies `data_adapter` but the `groupby` on line 173 uses `data_adapter` which groups by 'mes' string, and then `df_total` *re-calculates* the date on lines 179-181.
- **Therefore, line 162 is REDUNDANT and can be safely removed or fixed.**
- I will replace it with the robust logic just to be safe and consistent, as I can't be 100% sure `data_adapter` isn't used elsewhere in future versions.

```python
# Mapeamento explícito para evitar erro de locale
MESES_MAP_FIX = {m: i+1 for i, m in enumerate(['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'])}
data_adapter['month_num_temp'] = data_adapter['mes'].map(MESES_MAP_FIX)
data_adapter['data_ref'] = data_adapter.apply(lambda x: pd.Timestamp(year=2026, month=x['month_num_temp'], day=1), axis=1)
```

## Verification

- Run Forecast generation.
