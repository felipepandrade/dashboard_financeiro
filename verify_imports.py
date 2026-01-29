
import sys
import os

# Adicionar diretorio atual ao path
sys.path.append(os.getcwd())

print("Verificando imports dos serviços...")

try:
    from services import forecast_service
    print("[OK] services.forecast_service importado.")
except ImportError as e:
    print(f"[ERRO] ao importar forecast_service: {e}")

try:
    from services import provisioning_service
    print("[OK] services.provisioning_service importado.")
except ImportError as e:
    print(f"[ERRO] ao importar provisioning_service: {e}")

try:
    from services import budget_control
    print("[OK] services.budget_control importado.")
except ImportError as e:
    print(f"[ERRO] ao importar budget_control: {e}")

try:
    from services import ai_board
    print("[OK] services.ai_board importado.")
except ImportError as e:
    print(f"[ERRO] ao importar ai_board: {e}")

print("Verificação concluída.")
