# Improvements Plan for 'Lançamentos' Module

## Context

The user requested usability and data integrity improvements in the `Lancamentos` module, specifically for creating provisions and managing active commitments.

## Changes

### 1. `services/provisioning_service.py`

* **Update `listar_provisoes`:** Add optional `base` parameter.
* **Logic:** If `base` is provided, filter the query by `Provisao.base == base`.

### 2. `pages/02_📝_Lancamentos.py`

#### A. Tab "Nova Provisão"

* **Force Negative Value:** Ensure `valor_estimado` is saved as a negative number for expenses.
  * *Implementation:* In the save block, use `val_final = -abs(valor)`.
* **Mandatory Fields:**
  * Add validation for `Regional` and `Base` in the existing error checking block.
  * Ensure the logical flow forces a selection (or handle "Todas" if it implies missing data).

#### B. Tab "Compromissos Ativos"

* **Add "Base" Filter:**
  * Add a selectbox for "Base" (populated from unique bases in `df_centros`) alongside Mês and Status.
  * Pass this filter to `prov_service.listar_provisoes`.
* **Interactive Table Selection:**
  * Replace the "Selecione um item..." dropdown.
  * Use `event = st.dataframe(..., on_select="rerun", selection_mode="single-row")`.
  * Capture the selected row ID from `event`.
  * Display the "Gerenciar Item" form (`st.expander`) only when a row is selected.

## Verification

1. **Manual Test - New Provision:**
    * Try to save without Regional/Base. Should show error.
    * Save a provision with value 100. Check DB/List: should be -100.
2. **Manual Test - Commitments List:**
    * Filter by Base. Verify list updates.
    * Click a row in the table. Verify the "Gerenciar Item" form appears with correct data.
    * Edit/Cancel the item. Verify success.
