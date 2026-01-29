from database.models import get_session, LancamentoRealizado
from sqlalchemy import text

def verify():
    session = get_session()
    
    print(">>> VERIFICACAO DE INTEGRIDADE - IMPORTACAO HISTORICO <<<")
    
    # 1. Total de registros por Usuario
    print("\n[1] Registros por Usuario:")
    rows = session.execute(text("SELECT usuario, COUNT(*) FROM lancamentos_realizados GROUP BY usuario")).fetchall()
    for row in rows:
        print(f"    {row[0]}: {row[1]}")
        
    # 2. Verificar Códigos Sintéticos (Começam com H_)
    print("\n[2] Verificando Códigos Sintéticos (H_...):")
    count_synthetic = session.query(LancamentoRealizado).filter(
        LancamentoRealizado.conta_contabil_codigo.like('H_%')
    ).count()
    
    if count_synthetic == 0:
        print("    [OK] NENHUM código sintético encontrado.")
    else:
        print(f"    [FALHA] Foram encontrados {count_synthetic} códigos sintéticos!")
        
    # 3. Amostra de dados importados
    print("\n[3] Amostra de dados importados (Top 5):")
    sample = session.query(LancamentoRealizado).filter(
        LancamentoRealizado.usuario == 'Sistema (Import)'
    ).limit(5).all()
    
    for item in sample:
        print(f"    {item.ano}/{item.mes} | {item.conta_contabil_codigo} - {item.conta_contabil_descricao} | R$ {item.valor}")

    session.close()

if __name__ == "__main__":
    verify()
