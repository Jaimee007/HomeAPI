# Home API - Gestor de Menú Semanal

API FastAPI para la gestión de comidas, cenas y menú semanal con autenticación por API Key.

## Características

- ✅ Gestión de comidas (CRUD)
- ✅ Gestión de categorías predefinidas y editables
- ✅ Asignación de categorías a comidas (relación muchos a muchos)
- ✅ Gestión de menú diario (asignación de comidas y cenas)
- ✅ Obtener comidas por categoría específica
- ✅ Autenticación por API Key
- ✅ Soporte para menús del mes actual y siguiente
- ✅ Base de datos SQLite
- ✅ Docker y docker-compose incluido

## Instalación y Uso

### Requisitos

- Docker y docker-compose instalados
- Python 3.11+ (para desarrollo local)

### Opción 1: Con Docker (Recomendado para Proxmox)

```bash
# Clonar o navegar al directorio del proyecto
cd HomeAPI

# Construir la imagen y ejecutar
docker-compose up -d

# La API estará disponible en http://localhost:8000
```

Para cambiar la API Key, editar `docker-compose.yml`:

```yaml
environment:
  - API_KEY=tu_clave_personalizada
```

### Opción 2: Desarrollo Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
uvicorn app.main:app --reload
```

## Documentación de Endpoints

La documentación interactiva está disponible en: `http://localhost:8000/docs`

Todos los endpoints requieren el header `X-API-Key` con la clave correcta.

### Categorías

- `GET /categories` - Listar todas las categorías
- `POST /categories` - Crear categoría
- `GET /categories/{category_id}` - Obtener categoría
- `PUT /categories/{category_id}` - Actualizar categoría
- `DELETE /categories/{category_id}` - Eliminar categoría

### Comidas

- `GET /meals` - Listar todas las comidas
- `POST /meals` - Crear comida con categorías
- `GET /meals/{meal_id}` - Obtener comida específica
- `PUT /meals/{meal_id}` - Actualizar comida
- `DELETE /meals/{meal_id}` - Eliminar comida
- `GET /meals/category/{category_id}` - Obtener comidas de una categoría

### Menú Diario

- `GET /menu` - Listar menú (opcional: filtar por mes y año)
- `GET /menu?mes=4&año=2026` - Obtener menú de abril 2026
- `POST /menu` - Crear asignación de comida para un día
- `GET /menu/{daily_menu_id}` - Obtener menú de un día
- `PUT /menu/{daily_menu_id}` - Actualizar comidas de un día
- `DELETE /menu/{daily_menu_id}` - Eliminar asignación de un día

## Ejemplos de Uso

### 1. Listar categorías (con autenticación)

```bash
curl -X GET http://localhost:8000/categories \
  -H "X-API-Key: homeapi_default_key_2024"
```

### 2. Crear una comida

```bash
curl -X POST http://localhost:8000/meals \
  -H "X-API-Key: homeapi_default_key_2024" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Pasta Carbonara",
    "descripcion": "Pasta italiana con salsa de huevo y bacon",
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

### 4. Obtener comidas de una categoría

```bash
curl -X GET http://localhost:8000/meals/category/1 \
  -H "X-API-Key: homeapi_default_key_2024"
```

## Variables de Entorno

- `DB_PATH`: Ruta de la base de datos SQLite (por defecto: `/app/data/home_menu.db`)
- `API_KEY`: Clave de autenticación (por defecto: `homeapi_default_key_2024`)

## Estructura de la Base de Datos

### Tabla: categories
- `id`: ID único (INTEGER PRIMARY KEY)
- `nombre`: Nombre de la categoría (TEXT UNIQUE)
- `descripcion`: Descripción opcional (TEXT)
- `created_at`: Timestamp de creación (TIMESTAMP)

**Categorías predefinidas:**
- Saludable
- Rápida
- Vegetariana
- Postres
- Carnes
- Pescado

### Tabla: meals
- `id`: ID único (INTEGER PRIMARY KEY)
- `nombre`: Nombre de la comida (TEXT)
- `descripcion`: Descripción opcional (TEXT)
- `created_at`: Timestamp de creación (TIMESTAMP)
- `updated_at`: Timestamp de última actualización (TIMESTAMP)

### Tabla: meal_categories
- `id`: ID único (INTEGER PRIMARY KEY)
- `meal_id`: Referencia a meals (FOREIGN KEY)
- `category_id`: Referencia a categories (FOREIGN KEY)

### Tabla: daily_menu
- `id`: ID único (INTEGER PRIMARY KEY)
- `mes`: Mes (1-12)
- `año`: Año
- `dia`: Día del mes (1-31)
- `meal_lunch_id`: Referencia a meals para comida (FOREIGN KEY)
- `meal_dinner_id`: Referencia a meals para cena (FOREIGN KEY)
- `created_at`: Timestamp de creación (TIMESTAMP)
- `updated_at`: Timestamp de última actualización (TIMESTAMP)

## Autenticación

La API utiliza **API Key** en el header `X-API-Key`. 

### Para cambiar la clave:

**En Docker:**
```bash
docker-compose down
# Editar docker-compose.yml y cambiar API_KEY
docker-compose up -d
```

**En desarrollo local:**
```bash
export API_KEY=mi_nueva_clave
uvicorn app.main:app --reload
```

## Configuración en Proxmox

1. **Construir la imagen:**
   ```bash
   docker build -t homeapi:latest .
   ```

2. **Crear contenedor:**
   ```bash
   docker run -d \
     --name homeapi \
     -p 8000:8000 \
     -e API_KEY=tu_clave_segura \
     -v /var/homeapi/data:/data \
     homeapi:latest
   ```

3. **O con docker-compose:**
   ```bash
   docker-compose up -d
   ```

## Logs

Ver logs del contenedor:
```bash
docker logs -f homeapi
```

O con docker-compose:
```bash
docker-compose logs -f home-api
```

## Troubleshooting

### Error de conexión a la BD
- Verificar permisos de directorios en volúmenes
- Asegurar que `/data` existe y tiene permisos 755

### Error 401 Unauthorized
- Verificar que el header `X-API-Key` está presente
- Verificar que la clave es correcta
- Por defecto: `homeapi_default_key_2024`

## Desarrollo

```bash
# Instalar en modo desarrollo
pip install -r requirements.txt

# Ejecutar tests (cuando existan)
pytest

# Lint y formato
black app/
flake8 app/
```

## Licencia

MIT
