@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Instalar Conecta Interior

echo ==========================================
echo CONECTA INTERIOR - INSTALACAO AUTOMATICA
echo ==========================================

where python >nul 2>nul
if errorlevel 1 (
    echo ERRO: O comando python nao foi encontrado.
    pause
    exit /b 1
)

python --version

if not exist ".env" copy /Y ".env.example" ".env" >nul

if exist ".venv" rmdir /S /Q ".venv"
python -m venv ".venv"
if errorlevel 1 goto :erro

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :erro

python -m pip install --upgrade pip
if errorlevel 1 goto :erro

python -m pip install -r requirements.txt
if errorlevel 1 goto :erro

python manage.py makemigrations cidades categorias empresas
if errorlevel 1 goto :erro

python manage.py migrate
if errorlevel 1 goto :erro

python manage.py carga_inicial
if errorlevel 1 goto :erro

python manage.py check
if errorlevel 1 goto :erro

echo.
echo ==========================================
echo INSTALACAO CONCLUIDA COM SUCESSO
echo ==========================================
echo Agora execute CRIAR_ADMINISTRADOR.bat.
pause
exit /b 0

:erro
echo.
echo ==========================================
echo A INSTALACAO FOI INTERROMPIDA POR UM ERRO
echo Copie a mensagem acima e envie no chat.
echo ==========================================
pause
exit /b 1
