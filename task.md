# Task List - Sistema de Gestão Orçamentária 2026

## ✅ Fase 1: Análise e Fundação

- [x] Análise dos arquivos de referência (Orçamento, P&L)
- [x] Definição da stack (Streamlit, SQLite, Plotly)
- [x] Configuração do ambiente e repo

## ✅ Fase 2: Infraestrutura de Dados

- [x] Modelagem do banco de dados (`LancamentoRealizado`)
- [x] Scripts de carga de referência (`referencias_manager.py`)
- [x] Utilitários de processamento (`utils_financeiro.py`)

## ✅ Fase 2.1: Conciliação de Dados (Shadow Ledger)

- [x] **Database**: Criar tabela `RazaoRealizado` (Auditoria e Conciliação)
- [x] **Backend**: Atualizar `ProvisioningService` (Edição e Status)
- [x] **UI**: Funcionalidades de Edição e Exportação em `02_📝_Lancamentos.py`
- [x] **Dashboard**: Visualização Empilhada (Realizado + Provisionado)
- [x] **ETL**: Carga automática do Razão via upload de P&L

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
- [x] **Frontend**: Aba "Previsão & Inteligência" no Dashboard (`06_🔮_Previsao_IA.py`)
  - [x] Renomeado de 04 para 06 para evitar conflito
  - [x] Integração com Provisões (Sinergia Operacional) no gráfico de Forecast

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

## ✅ Fase 8.1: Visualização de Dados (Novo Requisito)

- [x] Criar página `04_📚_Biblia_Financeira.py` (Orçamento 2026 + Metadados)
- [x] Implementar suporte a múltiplos anos (2024, 2025) no upload de P&L
- [x] Adicionar filtro de anos na visualização de histórico

## 📥 Fase 8.2: Importação em Lote de Provisões (Novo Requisito)

- [x] Criar método `criar_provisoes_em_lote` em `ProvisioningService`
- [x] Criar gerador de template (Excel/CSV) para download
- [x] Implementar aba "Importação em Lote" na página `02_📝_Lancamentos.py`
- [x] Implementar lógica de leitura e validação do arquivo de importação

## 📝 Fase 8.3: Enriquecimento de Dados de Provisão (Novo Requisito)

- [x] **Database**: Adicionar colunas `numero_contrato`, `cadastrado_sistema`, `numero_registro`
- [x] **Backend**: Atualizar service para persistir novos campos (Unitário e Lote)
- [x] **Frontend**: Atualizar formulário com campos condicionais
- [x] **Frontend**: Atualizar template de importação e lógica de leitura

## 📊 Fase 8: Consolidação e Histórico

- [x] Processar P&L Dez/2025 para histórico comparativo
- [ ] Preparar ingestão do P&L Jan/2026 (nova estrutura)
- [ ] Testes integrados de todas as funcionalidades

## ✅ Fase 9: Reestruturação Conceitual e UI (Feedback Usuário)

- [x] Criar biblioteca de UI (`utils_ui.py`)
- [x] Refatorar `Home.py` (Remover upload obsoleto, novo design)
- [x] Refatorar `02_Lancamentos.py` (Foco em Provisões/Compromissos)
- [x] Refatorar `05_Controle_Orcamentario.py` (Foco em Remanejamentos, remover redundâncias)
- [x] Unificar UI Global (Estilo Premium em todas as páginas)
- [x] Refatorar `01_Analise_Financeira.py` (Aplicar UI Premium)
- [x] **Feature E**: Implementar Justificativa OBZ Real (DB, Backend, UI)

## ♻️ Fase 10: Refatoração e Otimização (Legacy Cleanup)

- [x] **Módulo Análise Financeira (`01_Analytics`)**
  - [x] Remover abas obsoletas: "Acompanhamento Orçamentário", "Qualidade de Dados", "Previsão Financeira" (Redundante)
  - [x] Limpeza de código morto em `utils_financeiro.py` (Scripts de importação de orçamento antigo)
  - [x] Restaurar funcionalidade de "Análise de Fornecedores" (Incluir carga da aba 'Razão_Gastos' no upload do P&L)
  - [x] Review de Código: Melhorar nomes, performance e tipagem
  - [x] UI/UX Review: Aplicar estilo Premium e simplificar navegação
  - [x] **Documentação**: Gerar `MANUAL_SISTEMA.md` (Filosofia, Arquitetura, Guia do Usuário)

## 🚀 Fase 11: Deploy e Infraestrutura (Novo)

- [x] **Pesquisa de Opções**:
  - [x] Analisar Free Tier Permanente (Streamlit Cloud, Render, Oracle Cloud)
  - [x] Pesquisar Banco de Dados Externo (Neon, Supabase)
  - [x] Gerar Relatório de Opções (`deployment_options.md`)
- [ ] **Decisão de Arquitetura**:
  - [ ] Selecionar combo (Ex: Streamlit Cloud + Neon)
- [ ] **Preparação para Deploy**:
  - [ ] Migrar SQLite para Postgres (Scripts de exportação/importação)
  - [ ] Configurar variáveis de ambiente (`secrets.toml`)
  - [ ] Criar arquivo `packages.txt` (se necessário)
- [ ] **Deploy**:
  - [ ] Configurar conexão GitHub
  - [ ] Deploy em Produção

## 🏗️ Fase 12: Melhoria Importação em Lote (Regional/Base Automatico)

- [x] Atualizar `ProvisioningService` para suportar `regional` e `base`
- [x] Atualizar `02_Lancamentos.py` para realizar lookup de `regional` e `base` no upload
- [x] Criar script de verificação `scripts/verify_provisao_import.py`

## 🐛 Fase 13: Investigação Discrepância de Dados (Histórico)

- [x] Analisar origem de dados da `04_Biblia_Financeira.py`
- [x] Verificar persistência real em `services/historical_import.py`
- [x] Verificar conexão de banco em `07_Gestao_Dados.py`
- [x] Corrigir divergência de leitura/escrita

## 🐛 Fase 14: Correção de Bugs (Criação de Provisão)

- [x] Investigar falha ao salvar `regional` e `base` (Lancamento Unitário)
- [x] Corrigir atribuição de `usuario` (está salvando "Sistema")
- [x] Validar correções

## 🚨 Fase 15: Correção Crítica de Schema (Produção)

- [x] Implementar botão de reparo ("Hotfix") em `07_Gestao_Dados.py`
- [x] Refatorar lógica de "Salvar Alterações" para evitar `replace`
- [x] Validar fluxo de correção e salvamento seguro

## 🔄 Fase 16: Correção de Cache (Gestão de Dados)

- [x] Adicionar botão "Recarregar Dados" em `07_Gestao_Dados.py`
- [x] Validar atualização da tabela `provisoes`

## 🚀 Fase 17: Melhorias em Lançamentos

- [x] Backend: Adicionar filtro por Base em `listar_provisoes`
- [x] UI: Forçar valor negativo em `Nova Provisão`
- [x] UI: Tornar campos Regional/Base obrigatórios
- [x] UI: Implementar seleção por tabela em `Compromissos Ativos`
- [x] Validar UX e funcionalidade

## 📥 Fase 18: Consistência na Importação em Lote

- [x] UI: Forçar valor negativo no processamento do arquivo
- [x] UI: Atribuir `usuario` logado (com fallback)
- [x] UI: Garantir robustez no lookup de Regional/Base
- [x] Validar fluxo de importação

## 🧠 Fase 19: Atualização de Modelos IA

- [x] UI: Remover OpenAI e atualizar opções para Gemini 3 Pro/Flash
- [x] Backend: Atualizar mapeamento de modelos (gemini-3-pro/flash-preview)
- [x] Backend: Remover lógica legado da OpenAI
- [x] Validar integração com novas APIs

## 🕵️‍♂️ Fase 20: Debug AI e Integridade de Dados

- [x] Backend: Corrigir dependência `tabulate` em `ai_board.py` (Fallback para `to_string`)
- [x] Validar resposta do Conselho Consultivo sem erros

## 📅 Fase 21: Debug Forecast Date Error

- [x] UI: Corrigir parsing de data "FEV/2026" (Remover dependência de locale)
- [x] Validar geração de forecast
