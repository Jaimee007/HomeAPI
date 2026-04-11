# 🚀 INICIO RÁPIDO - HomeAPI + Web

## ⚡ Opción Más Fácil (Recomendado)

### 1. Abre PowerShell en esta carpeta

```
Haz Shift + Click derecho en la carpeta HomeAPI
Selecciona "Abrir ventana de PowerShell aquí"
```

### 2. Ejecuta este comando

```powershell
.\run-api.ps1
```

**¡Listo!** La API comenzará a ejecutarse. 

### 3. Abre la web

```
Abre en tu navegador: file:///c:/Git/HomeAPI/index.html
```

---

## 🖱️ Opción Aún Más Fácil (Windows)

### 1. Haz doble clic en `START.bat`

El script automáticamente:
- ✅ Instala Python si es necesario
- ✅ Crea el entorno virtual
- ✅ Instala dependencias
- ✅ Inicia la API
- ✅ Abre la web en tu navegador

---

## 🧪 Probar que funciona

### 1. API - Documentación Interactiva
```
http://localhost:8000/docs
```

Aquí puedes:
- ✅ Ver todos los endpoints
- ✅ Probarlos sin código
- ✅ Ver las respuestas en JSON

### 2. Web - Crear una Receta
1. Haz clic en **"+ Nueva Receta"**
2. Llena: Nombre, Precio (ej: 5.50)
3. Haz clic en **"Crear Receta"**
4. ¡Debería aparecer en la lista!

### 3. Calendario - Asignar Comida
1. Haz clic en cualquier tarjeta de **Almuerzo** o **Cena**
2. Elige la receta que creaste
3. ¡Aparecerá en el calendario!

---

## 📊 URL Importante

| Interfaz | URL |
|---|---|
| **Web Local** | `file:///c:/Git/HomeAPI/index.html` |
| **API Docs** | `http://localhost:8000/docs` |
| **API Base URL** | `http://localhost:8000` |

---

## ❌ Si algo falla

### Error: "No se puede abrir el script"
```powershell
# Ejecuta PRIMERO esto en PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "Connection refused" en la web
1. Verifica que la ventana de PowerShell esté ejecutándose
2. Comprueba que diga: `Uvicorn running on http://0.0.0.0:8000`
3. Espera 3-5 segundos después de iniciar

### Error: "ModuleNotFoundError"
```powershell
# Ejecuta esto:
pip install -r requirements.txt
```

---

## 🌐 Cuando hayas terminado de probar

### 1. Sube `index.html` a Cloudflare Pages
- Ve a https://pages.cloudflare.com
- Conecta tu repositorio de GitHub
- ¡Cloudflare automáticamente lo desplegará!

### 2. La web se conectará automáticamente a `https://homeapi.beadpaws.es`
- No necesitas cambiar nada en el código
- El detecta automáticamente si estás en localhost o producción

### 3. Asegúrate de que tu API esté accesible en `https://homeapi.beadpaws.es`
- Verifica que CORS esté habilitado (ya lo está por defecto)
- Prueba: `https://homeapi.beadpaws.es/docs`

---

## 📝 Resumen Rápido

```bash
# Paso 1: Abre PowerShell en la carpeta HomeAPI
cd c:\Git\HomeAPI

# Paso 2: Ejecuta la API
.\run-api.ps1

# Paso 3: Abre en navegador
file:///c:/Git/HomeAPI/index.html

# ¡LISTO! Empieza a añadir recetas y planificar tu menú
```

---

¿Necesitas ayuda con algún paso? 💬
