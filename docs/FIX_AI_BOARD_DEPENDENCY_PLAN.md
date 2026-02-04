# Fix AI Board Dependency Plan

## Problem

The `AIBoard` service uses `pandas.DataFrame.to_markdown()` which requires `tabulate`. Failure leads to error messages being treated as data by the AI.

## Solution

Modify `services/ai_board.py` to robustly handle the string conversion using a fallback to `to_string()`.

### Changes in `services/ai_board.py`

In `_get_contexto_financeiro()`:
Replace:

```python
resumo = df.groupby('mes')[['orcado', 'realizado']].sum().to_markdown()
```

With a try-except block enabling fallback to `to_string()`.

## Verification

1. **Manual Test:** Run AI Board and verify valid financial response.
