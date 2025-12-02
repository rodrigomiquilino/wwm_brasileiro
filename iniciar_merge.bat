@echo off
chcp 65001 >nul
title WWM Merge TSV - Mesclador de Traduções
cd /d "%~dp0"
echo.
echo ⚔️  WWM Merge TSV - Mesclador de Traduções
echo ==========================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo Instale Python 3.8+ em: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Executa o script
python tools\wwm_merge_tsv.py

pause
