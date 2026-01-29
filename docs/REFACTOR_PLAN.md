# Refactor Plan: Conceptual Alignment & UI Unification

## 1. Vision

Align the system with the user's operational reality:

- **Budget 2026**: Static/Loaded. No upload needed in Home.
- **Manual Entries (`02_Lancamentos`)**: These act as **Provisions** (commitments made but not yet paid/officialized). They should feed the Provisioning engine, not the "Realized" table directly.
- **P&L Upload**: The sole source of "Official Truth" for Realized costs. It validates/clears the provisions.
- **UI/UX**: Consolidate visuals using the "Premium" dark theme from the Dashboard across all modules.

## 2. Architecture Changes

### A. Data Flow Redesign

- **Current**: `02_Lancamentos` -> `LancamentoRealizado` table.
- **New**: `02_Lancamentos` -> `Provisao` table (Status: 'PENDENTE').
- **P&L Import**: Continues to feed `LancamentoRealizado` (The Official Record).
  - *Future consideration (out of scope for this immediate task but kept in mind): Reconciliation between Provisao vs Realized.*

### B. Module Restructuring

| File | Current Role | New Role | Action |
|------|--------------|----------|--------|
| `Home.py` | Upload Budget + P&L | System Status + P&L Upload Only. New Premium Layout. | **Refactor** |
| `02_Lancamentos.py` | Input Realized | Input **Provisions**. List/Edit Active Provisions. | **Refactor Logic & Target** |
| `05_Controle.py` | Provision CRUD + Transfers | **Budget Transfers (Remanejamento)** Only. Provision CRUD moves to `02`. | **Refactor/Split** |

## 3. Detailed Steps

### Step 1: Home Page Overhaul

- Remove "Upload Orçamento" section.
- Keep "Upload P&L" (Essential for closing the loop).
- Apply `03_Acompanhamento` CSS styles (Cards, Gradients, Typography).
- Improve "Metrics/Status" display.

### Step 2: Lançamentos Module (`02`)

- **Backend Change**: `salvar_lancamento` should create a `Provisao` record, not `LancamentoRealizado`.
- **Frontend Change**:
  - Rename page header to "Registro de Compromissos (Provisões)".
  - Add a "Recent Provisions" table below the form (Moving the CRUD view from `05` to here).
  - Apply Premium UI Styling.

### Step 3: Controle Orçamentário (`05`)

- Remove "Nova Provisão" and "Gerenciar Provisões" tabs (moved to `02`).
- Focus page solely on **Remanejamentos** (Budget Transfers) and OBZ Justifications (if applicable).
- Rename page/menu label if needed (e.g., "Gestão Orçamentária").
- Apply Premium UI Styling.

### Step 4: UI Unification (Global)

- Create a `styles.css` or shared `utils_ui.py` function to inject the common CSS (Gradient buttons, Dark cards, Inter font).
- Apply this to all pages.

## 4. User Review

- This plan addresses the specific quote: *"Os lançamentos... serão provisionados... não vejo sentido em haver um sistema separado"*.
