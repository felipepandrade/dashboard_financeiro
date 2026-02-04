# Fix Data Persistence Visibility (Cache Invalidation)

## Problem Description

The user reports that `lancamentos_realizados` appears empty in the "Gestão de Dados" module even after a successful "Importação Histórica".

- **Cause:** The "Editar Dados" tab caches the table data in `st.session_state['df_lancamentos_realizados']`. When "Importação Histórica" runs (in a different tab), it updates the database but **does not clear this cache**.
- **Result:** The user sees the old (empty) cached dataframe instead of the newly imported data.

## Proposed Changes

### `pages/07_⚙️_Gestao_Dados.py`

In the **Tab 3: Importação Histórica** success block:

1. Identify the table names affected: `lancamentos_realizados` and `razao_realizados`.
2. Check if `df_lancamentos_realizados` and `df_razao_realizados` exist in `st.session_state`.
3. Delete these keys from `st.session_state` to force a reload on the next visit to "Editar Dados".

#### Code Snippet (Conceptual)

```python
if success:
    status.update(label="✅ Importação Concluída!", state="complete", expanded=False)
    st.success(msg)
    st.balloons()
    
    # --- INVALIDATE CACHE TO REFRESH DATA TAB ---
    for table_key in ['df_lancamentos_realizados', 'df_razao_realizados']:
        if table_key in st.session_state:
            del st.session_state[table_key]
    st.toast("Cache de visualização atualizado!", icon="🔄")
```

## Verification Plan

### Manual Verification

1. Go to **Gestão de Dados** > **Editar Dados**.
2. Select `lancamentos_realizados` (Verify it is empty/stale).
3. Go to **Importação Histórica**.
4. Run Import (Success).
5. Return to **Editar Dados**.
6. **Expectation:** The table reload trigger should happen, and data should appear.
