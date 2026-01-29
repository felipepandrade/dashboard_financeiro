from database.models import init_db, get_engine
from sqlalchemy import inspect
import os

print("Iniciando criação de tabelas...")
try:
    init_db()
    print("init_db executado.")
except Exception as e:
    print(f"Erro ao executar init_db: {e}")

try:
    inspector = inspect(get_engine())
    tables = inspector.get_table_names()
    print(f"Tabelas encontradas: {tables}")

    expected = ['lancamentos_realizados', 'forecast_cenarios', 'forecast_entries', 'provisoes', 'remanejamentos']
    missing = [t for t in expected if t not in tables]

    if not missing:
        print("SUCESSO: Todas as tabelas foram criadas.")
    else:
        print(f"ERRO: Faltam as tabelas: {missing}")
except Exception as e:
    print(f"Erro ao inspecionar banco: {e}")
