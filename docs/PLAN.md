# Plano de Otimização de Performance

> **Projeto:** Dashboard Financeiro v2.0  
> **Ambiente:** Streamlit Cloud + Neon (PostgreSQL Serverless)  
> **Origem:** [performance_audit_report.md](file:///C:/Users/WN6241/.gemini/antigravity/brain/58e2fd79-83c2-401b-b562-5d3a537b3e71/performance_audit_report.md)

---

## 📋 Sumário do Plano

| Fase | Foco | Duração | Agentes |
|------|------|---------|---------|
| 1 | Quick Wins - DB & Cache | 1-2 dias | performance-optimizer, backend-specialist |
| 2 | Lazy Loading & Imports | 1 dia | backend-specialist |
| 3 | Refatoração Estrutural | 2-3 dias | backend-specialist, test-engineer |

**Total Estimado:** 4-6 dias de trabalho

---

## 🚨 Itens para Revisão do Usuário

> [!IMPORTANT]
> Decisões que requerem confirmação antes da implementação:

1. **Pool de Conexões:** Reduzir de ilimitado para `pool_size=3, max_overflow=2`?
2. **TTL de Cache:** Aumentar de 60-300s para 3600s (1 hora)?
3. **Refatoração de utils_financeiro.py:** Dividir em módulos menores?

---

## Fase 1: Quick Wins - Database & Cache (1-2 dias)

### 1.1 Connection Pooling Singleton

**Problema:** `get_engine()` recria engine a cada chamada (52+ sessões).

**Arquivo:** [database/models.py](file:///c:/Aplicativos%20Desenvolvidos/dashboard_financeiro/database/models.py)

**Alterações:**

```python
# ANTES - Linha 46-89
def get_engine():
    ...
    return create_engine(db_url, pool_pre_ping=True, pool_recycle=300)

# DEPOIS
@st.cache_resource
def get_engine():
    ...
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=280,    # Antes do auto-suspend do Neon (5min)
        pool_size=3,         # Limitar conexões ativas
        max_overflow=2       # Burst controlado
    )
```

**Impacto:** 🔴 Alto - Evita esgotamento de conexões no Neon

---

### 1.2 Aumentar TTL de Cache

**Problema:** TTLs curtos (60-300s) causam reprocessamento frequente.

**Arquivo:** [data/comparador.py](file:///c:/Aplicativos%20Desenvolvidos/dashboard_financeiro/data/comparador.py)

**Alterações:**

| Linha | Atual | Proposto |
|-------|-------|----------|
| 55, 78, 121 | `ttl=300` | `ttl=3600` |
| 169, 187, 216 | `ttl=60` | `ttl=600` |

**Impacto:** 🔴 Alto - Reduz queries ao DB em ~80%

---

### 1.3 Centralizar Layout Plotly

**Problema:** Código duplicado em 5+ arquivos.

**Arquivo:** [utils_ui.py](file:///c:/Aplicativos%20Desenvolvidos/dashboard_financeiro/utils_ui.py)

**Adicionar:**

```python
def aplicar_tema_plotly(fig):
    """Aplica tema dark padrão a figura Plotly."""
    return fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"}
    )
```

**Impacto:** 🟢 Baixo - Manutenibilidade

---

## Fase 2: Lazy Loading & Imports (1 dia)

### 2.1 Lazy Imports para Bibliotecas Pesadas

**Problema:** sklearn, statsmodels, genai carregados no cold start (~3s).

**Arquivo:** [utils_financeiro.py](file:///c:/Aplicativos%20Desenvolvidos/dashboard_financeiro/utils_financeiro.py)

**Alterações:**

```python
# ANTES - Linhas 30-35 (imports globais)
from sklearn.linear_model import LinearRegression
from statsmodels.tsa.seasonal import seasonal_decompose
from google import generativeai as genai

# DEPOIS - Imports locais dentro das funções
def _seasonal_decompose(self, periods):
    from statsmodels.tsa.seasonal import seasonal_decompose
    ...

def get_ai_chat_response(messages, api_key, provider):
    if 'Gemini' in provider:
        from google import generativeai as genai
    ...
```

**Impacto:** 🟡 Médio - Cold start ~2s mais rápido

---

## Fase 3: Refatoração Estrutural (2-3 dias)

### 3.1 Dividir utils_financeiro.py

**Problema:** Arquivo monolítico com 1416 linhas e 48 funções.

**Estrutura Proposta:**

```
utils/
├── __init__.py          # Re-exports para compatibilidade
├── etl.py               # Funções de processamento (linhas 67-370)
├── validation.py        # Schemas Pandera (linhas 370-600)
├── charts.py            # Gráficos Plotly (linhas 600-750)
├── ai.py                # Integração Gemini/OpenAI (linhas 750-830)
├── forecasting.py       # Modelos matemáticos (linhas 830-1080)
└── persistence.py       # DB Integration (linhas 1230-1416)
```

**Impacto:** 🟡 Médio - Manutenibilidade e imports seletivos

---

### 3.2 Cache de Figuras Plotly

**Problema:** 23+ gráficos recriados a cada interação.

**Arquivos:** Páginas 01, 03, 06

**Padrão a implementar:**

```python
@st.cache_data
def _criar_grafico_cached(df_hash: str, params: dict):
    fig = go.Figure()
    ...
    return fig

def criar_grafico_comparativo_mensal(df):
    df_hash = hash(df.to_json())
    return _criar_grafico_cached(df_hash, {...})
```

---

## 📊 Verificação

### Scripts de Validação

```bash
# Executar após cada fase
streamlit run Home.py --profile   # Verificar cold start
python -c "from utils_financeiro import *"  # Verificar imports
```

### Métricas Target

| Métrica | Antes | Target |
|---------|-------|--------|
| Cold Start | ~4-6s | < 2s |
| Rerun com filtro | ~1-2s | < 500ms |
| Conexões DB ativas | Ilimitado | ≤ 5 |

---

## 🔴 Agentes Necessários

| # | Agente | Responsabilidade | Fase |
|---|--------|------------------|------|
| 1 | `performance-optimizer` | Validar métricas antes/depois | 1, 2, 3 |
| 2 | `backend-specialist` | Implementar alterações em DB e services | 1, 2, 3 |
| 3 | `test-engineer` | Garantir que nada quebrou | 3 |

---

## ✅ Checklist de Aprovação

- [ ] **Fase 1.1:** Confirma `pool_size=3, max_overflow=2`?
- [ ] **Fase 1.2:** Confirma TTL de 1 hora para dados orçamentários?
- [ ] **Fase 3.1:** Deseja dividir utils_financeiro.py em módulos?

---

*Aguardando aprovação para iniciar implementação.*
