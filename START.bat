@echo off
REM Script para ejecutar la API y abrir la web automáticamente en Windows
REM Uso: Hacer doble clic en este archivo

echo.
echo ===============================================
echo   ^!  HomeAPI - Gestor de Menus Semanal
echo ===============================================
echo.

REM Cambiar a la carpeta del proyecto
cd /d "%~dp0"

REM Verificar si existe el entorno virtual
if not exist "venv\" (
    echo [*] Creando entorno virtual...
    python -m venv venv
    echo [OK] Entorno virtual creado
)

REM Activar entorno virtual
echo [*] Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo [*] Instalando dependencias...
pip install -q -r requirements.txt
echo [OK] Dependencias listas

echo.
echo ===============================================
echo [✓] API iniciando en http://localhost:8000
echo ===============================================
echo.
echo [INFO] Documentacion: http://localhost:8000/docs
echo [INFO] Web local: file:///%cd%\index.html
echo.
echo Presiona Ctrl+C para detener la API
echo.

REM Iniciar la API en segundo plano
start /min cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Esperar 2 segundos para que la API inicie
timeout /t 2 /nobreak

REM Abrir la web automáticamente
echo [*] Abriendo web en navegador...
start "" "file:///%cd%\index.html"

REM Mostrando una ventana de estado
echo [OK] Todo iniciado. Puedes cerrar esta ventana.
echo La API continuara ejecutandose en segundo plano.
echo.
echo Para detener la API, abre el Administrador de tareas y termina la ventana de Uvicorn
pause
