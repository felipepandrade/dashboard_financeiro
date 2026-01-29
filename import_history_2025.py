
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

def load_user_mapping():
    """Carrega o mapeamento validado pelo usuário com parser manual robusto."""
    csv_path = "de_para_contas.csv"
    if not os.path.exists(csv_path):
        print(f"[ERRO] Arquivo {csv_path} nao encontrado.")
        return {}
    
    mapping = {}
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for enc in encodings:
        try:
            with open(csv_path, 'r', encoding=enc) as f:
                lines = f.readlines()
            
            print(f"[DEBUG] Arquivo lido com encoding {enc}. {len(lines)} linhas.")
            
            # Skip header
            if len(lines) > 0 and "from_description" in lines[0]:
                lines = lines[1:]
            
            success_count = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Split apenas nas 2 primeiras virgulas
                parts = line.split(',', 2)
                
                if len(parts) >= 3:
                    from_desc = parts[0].strip()
                    to_code = parts[1].strip()
                    to_desc = parts[2].strip()
                    mapping[from_desc] = {'code': to_code, 'desc': to_desc}
                    success_count += 1
                elif len(parts) == 2:
                    # Caso to_desc esteja vazio ou falte
                    from_desc = parts[0].strip()
                    to_code = parts[1].strip()
                    mapping[from_desc] = {'code': to_code, 'desc': ""}
                    success_count += 1
                    
            if success_count > 0:
                print(f"[DEBUG] Parser manual: {success_count} mapeamentos carregados.")
                return mapping
                
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"[ERRO] Erro ao processar arquivo com {enc}: {e}")
            continue
            
    print("[ERRO] Falha critica ao ler CSV de mapeamento.")
    return {}

def main():
    print("[INFO] Iniciando RE-importacao de historico com De-Para...")
    
    # 1. Carregar mapeamento validado
    user_mapping = load_user_mapping()
    if not user_mapping:
        print("[ABORTAR] Mapeamento obrigatorio.")
        return
        
    # 2. Carregar Dados do Excel
    file_path = "Doc referencia/P&L - Dezembro_2025.xlsx"
    if not os.path.exists(file_path):
        print(f"[ERRO] Arquivo nao encontrado: {file_path}")
        return

    print("[INFO] Lendo arquivo Excel...")
    with open(file_path, "rb") as f:
        try:
            df_raw = processar_pl_baseal(f)
        except Exception as e:
            print(f"[ERRO] processar_pl_baseal falhou: {e}")
            return
    
    if df_raw.empty:
        print("[ERRO] Nenhum dado retornado.")
        return

    # Ajustar Anos
    df_2025 = df_raw[df_raw['tipo_valor'] == 'Realizado'].copy()
    df_2025['ano_real'] = 2025
    df_2024 = df_raw[df_raw['tipo_valor'] == 'LY - Actual'].copy()
    df_2024['ano_real'] = 2024
    df_final = pd.concat([df_2025, df_2024])
    
    # 3. Carregar Mapa de Centros (para enriquecimento)
    center_map = load_center_map()

    # 4. Banco de Dados: Limpeza e Inserção
    session = get_session()
    
    # LIMPEZA PREVIA
    print("[INFO] Limpando importacoes anteriores (usuario='Sistema (Import)')...")
    deleted = session.query(LancamentoRealizado).filter(
        LancamentoRealizado.usuario == "Sistema (Import)"
    ).delete()
    print(f"[INFO] {deleted} registros removidos.")
    
    count_ok = 0
    count_ignored = 0
    count_nomap = 0
    
    for idx, row in df_final.iterrows():
        try:
            # Centro de Gasto
            cc_codigo = str(row['codigo_centro_gasto']).zfill(11)
            cc_info = center_map.get(cc_codigo, {})
            
            # Conta Contábil (Via Mapa do Usuario)
            conta_origem = str(row['conta_contabil']).strip()
            
            map_entry = user_mapping.get(conta_origem)
            
            if not map_entry:
                # Se nao esta no mapa (pode acontecer se o P&L mudou?), gera sintetico ou ignora?
                # Vamos logar e pular ou sintetico.
                # Como o usuario validou TODOS do arquivo atual, isso nao deve ocorrer.
                # Fallback seguro: Ignorar ou avisar.
                # print(f"[AVISO] Conta sem mapeamento no CSV: {conta_origem}")
                count_nomap += 1
                continue
                
            if map_entry['code'] == 'IGNORE':
                count_ignored += 1
                continue
                
            conta_codigo = map_entry['code']
            conta_desc = map_entry['desc']
            
            # Atributos do Centro
            cc_pai = cc_codigo[:8]
            cc_classe = cc_codigo[8] if len(cc_codigo) > 8 else '0'
            
            val = float(row['valor'])
            if val == 0:
                continue 
            
            lanc = LancamentoRealizado(
                ano=int(row['ano_real']),
                mes=row['mes'],
                centro_gasto_codigo=cc_codigo,
                centro_gasto_pai=cc_pai,
                centro_gasto_classe=cc_classe,
                centro_gasto_classe_nome="Importado",
                centro_gasto_descricao=cc_info.get('descricao', row.get('centro_gasto_nome', 'N/A')),
                ativo=cc_info.get('ativo', 'N/A'),
                is_cos=cc_info.get('is_cos', False),
                is_ga=cc_info.get('is_ga', False),
                is_sem_hierarquia=False,
                conta_contabil_codigo=conta_codigo,
                conta_contabil_descricao=conta_desc, # Usa descricao validada (PT)
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
    print(f"[SUCESSO] Re-importacao Concluida!")
    print(f"[INFO] Inseridos: {count_ok}")
    print(f"[INFO] Ignorados (Receita/Calc): {count_ignored}")
    print(f"[INFO] Nao Mapeados (Erro): {count_nomap}")
    session.close()

if __name__ == "__main__":
    main()
