# Script de verificación - Comprueba que todo esté bien instalado
# Uso: .\check-setup.ps1

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✓  VERIFICACIÓN DE HOMEAPI                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Verificar Python
Write-Host "🔍 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = (python --version 2>&1)
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no está instalado" -ForegroundColor Red
    $allGood = $false
}

# Verificar archivos necesarios
Write-Host ""
Write-Host "🔍 Verificando archivos..." -ForegroundColor Yellow

$requiredFiles = @(
    "requirements.txt",
    "app/main.py",
    "app/db.py",
    "app/crud.py",
    "app/schemas.py",
    "index.html",
    "app/routers/categories.py",
    "app/routers/meals.py",
    "app/routers/daily_menu.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file - FALTA" -ForegroundColor Red
        $allGood = $false
    }
}

# Verificar entorno virtual
Write-Host ""
Write-Host "🔍 Verificando entorno virtual..." -ForegroundColor Yellow

if (Test-Path "venv") {
    Write-Host "  ✅ Entorno virtual existe" -ForegroundColor Green
    
    # Activar y verificar paquetes
    . .\venv\Scripts\Activate.ps1
    
    Write-Host "🔍 Verificando paquetes..." -ForegroundColor Yellow
    $packages = @("fastapi", "uvicorn", "pydantic")
    
    foreach ($pkg in $packages) {
        try {
            $null = pip show $pkg 2>$null
            if ($?) {
                Write-Host "  ✅ $pkg instalado" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  $pkg no encontrado" -ForegroundColor Yellow
                $allGood = $false
            }
        } catch {
            Write-Host "  ⚠️  $pkg no encontrado" -ForegroundColor Yellow
            $allGood = $false
        }
    }
} else {
    Write-Host "  ⚠️  Entorno virtual no existe" -ForegroundColor Yellow
    Write-Host "     Se creará automáticamente al ejecutar run-api.ps1" -ForegroundColor Yellow
}

# Verificar base de datos
Write-Host ""
Write-Host "🔍 Verificando base de datos..." -ForegroundColor Yellow

if (Test-Path "data/home_menu.db") {
    Write-Host "  ✅ Base de datos SQLite existe" -ForegroundColor Green
} else {
    Write-Host "  ℹ️  Base de datos se creará al iniciar la API" -ForegroundColor Cyan
}

# Resultado final
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "║  ✅ TODO ESTÁ BIEN CONFIGURADO                   ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🚀 Puedes comenzar con:" -ForegroundColor Green
    Write-Host "   .\run-api.ps1" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "║  ⚠️  HAY PROBLEMAS A RESOLVER                    ║" -ForegroundColor Yellow
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📖 Lee QUICK_START.md para solucionar" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ""
pause
