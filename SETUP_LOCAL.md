# 🚀 Guía de Ejecución - API + Web Local

## Opción 1: Ejecución Local (Sin Docker) - **MÁS RÁPIDO PARA DESARROLLO**

### Paso 1: Instalar Python y dependencias

```bash
# Asegúrate de tener Python 3.11+ instalado
python --version

# Navega a la carpeta del proyecto
cd c:\Git\HomeAPI

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
venv\Scripts\activate

# En caso de estar en otra terminal, ejecutar primero:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Paso 2: Instalar dependencias

```bash
# Con el entorno activado
pip install -r requirements.txt
```

### Paso 3: Ejecutar la API

```bash
# Desde la carpeta c:\Git\HomeAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Salida esperada:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Paso 4: Abre la web en el navegador

```
Abre: file:///c:/Git/HomeAPI/index.html
O simplemente arrastra el archivo al navegador
```

**¡La web debería conectarse automáticamente a `http://localhost:8000`!**

---

## Opción 2: Ejecución con Docker

### Paso 1: Instalar Docker y Docker Compose

- Descargar [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop)
- Verificar instalación:
```bash
docker --version
docker-compose --version
```

### Paso 2: Construir y ejecutar

```bash
cd c:\Git\HomeAPI

# Construir imagen y ejecutar contenedor
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f
```

### Paso 3: Abre la web

```
Abre: file:///c:/Git/HomeAPI/index.html
```

**Para detener la API:**
```bash
docker-compose down
```

---

## 📝 Configuración de URL de API

### Desarrollo Local ✅
El `index.html` detecta automáticamente que estás en `localhost` y usa:
```
http://localhost:8000
```

### Producción (Cloudflare Pages)
Cuando subes a Cloudflare Pages, el detectará automáticamente que **no es localhost** y usará:
```
https://homeapi.beadpaws.es
```

**No necesitas cambiar nada en el código!** ✨

---

## 🔍 Testear la API

### 1. Desde el navegador (Documentación interactiva)

```
http://localhost:8000/docs
```

Aquí puedes ver y probar todos los endpoints.

### 2. Desde PowerShell (curl)

**Crear categoría:**
```powershell
$headers = @{"X-API-Key" = "homeapi_default_key_2024"}
Invoke-RestMethod -Uri "http://localhost:8000/categories" `
  -Method POST `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"nombre":"Dieta"}'
```

**Crear receta:**
```powershell
$headers = @{"X-API-Key" = "homeapi_default_key_2024"}
$body = @{
    nombre = "Pasta Carbonara"
    precio = 8.50
    category_ids = @(1)
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/meals" `
  -Method POST `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

**Obtener todas las recetas:**
```powershell
$headers = @{"X-API-Key" = "homeapi_default_key_2024"}
Invoke-RestMethod -Uri "http://localhost:8000/meals" `
  -Method GET `
  -Headers $headers | ConvertTo-Json
```

---

## ✅ Checklist de Verificación

### En la Web
- [ ] Se ve el calendario con dos semanas
- [ ] Aparece "HOY" en el día actual con color diferente
- [ ] Puedo hacer clic en un día para agregar una comida
- [ ] Puedo crear una nueva receta y asignarla
- [ ] Puedo crear categorías
- [ ] El precio aparece en las tarjetas
- [ ] Se calcula el total de la semana (abajo a la derecha)

### En la API (http://localhost:8000/docs)
- [ ] GET /categories → devuelve lista de categorías
- [ ] POST /categories → crea categorías correctamente
- [ ] GET /meals → devuelve lista de recetas
- [ ] POST /meals → crea recetas con precio
- [ ] GET /daily-menu → devuelve menús del día

---

## 🐛 Solucionar Problemas

### Error: "No module named 'fastapi'"
```bash
# Asegúrate de haber activado el entorno virtual
venv\Scripts\activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "Connection refused" en la web
- ❌ Verifica que la API esté ejecutándose
- ❌ Verifica que sea en el puerto 8000
- ❌ Si usas Docker, comprueba: `docker ps`

### Error: "CORS" en la consola del navegador
- La API ya tiene CORS habilitado para "*"
- Si aún tienes problemas, revisa los headers en Swagger (/docs)

### La web no se conecta a la API
1. Abre la consola del navegador (F12)
2. Verifica los errores en Network
3. Comprueba que la URL base es correcta:
   - Para localhost: `http://localhost:8000`
   - Para producción: `https://homeapi.beadpaws.es`

---

## 📤 Cuando Estés Listo para Producción

### 1. Sube el `index.html` a Cloudflare Pages

```bash
# Opcion A: Subir directamente desde GitHub
# 1. Crea un repositorio en GitHub con tu proyecto
# 2. Ve a https://pages.cloudflare.com
# 3. Conecta tu repositorio
# 4. Cloudflare automáticamente desplegará los cambios

# Opcion B: Subir con Wrangler CLI
npm install -g wrangler
wrangler pages deploy
```

### 2. Asegúrate de que `homeapi.beadpaws.es` esté correctamente configurado

```bash
# Verifica que tu dominio apunta al servidor correcto
# La API debe estar accesible en: https://homeapi.beadpaws.es

# Desde PowerShell, prueba:
Invoke-RestMethod -Uri "https://homeapi.beadpaws.es/docs"
```

### 3. La web automáticamente usará la URL de producción

Cuando accedas a la web desde Cloudflare Pages:
- El `hostname` NO será "localhost"
- Automáticamente usará `https://homeapi.beadpaws.es`
- ¡Sin cambios de código necesarios!

---

## 📊 Estructura de Carpetas

```
HomeAPI/
├── index.html                 ← Web (abre en navegador)
├── app/
│   ├── main.py               ← Punto de entrada de la API
│   ├── schemas.py            ← Modelos Pydantic
│   ├── crud.py               ← Lógica de base de datos
│   ├── db.py                 ← Inicialización de BD
│   └── routers/
│       ├── categories.py      ← Endpoints de categorías
│       ├── meals.py          ← Endpoints de comidas
│       └── daily_menu.py     ← Endpoints de menú diario
├── requirements.txt          ← Dependencias Python
├── Dockerfile                ← Para Docker
├── docker-compose.yml        ← Orchestración
├── data/
│   └── home_menu.db          ← Base de datos SQLite
└── venv/                     ← Entorno virtual (tras instalación)
```

---

## 🔐 Cambiar la API Key

### En desarrollo local:
```bash
# Opción 1: Variable de entorno
$env:API_KEY = "tu_clave_nueva"
uvicorn app.main:app --reload

# Opción 2: Editar docker-compose.yml
# environment:
#   - API_KEY=tu_clave_nueva
```

### En el `index.html`:
```javascript
const API_KEY = 'tu_clave_nueva';  // Cambiar esta línea
```

---

## 📞 Verificar que todo funciona

**Prueba 1: API respondiendo**
```bash
# Abre esto en el navegador
http://localhost:8000/docs
```

**Prueba 2: Web conectándose**
```
Abre index.html en el navegador
Abre consola (F12)
No debe haber errores de conexión
```

**Prueba 3: Crear datos**
1. En la web: "+ Nueva Receta"
2. Rellena: Nombre, Precio, Categoría
3. Haz clic en "Crear Receta"
4. Verifica en http://localhost:8000/docs → GET /meals

---

¡Listo para comenzar! 🎉 Ejecuta la API y prueba la web localmente.
