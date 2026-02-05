"""
tests/test_provisioning_batch.py
================================
Unit tests for bulk update functionality in ProvisioningService.
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.provisioning_service import ProvisioningService


def test_batch_update_success():
    """Test successful batch update of provisions."""
    print("\n>>> Test: Batch Update Success")
    
    service = ProvisioningService()
    
    # 1. Create test provisions
    test_ids = []
    for i in range(3):
        dados = {
            "descricao": f"Test Provision {i} for Batch",
            "valor_estimado": -1000.0 * (i + 1),
            "centro_gasto_codigo": "01020504001",
            "conta_contabil_codigo": "3010101",
            "mes_competencia": "JAN",
            "usuario": "pytest"
        }
        prov = service.criar_provisao(dados)
        test_ids.append(prov.id)
        print(f"  Created: ID={prov.id}")
    
    # 2. Prepare batch update data
    update_data = []
    for i, prov_id in enumerate(test_ids):
        update_data.append({
            "id": prov_id,
            "valor_estimado": -5000.0 - (i * 100),  # New values
            "numero_registro": f"RC-TEST-{i}"
        })
    
    # 3. Execute batch update
    updated, conflicts, errors = service.atualizar_provisoes_em_lote(update_data)
    
    print(f"  Updated: {updated}, Conflicts: {conflicts}, Errors: {len(errors)}")
    
    # 4. Assert
    assert updated == 3, f"Expected 3 updated, got {updated}"
    assert conflicts == 0, f"Expected 0 conflicts, got {conflicts}"
    assert len(errors) == 0, f"Expected 0 errors, got {len(errors)}"
    
    print("[OK] Batch update success test passed!")
    
    # Cleanup: Cancel test provisions
    for prov_id in test_ids:
        try:
            service.cancelar_provisao(prov_id, "Test cleanup")
        except:
            pass


def test_batch_update_invalid_id():
    """Test batch update with non-existent ID."""
    print("\n>>> Test: Batch Update Invalid ID")
    
    service = ProvisioningService()
    
    # 1. Prepare data with fake ID
    update_data = [{
        "id": 999999,  # Non-existent
        "valor_estimado": -1000.0
    }]
    
    # 2. Execute
    updated, conflicts, errors = service.atualizar_provisoes_em_lote(update_data)
    
    print(f"  Updated: {updated}, Conflicts: {conflicts}, Errors: {len(errors)}")
    
    # 3. Assert
    assert updated == 0, f"Expected 0 updated, got {updated}"
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}"
    assert "não encontrado" in errors[0], f"Expected 'não encontrado' in error message"
    
    print("[OK] Invalid ID test passed!")


def test_batch_update_non_pending_status():
    """Test batch update rejects non-PENDENTE provisions."""
    print("\n>>> Test: Batch Update Non-Pending")
    
    service = ProvisioningService()
    
    # 1. Create and mark as REALIZADA
    dados = {
        "descricao": "Test Non-Pending",
        "valor_estimado": -2000.0,
        "centro_gasto_codigo": "01020504001",
        "conta_contabil_codigo": "3010101",
        "mes_competencia": "JAN",
        "usuario": "pytest"
    }
    prov = service.criar_provisao(dados)
    
    # Mark as REALIZADA
    service.atualizar_provisao(prov.id, {"status": "REALIZADA", "numero_registro": "RC-DONE"})
    
    # 2. Try to batch update
    update_data = [{
        "id": prov.id,
        "valor_estimado": -9999.0
    }]
    
    updated, conflicts, errors = service.atualizar_provisoes_em_lote(update_data)
    
    print(f"  Updated: {updated}, Conflicts: {conflicts}, Errors: {len(errors)}")
    
    # 3. Assert
    assert updated == 0, f"Expected 0 updated, got {updated}"
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}"
    assert "PENDENTE" in errors[0], f"Expected 'PENDENTE' in error message"
    
    print("[OK] Non-pending status test passed!")


def run_all_tests():
    """Run all batch update tests."""
    print("=" * 60)
    print("PROVISIONING BATCH UPDATE TESTS")
    print("=" * 60)
    
    try:
        test_batch_update_success()
        test_batch_update_invalid_id()
        test_batch_update_non_pending_status()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✅")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(run_all_tests())
