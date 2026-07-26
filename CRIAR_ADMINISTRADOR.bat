@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Criar Administrador - Conecta Interior
if not exist ".venv\Scripts\python.exe" (
    echo Execute primeiro INSTALAR_CONECTA_INTERIOR.bat.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
python manage.py createsuperuser
pause
