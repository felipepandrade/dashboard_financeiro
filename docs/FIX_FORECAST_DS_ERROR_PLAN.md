# Fix Forecast KeyError 'ds' Plan

## Analysis

The `SimpleForecaster.predict` method returns a DataFrame with column **'data'**, NOT **'ds'**.

```python
    self.forecast = pd.DataFrame({
        'data': future_dates,
        'previsao': predictions,
        ...
    })
```

However, `services/forecast_service.py` expects 'ds' and 'yhat':

```python
                for _, row in df_pred.iterrows():
                    mes_idx = row['ds'].month - 1 # Error here
                    ...
                        valor_previsto=float(row['yhat']), # Error likely here too ('previsao' vs 'yhat')
```

## Solution

I must update `services/forecast_service.py` to match the `SimpleForecaster` output schema.

**Mapping:**

* `row['ds']` -> `row['data']`
* `row['yhat']` -> `row['previsao']`

### Changes in `services/forecast_service.py`

Around line 79:

```python
                # Converter para ForecastEntries
                for _, row in df_pred.iterrows():
                    mes_idx = row['data'].month - 1  # Changed from 'ds' to 'data'
                    if 0 <= mes_idx < 12:
                        mes_str = MESES_ORDEM[mes_idx]
                        
                        # ...
                        
                        entry = ForecastEntry(
                            # ...
                            valor_previsto=float(row['previsao']), # Changed from 'yhat' to 'previsao'
                            metodo_calculo=metodo
                        )
                        entries.append(entry)
```

## Verification

- Run Forecast generation.
