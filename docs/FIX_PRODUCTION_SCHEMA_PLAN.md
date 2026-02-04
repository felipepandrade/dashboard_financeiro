# Production Schema Repair Plan

## Context

The production database (Postgres/Neon) has a broken schema for the `provisoes` table because the "Salvar Alterações" feature in "Gestão de Dados" used `to_sql(if_exists='replace')`, which drops the table and recreates it without Primary Keys or Sequences. This causes `NULL identity key` errors when trying to insert new records.

## Changes

### 1. `pages/07_⚙️_Gestao_Dados.py`

#### A. Add "Reparar Schema" Button

In the `tab_schema` (Estrutura), add a section "Reparos de Emergência (Hotfix)".

* **Action:** When clicked, executes the raw SQL commands to fix the `id` column (SET NOT NULL, CREATE SEQUENCE, ATTACH SEQUENCE, RESTORE PK).
* **Why:** Allows the user to fix the production DB immediately without console access.

#### B. Fix "Salvar Alterações" Logic (The Root Cause)

Replace the unsafe `to_sql(..., if_exists='replace')` with a safe transaction pattern:

1. **Transaction Start**
2. **Delete All:** `DELETE FROM table_name` (keeps schema, constraints, sequences).
3. **Insert New:** `df.to_sql(..., if_exists='append')`.
    * *Constraint:* We must ensure the DataFrame columns match the table columns exactly.
    * *ID Handling:* If `id` is in the DataFrame, it will be inserted. This preserves existing IDs. New rows added via UI (if any) might have empty IDs - need to ensure we don't insert explicit NULLs if depend on auto-increment.
    * *Correction:* If functionality is "Edit existing data", preserving IDs is crucial. `delete` + `insert` with IDs works.

## Verification

1. **Deploy:** User deploys the changes.
2. **Fix:** User goes to "Gestão de Dados" > "Estrutura" > Clicks "Reparar Tabela 'provisoes'".
    * *Success Indicator:* Toast message "Schema reparado com sucesso!".
3. **Test Bug Fix:** User tries to create a new provision in "Lançamentos".
    * *Success:* No "NULL identity key" error.
4. **Test Prevention:** User goes to "Gestão de Dados" > Edits a value > Saves.
    * *Success:* Saves correctly and DOES NOT break the schema (verified by creating another provision afterwards).
