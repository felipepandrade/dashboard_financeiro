# Plano de Implementação - Refatoração Análise Financeira (Legacy Cleanup)

## Objetivos

1. Modernizar o módulo `01_Analise_Financeira.py`.
2. Eliminar dívida técnica (código morto, features obsoletas).
3. Restaurar análise de fornecedores integrando-a ao fluxo de upload do P&L.
4. Centralizar lógica de negócio.

## Estratégia de Mudança

### 1. Backend (`utils_financeiro.py`)

- [ ] **Remoção**: `processar_aba_orcamento`, `processar_acompanhamento_orcamento_completo`, `gerar_estatisticas_orcamento`, `limpar_e_enriquecer_dados`.
- [ ] **Limpeza**: Remover referências ao `ValidadorDados` para orçamento antigo (manter P&L se útil, ou simplificar).
- [ ] **Refatoração - Upload P&L**:
  - Atualizar `processar_pl_baseal` para aceitar leitura de 'Razão_Gastos' (ou criar função integrada).
  - Atualizar `Home.py` ou wrapper para garantir que, ao subir o Excel, ambas as abas (P&L e Razão) sejam lidas.

### 2. Frontend (`01_Analise_Financeira.py`)

- [ ] **Simplificação**: Remover Tabs "Acompanhamento Orçamentário", "Qualidade de Dados" e "Previsão Financeira".
- [ ] **Foco**: Manter apenas "Análise Financeira (P&L)".
- [ ] **Feature Fornecedores**:
  - Garantir que a sub-aba "Fornecedores" leia corretamente do `st.session_state['razao_df']` populado pelo novo fluxo.

## Passos de Execução

1. Modificar `utils_financeiro.py` (Limpeza e Melhoria de Upload).
2. Modificar `01_Analise_Financeira.py` (UI Cleanup).
