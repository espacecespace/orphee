@echo off
setlocal
cd /d "%~dp0"

set /p "TEST_NAME=Nom court du nouvel essai : "
if "%TEST_NAME%"=="" (
    echo Aucun nom fourni.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CD%\scripts\new_eval.ps1" -Name "%TEST_NAME%"
if errorlevel 1 pause
