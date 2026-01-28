# PLAN.md - Fase 4: Acompanhamento Orçamentário

## Visão Geral

Implementar página de acompanhamento orçamentário (`03_📈_Acompanhamento.py`) que permite:

- Comparativo orçado x realizado por mês
- Análise por centro de custo e conta contábil
- Drill-down por ativo (hierarquia pai-filho)
- Gráficos de desvio
- Exportação de relatórios

## Domínios Envolvidos

| Domínio | Agente | Responsabilidade |
|---------|--------|-----------------|
| Frontend/UI | `frontend-specialist` | Página Streamlit, UX, gráficos Plotly |
| Backend/Data | `backend-specialist` | Lógica de comparação, agregações |
| Testing | `test-engineer` | Validação funcional, testes de dados |

## Arquitetura

```
pages/
└── 03_📈_Acompanhamento.py     # Página principal

data/
└── comparador.py               # Lógica de comparação orçado x realizado

utils/
└── graficos_orcamento.py       # Componentes gráficos reutilizáveis
```

## Funcionalidades Detalhadas

### 1. Visão Geral do Ano

- **Resumo executivo**: Total orçado vs realizado do ano
- **KPIs principais**: % execução, desvio absoluto, desvio %
- **Gráfico de barras**: Orçado vs Realizado por mês

### 2. Análise por Mês

- **Seletor de mês**: JAN a DEZ
- **Tabela comparativa**: Por centro de custo
- **Heatmap de desvios**: Visualização rápida de problemas

### 3. Análise por Centro de Custo

- **Filtro por ativo**: GASCOM, GASCAC, COS, G&A, etc.
- **Drill-down hierárquico**: Pai → Filhos
- **Gráfico treemap**: Distribuição de custos

### 4. Análise por Conta Contábil

- **Top 10 contas**: Por valor realizado
- **Comparativo**: Orçado vs Realizado por conta

### 5. Exportação

- **CSV**: Dados tabulares
- **Excel**: Relatório formatado
- **PDF**: Relatório gerencial (opcional)

## Especificações Técnicas

### Dados de Entrada

1. **Orçamento V1 2026**: `data/referencias/orcamento_v1_2026.xlsx`
   - Colunas: `jan/26` a `dez/26` (valores orçados)
   - Chaves: CENTRO DE GASTO, CÓDIGO CONTA CONTÁBIL

2. **Lançamentos Realizados**: `database/lancamentos_2026.db`
   - Tabela: `lancamentos_realizados`
   - Chaves: centro_gasto_codigo, conta_contabil_codigo, mes

### Funções de Comparação (backend)

```python
def get_comparativo_por_mes(ano: int = 2026) -> pd.DataFrame:
    """Retorna DataFrame com colunas: mes, orcado, realizado, desvio, desvio_pct"""

def get_comparativo_por_centro(mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """Retorna DataFrame com comparativo por centro de custo"""

def get_comparativo_por_conta(mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """Retorna DataFrame com comparativo por conta contábil"""

def get_drill_down_ativo(ativo: str, mes: str = None) -> pd.DataFrame:
    """Retorna centros filhos com orçado/realizado"""
```

### Componentes UI (frontend)

```python
# Cards de KPI
def card_kpi(titulo, valor, variacao, cor)

# Gráfico de barras comparativo
def grafico_comparativo_mensal(df)

# Heatmap de desvios
def heatmap_desvios(df)

# Treemap de custos
def treemap_custos(df)
```

## Paleta de Cores

| Elemento | Cor | Código |
|----------|-----|--------|
| Orçado | Azul | `#1e40af` |
| Realizado | Verde | `#059669` |
| Desvio Negativo | Vermelho | `#dc2626` |
| Desvio Positivo | Amarelo | `#ca8a04` |
| Background | Slate | `#0f172a` |

## Critérios de Aceite

- [ ] Página carrega sem erros
- [ ] Comparativo mensal funciona para todos os meses
- [ ] Filtros por ativo funcionam corretamente
- [ ] Drill-down hierárquico exibe centros filhos
- [ ] Exceções COS e G&A são tratadas corretamente
- [ ] Gráficos são interativos e responsivos
- [ ] Exportação CSV funciona
- [ ] Performance: carrega em < 3 segundos

## Cronograma de Implementação

| Etapa | Agente | Duração | Dependências |
|-------|--------|---------|--------------|
| 1. Lógica de comparação | backend-specialist | - | referencias_manager.py, crud.py |
| 2. Página principal | frontend-specialist | - | Etapa 1 |
| 3. Gráficos | frontend-specialist | - | Etapa 2 |
| 4. Validação | test-engineer | - | Etapas 1-3 |

## Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Dados não batem | Alta | Validar mapeamento de colunas |
| Performance lenta | Média | Cache com @st.cache_data |
| Centros sem orçamento | Alta | Tratar como "não orçado" |

---

**Status**: Aguardando aprovação para iniciar implementação.
