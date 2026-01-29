@echo off
echo ==========================================
echo Instalando dependencias do Sistema Orcamentario 2026
echo ==========================================

:: Verificar se Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado. Por favor, instale o Python antes de continuar.
    pause
    exit /b
)

:: Criar ambiente virtual se nao existir
if not exist .venv (
    echo [INFO] Criando ambiente virtual .venv...
    python -m venv .venv
) else (
    echo [INFO] Ambiente virtual ja existe.
)

:: Ativar ambiente virtual
echo [INFO] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

:: Atualizar pip
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip

:: Instalar dependencias
if exist requirements.txt (
    echo [INFO] Instalando bibliotecas do requirements.txt...
    pip install -r requirements.txt
) else (
    echo [AVISO] Arquivo requirements.txt nao encontrado.
)

echo.
echo ==========================================
echo Instalacao concluida com sucesso!
echo ==========================================
pause
