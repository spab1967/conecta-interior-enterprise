@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

title Conecta Interior

echo.
echo ==========================================
echo        CONECTA INTERIOR ENTERPRISE
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERRO: Ambiente virtual nao encontrado.
    echo Execute primeiro INSTALAR_CONECTA_INTERIOR.bat.
    echo.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo [1/3] Verificando o sistema...
python manage.py check

if errorlevel 1 (
    echo.
    echo ERRO: O Django encontrou problemas.
    echo O servidor nao sera iniciado.
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Atualizando assinaturas vencidas...
python manage.py atualizar_assinaturas

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel atualizar as assinaturas.
    echo O servidor nao sera iniciado.
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] Iniciando Conecta Interior...
echo.
echo Acesso:
echo http://127.0.0.1:8000/
echo.
echo Para encerrar o servidor, pressione CTRL+C.
echo.

start "" "http://127.0.0.1:8000"

python manage.py runserver 127.0.0.1:8000

echo.
echo Servidor encerrado.
pause