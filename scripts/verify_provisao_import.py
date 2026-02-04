import os
import sys
from unittest.mock import MagicMock

# 1. SETUP PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. AGGRESSIVE MOCKING OF STREAMLIT
# We mock it BEFORE any import to prevent it from reading secrets.toml
mock_st = MagicMock()
mock_st.secrets = {} # Empty secrets
sys.modules["streamlit"] = mock_st

# 3. FORCE ENV VAR
os.environ["DATABASE_URL"] = "sqlite:///:memory:" 

# 4. IMPORTS
import database.models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 5. EXPLICIT PATCHING (Double Safety)
# We override the global function in the module
def mock_get_engine():
    return create_engine("sqlite:///:memory:", echo=False)

database.models.get_engine = mock_get_engine
database.models.get_session = lambda: sessionmaker(bind=mock_get_engine())()

# Initialize DB in memory
database.models.Base.metadata.create_all(mock_get_engine())

# 6. IMPORT SERVICE
from services.provisioning_service import ProvisioningService
from database.models import Provisao, get_session

def test_batch_enrichment():
    print(">>> Testing Batch Provision Creation with Enrichment (Heavy Mocking)")
    import pandas as pd

    # Mock Data
    df_centros_mock = pd.DataFrame([
        {
            'codigo': '99999999999', 
            'descricao': 'Test Center Automated', 
            'regional': 'REGIONAL_TESTE', 
            'base': 'BASE_TESTE'
        }
    ])
    
    lista_dados = [{
        'descricao': 'Teste Import Script',
        'valor_estimado': 123.45,
        'centro_gasto_codigo': '99999999999', 
        'conta_contabil_codigo': '999999',
        'mes_competencia': 'DEZ',
        'tipo_despesa': 'Variavel'
    }]
    
    # Enrichment Logic
    print(">>> Running UI Enrichment Logic...")
    if not df_centros_mock.empty:
        for item in lista_dados:
            cod_std = str(item.get('centro_gasto_codigo', '')).strip().zfill(11)
            match = df_centros_mock[df_centros_mock['codigo'] == cod_std]
            if not match.empty:
                item['regional'] = match.iloc[0]['regional']
                item['base'] = match.iloc[0]['base']
                print(f"    Enriched: {item.get('regional')} / {item.get('base')}")

    # Service Call
    print(">>> Calling ProvisioningService...")
    service = ProvisioningService()
    
    count, errors = service.criar_provisoes_em_lote(lista_dados)
    
    if errors:
        print("f[FAIL] Service returned errors:", errors)
        return

    print(f"    Created {count} records in Memory DB.")

    # Verify
    session = get_session()
    try:
        prov = session.query(Provisao).all()
        if not prov:
            print("❌ TEST FAILED: No records in DB.")
            return

        p = prov[0]
        print(f"    Found: ID={p.id}, Regional={p.regional}, Base={p.base}")
        
        if p.regional == 'REGIONAL_TESTE' and p.base == 'BASE_TESTE':
             print("✅ TEST PASSED: Success!")
        else:
             print("❌ TEST FAILED: Data incorrect.")
            
    finally:
        session.close()

if __name__ == "__main__":
    test_batch_enrichment()
