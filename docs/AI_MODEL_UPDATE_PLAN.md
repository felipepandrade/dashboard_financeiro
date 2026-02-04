# AI Model Update Plan

## Context

The user requested to remove OpenAI support and update the Google Gemini integration to use the latest models available as of Feb 2026: **Gemini 3 Pro** and **Gemini 3 Flash**.
Web search confirmed model names: `gemini-3-pro-preview` and `gemini-3-flash-preview`.

## Changes

### 1. `utils_ui.py` (Sidebar Configuration)

* **Locate:** Sidebar "Provedor de Inteligência" selectbox.
* **Update:**
  * Change options to: `["Gemini 3 Pro", "Gemini 3 Flash"]`.
  * Default index: 0.

### 2. `utils_financeiro.py` (Service Logic)

* **Locate:** `get_ai_chat_response` function.
* **Update:**
  * Remove `elif "OpenAI" in provider...` block entirely.
  * Update `model_name` mapping logic:
    * If `provider == "Gemini 3 Pro"` -> `gemini-3-pro-preview`.
    * If `provider == "Gemini 3 Flash"` -> `gemini-3-flash-preview`.

## Verification

1. **Manual Test:**
    * Verify "OpenAI" is gone from sidebar.
    * Select "Gemini 3 Flash" and check functionality (subject to API key validity).
