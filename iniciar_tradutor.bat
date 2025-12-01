@echo off
echo ========================================
echo    WWM Brasileiro - Tradutor
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Instale: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Verificando dependencias...
python -c "import pyzstd; import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias!
        pause
        exit /b 1
    )
)

echo Iniciando...
python tools\wwm_tradutor_ptbr.py

pause
