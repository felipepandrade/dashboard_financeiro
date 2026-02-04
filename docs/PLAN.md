# Plan for "Lançamentos" Batch Import Improvement

## Goal

Automatically fill "Regional" and "Base" fields during the batch import of provisions (importação em lote) in the "Lançamentos" module, ensuring the database is complete for both single and batch entries.

## Proposed Changes

### 1. Update `services/provisioning_service.py`

The `ProvisioningService` currently ignores `regional` and `base` fields when creating provisions. We need to update it to persist these fields into the `Provisao` table.

#### [MODIFY] `services/provisioning_service.py`

- In `criar_provisao(self, dados: dict)`:
  - Extract `regional` and `base` from `dados` (if present).
  - Pass them to the `Provisao` constructor.
- In `criar_provisoes_em_lote(self, lista_dados: List[dict])`:
  - Extract `regional` and `base` from `dados`.
  - Pass them to the `Provisao` constructor.

### 2. Update `pages/02_📝_Lancamentos.py`

The UI module handles the file upload and conversion to dictionary. We will add the logic to look up "Regional" and "Base" from the `df_centros` reference dataframe before calling the service.

#### [MODIFY] `pages/02_📝_Lancamentos.py`

- In the "Importação em Lote" tab (`with tab_import:`):
  - Before calling `prov_service.criar_provisoes_em_lote(lista_dados)`:
  - Iterate over `lista_dados`.
  - For each record, use `centro_gasto_codigo` to find the corresponding row in `df_centros` (which is already loaded in the page scope).
  - Retrieve `regional` and `base`.
  - Populate these keys in the record dictionary.

## Verification Plan

### Automated Verification Script

Since manual UI testing is limited in this environment, I will create a python script `scripts/verify_provisao_import.py` to simulate the process.

**Script Steps:**

1. Setup specific database session (using existing `get_session`).
2. Instantiate `ProvisioningService`.
3. Create a mock list of import data (dicts) containing `centro_gasto_codigo` but MISSING `regional` / `base`.
4. Perform the logic that will be in the UI (lookup `regional`/`base` from a mock `df_centros` or the actual one if loadable).
5. Call `criar_provisoes_em_lote` with the enriched data.
6. Query the database (`Provisao` table) created by the script (or valid test DB) to verify the new records have `regional` and `base` correctly populated.
7. Clean up the test data.

### Manual Validation (Post-Implementation)

- If the user has access to the UI:
  1. Upload a template Excel with a known Centro de Gasto.
  2. Verify in the "Compromissos Ativos" list (or via export) that Regional/Base are filled.
