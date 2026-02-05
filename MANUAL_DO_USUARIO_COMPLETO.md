# MANUAL DO USUÁRIO COMPLETO: SGO-2026 (Sistema de Gestão Orçamentária)

**Data da Revisão:** 02/02/2026  
**Status:** Documento Mestre (Final)  
**Versão do Sistema:** 2.2 (Full Suite)

---

# 📚 Prefácio: O Que É e Para Que Serve?

Bem-vindo ao **SGO-2026**. Este não é apenas um dashboard de visualização; é um **Sistema Operacional de Finanças**.

Diferente de relatórios estáticos em PowerBI ou Excel que mostram "o que aconteceu mês passado" (Retrovisor), o SGO-2026 foi desenhado para gerir **"o que vai acontecer"** (Para-brisa).

### A Filosofia Central: "Shadow Ledger" (Para Analistas e Gestores)

Você já passou pela situação de olhar o relatório oficial do SAP, ver que gastou R$ 50k a menos que o budget, comemorar, e 10 dias depois receber uma nota fiscal de R$ 80k referente a um serviço do mês passado?

Isso acontece porque a **Contabilidade (Realizado)** tem um atraso natural (o fornecedor demora a emitir a NF, o pagamento demora a cair).

O SGO resolve isso criando uma **Realidade Paralela (Shadow Ledger)**:

1. **Camada Real (Verde):** O que a contabilidade já processou.
2. **Camada Sombra (Laranja):** O que você sabe que gastou (pedidos emitidos, contratos assinados), mas que ainda não virou nota fiscal.

O sistema soma essas duas camadas. Se a soma estourar o orçamento, o sistema te avisa **antes** do fechamento contábil.

---

# 🚀 Módulo 1: Home e Ingestão de Dados (A Verdade Contábil)

A tela **Home** (`🏠`) é o coração da atualização de dados. É aqui que você carrega a "Verdade Oficial" vinda do seu ERP (SAP, Oracle, Totvs).

### 1.1 Painel de Status

No topo, você verá três cartões:

* **Status Orçamento:** Deve estar `✅ Carregado`. Indica que as metas do ano estão ativas.
* **Dados Realizados:** Indica a data da última carga do P&L. Se estiver vermelho, seus dados estão obsoletos.
* **Mês de Fechamento:** O último mês contábil encerrado encontrado no sistema.

### 1.2 Como Fazer o Upload (Passo a Passo)

1. Exporte o relatório financeiro do seu ERP em Excel. Certifique-se de que ele tenha as abas:
    * `P&L BASEAL`: Resumo gerencial.
    * `Razão_Gastos`: Detalhe linha a linha (obrigatório para auditoria).
2. Vá na seção **"📥 Carga de Dados"**.
3. Selecione o **Ano de Referência** (Geralmente o ano atual).
4. Arraste o arquivo para a área pontilhada.
5. **Aguarde a validação:** O sistema verifica se todas as colunas necessárias existem.
    * *Sucesso:* Balões subirão na tela.
    * *Erro:* Uma caixa vermelha dirá exatamente qual coluna sumiu.

---

# 📝 Módulo 2: Motor Operacional (Lançamentos e Provisões)

Acesse no menu lateral: **"02_Lancamentos"**. Aqui é onde você trabalha no dia a dia.

### 2.1 Criando uma Nova Provisão (Aba "➕ Nova Provisão")

Use isso sempre que assinar um contrato ou aprovar um pedido de compra (RC).

* **Descrição:** Seja específico (Ex: "Manutenção Preventiva Chillers - Contrato Anual").
* **Valor Estimado:** O valor bruto.
* **Classificação:**
  * *Variável:* Depende de volume (Produção, Vendas).
  * *Fixa:* Aluguel, Salários.
  * *Emergencial:* Gastos não planejados (Quebras).
* **Mês Competência:** Quando o serviço será prestado (não necessariamente quando será pago).
* **Centro de Custo & Conta:** Selecione nas listas.
  * *Dica:* Ao selecionar um centro, observe o cartão azul que aparece abaixo: ele mostra a **Hierarquia** e o **Ativo** ao qual aquele centro pertence. Isso evita erros de alocação.
* **Dados de Rastreio (Novidade V2):**
  * *Contrato:* Número do contrato jurídico.
  * *Cadastrado no Sistema (Sim/Não):* Se você já abriu a RC no Oracle, marque **Sim**.
  * *Número de Registro:* **Obrigatório se Sim**. Coloque o número da RC ou Pedido. Isso é vital para cruzar dados depois.
* **Botão "Registrar":** Salva instantaneamente no banco de dados.

### 2.2 Importação em Lote (Aba "📥 Importação")

Vai lançar 50 provisões de uma vez? Não digite uma por uma.

1. Clique em **"Baixar Modelo de Importação"**.
2. Preencha o Excel mantendo as colunas exatas.
3. Faça o upload na mesma tela.
4. O sistema validará linha por linha e mostrará o que será importado.

### 2.3 Gerenciando a Vida da Provisão (Aba "📋 Compromissos Ativos")

Aqui vive o conceito de Shadow Ledger. Você tem duas formas de trabalhar:

**A. Edição via Tabela (Um a Um):**

* Selecione um item na tabela.
* Use o formulário "Gerenciar Item" no fim da página para alterar valor, status ou cancelar.

**B. Atualização em Lote (Excel) - NOVIDADE 🚀:**
Precisa atualizar o status de 50 itens de PENDENTE para REALIZADA?

1. Clique em **"📥 Baixar Pendentes para Edição"**.
2. Abra o Excel gerado. As colunas cinzas (ID, Descrição) são protegidas/informativas.
3. Edite as colunas liberadas:
   * **Valor Estimado:** Corrija o valor final.
   * **Status:** Use a lista suspensa (PENDENTE, REALIZADA, CANCELADA).
   * **Cadastrado Sistema:** Use a lista suspensa (VERDADEIRO/FALSO).
   * **Número Registro:** Informe o RC/Pedido (Obrigatório se REALIZADA).
4. Salve e faça o upload em **"📤 Importar Atualizações"**.
5. O sistema validará conflitos (se alguém editou ao mesmo tempo) e atualizará tudo de uma vez.

* **Exportar Relatório:** Use o botão "Exportar" simples do topo para gerar um snapshot apenas para leitura/envio.

---

# 📈 Módulo 3: O Painel de Controle (Acompanhamento)

Acesse: **"03_Acompanhamento"**.

### 3.1 Entendendo o Gráfico Principal (Mensal)

É um gráfico de barras **Empilhadas** e **Sobrepostas**.

* **Barra Verde (Base):** Dinheiro já gasto oficialmente (P&L).
* **Barra Amarela (Topo):** Dinheiro comprometido (Provisões Pendentes).
* **Linha Azul:** Seu Orçamento (Budget).

**Regra de Ouro:** Se a ponta da barra Amarela cruzar a linha Azul, você terá um problema. Aja agora (cancele ou postergue gastos).

### 3.2 Análise de Desvios (Drill-Down)

As abas abaixo do gráfico permitem investigar o "Porquê".

* **Aba "Por Centro de Custo":** Mostra uma tabela de calor. Centros vermelhos estão estourados.
* **Aba "Por Ativo":** Agrupa os centros por ativo físico (Ex: "Base Catu", "Base Pilar"). Útil para gerentes regionais.

---

# 📚 Módulo 4: Bíblia Financeira (Dados Mestres)

Acesse: **"04_Biblia_Financeira"**.

Este módulo serve para **Auditores** e **Data Discovery**. Ele expõe os dados brutos sem filtros de visualização.

### 4.1 Orçamento Base (V1)

Consulte o detalhe original do orçamento aprovado.

* Use a caixa **"Buscar"** para encontrar um fornecedor específico ou conta contábil em toda a base orçamentária.
* Ative **"Ver abertura mensal"** para ver quanto foi orçado mês a mês para aquela linha.

### 4.2 Histórico Realizado

Semelhante à Home, mas focado em análise multi-ano. Se você carregou 2024, 2025 e 2026, pode selecionar todos no filtro para ver a evolução histórica de longo prazo.

---

# 🧱 Módulo 5: Controle e Governança (OBZ)

Acesse: **"05_Controle_Orcamentario"**.

Este módulo é o "Juiz" do sistema. É onde você negocia verba.

### 5.1 Solicitar Remanejamento (Transferência)

O dinheiro acabou em uma conta, mas sobrou em outra?

1. **Origem e Destino:** Selecione de onde sai e para onde vai o recurso.
2. **Valor e Mês:** Defina o montante.
3. **Justificativa:** Obrigatório. O aprovador verá este texto.
4. **Aprovação:** Se você for Admin, verá a seção "Painel do Aprovador" para dar De Acordo/Recusar.

### 5.2 Justificativa OBZ (Orçamento Base Zero)

Prepare-se para o ciclo orçamentário do ano que vem.

1. Selecione seu Centro de Custo.
2. Expanda **"Detalhes Operacionais"** para ver tudo que você gastou este ano.
3. Crie **Pacotes de Decisão**:
    * Defina um nome para o pacote (Ex: "Segurança Patrimonial").
    * Classifique a urgência (Obrigatório, Estratégico, Necessário).
    * O sistema plota esses pacotes na **Matriz de Criticidade**. Pacotes "Caros e Não-Essenciais" serão os primeiros a serem cortados num cenário de crise.

---

# 🧠 Módulo 6: Inteligência Artificial (Forecast)

Acesse: **"06_Previsao_IA"**.

### 6.1 O "AI Board Advisor"

Imagine que você tem um conselho de 4 especialistas disponíveis 24/7. Digite sua dúvida sobre os números e receba uma análise sob 4 perspectivas (Financeira, Operacional, Risco e Estratégica).

### 6.2 Forecast Matemático

Projeta o fechamento do ano usando algoritmos:

* **Regressão Linear:** Tendência simples.
* **SARIMAX:** Tendência + Sazonalidade (picos recorrentes).

---

# ⚙️ Módulo 7: Gestão do Sistema (Admin)

Acesse: **"07_Gestao_Dados"**. (Acesso Restrito)

### 7.1 Editor de Banco de Dados

Precisa corrigir um erro de digitação num lançamento de 3 meses atrás que não aparece mais na tela de edição simples?

* Selecione a tabela (ex: `provisoes`).
* Edite a célula como se fosse um Excel.
* Clique em **"Salvar Alterações"**. (Cuidado: Isso altera diretamente o banco de produção).

### 7.2 Evolução de Schema

O sistema cresceu e você precisa de um novo campo na tabela de Provisões (Ex: `numero_pedido_sap`)?

* Use a aba **"Estrutura"** para adicionar novas colunas sem precisar chamar a TI/Desenvolvedor.

---

# ❓ FAQ e Solução de Problemas

**Q: Fiz uma provisão, mas a nota fiscal chegou com valor diferente. O que faço?**
R: Vá em `02_Lancamentos` -> Aba Lista -> Editar. Corrija o valor para o valor final da NF e mude o status para `REALIZADA`.

**Q: Por que meu "Realizado" na Home está diferente do SAP?**
R: Verifique a data da carga na Home. Se o arquivo for antigo, os dados estarão antigos. Faça um novo upload.

**Q: O sistema suporta múltiplos usuários editando ao mesmo tempo?**
R: Sim, o banco de dados suporta concorrência, mas recomendamos que cada analista cuide do seu centro de custo para evitar confusão.

---
*Este manual deve ser lido por todos os usuários antes de operar o sistema.*
