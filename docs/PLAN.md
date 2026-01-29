# PLAN.md - Fases 5, 6 e 7: Evolução do Sistema

## Visão Geral

Implementação das funcionalidades avançadas de gestão orçamentária (A a E) conforme brainstorm aprovado e workflow de orquestração.
Objetivo: Transformar o dashboard em sistema completo de previsão, controle e governança.

---

## 🏗️ Arquitetura e Modelagem de Dados

### 1. Banco de Dados (Novas Tabelas)

#### Tabela: `provisoes` (Feature B)

Gestão do ciclo de vida de despesas estimadas.

- `id`: PK
- `descricao`: Texto
- `valor_estimado`: Float
- `centro_gasto_codigo`: FK
- `conta_contabil_codigo`: FK
- `mes_competencia`: String (JAN, FEV...)
- `status`: Enum (PENDENTE, REALIZADA, CANCELADA)
- `lancamento_realizado_id`: FK (Link para quando a provisão virar lançamento real)
- `justificativa_base_zero`: Text (Suporte Feature E)

#### Tabela: `remanejamentos` (Feature D)

Transferências de orçamento entre centros.

- `id`: PK
- `centro_origem`: FK
- `centro_destino`: FK
- `valor`: Float
- `mes`: String
- `justificativa`: Texto
- `status`: Enum (SOLICITADO, APROVADO, REJEITADO)
- `aprovador`: String

#### Tabela: `forecast_cenarios` (Feature A)

- `id`: PK
- `nome`: String (ex: "Cenário Otimista Jan/26")
- `data_criacao`: DateTime
- `tipo`: Enum (AUTOMATICO, MANUAL)

#### Tabela: `forecast_entries`

- `cenario_id`: FK
- `mes`: String
- `centro_gasto_codigo`: String
- `valor_previsto`: Float

---

## 🧠 Backend: Módulos e Serviços

### 1. `services/forecast_service.py`

- Lógica de projeção matemática (Linear, Média Móvel).
- Integração com dados históricos do P&L (Dec 2025).
- Geração de cenários automáticos.

### 2. `services/provisioning_service.py`

- CRUD de provisões.
- Função `conciliar_provisao(provisao_id, lancamento_id)`:
  - Atualiza status para REALIZADA.
  - Calcula delta (Estimado vs Realizado).

### 3. `services/budget_control.py` (Remanejamento + OBZ)

- Validação de regras:
  - Origem tem saldo disponível?
  - Valor excede % permitido?
- Histórico de movimentações.
- Cálculo de "Orçamento Ajustado" (`Orcamento Original +/- Remanejamentos`).

### 4. `services/ai_board.py` (AI Board of Directors)

Arquitetura multi-agente para análise holística. O `SimpleAdvisor` será substituído por um orquestrador que consulta personas especializadas:

- **Board Orchestrator**: Recebe a consulta do usuário e distribui para os especialistas relevantes. Sintetiza as respostas em uma visão única.
- **Agentes Especialistas**:
    1. **Strategic CFO**: Foco em estratégia, tendências macro e P&L consolidado. Usa base de conhecimento "Finanças Corporativas" (NotebookLM) para alinhar com melhores práticas de mercado.
    2. **Operational Controller**: Foco em desvios orçamentários, centros de custo e "chão de fábrica". Analisa o realizado vs orçado detalhado.
    3. **Risk Auditor**: Foco em compliance, provisões (IAS 37) e riscos. Verifica se provisões estão adequadas e alerta sobre gastos anômalos ou sem justificativa (OBZ).
    4. **Forecast Analyst**: Foco em futuro. Analisa tendências matemáticas e projeta cenários (Otimista/Pessimista) com base nos dados históricos.

**Fluxo Técnico**:

- Prompt Engineering avançado com "Personas".
- Contexto injetado diferenciado para cada agente (ex: Controller recebe tabelas detalhadas, CFO recebe sumarizado).
- Round-table synthesis: O orquestrador consolida os insights divergentes/complementares.

---

## 🖥️ Frontend: Interfaces (Streamlit)

### Página: `04_🔮_Previsao_IA.py` (Features A & C)

- **Aba 1: Forecast**: Gráficos de projeção, seletor de cenários.
- **Aba 2: Consultor IA**: Chat interface com contexto financeiro carregado.

### Página: `05_🧱_Controle_Orcamentario.py` (Features B, D, E)

- **Aba 1: Provisões**:
  - Grid editável de provisões.
  - Botão "Conciliar" (abre modal para selecionar lançamento).
- **Aba 2: Remanejamentos**:
  - Form de solicitação (De -> Para).
  - Lista de aprovação.
- **Aba 3: OBZ Light**:
  - Análise de justificativas e scoring de gastos.

---

## 🔄 Integração e Fluxo

1. **P&L Histórico**:
    - O sistema lerá `Doc referencia/P&L - Dezembro_2025.xlsx` para calibrar o forecast.
    - Mapeamento de contas contábeis será mantido (conforme instrução do usuário).

2. **Fluxo Lançamento -> Provisão**:
    - Ao criar um item na página de Provisões, ele aparece no Dashboard de "Previsto".
    - Quando o usuário faz o input real em `02_📝_Lancamentos.py`, ele poderá ver "Provisões em Aberto" e vincular.

---

## ✅ Critérios de Aceite

1. **Forecast**: Deve projetar fechamento do ano com base no realizado + histórico.
2. **Provisão**: Deve permitir criar provisão e depois "baixar" contra um lançamento real.
3. **Remanejamento**: O comparativo orçado x realizado deve refletir o orçamento *ajustado* pelos remanejamentos.
4. **IA**: O chat deve responder perguntas sobre o orçamento usando a base de conhecimento do NotebookLM.
