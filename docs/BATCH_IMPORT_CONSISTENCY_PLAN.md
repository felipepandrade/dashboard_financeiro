# Batch Import Consistency Plan

## Analysis of Current State

* **Values:** Currently accepts positive values directly from Excel. **Inconsistent** with single entry (which forces negative).
* **User:** Defaults to "Importação em Lote". **Inconsistent** with single entry (which uses logged-in user).
* **Regional/Base:** Already implemented in `Lancamentos.py` via lookup from `df_centros`. Logic seems sound but needs to be robust.

## Changes

### 1. `pages/02_📝_Lancamentos.py`

In the batch processing block:

* **User Attribution:** Pass `usuario` field in the `lista_dados` (enriched with `st.session_state.get('username')`).
* **Value Normalization:** Before calling the service, ensure `valor_estimado` is negative: `item['valor_estimado'] = -abs(float(item['valor_estimado']))`.

## Verification

1. **Manual Test:**
    * Upload file with positive value.
    * Verify result is negative.
    * Verify user attribution.
