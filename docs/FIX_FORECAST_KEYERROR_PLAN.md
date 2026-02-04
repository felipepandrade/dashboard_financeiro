# Fix Forecast KeyError Plan

## Problem

`KeyError: 'mes'` in `pages/06_🔮_Previsao_IA.py` when trying to plot `df_forecast['mes']`.

## Analysis

`forecast_service.get_dados_cenario` (lines 118-131 of service) returns a DataFrame with columns: `['mes', 'conta_contabil', 'centro_custo', 'valor_previsto']`.
Wait! The service **DOES** return `mes` (line 124 of `forecast_service.py`).

```python
            data = [{
                'mes': e.mes,
                ...
            } for e in entries]
```

So why the KeyError?
Possible reasons:

1. `df_forecast` is empty? `pd.DataFrame(data)` on an empty list `[]` results in an Empty DataFrame with NO columns. If `entries` is empty, `df_forecast` is empty and calling `df_forecast['mes']` raises KeyError.
2. `get_dados_cenario` is returning something else? No, code looks clear.

## Revised Solution

Check if `df_forecast` is empty before trying to plot it. If it is empty, show an info message.

### Changes in `pages/06_🔮_Previsao_IA.py`

Around line 198:

```python
df_forecast = forecast_service.get_dados_cenario(cenario_sel['id'])

if df_forecast.empty:
    st.warning("O cenário selecionado não possui dados.")
else:
    # ... Plotting code ...
```

## Verification

- Run Forecast plotting with an empty scenario (or confirm that was the case).
