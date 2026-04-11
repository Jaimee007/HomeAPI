@echo off
REM Script completo para ejecutar API + Servidor HTTP desde Windows
REM Ejecuta:
REM - API en http://localhost:8000
REM - Servidor web en http://localhost:3000
REM - Abre navegador automáticamente

cls
color 0A
echo.
echo ╔════════════════════════════════════════════════════╗
echo ║  🚀 HomeAPI - Iniciando API + Servidor Web         ║
echo ╚════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM Crear venv si no existe
if not exist "venv\" (
    echo [*] Creando entorno virtual...
    python -m venv venv
    echo [OK] Entorno virtual creado
)

REM Activar venv
echo [*] Activando entorno virtual...
call venv\Scripts\activate.bat
echo [OK] Entorno activado
echo.

REM Instalar dependencias
echo [*] Verificando dependencias...
pip install -q -r requirements.txt
echo [OK] Dependencias listas
echo.

echo ╔════════════════════════════════════════════════════╗
echo ║  ✨ Iniciando servicios...                         ║
echo ╚════════════════════════════════════════════════════╝
echo.

REM Iniciar API en ventana minimizada
echo [*] Iniciando API en http://localhost:8000...
start "HomeAPI Backend" /min cmd /c "cd /d "%~dp0" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Iniciar servidor HTTP en ventana minimizada
echo [*] Iniciando servidor web en http://localhost:3000...
start "HomeAPI Frontend" /min cmd /c "cd /d "%~dp0" && python -m http.server 3000"

REM Esperar a que se inicien
timeout /t 2 /nobreak > nul

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║  ✅ ¡TODO ESTÁ INICIADO!                          ║
echo ╚════════════════════════════════════════════════════╝
echo.

echo [INFO] URLs disponibles:
echo        🌐 Web:          http://localhost:3000
echo        📖 API Docs:     http://localhost:8000/docs
echo        🔧 API Base:     http://localhost:8000
echo.

REM Abrir navegador
echo [*] Abriendo navegador...
timeout /t 1 /nobreak > nul
start "" "http://localhost:3000/index.html"

echo.
echo [INFO] Los servicios están corriendo en segundo plano
echo [INFO] Abre el Administrador de tareas para verlos
echo.
pause
