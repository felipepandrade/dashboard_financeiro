# Walkthrough: Batch Import with Automatic Regional/Base Filling

## Overview

We enhanced the "Importação em Lote" feature in the "Lançamentos" module to automatically enrich provision records with "Regional" and "Base" information based on the selected "Centro de Custo". This ensures data consistency with single-entry provisions and properly populates the database columns.

## Changes Created

### 1. Service Update: `services/provisioning_service.py`

Modified `ProvisioningService` to accept and persist `regional` and `base` fields in the `Provisao` entity.

- **Method `criar_provisao`**: Added `regional` and `base` to constructor.
- **Method `criar_provisoes_em_lote`**: Added extraction and passing of these fields from the input dictionary.

### 2. UI Update: `pages/02_📝_Lancamentos.py`

Updated the batch processing logic to lookup metadata before sending to the service.

- **Logic Added**:
  - Iterates through imported records.
  - Matches `centro_gasto_codigo` against `df_centros` reference.
  - Injects `regional` and `base` into the record if a match is found.

### 3. Verification

Created `scripts/verify_provisao_import.py` to simulate the enrichment process.

**Verification Results:**

- Input: Import record with only `centro_gasto_codigo`.
- Output: Record enriched with correct `Regional` and `Base` from reference.
- Status: **Verified**.

## How to Test

1. Go to **"Lançamentos" > "Importação em Lote"**.
2. Upload an Excel/CSV file with `centro_gasto_codigo` populated.
3. Process the import.
4. Check the database (or export report) to confirm `regional` and `base` are filled.
