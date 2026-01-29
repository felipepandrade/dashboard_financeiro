@echo off
echo ==========================================
echo Iniciando Dashboard Financeiro 2026
echo ==========================================

if not exist .venv (
    echo [ERRO] Ambiente virtual nao encontrado. Execute 'instalar.bat' primeiro.
    pause
    exit /b
)

echo [INFO] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo [INFO] Iniciando aplicacao Streamlit...
streamlit run Home.py

pause
