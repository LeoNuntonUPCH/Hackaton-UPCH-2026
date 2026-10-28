@echo off
setlocal
REM SATQ Digital - arranque en Windows
REM Prueba FastAPI; si algo falla, usa el servidor de respaldo sin interrumpir.

cd /d "%~dp0"
echo.
echo   SATQ Digital - Sistema de Alerta Temprana de Quebradas
echo   Prototipo de demostracion - Datos simulados
echo.

REM Paso 1: comprobar que Python existe.
python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: no se encontro Python en el PATH.
    echo   Abre "Anaconda Prompt" y vuelve a ejecutar este archivo desde ahi.
    echo.
    pause
    exit /b 1
)

REM Paso 2: comprobar que la aplicacion FastAPI carga de verdad.
REM No basta con que fastapi este instalado: tiene que importarse app.py.
python -c "import app" >nul 2>&1
if errorlevel 1 goto respaldo

echo   Iniciando con FastAPI.  http://127.0.0.1:8000
echo   Documentacion de la API: http://127.0.0.1:8000/docs
echo   Ctrl+C para detener.
echo.
python -m uvicorn app:app --host 127.0.0.1 --port 8000
goto fin

:respaldo
echo   FastAPI no esta disponible; se usa el servidor de respaldo.
echo   (Las 8 pantallas funcionan igual; solo no habra /docs.)
echo.
echo   Para ver el motivo exacto:  python diagnostico.py
echo.
echo   Iniciando.  http://127.0.0.1:8000
echo   Ctrl+C para detener.
echo.
python servidor_demo.py 8000

:fin
echo.
pause
