@echo off
setlocal
cd /d "%~dp0"

set "ORPHEE_PYTHON=%CD%\.venv\Scripts\python.exe"

if not exist "%ORPHEE_PYTHON%" (
    echo L'environnement Python local est absent.
    echo Ouvrez le projet dans Codex et demandez : "Configurer l'environnement local ORPHEE".
    pause
    exit /b 1
)

"%ORPHEE_PYTHON%" -m streamlit run app.py

if errorlevel 1 (
    echo.
    echo ORPHEE s'est arrete avec une erreur. Conservez cette fenetre ouverte pour le diagnostic.
    pause
)
