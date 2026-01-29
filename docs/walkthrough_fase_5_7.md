# Walkthrough: Novas Funcionalidades de Gestão Orçamentária

Este documento apresenta as novas funcionalidades implementadas no sistema (Fases 5, 6 e 7), transformando o dashboard em uma plataforma completa de governança e previsão.

## 1. 🔮 Previsão e Inteligência (`04_🔮_Previsao_IA`)

Nesta página, você tem acesso a ferramentas de futuro (Forecast) e análise estratégica (IA).

### Aba: AI Board Advisor

Substituímos o "Consultor Simples" por um **Board de Diretores Digitais**.

- **Como usar**: Digite uma pergunta na caixa de texto (Ex: "Como está performando a conta de Viagens? Devemos nos preocupar?").
- **O que acontece**:
  - **CFO**: Analisa sob a ótica estratégica.
  - **Controller**: Olha os números realizados e desvios.
  - **Auditor**: Verifica riscos e compliance.
  - **Analyst**: Tenta projetar o futuro.
  - **Chairman**: Sintetiza tudo em uma resposta final.

### Aba: Previsão (Forecast)

Gera cenários de fechamento anual com base no realizado até o momento.

- **Gerar Cenário**: Escolha o método (Linear, Média Móvel) e clique em "Gerar Novo Forecast".
- **Visualizar**: Compare o Realizado (Verde) vs Forecast (Roxo) vs Budget (Linha Azul).

---

## 2. 🧱 Controle Orçamentário (`05_🧱_Controle_Orcamentario`)

Central de comando para governança e ajustes do dia a dia.

### Aba: Gestão de Provisões (Feature B)

Use para registrar despesas que você *sabe* que vão ocorrer, mas ainda não foram faturadas (ex: nota fiscal pendente).

- **Criar**: Preencha o formulário com o valor estimado.
- **Conciliar**: Quando a despesa real chegar no mês seguinte (via importação de planilha), use o botão "Conciliar" para vincular a provisão ao lançamento real, baixando a pendência.

### Aba: Remanejamentos (Feature D)

Workflow para mover orçamento de um centro para outro.

- **Solicitar**: Indique Origem -> Destino e a justificativa.
- **Aprovar**: (Simulado) Use a área de aprovação para validar as solicitações.
- **Impacto**: O sistema mantém o histórico de quem aprovou o quê.

### Aba: Justificativa OBZ (Feature E)

Matriz de análise de gastos.

- Atualmente exibe uma visão demonstrativa de como classificar pacotes de gastos por "Essencialidade".

---

## ✅ Próximos Passos

1. Execute o sistema: `iniciar.bat`
2. Navegue até a página **🔮 Previsão IA** e teste o Board.
3. Crie uma **Provisão** na página **🧱 Controle**.
4. Teste um **Remanejamento** de saldo.

**Nota Técnica**:

- As tabelas de banco de dados (`forecast_cenarios`, `provisoes`, `remanejamentos`) foram criadas automaticamente.
- Se houver erro de "Tabela não encontrada", reinicie a aplicação para que o `models.py` garanta a criação.
