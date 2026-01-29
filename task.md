# Task List - Sistema de Gestão Orçamentária 2026

## ✅ Fase 1: Análise e Fundação

- [x] Análise dos arquivos de referência (Orçamento, P&L)
- [x] Definição da stack (Streamlit, SQLite, Plotly)
- [x] Configuração do ambiente e repo

## ✅ Fase 2: Infraestrutura de Dados

- [x] Modelagem do banco de dados (`LancamentoRealizado`)
- [x] Scripts de carga de referência (`referencias_manager.py`)
- [x] Utilitários de processamento (`utils_financeiro.py`)

## ✅ Fase 3: Módulo de Lançamentos

- [x] Formulário de input mensal (`02_📝_Lancamentos.py`)
- [x] Validação de dados e hierarquia
- [x] Tratamento de exceções (COS, G&A)

## ✅ Fase 4: Acompanhamento (Dashboard)

- [x] Lógica de comparação Orçado x Realizado (`comparador.py`)
- [x] Dashboard interativo (`03_📈_Acompanhamento.py`)
- [x] KPIs, Gráficos e Drill-down

## ✅ Fase 5: Inteligência e Previsão (Features A & C)

- [x] **Infra**: Analisar P&L Dez/2025 para base histórica
- [x] **Backend (Forecast)**:
  - [x] Implementar `ForecastService` (Linear, Média Móvel, Sazonal)
  - [x] Persistência de cenários (Otimista, Realista, Pessimista)
- [x] **Backend (IA Board)**:
  - [x] Arquitetura de Orquestração (`services/ai_board.py`)
  - [x] Definir Personas (CFO, Controller, Auditor, Analyst)
  - [x] Integrar `NotebookLM` via MCP (Contexto estendido)
  - [x] Log de raciocínio multi-agente
- [x] **Frontend**: Aba "Previsão & Inteligência" no Dashboard

## ✅ Fase 6: Gestão de Provisões (Feature B)

- [x] **Database**: Criar tabela `Provisao` (com status e vínculo a `Lancamento`)
- [x] **Backend**:
  - [x] Regras de negócio (Provisionar -> Realizar -> Reverter)
  - [x] Serviço de conciliação
- [x] **Frontend**: Interface de gestão de provisões (CRUD)
- [x] **Relatórios**: Aging de provisões e impacto no Cash Flow

## ✅ Fase 7: Controle Orçamentário (Features D & E)

- [x] **Database**: Tabela `Remanejamento`
- [x] **Backend**:
  - [x] Workflow de aprovação de transferências
  - [x] Validação de saldos (Origem -> Destino)
- [x] **Frontend**:
  - [x] Tela de solicitação de remanejamento
  - [x] Visão OBZ Light (Justificativa de gastos por pacote)

## 📊 Fase 8: Consolidação e Histórico

- [x] Processar P&L Dez/2025 para histórico comparativo
- [ ] Preparar ingestão do P&L Jan/2026 (nova estrutura)
- [ ] Testes integrados de todas as funcionalidades
