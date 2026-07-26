@echo off
chcp 65001 >nul
title Conecta Interior - Aplicar Sprint 002 Real
setlocal

set "PROJETO=C:\ConectaInterior\ConectaInterior"
set "PACOTE=%~dp0arquivos"

echo ==========================================
echo CONECTA INTERIOR - SPRINT 002 REAL
echo ==========================================

if not exist "%PROJETO%\manage.py" (
    echo ERRO: projeto nao encontrado em:
    echo %PROJETO%
    echo.
    echo Mova o projeto para esse endereco ou ajuste a variavel PROJETO.
    pause
    exit /b 1
)

if not exist "%PROJETO%\apps\cidades" (
    echo ERRO: pasta apps\cidades nao encontrada no projeto.
    pause
    exit /b 1
)

if not exist "%PROJETO%\backup_sprint_002" mkdir "%PROJETO%\backup_sprint_002"
copy /Y "%PROJETO%\apps\cidades\models.py" "%PROJETO%\backup_sprint_002\models.py" >nul
copy /Y "%PROJETO%\apps\cidades\admin.py" "%PROJETO%\backup_sprint_002\admin.py" >nul
copy /Y "%PROJETO%\templates\core\cidade_home.html" "%PROJETO%\backup_sprint_002\cidade_home.html" >nul

xcopy "%PACOTE%\apps" "%PROJETO%\apps\" /E /I /Y >nul
xcopy "%PACOTE%\templates" "%PROJETO%\templates\" /E /I /Y >nul
xcopy "%PACOTE%\static" "%PROJETO%\static\" /E /I /Y >nul

findstr /C:"sprint_002_cidades.css" "%PROJETO%\templates\base.html" >nul
if errorlevel 1 (
    powershell -NoProfile -Command "$p='%PROJETO%\templates\base.html'; $c=Get-Content -Raw -Encoding UTF8 $p; $c=$c -replace '</head>','  <link rel=\"stylesheet\" href=\"{% static ''css/sprint_002_cidades.css'' %}\">`r`n</head>'; Set-Content -Encoding UTF8 $p $c"
)

cd /d "%PROJETO%"
call ".venv\Scripts\activate.bat"

python manage.py migrate
if errorlevel 1 goto erro

python manage.py check
if errorlevel 1 goto erro

echo.
echo ==========================================
echo SPRINT 002 APLICADA COM SUCESSO
echo ==========================================
echo A migracao cidades.0002 deve aparecer como OK.
echo Entre em /admin e abra Cidades.
pause
exit /b 0

:erro
echo.
echo ERRO AO APLICAR A SPRINT 002.
echo Os arquivos anteriores foram preservados em backup_sprint_002.
pause
exit /b 1
