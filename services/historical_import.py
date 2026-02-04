
import pandas as pd
from sqlalchemy.orm import Session
from database.models import get_session, LancamentoRealizado
from data.referencias_manager import carregar_centros_gasto
import streamlit as st
import os

# Configurações Internas
# Caminho relativo assumindo execução da raiz
FILE_PATH = "Doc referencia/P&L - Dezembro_2025.xlsx"

MAPA_MESES_IDX = {
    'JAN': {3: 'Realizado', 7: 'LY - Actual'},
    'FEV': {8: 'Realizado', 12: 'LY - Actual'},
    'MAR': {13: 'Realizado', 17: 'LY - Actual'},
    'ABR': {18: 'Realizado', 22: 'LY - Actual'},
    'MAI': {23: 'Realizado', 27: 'LY - Actual'},
    'JUN': {28: 'Realizado', 32: 'LY - Actual'},
    'JUL': {33: 'Realizado', 37: 'LY - Actual'},
    'AGO': {38: 'Realizado', 42: 'LY - Actual'},
    'SET': {43: 'Realizado', 47: 'LY - Actual'},
    'OUT': {48: 'Realizado', 52: 'LY - Actual'},
    'NOV': {53: 'Realizado', 57: 'LY - Actual'},
    'DEZ': {58: 'Realizado', 62: 'LY - Actual'}
}

def clean_money(val):
    return pd.to_numeric(val, errors='coerce') or 0.0

def run_historical_import():
    """Executa a importação do histórico P&L 2024/2025."""
    logs = []
    def log(msg):
        logs.append(msg)
        print(msg)
        
    log("🚀 Iniciando Importação de Histórico (2024-2025)...")
    
    if not os.path.exists(FILE_PATH):
        return False, f"Arquivo não encontrado: {FILE_PATH}", logs

    # 1. Carregar Referências
    log("📚 Carregando referências...")
    df_ref = carregar_centros_gasto()
    mapa_ref = {}
    if not df_ref.empty:
        df_ref.columns = [c.upper().strip() for c in df_ref.columns]
        for _, row in df_ref.iterrows():
            codigo = str(row.get('CENTRO DE GASTO', '')).strip()
            if codigo:
                mapa_ref[codigo] = {
                    'regional': row.get('REGIONAL'),
                    'base': row.get('BASE'),
                    'descricao': row.get('DESCRIÇÃO'),
                    'classe': row.get('CLASSE')
                }

    # 2. Ler Excel
    log(f"📂 Lendo Excel: {FILE_PATH}")
    try:
        df = pd.read_excel(FILE_PATH, sheet_name='P&L BASEAL', skiprows=15, header=0)
    except Exception as e:
        return False, f"Erro ao ler Excel: {e}", logs

    # Limpeza
    df.rename(columns={df.columns[0]: 'codigo_centro_gasto', df.columns[2]: 'conta_contabil'}, inplace=True)
    df['codigo_centro_gasto'] = df['codigo_centro_gasto'].fillna(0)
    
    lancamentos = []
    
    # Iterar
    for mes, indices in MAPA_MESES_IDX.items():
        # log(f"   > Processando {mes}...")
        cols_idx = list(indices.keys())
        valid_cols = [c for c in cols_idx if c < len(df.columns)]
        
        for idx in valid_cols:
            tipo_origem = indices[idx] 
            
            if tipo_origem == 'Realizado':
                ano_lanc = 2025
            elif tipo_origem == 'LY - Actual':
                ano_lanc = 2024
            else:
                continue

            col_nome = df.columns[idx]
            
            for i, row in df.iterrows():
                centro = row['codigo_centro_gasto']
                conta = row['conta_contabil']
                valor = row[col_nome]
                
                val_float = clean_money(valor)
                if val_float == 0: continue

                centro_str = str(centro).replace('.0', '').strip()
                if len(centro_str) == 10: centro_str = '0' + centro_str
                
                ref_data = mapa_ref.get(centro_str, {})
                
                lanc = LancamentoRealizado(
                    ano=ano_lanc,
                    mes=mes,
                    centro_gasto_codigo=centro_str,
                    centro_gasto_pai=centro_str[:8] if len(centro_str) >= 8 else centro_str,
                    centro_gasto_classe=ref_data.get('classe', '0')[-1] if ref_data.get('classe') else '0',
                    centro_gasto_classe_nome=str(ref_data.get('classe', '')),
                    centro_gasto_descricao=str(ref_data.get('descricao', '')),
                    ativo='BASEAL',
                    regional=ref_data.get('regional'),
                    base=ref_data.get('base'),
                    conta_contabil_codigo=str(conta),
                    conta_contabil_descricao=str(conta),
                    valor=val_float,
                    usuario='system/import_history'
                )
                lancamentos.append(lanc)

    log(f"📊 Total de lançamentos preparados: {len(lancamentos)}")
    
    if not lancamentos:
        return False, "Nenhum lançamento gerado.", logs

    session = get_session()
    try:
        log("🧹 Limpando dados antigos (2024/2025)...")
        session.query(LancamentoRealizado).filter(LancamentoRealizado.ano.in_([2024, 2025])).delete(synchronize_session=False)
        
        log("💾 Inserindo novos registros...")
        chunk_size = 2000
        for i in range(0, len(lancamentos), chunk_size):
            chunk = lancamentos[i:i + chunk_size]
            session.add_all(chunk)
        
        session.commit()
        log("✅ Importação concluída!")
        return True, "Sucesso", logs
        
    except Exception as e:
        session.rollback()
        return False, f"Erro DB: {e}", logs
    finally:
        session.close()
