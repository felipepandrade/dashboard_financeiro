# Plano de Revisão e Correção - Importação P&L Histórico

## 1. Diagnóstico da Situação Atual

A importação realizada via `import_history_2025.py` inseriu 2.344 registros no banco de dados para os anos de 2024 e 2025.
No entanto, **100% das contas contábeis (3.792 ocorrências)** não encontraram correspondência na base de referência do sistema e receberam **Códigos Sintéticos** (ex: `H_1A2B3C`).

### Causa Raiz

- O arquivo de entrada (`P&L - Dezembro_2025.xlsx`) possui descrições de contas em **Inglês** (ex: "Gross Sales").
- A base de referência do sistema (`referencias/conta_contabil.xlsx`) utiliza o Plano de Contas padrão em **Português** (ex: "Receita Bruta").
- O script atual tenta fazer um match exato de string (normalizada), que falha para todos os casos.

### Impacto

- **Forecast (Preditivo)**: Funciona isoladamente, projetando tendências baseadas no histórico sintético.
- **Comparativo (Orçado x Realizado)**: Falha crítica. O Orçamento 2026 usa códigos reais. O Histórico usa códigos sintéticos. Não será possível comparar a performance histórica com a meta de 2026 no nível de conta contábil.
- **Relatórios**: A visualização detalhada ficará "suja" com códigos criptografados.

## 2. Soluções Propostas

| Opção | Descrição | Prós | Contras |
|-------|-----------|------|---------|
| **A. Mapeamento Manual** | Gerar planilha com nomes em Inglês e pedir para o usuário preencher o código correspondente em Português. | 100% preciso. | Trabalhoso para o usuário. |
| **B. De-Para Semântico (IA)** | Usar IA para sugerir o mapeamento (Inglês -> Português) e gerar um arquivo para validação rápida do usuário. | Menor esforço do usuário. Alta assertividade. | Requer revisão humana para garantir precisão contábil. |
| **C. Novo Arquivo Fonte** | Solicitar ao usuário um arquivo P&L já ajustado com os códigos oficiais ou descrições em Português. | Solução definitiva na fonte. | Pode não ser viável se o sistema de origem do usuário só exporta em Inglês. |

## 3. Caminho Recomendado (Assertivo)

Adotar a **Opção B (Híbrida)**:

1. Extrair todas as descrições únicas do P&L (Inglês).
2. Extrair todas as contas do Plano de Contas (Português).
3. Utilizar o Agente (Backend Specialist + AI Skills) para gerar um `mapping_suggestion.csv` com as melhores correspondências.
4. Pausar e solicitar validação do usuário (via `notify_user`).
5. O usuário edita/confirma o CSV.
6. O sistema re-processa a importação usando o mapa validado, substituindo os registros sintéticos.

## 4. Plano de Execução (Orchestration)

Este plano será executado seguindo o workflow de orquestração.

### Fase 1: Análise (Project Planner) - [Atual]

- Criar este documento de diagnóstico.

### Fase 2: Implementação da Solução (Backend Specialist)

- **Tarefa 1**: Criar script `generate_mapping.py` para extrair descrições e usar IA (fuzzy/semantic matching) para criar `de_para_contas.csv`.
- **Tarefa 2**: Notificar usuário para revisar `de_para_contas.csv`.
- **Tarefa 3**: Atualizar `import_history_2025.py` para ler `de_para_contas.csv` (se existir) e forçar o uso dos códigos mapeados.
- **Tarefa 4**: Executar script de limpeza (remover lançamentos sintéticos) e re-importação.

### Fase 3: Verificação (Test Engineer)

- Verificar se `lancamentos_realizados` contém códigos reais (sem prefixo `H_`).
- Verificar integridade dos dados (totais batendo).

## 5. Aprovação Necessária

O usuário deve aprovar esta abordagem antes de prosseguirmos para a geração do mapa.
