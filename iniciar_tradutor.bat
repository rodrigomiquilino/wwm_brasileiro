@echo off
echo ========================================
echo    WWM Tradutor PT-BR
echo    Ferramenta de Traducao para
echo    Where Winds Meet
echo ========================================
echo.

REM Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado! 
    echo Instale Python 3.x de: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verifica dependencias
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

echo Iniciando WWM Tradutor PT-BR...
python tools\wwm_tradutor_ptbr.py

pause
