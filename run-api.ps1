# Script para ejecutar la API rápidamente en Windows PowerShell
# Uso: .\run-api.ps1

# Cambiar a la carpeta del proyecto
$projectPath = Split-Path -Parent $MyInvocation.MyCommandPath
Set-Location $projectPath

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🚀 Iniciando HomeAPI - Gestor de Menú" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Verificar si existe el entorno virtual
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✅ Entorno virtual creado" -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "🔌 Activando entorno virtual..." -ForegroundColor Yellow
. .\venv\Scripts\Activate.ps1

# Instalar/actualizar dependencias
Write-Host "📥 Verificando dependencias..." -ForegroundColor Yellow
pip install -q -r requirements.txt
Write-Host "✅ Dependencias listas" -ForegroundColor Green

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  ✨ API iniciando en http://localhost:8000" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Documentación interactiva:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "🌐 Web local:                  file://$(Get-Location)/index.html" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona Ctrl+C para detener la API" -ForegroundColor Yellow
Write-Host ""

# Ejecutar la API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
