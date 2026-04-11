# Script completo para ejecutar API + Servidor HTTP + Abrir web
# Usa Python para servir el HTML en http://localhost:3000

$projectPath = Split-Path -Parent $MyInvocation.MyCommandPath
Set-Location $projectPath

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 HomeAPI - Iniciando API + Servidor Web        ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar si existe el entorno virtual
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Entorno virtual creado" -ForegroundColor Green
    Write-Host ""
}

# Activar entorno virtual
Write-Host "🔌 Activando entorno virtual..." -ForegroundColor Yellow
. .\venv\Scripts\Activate.ps1
Write-Host "✅ Entorno activado" -ForegroundColor Green
Write-Host ""

# Instalar dependencias
Write-Host "📥 Verificando dependencias..." -ForegroundColor Yellow
pip install -q -r requirements.txt
Write-Host "✅ Dependencias listas" -ForegroundColor Green
Write-Host ""

Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✨ Iniciando servicios...                         ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Iniciar API en background
Write-Host "🚀 Iniciando API en http://localhost:8000..." -ForegroundColor Yellow
$apiProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectPath'; `$null = . .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru -WindowStyle Minimized

# Iniciar servidor HTTP en background (Python)
Write-Host "🌐 Iniciando servidor web en http://localhost:3000..." -ForegroundColor Yellow
$webProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectPath'; python -m http.server 3000" -PassThru -WindowStyle Minimized

# Esperar a que los servicios se inicien
Write-Host ""
Write-Host "⏳ Esperando a que los servicios se inicien..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ ¡TODO ESTÁ INICIADO!                          ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📍 URLs disponibles:" -ForegroundColor Cyan
Write-Host "   🌐 Web:          http://localhost:3000" -ForegroundColor Green
Write-Host "   📖 API Docs:     http://localhost:8000/docs" -ForegroundColor Green
Write-Host "   🔧 API Base:     http://localhost:8000" -ForegroundColor Green
Write-Host ""

Write-Host "⏹️  Para detener todo, cierra esta ventana o presiona Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Abrir navegador automáticamente
Write-Host "🌐 Abriendo navegador..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
Start-Process "http://localhost:3000/index.html"

# Esperar a que el usuario presione Ctrl+C
Write-Host "Presiona Ctrl+C para cerrar todo..." -ForegroundColor Yellow
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
catch {
    Write-Host ""
    Write-Host "⏹️  Deteniendo servicios..." -ForegroundColor Yellow
    
    try {
        Stop-Process -Id $apiProcess.Id -Force -ErrorAction SilentlyContinue
        Stop-Process -Id $webProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Servicios detenidos" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Error al detener servicios" -ForegroundColor Yellow
    }
}
