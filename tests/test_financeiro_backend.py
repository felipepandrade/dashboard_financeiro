import pandas as pd
import numpy as np
import os
import sys
from io import BytesIO

# Adicionar diretório raiz ao path para importar utils_financeiro
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils_financeiro import processar_upload_completo

def create_mock_excel():
    """Cria um arquivo Excel em memória com as abas P&L e Razão."""
    buffer = BytesIO()
    
    # --- 1. Dados P&L ---
    # Estrutura esperada: 15 linhas de cabeçalho ignoradas, header na linha 16 (index 0 do read_excel parms)
    # Colunas: Index 0=Codigo, Index 2=Conta
    # JAN..DEZ com colunas de Realizado, Budget V1, etc.
    
    # Criando colunas de meses (JAN..DEZ) x (Realizado, Budget V1, Budget V3, LY - Actual)
    # Total 4 colunas * 12 meses = 48 colunas.
    # Mais as colunas iniciais.
    
    # Vamos simplificar criando apenas JAN e FEV e colunas iniciais suficientes
    
    cols = ['Codigo', 'Descricao', 'Conta Contabil']
    # Adicionando colunas dummy até chegar nas de meses (index 3 a ...?)
    # O código espera:
    # JAN começa no index 3? Não, ver mapa:
    # 'JAN': {3: 'Realizado', ...} -> Index 3 é a 4ª coluna (0,1,2,3)
    
    # Pela função:
    # df.columns[0]: 'codigo_centro_gasto'
    # df.columns[2]: 'conta_contabil'
    
    # Estrutura Mock:
    # Col 0: Codigo
    # Col 1: Descricao
    # Col 2: Conta
    # Col 3: JAN Realizado
    # Col 4: JAN Budget V1
    # Col 5: JAN Budget V2 (Ignorado)
    # Col 6: JAN Budget V3
    # Col 7: JAN LY
    # ... e assim por diante.
    
    data_pl = {
        'Codigo': ['01020504001', '01020504101', '0'], # 2 custos, 1 financeiro (0)
        'Descricao': ['Gerencia BA', 'Coord Catu', 'Receita'],
        'Conta Contabil': ['Despesa Viagem', 'Materiais', 'Net Revenue'],
        # JAN
        'Jan_Real': [1000, 500, 50000],
        'Jan_Bud1': [1200, 600, 55000],
        'Jan_Ign': [0, 0, 0],
        'Jan_Bud3': [1100, 550, 52000],
        'Jan_LY': [900, 450, 48000],
        # FEV (Indices: 8,9,11,12) -> Col 8 é a 9ª. 
        # Atual: 0,1,2,3,4,5,6,7 -> Próxima 8.
        'Fev_Real': [1100, 510, 51000],
        'Fev_Bud1': [1200, 600, 55000],
        'Fev_Ign': [0, 0, 0],
        'Fev_Bud3': [1150, 550, 53000],
        'Fev_LY': [950, 460, 49000],
    }
    # Preencher resto dos meses com zeros se necessário, mas o código itera sobre o que existe.
    # Se o DataFrame tiver menos colunas que o esperado para DEZ, o código vai ignorar DEZ.
    
    df_pl = pd.DataFrame(data_pl)
    
    # --- 2. Dados Razão ---
    # Header na linha 2 (index 1).
    # Colunas esperadas padronizadas: 'valor_credito', 'nome_do_fornecedor', 'centro_gasto'
    data_razao = {
        'Data': ['2026-01-15', '2026-01-20'],
        'Empty': [None, None],
        'nome_do_fornecedor': ['Fornecedor A', 'Fornecedor B'],
        'centro_gasto': ['01020504001', '01020504101'],
        'valor_credito': [1000, 500],
        'historico': ['Serviço X', 'Compra Y']
    }
    df_razao = pd.DataFrame(data_razao)
    
    # Criar Excel Writer
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # P&L: skiprows=15 -> dados começam na linha 16 (Excel) -> linha 15 (0-idx).
        pd.DataFrame([['']]*15).to_excel(writer, sheet_name='P&L BASEAL', index=False, header=False)
        # Escrever header e dados na linha correta
        df_pl.to_excel(writer, sheet_name='P&L BASEAL', startrow=15, index=False)
        
        # Razão: header=1 -> Linha 0 ignorada, Linha 1 header, Dados linha 2+.
        pd.DataFrame([['Ignored']]).to_excel(writer, sheet_name='Razão_Gastos', index=False, header=False)
        df_razao.to_excel(writer, sheet_name='Razão_Gastos', startrow=1, index=False)
        
    buffer.seek(0)
    return buffer

def test_processamento():
    print(">>> Iniciando Teste de Processamento Financeiro (Refatoração)")
    
    # 1. Criar Mock
    mock_file = create_mock_excel()
    print("[OK] Arquivo Excel Mock criado em memória.")
    
    # 2. Executar Função
    print(">>> Executando processar_upload_completo...")
    try:
        df_pl, df_razao = processar_upload_completo(mock_file, ano=2026)
    except Exception as e:
        print(f"[FALHA] Erro de execução: {e}")
        return
        
    # 3. Validar P&L
    print("\n>>> Validando P&L:")
    if df_pl.empty:
        print("[FALHA] DataFrame P&L vazio.")
    else:
        print(f"[OK] Linhas retornadas: {len(df_pl)}")
        print(f"[INFO] Colunas: {list(df_pl.columns)}")
        
        # Verificar normalização de Custos vs Receita
        total_realizado = df_pl[df_pl['tipo_valor'] == 'Realizado']['valor'].sum()
        # Esperado: (1000+500+50000) Jan + (1100+510+51000) Fev = 51500 + 52610 = 104110
        print(f"[INFO] Total Realizado calculado: {total_realizado}")
        
        # Verificar mapeamento de centro de custo
        exemplo_cc = df_pl[df_pl['codigo_centro_gasto'] == '01020504001']['centro_gasto_nome'].iloc[0]
        if exemplo_cc == 'Gerência Regional BA':
             print("[OK] Mapeamento de Centro de Custo (Gerência Regional BA) correto.")
        else:
             print(f"[FALHA] Mapeamento incorreto: {exemplo_cc}")

    # 4. Validar Razão
    print("\n>>> Validando Razão:")
    if df_razao.empty:
        print("[FALHA] DataFrame Razão vazio.")
    else:
        print(f"[OK] Linhas retornadas: {len(df_razao)}")
        
        # Verificar colunas renomeadas
        esperadas = ['fornecedor', 'valor', 'codigo_centro_gasto', 'centro_gasto_nome']
        missing = [col for col in esperadas if col not in df_razao.columns]
        if not missing:
            print("[OK] Todas as colunas essenciais do Razão presentes.")
        else:
            print(f"[FALHA] Colunas faltando no Razão: {missing}")
            
        # Verificar valores
        total_zao = df_razao['valor'].sum()
        if total_zao == 1500:
            print("[OK] Total do Razão confere (1500).")
        else:
            print(f"[FALHA] Total do Razão incorreto: {total_zao} (Esperado 1500)")

if __name__ == "__main__":
    test_processamento()
