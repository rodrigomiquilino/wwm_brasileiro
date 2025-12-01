@echo off
:: WWM Brasileiro - Build Script
:: Compila o launcher em executável

echo.
echo ========================================
echo  WWM Brasileiro - Build
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias...
pip install PyQt5 requests pyinstaller --quiet

cd /d "%~dp0"

echo.
echo [2/3] Compilando...
pyinstaller --noconfirm --onefile --windowed ^
    --name "WWM_Tradutor_PTBR" ^
    --icon "icon.ico" ^
    wwm_ptbr_launcher.py 2>nul || (
        pyinstaller --noconfirm --onefile --windowed ^
            --name "WWM_Tradutor_PTBR" ^
            wwm_ptbr_launcher.py
    )

echo.
echo [3/3] Finalizando...

if exist "dist\WWM Tradutor PT-BR.exe" (
    echo.
    echo ========================================
    echo  BUILD OK
    echo ========================================
    echo.
    echo Arquivo: dist\WWM Tradutor PT-BR.exe
    echo.
    explorer dist
) else (
    echo [ERRO] Falha no build!
)

pause
