# Fix Provisioning Bugs Plan

## Bugs Identified

1. **Field `usuario` is incorrect:** Saves as "Sistema" hardcoded, ignoring the logged-in user.
2. **Fields `regional` and `base` are empty:** The `criar_provisao` (single entry) function in the UI attempts to look up these values from `df_centros` again. Even though they should exist, the lookup might be failing or the service might not be persisting them (to be verified).

## Proposed Changes

### 1. `pages/02_📝_Lancamentos.py`

#### A. Fix Auth User

* Replace `"usuario": "Sistema"` with `"usuario": st.session_state.get('username', 'Sistema')`.

#### B. Fix Regional/Base Saving

* Instead of looking up `regional` and `base` again from `df_centros` using code matching, simply use the `sel_regional` and `sel_base` variables that the user already selected in the UI.
* **Logic:**

    ```python
    "regional": sel_regional if sel_regional != "Todas" else None,
    "base": sel_base if sel_base != "Todas" else None
    ```

  * **Fallback:** If "Todas" is selected, we DO NOT populate `None`. We should try to lookup from `df_centros` as a fallback, because the center *must* belong to a region.
  * **Refined Logic:**
        1. Use `sel_regional`/`sel_base` if not "Todas".
        2. Else, use `df_centros` lookup.

### 2. `services/provisioning_service.py`

* Verified that `criar_provisao` extracts `regional` and `base` correctly. No changes needed here.

## Verification Plan

1. **Manual Test:**
    * Log in as `admin`.
    * Go to "Nova Provisão".
    * Create a provision:
        * Desc: "Teste Debug"
        * Regional: Select "SUL" (or available)
        * Base: Select one
        * Centro: Select one
    * Save.
    * Go to "Gestão de Dados" -> "Provisao" (requires admin).
    * Check if `regional` and `base` columns are populated.
    * Check if `usuario` matches login.
