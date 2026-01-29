
import pandas as pd
import os
import sys
import hashlib
from datetime import datetime

# Setup environment to allow imports
sys.path.append(os.getcwd())

from database.models import get_session, LancamentoRealizado
from utils_financeiro import processar_pl_baseal
from data.referencias_manager import REFERENCIAS_DIR

def load_account_map():
    path = REFERENCIAS_DIR / "conta_contabil.xlsx"
    if not path.exists():
        print("[ERRO] Arquivo de conta_contabil.xlsx nao encontrado. Usando nomes originais.")
        return {}
    
    df = pd.read_excel(path)
    # RENAME cols to standard
    df.rename(columns={'CÓDIGO CONTA CONTÁBIL': 'codigo', 'DESCRIÇÃO CONTA CONTÁBIL': 'descricao'}, inplace=True)
    
    # Map Description -> Reference Code
    # Normalize: Upper and Strip
    mapping = {}
    for _, row in df.iterrows():
        desc = str(row['descricao']).strip().upper()
        code = str(row['codigo']).strip()
        mapping[desc] = code
    return mapping

def load_center_map():
    path = REFERENCIAS_DIR / "centro_gasto.xlsx"
    if not path.exists():
        return {}
    
    df = pd.read_excel(path)
    # Map Code -> Info Dict
    mapping = {}
    for _, row in df.iterrows():
        code = str(row['CENTRO DE GASTO']).strip().zfill(11)
        ativo = str(row['ATIVO']).strip()
        desc = str(row['DESCRIÇÃO CENTRO DE GASTO']).strip()
        
        # Determine specific attributes
        is_cos = (ativo == 'COS')
        is_ga = (ativo == 'G&A')
        
        mapping[code] = {
            'ativo': ativo,
            'descricao': desc,
            'is_cos': is_cos,
            'is_ga': is_ga
        }
    return mapping

def generate_synthetic_code(desc):
    """Gera codigo hash curto para contas sem mapeamento."""
    # Use simple ascii chars only
    hash_obj = hashlib.md5(desc.encode('utf-8', errors='ignore'))
    return "H_" + hash_obj.hexdigest()[:8].upper()

def main():
    print("[INFO] Iniciando importacao de historico...")
    
    # 1. Carregar Dados do Excel usando script existente
    file_path = "Doc referencia/P&L - Dezembro_2025.xlsx"
    if not os.path.exists(file_path):
        print(f"[ERRO] Arquivo nao encontrado: {file_path}")
        return

    print("[INFO] Lendo arquivo Excel...")
    with open(file_path, "rb") as f:
        # User defined utils function
        df_raw = processar_pl_baseal(f)
    
    if df_raw.empty:
        print("[ERRO] Nenhum dado retornado de processar_pl_baseal.")
        return

    print(f"[OK] Dados carregados: {len(df_raw)} linhas.")
    
    # 2. Filtrar e Ajustar Anos
    # 'Realizado' -> 2025
    # 'LY - Actual' -> 2024
    
    df_2025 = df_raw[df_raw['tipo_valor'] == 'Realizado'].copy()
    df_2025['ano_real'] = 2025
    
    df_2024 = df_raw[df_raw['tipo_valor'] == 'LY - Actual'].copy()
    df_2024['ano_real'] = 2024
    
    df_final = pd.concat([df_2025, df_2024])
    print(f"[INFO] Filtrados: {len(df_2025)} registros de 2025 e {len(df_2024)} registros de 2024.")

    # 3. Carregar Mapas de Referência
    account_map = load_account_map()
    center_map = load_center_map()
    print(f"[DEBUG] Mapa de Contas carregado: {len(account_map)} itens.")
    print(f"[DEBUG] Mapa de Centros carregado: {len(center_map)} itens.")
    
    # 4. Inserir no Banco
    session = get_session()
    count_ok = 0
    count_nomap = 0
    
    for idx, row in df_final.iterrows():
        try:
            # Centro de Gasto
            cc_codigo = str(row['codigo_centro_gasto']).zfill(11)
            cc_info = center_map.get(cc_codigo, {})
            
            cc_pai = cc_codigo[:8]
            cc_classe = cc_codigo[8] if len(cc_codigo) > 8 else '0'
            
            # Conta Contábil
            conta_desc = str(row['conta_contabil']).strip()
            conta_desc_norm = conta_desc.upper()
            
            conta_codigo = account_map.get(conta_desc_norm)
            if not conta_codigo:
                # Tentar encontrar por substring ou fallback
                conta_codigo = generate_synthetic_code(conta_desc)
                count_nomap += 1
            
            # Valor
            val = float(row['valor'])
            if val == 0:
                continue # Pula zeros para economizar DB
            
            # Criar Objeto - REMOVIDO REALIZADO=TRUE POIS NAO EXISTE NO MODELO
            lanc = LancamentoRealizado(
                ano=int(row['ano_real']),
                mes=row['mes'],
                
                centro_gasto_codigo=cc_codigo,
                centro_gasto_pai=cc_pai,
                centro_gasto_classe=cc_classe,
                centro_gasto_classe_nome="Importado", # Simplificado
                centro_gasto_descricao=cc_info.get('descricao', row.get('centro_gasto_nome', 'N/A')),
                ativo=cc_info.get('ativo', 'N/A'),
                
                is_cos=cc_info.get('is_cos', False),
                is_ga=cc_info.get('is_ga', False),
                is_sem_hierarquia=False, # Assume false
                
                conta_contabil_codigo=conta_codigo,
                conta_contabil_descricao=conta_desc,
                
                fornecedor="Historico Imports",
                descricao=f"P&L {row['tipo_valor']} - {row['mes']}/{row['ano_real']}",
                valor=val,
                usuario="Sistema (Import)"
            )
            session.add(lanc)
            count_ok += 1
            
            if count_ok % 1000 == 0:
                print(f"[...] Processados {count_ok}...")
                
        except Exception as e:
            print(f"[ERRO] Erro na linha {idx}: {e}")

    session.commit()
    print("="*40)
    print(f"[SUCESSO] Importacao Concluida!")
    print(f"[INFO] Total Inserido: {count_ok}")
    print(f"[AVISO] Contas sem mapeamento (Synthetic Codes): {count_nomap}")
    session.close()

if __name__ == "__main__":
    main()
