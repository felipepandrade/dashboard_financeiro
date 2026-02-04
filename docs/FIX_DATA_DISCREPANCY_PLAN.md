# Fix AI Board Data Discrepancy Plan

## Problem

The AI Board Advisor claims "Zero Realized" execution and hallucinates "Manager Incompetence" because the database likely has no realized data for Jan 2026 yet (common in early year or pending upload).
Also, potential case-sensitivity issues in database queries might hide existing data.

## Analysis

1. **Missing Data**: Inspecting the codebase reveals no dedicated "Upload Realized 2026" feature (only 2024/2025 legacy). Users likely haven't uploaded Jan 2026 data.
2. **AI Response**: The AI sees `Realized = 0` and `Budget = 60M` and concludes "Paralysis". It lacks context that data might simply be missing.
3. **Query Robustness**: `database/crud.py` filters `mes` with exact match `== mes.upper()`. If data was inserted as 'Jan' manualy, it filters out.

## Proposed Changes

### 1. Robustify Database Queries

**File**: `database/crud.py`
Use `func.upper()` for month filtering to ensure case-insensitivity.

```python
# Before
if mes:
    query = query.filter(LancamentoRealizado.mes == mes.upper())

# After
if mes:
    query = query.filter(func.upper(LancamentoRealizado.mes) == mes.upper())
```

### 2. Improve AI Context (Smart Diagnostics)

**File**: `services/ai_board.py`
In `_get_contexto_financeiro`:

- Check if `total_realizado == 0` for the period.
- If zero, append a specific **SYSTEM NOTE** to the prompt:
    > "Note: Total Realized is 0.00. This strongly indicates that the monthly financial data has NOT been uploaded yet. Do NOT assume execution failure or paralysis. State clearly that data is pending."

## Verification

### Automated Verification

- None (Database dependent).

### Manual Verification

1. **Run AI Board**: Ask "Qual a situação de Janeiro?".
2. **Expectation**: AI should say "Dados de realizado não constam no sistema..." instead of "Execução zero inadmissível".
