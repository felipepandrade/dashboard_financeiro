# PLANO DE IMPLEMENTAÇÃO: Atualização de Hierarquia (Regional/Base)

## 🎯 Objetivo

Incorporar os campos **Regional** e **Base** na estrutura de "Centros de Gasto", refletindo essa mudança no banco de dados, na visualização de metadados e facilitando o cadastro de provisões com filtros hierárquicos.

## 📋 Contexto

- **Solicitante**: Usuário
- **Fonte de Dados**: `Doc referencia/Centro de Gasto.xlsx` (contém novas colunas).
- **Impacto**: Banco de Dados (Postgres/SQLite), UI de Lançamentos, UI de Bíblia Financeira.

## 🛠️ Alterações Propostas

### 1. Camada de Dados (Referências)

- **Atualizar Arquivo Mestre**: Substituir `data/referencias/centro_gasto.xlsx` pelo novo arquivo em `Doc referencia/Centro de Gasto.xlsx`.
- **Atualizar `referencias_manager.py`**:
  - Ajustar `carregar_centros_gasto()` para ler e limpar as colunas `REGIONAL` e `BASE`.
  - Garantir que `buscar_centros_gasto()` suporte filtros por esses novos campos.

### 2. Camada de Banco de Dados (Schema)

- **Tabela `lancamentos_realizados`**:
  - Adicionar coluna `regional` (String)
  - Adicionar coluna `base` (String)
  - *Motivo*: Manter consistência histórica desnormalizada (como já é feito com `ativo` e `classe`).
- **Migração (Alembic)**:
  - Criar script de migração `add_regional_base_to_lancamentos`.

### 3. Camada de Interface (UI)

#### A. Página `04_📚_Biblia_Financeira.py`

- Atualizar aba "Metadados" para exibir as novas colunas na tabela de Centros de Custo.

#### B. Página `02_📝_Lancamentos.py` (Aba "Nova Provisão")

- **Refatorar Seleção de Centro**:
  - Adicionar Selectbox: **Regional** (populado dinamicamente).
  - Adicionar Selectbox: **Base** (filtrado pela Regional selecionada).
  - Atualizar Selectbox: **Centro de Custo** (filtrado pela Base selecionada).
  - *Regra*: Se nenhuma Regional for selecionada, comportamento atual (listar tudo) ou forçar filtro? -> *Proposta: Filtros opcionais que "afunilam" a lista.*

### 4. Deploy

- O script de migração será executado automaticamente no deploy (via `alembic upgrade head` ou `init_db` se suportado).

## 📅 Etapas de Execução

1. **Backup & Replace**: Atualizar o arquivo Excel de referência.
2. **Backend Logic**: Atualizar `referencias_manager.py`.
3. **Database Migration**: Alterar `models.py` e gerar migração Alembic.
4. **Frontend Update**: Implementar UI em `Lancamentos.py` e `Biblia.py`.
5. **Verificação**: Testar fluxo de cadastro e visualização.

## ⚠️ Pontos de Atenção

- Verificar se o nome exato das colunas no Excel novo é `REGIONAL` e `BASE` ou variações.
- Garantir que registros antigos no banco (sem regional) fiquem como `NULL` ou `N/A`.
