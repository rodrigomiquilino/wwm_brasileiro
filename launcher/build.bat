@echo off
:: ============================================================================
:: Script para compilar o Launcher WWM PT-BR em executável
:: ============================================================================

echo.
echo ========================================
echo  WWM Tradutor PT-BR - Build Script
echo ========================================
echo.

:: Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado! Instale Python 3.8+
    pause
    exit /b 1
)

:: Instala dependências
echo [1/3] Instalando dependencias...
pip install PyQt5 requests pyinstaller --quiet

:: Vai para o diretório do launcher
cd /d "%~dp0"

:: Compila com PyInstaller
echo.
echo [2/3] Compilando executavel...
pyinstaller --noconfirm --onefile --windowed ^
    --name "WWM Tradutor PT-BR" ^
    --icon "../docs/icon.ico" ^
    --add-data "wwm_ptbr_config.json;." ^
    --hidden-import "PyQt5.sip" ^
    wwm_ptbr_launcher.py

:: Move para pasta dist
echo.
echo [3/3] Finalizando...

if exist "dist\WWM Tradutor PT-BR.exe" (
    echo.
    echo ========================================
    echo  BUILD CONCLUIDO COM SUCESSO!
    echo ========================================
    echo.
    echo Executavel criado em: dist\WWM Tradutor PT-BR.exe
    echo.
    explorer dist
) else (
    echo.
    echo [ERRO] Falha ao criar executavel!
)

pause
