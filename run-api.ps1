# Script para ejecutar la API rápidamente en Windows PowerShell
# Uso: .\run-api.ps1

$ErrorActionPreference = 'Stop'

# Cambiar a la carpeta del proyecto
$projectPath = if ($PSScriptRoot) {
    $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path) {
    Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    (Get-Location).Path
}
Set-Location $projectPath

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  🚀 Iniciando HomeAPI - Gestor de Menú" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Verificar si existe el entorno virtual
$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "✅ Entorno virtual creado" -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "🔌 Activando entorno virtual..." -ForegroundColor Yellow
. "$venvPath\Scripts\Activate.ps1"

# Instalar/actualizar dependencias
Write-Host "📥 Verificando dependencias..." -ForegroundColor Yellow
$requirementsPath = Join-Path $projectPath "requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    throw "No se encontró requirements.txt en: $requirementsPath"
}

pip install -q -r $requirementsPath
Write-Host "✅ Dependencias listas" -ForegroundColor Green

# Modo local de pruebas: evita bloquear peticiones del frontend file:// por auth
$env:DISABLE_API_KEY_AUTH = "1"
Write-Host "🧪 Modo prueba local: autenticación API Key desactivada" -ForegroundColor Yellow

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
