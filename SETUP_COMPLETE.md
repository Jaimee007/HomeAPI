# HomeAPI - Documentación Completa

## Resumen del Proyecto

Se ha creado una **API FastAPI completa** para gestión de menú semanal con las siguientes características:

- ✅ Gestión de comidas (CRUD)
- ✅ Gestión de categorías (CRUD)
- ✅ Asignación de comidas a categorías (relación muchos a muchos)
- ✅ Gestión de menú diario (asignación de comidas y cenas por día)
- ✅ Obtención de comidas por categoría
- ✅ Autenticación por API Key
- ✅ Base de datos SQLite
- ✅ Docker y docker-compose listos
- ✅ Documentación interactiva con Swagger

## Estructura de Archivos

```
HomeAPI/
├── app/
│   ├── __init__.py                 # Inicializador del paquete
│   ├── main.py                     # Aplicación FastAPI principal
│   ├── db.py                       # Configuración de SQLite
│   ├── schemas.py                  # Modelos Pydantic
│   ├── crud.py                     # Operaciones de base de datos
│   └── routers/
│       ├── __init__.py
│       ├── categories.py           # Endpoints de categorías
│       ├── meals.py                # Endpoints de comidas
│       └── daily_menu.py           # Endpoints de menú diario
├── requirements.txt                # Dependencias Python
├── Dockerfile                      # Configuración Docker
├── docker-compose.yml              # Orquestación Docker
├── entrypoint.sh                   # Script de inicialización
├── README.md                       # Documentación principal
├── API_EXAMPLES.md                 # Ejemplos de uso
├── SETUP_COMPLETE.md               # Este archivo
└── test_api.py                     # Script de pruebas
```

## Instalación y Uso

### Opción 1: Docker (Recomendado para Proxmox)

```bash
cd HomeAPI
docker-compose up -d
```

La API estará disponible en: `http://localhost:8000`
Documentación interactiva: `http://localhost:8000/docs`

### Opción 2: Desarrollo Local

```bash
cd HomeAPI
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Autenticación

**Todos los endpoints (excepto `/`, `/docs`, `/openapi.json`, `/redoc`) requieren:**

Header: `X-API-Key`
Valor por defecto: `homeapi_default_key_2024`

### Cambiar API Key en Docker:

Editar `docker-compose.yml`:
```yaml
environment:
  - API_KEY=tu_clave_personalizada
```

## Endpoints Disponibles

### Categorías
- `GET /categories` - Listar todas
- `POST /categories` - Crear nueva
- `GET /categories/{id}` - Obtener una
- `PUT /categories/{id}` - Actualizar
- `DELETE /categories/{id}` - Eliminar

### Comidas
- `GET /meals` - Listar todas
- `POST /meals` - Crear nueva
- `GET /meals/{id}` - Obtener una
- `PUT /meals/{id}` - Actualizar
- `DELETE /meals/{id}` - Eliminar
- `GET /meals/category/{category_id}` - Obtener por categoría

### Menú Diario
- `GET /menu` - Listar menú completo
- `GET /menu?mes=4&año=2026` - Filtrar por mes
- `POST /menu` - Crear asignación de día
- `GET /menu/{id}` - Obtener un día
- `PUT /menu/{id}` - Actualizar un día
- `DELETE /menu/{id}` - Eliminar un día

## Base de Datos

### Tablas SQLite

**categories:** Almacena categorías predefinidas y editables
**meals:** Almacena información de comidas
**meal_categories:** Relación muchos a muchos entre comidas y categorías
**daily_menu:** Asignaciones de comidas a días específicos

### Categorías Predefinidas

- Saludable
- Rápida
- Vegetariana
- Postres
- Carnes
- Pescado

Todas son editables y se pueden añadir nuevas.

## Ejemplos de Uso

### 1. Obtener todas las comidas

```bash
curl -X GET http://localhost:8000/meals \
  -H "X-API-Key: homeapi_default_key_2024"
```

### 2. Crear una comida

```bash
curl -X POST http://localhost:8000/meals \
  -H "X-API-Key: homeapi_default_key_2024" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Pasta Carbonara",
    "descripcion": "Pasta italiana",
    "category_ids": [1, 3]
  }'
```

### 3. Asignar comida a un día

```bash
curl -X POST http://localhost:8000/menu \
  -H "X-API-Key: homeapi_default_key_2024" \
  -H "Content-Type: application/json" \
  -d '{
    "mes": 4,
    "año": 2026,
    "dia": 10,
    "meal_lunch_id": 1,
    "meal_dinner_id": 2
  }'
```

### 4. Obtener menú de un mes

```bash
curl -X GET "http://localhost:8000/menu?mes=4&año=2026" \
  -H "X-API-Key: homeapi_default_key_2024"
```

## Pruebas

El proyecto incluye `test_api.py` que verifica:

- ✅ Importación de módulos
- ✅ Inicialización de base de datos
- ✅ Operaciones CRUD
- ✅ Configuración de FastAPI

Ejecutar pruebas:
```bash
python test_api.py
```

## Estructura de Datos

### Respuesta de Comida
```json
{
  "id": 1,
  "nombre": "Pollo al horno",
  "descripcion": "Pechuga de pollo con limón",
  "categories": [
    {
      "id": 1,
      "nombre": "Saludable",
      "descripcion": "Comidas bajas en calorías",
      "created_at": "2026-04-10T10:30:00"
    }
  ],
  "created_at": "2026-04-10T10:30:00",
  "updated_at": "2026-04-10T10:30:00"
}
```

### Respuesta de Menú Diario
```json
{
  "id": 1,
  "mes": 4,
  "año": 2026,
  "dia": 10,
  "meal_lunch": { /* comida */ },
  "meal_dinner": { /* comida */ },
  "created_at": "2026-04-10T10:30:00",
  "updated_at": "2026-04-10T10:30:00"
}
```

## Variables de Entorno

- `DB_PATH` - Ruta de la base de datos (defecto: `/app/data/home_menu.db`)
- `API_KEY` - Clave de autenticación (defecto: `homeapi_default_key_2024`)

## Configuración en Proxmox

```bash
# 1. Construir imagen
docker build -t homeapi:latest .

# 2. Ejecutar contenedor
docker run -d \
  --name homeapi \
  -p 8000:8000 \
  -e API_KEY=tu_clave_segura \
  -v /var/homeapi/data:/data \
  homeapi:latest

# 3. O con docker-compose
docker-compose up -d
```

## Características Implementadas

### 1. Gestión de Comidas
- Crear, leer, actualizar, eliminar comidas
- Cada comida puede tener descripción
- Cada comida puede asignarse a múltiples categorías
- Obtener comidas de una categoría específica

### 2. Gestión de Categorías
- Categorías predefinidas (6 por defecto)
- Crear nuevas categorías
- Actualizar y eliminar categorías
- Relación muchos a muchos con comidas

### 3. Menú Diario
- Asignar comida almuerzo y cena para cada día
- Soporte para mes actual y siguiente
- Actualizar asignaciones
- Obtener menú por mes
- Eliminar asignaciones

### 4. Autenticación
- API Key en header `X-API-Key`
- Endpoints públicos: `/`, `/docs`, `/openapi.json`, `/redoc`
- Configurable por variable de entorno

### 5. Base de Datos
- SQLite con WAL mode para mejor concurrencia
- Timestamps automáticos
- Constraints de unicidad
- Relaciones con foreign keys

## Próximos Pasos

1. **Iniciar en Docker:**
   ```bash
   docker-compose up -d
   ```

2. **Acceder a documentación:**
   - Swagger: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Integrar con Frontend:**
   - Usar ejemplos de `API_EXAMPLES.md`
   - Header requerido: `X-API-Key: homeapi_default_key_2024`

4. **Personalizar:**
   - Cambiar API Key en `docker-compose.yml`
   - Añadir categorías personalizadas
   - Expandir con nuevos endpoints

## Soporte

Para dudas o problemas:
1. Revisar `/docs` en la API
2. Consultar `API_EXAMPLES.md`
3. Ver logs: `docker-compose logs home-api`
4. Verificar BD: `sqlite3 data/home_menu.db`

---

**Estado:** ✅ Listo para producción en Proxmox

**Fecha de creación:** 2026-04-10

**Versión:** 1.0.0
