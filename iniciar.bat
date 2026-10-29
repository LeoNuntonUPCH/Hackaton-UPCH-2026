@echo off
setlocal
REM SATQ Digital - arranque en Windows
REM Prueba FastAPI; si algo falla, dice por que y usa el servidor de respaldo.

cd /d "%~dp0"
echo.
echo   SATQ Digital - Sistema de Alerta Temprana de Quebradas
echo   Prototipo de demostracion - Datos simulados
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: no se encontro Python en el PATH.
    echo   Abre "Anaconda Prompt" y ejecuta este archivo desde ahi.
    echo.
    pause
    exit /b 1
)

REM Comprueba que app.py carga. Si no, imprime el motivo en una linea.
python diagnostico.py --check
if errorlevel 1 goto respaldo

echo   Iniciando con FastAPI.  http://127.0.0.1:8000
echo   Documentacion de la API: http://127.0.0.1:8000/docs
echo   Ctrl+C para detener.
echo.
python -m uvicorn app:app --host 127.0.0.1 --port 8000
goto fin

:respaldo
echo.
echo   FastAPI no pudo cargarse por el motivo de arriba.
echo   Se usa el servidor de respaldo: las 8 pantallas funcionan igual,
echo   solo no habra /docs.
echo.
echo   Detalle completo:  python diagnostico.py
echo.
python servidor_demo.py 8000

:fin
echo.
pause
