# Critical Schema Repair Plan

## Diagnosis

The error `Instance <Provisao ...> has a NULL identity key` indicates the database is failing to auto-generate a Primary Key for the `provisoes` table.
**Root Cause:** The "Salvar Alterações" feature in `pages/07_⚙️_Gestao_Dados.py` uses `df.to_sql(..., if_exists='replace')`. This Pandas method **DROPS the database table** and recreates it using minimal types inferred from the DataFrame. This **destroys** the `SERIAL` sequence, Primary Key definition, and Indexes defined in the SQLAlchemy model.

## Steps to Fix

### 1. Database Repair Script (`scripts/fix_schema_provisoes.py`)

Create a Python script to executing raw SQL commands to fix the table structure in the Production (Neon) database:

1. Check if `id` column exists.
2. Make `id` NOT NULL.
3. Create a sequence `provisoes_id_seq`.
4. Attach sequence to `id` (Default value).
5. Sync sequence with max(id).
6. Restore Primary Key Constraint.

### 2. Fix `pages/07_⚙️_Gestao_Dados.py`

Modify the "Salvar Alterações" logic to avoid `if_exists='replace'`.
**Safe Strategy:**

1. Use `session.query(Model).delete()` to empty the table (keeping schema).
2. Use `df.to_sql(..., if_exists='append')` to insert data into the *existing* structure.
    * *Note:* Need to handle the `id` column carefully. if the DF has IDs, we insert them.

## Verification

1. Run the repair script.
2. Try creating a provision again (should work).
3. Try saving in Gestao Dados again (should not break schema).
