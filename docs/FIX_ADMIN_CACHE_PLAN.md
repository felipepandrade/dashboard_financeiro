# Fix Admin Data Visibility (Cache Issue)

## Problem

The "Gestão de Dados" page caches table data in `st.session_state` indefinitely. When data is updated in other modules (e.g., creating a provision in "Lançamentos"), the Admin page continues to show the old data until the session is cleared or the app restarts.

## Solution

Add a **"recarregar" (refresh)** mechanism to the Admin UI.

### 1. `pages/07_⚙️_Gestao_Dados.py`

#### A. Add Refresh Button

* Place a button "🔄 Recarregar Dados" next to the table selector (using `st.columns`).
* **Action:**
  * Delete the specific cache key: `del st.session_state[f'df_{tabela_sel}']`
  * Triggers `st.rerun()`, which forces `load_data()` to fetch fresh data from the DB.

## Verification

1. **Manual Test:**
    * Open "Gestão de Dados" -> Select "provisoes".
    * Open "Lançamentos" in a new tab (or same) -> Create a new provision.
    * Go back to "Gestão de Dados". Old data should be visible.
    * Click "🔄 Recarregar Dados".
    * **Success:** The new provision appears in the table.
