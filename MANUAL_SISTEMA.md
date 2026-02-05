# manual_sistema.md

# Sistema de Gestão Financeira Integrada - 2026

**Versão do Documento:** 1.0  
**Data:** 02/02/2026  
**Status:** Produção

---

## 1. Visão Geral e Filosofia

### O Propósito

Este sistema foi desenvolvido para superar as limitações das planilhas tradicionais de controle orçamentário. O objetivo central é fornecer uma **"Single Source of Truth" (Fonte Única da Verdade)** para a gestão financeira, unificando dados oficiais (P&L Contábil/SAP) com a agilidade necessária para a gestão do dia a dia (Provisões e Compromissos).

### A Filosofia "Shadow Ledger"

A principal inovação arquitetural deste sistema é o conceito de **Shadow Ledger** (Razão Sombra).

- **O Problema:** Sistemas oficiais (SAP) são lentos e retroativos (D-1 ou D-30). O controle operacional precisa ser em tempo real.
- **A Solução:** O sistema mantém duas linhas de dados paralelas que se reconciliam:
    1. **Realizado (Oficial):** Dados importados do SAP/P&L, imutáveis e auditáveis.
    2. **Provisionado (Operacional):** Compromissos futuros inseridos manualmente pela equipe.
- **O Resultado:** No Dashboard, o gestor vê `Total Executado = Realizado Ofical + Provisões Pendentes`. À medida que uma nota fiscal é paga (vira Realizado), a Provisão correspondente é baixada, mantendo o saldo sempre atualizado sem duplicidade.

### Experiência do Usuário (UX) "Premium"

A interface foi desenhada seguindo princípios de **Glassmorphism** e **Hierarquia Visual Clara**, fugindo do padrão "tabela de dados". O foco é permitir que executivos (C-Level) e Analistas usem a mesma ferramenta, com níveis de profundidade diferentes (KPIs gerais -> Drill-down por Centro de Custo -> Detalhe da Transação).

---

## 2. Arquitetura do Sistema

### Stack Tecnológica

- **Frontend/App:** Streamlit (Python) - Escolhido pela velocidade de desenvolvimento e facilidade com dados.
- **Backend/ORM:** SQLAlchemy - Garante robustez e independência de banco de dados (atualmente SQLite, pronto para PostgreSQL).
- **Visualização:** Plotly - Gráficos interativos de alta performance.
- **Migrações:** Alembic - Controle de versão da estrutura do banco de dados.

### Estrutura de Dados (Módulos Principais)

1. **Lançamentos & Provisões (`provisoes`)**:
    - Tabela viva onde a equipe insere compromissos futuros.
    - Campos chave: `status` (PENDENTE, REALIZADA, CANCELADA), `numero_registro` (Link com Oracle/SAP).

2. **Dados Oficiais (`lancamentos_realizados`)**:
    - Espelho dos dados sumarizados do P&L.
    - Alimentado via Upload de Arquivo Excel Padrão.

3. **Shadow Ledger (`razao_realizados`)**:
    - Tabela de auditoria que armazena *cada linha* do razão contábil importado.
    - Permite "drill-down" para saber exatamente qual fornecedor compôs aquele saldo no gráfico.

---

## 3. Manual do Usuário

### 3.1 Dashboards de Acompanhamento (`03_📈_Acompanhamento`)

Esta é a tela principal para gestão.

- **Visão Mensal:** Gráfico de barras combinando o que já foi pago (Verde) com o que está comprometido para o futuro (Amarelo/Laranja). A linha azul indica o Orçamento (Target).
  - *Dica:* Se a barra (Verde+Amarela) ultrapassar a linha Azul, haverá estouro orçamentário.
- **Drill-down por Centro de Custo:** Clique na aba "Por Centro de Custo" para ver um Heatmap de onde estão os maiores desvios.
- **Tabelas Detalhadas:** Todas as abas possuem tabelas no final. Use a coluna "Provisionado" para ver quanto do gasto é apenas estimado.

### 3.2 Gestão de Compromissos (`02_📝_Lancamentos`)

Use este módulo para dizer ao sistema o que você *vai* gastar.

- **Criar Provisão:** Preencha o formulário na aba lateral. O valor entrará imediatamente nos gráficos como "Provisionado".
- **Editar/Atualizar:**
  - **Edição Unitária:** Interface direta na grid com formulário.
  - **Atualização em Lote (Bulk Update):**
    - Exportação de Excel com colunas protegidas (ID, Metadados).
    - Listas suspensas (Data Validation) para Status e Booleanos.
    - **Controle de Concorrência:** Implementação de Optimistic Locking via timestamp (`data_atualizacao`). O sistema rejeita atualizações se o registro mudou no banco após o download.
    - Transação Atômica: Ou atualiza todo o lote ou faz rollback em caso de erro.
  - **Importante:** Ao mudar o status para `REALIZADA`, informe o "Número de Registro" (RC/Pedido).
- **Exportar:** Use o botão "Exportar Excel" para gerar um relatório para a Controladoria.

### 3.3 Importação de Dados (Admin)

Para atualizar os dados "Realizados" (Verdes):

1. Acesse a página `Home`.
2. Faça o upload do arquivo Excel padrão de P&L.
3. O sistema processará:
    - Aba "Realizado" -> Atualiza os gráficos de histórico.
    - Aba "Razão_Gastos" -> Popula o *Shadow Ledger* para auditoria.

---

## 4. Guia Técnico e Manutenção

### Estrutura de Arquivos

```
/
├── Home.py                  # Ponto de entrada (Uploads)
├── pages/
│   ├── 02_Lancamentos.py    # CRUD de Provisões
│   └── 03_Acompanhamento.py # Dashboard Principal
├── services/
│   └── provisioning_service.py # Regras de negócio de provisões
├── data/
│   └── comparador.py        # Lógica de agregação (Real vs Orcado)
├── database/                # Modelos SQLAlchemy
└── utils_financeiro.py      # ETL e Processamento de Excel
```

### Comandos Úteis

- **Rodar o Sistema:** `streamlit run Home.py`
- **Criar nova migração de banco:** `alembic revision --autogenerate -m "mensagem"`
- **Aplicar migrações:** `alembic upgrade head`
