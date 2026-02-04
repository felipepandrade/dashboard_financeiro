import sys
import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import get_engine, LancamentoRealizado, RazaoRealizado, Base
from data.referencias_manager import carregar_centros_gasto

# Configurações
FILE_PATH = r"c:\Aplicativos Desenvolvidos\dashboard_financeiro\Doc referencia\P&L - Dezembro_2025.xlsx"
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
MESES_NUM = {
    'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
    'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
}

def clean_money(val):
    return pd.to_numeric(val, errors='coerce') or 0.0

def get_db_session():
    engine = get_engine()
    return Session(bind=engine)

def main():
    print("🚀 Iniciando Importação de Histórico (2024-2025)...")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ Arquivo não encontrado: {FILE_PATH}")
        return

    # 1. Carregar Referências (Regional/Base)
    print("📚 Carregando referências de Centros de Custo...")
    df_ref = carregar_centros_gasto()
    # Criar mapa código -> dict
    mapa_ref = {}
    if not df_ref.empty:
        # Normalizar colunas
        df_ref.columns = [c.upper().strip() for c in df_ref.columns]
        for _, row in df_ref.iterrows():
            # Tentar pegar código. Adapte conforme o nome real da coluna no arquivo de ref
            codigo = str(row.get('CENTRO DE GASTO', '')).strip()
            if codigo:
                mapa_ref[codigo] = {
                    'regional': row.get('REGIONAL'),
                    'base': row.get('BASE'),
                    'descricao': row.get('DESCRIÇÃO'),
                    'classe': row.get('CLASSE')
                }

    # 2. Ler Excel
    print(f"📂 Lendo arquivo Excel: {FILE_PATH}")
    try:
        df = pd.read_excel(FILE_PATH, sheet_name='P&L BASEAL', skiprows=15, header=0)
    except Exception as e:
        print(f"❌ Erro ao ler Excel: {e}")
        return

    # Limpeza Inicial
    df.rename(columns={df.columns[0]: 'codigo_centro_gasto', df.columns[2]: 'conta_contabil'}, inplace=True)
    df['codigo_centro_gasto'] = df['codigo_centro_gasto'].fillna(0)
    
    # Processar Registros
    lancamentos = []
    
    print("🔄 Processando dados...")
    
    # Iterar sobre meses
    for mes, indices in MAPA_MESES_IDX.items():
        print(f"   > Processando {mes}...")
        
        # Pega colunas relevantes para este mês
        cols_idx = list(indices.keys())
        # Tenta pegar apenas se existirem (segurança)
        valid_cols = [c for c in cols_idx if c < len(df.columns)]
        
        for idx in valid_cols:
            tipo_origem = indices[idx] # 'Realizado' ou 'LY - Actual'
            
            # Definir Ano e Tipo Final
            if tipo_origem == 'Realizado':
                ano_lanc = 2025
                tipo_final = 'Realizado'
            elif tipo_origem == 'LY - Actual':
                ano_lanc = 2024
                tipo_final = 'Realizado' # Convertemos para Realizado no histórico
            else:
                continue

            col_nome = df.columns[idx]
            
            # Filtrar e Iterar
            # Pega linhas que têm valor numérico
            # Ignora linhas de cabeçalho ou totalizadores que não sejam lançamentos válidos
            # Regra: codigo_centro_gasto deve ser string válida de centro ou conta financeira (0)
            
            for i, row in df.iterrows():
                centro = row['codigo_centro_gasto']
                conta = row['conta_contabil']
                valor = row[col_nome]
                
                # Pular vazios ou zeros (opcional, mas economiza banco)
                val_float = clean_money(valor)
                if val_float == 0:
                    continue

                # Tratar Centro de Gasto
                centro_str = str(centro).replace('.0', '').strip()
                if len(centro_str) == 10: centro_str = '0' + centro_str # Padronizar 11 digitos
                
                # Enriquecer
                ref_data = mapa_ref.get(centro_str, {})
                
                # Criar Objeto
                lanc = LancamentoRealizado(
                    ano=ano_lanc,
                    mes=mes,
                    centro_gasto_codigo=centro_str,
                    centro_gasto_pai=centro_str[:8] if len(centro_str) >= 8 else centro_str,
                    centro_gasto_classe=ref_data.get('classe', '0')[-1] if ref_data.get('classe') else '0',
                    centro_gasto_classe_nome=str(ref_data.get('classe', '')),
                    centro_gasto_descricao=str(ref_data.get('descricao', '')),
                    ativo='BASEAL', # Padrão ou extrair
                    regional=ref_data.get('regional'),
                    base=ref_data.get('base'),
                    conta_contabil_codigo=str(conta),
                    conta_contabil_descricao=str(conta), # Se tiver noutra coluna, ajustar
                    valor=val_float,
                    usuario='scripts/import_history'
                )
                lancamentos.append(lanc)

    print(f"📊 Total de lançamentos preparados: {len(lancamentos)}")
    
    # 3. Persistência
    if not lancamentos:
        print("⚠️ Nenhum lançamento gerado.")
        return

    session = get_db_session()
    try:
        print("🧹 Limpando dados antigos de 2024 e 2025...")
        session.query(LancamentoRealizado).filter(LancamentoRealizado.ano.in_([2024, 2025])).delete(synchronize_session=False)
        
        print("💾 Inserindo novos registros (Bulk Insert)...")
        # Dividir em chunks se for muito grande
        chunk_size = 1000
        for i in range(0, len(lancamentos), chunk_size):
            chunk = lancamentos[i:i + chunk_size]
            session.add_all(chunk)
            print(f"   Saved {i + len(chunk)} / {len(lancamentos)}")
        
        session.commit()
        print("✅ Importação concluída com SUCESSO!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao salvar no banco: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
