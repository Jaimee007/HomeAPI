# 📅 Guía de Uso - Gestor de Menú Semanal

## Cambios Realizados en el Backend

### 1. **Categorías Simplificadas**
- Las categorías ahora **solo contienen nombre e ID**
- Se eliminó la descripción completamente
- API endpoints funcionan igual: `GET /categories`, `POST /categories`, etc.

### 2. **Comidas con Precio**
- Se agregó un nuevo campo **`precio`** (decimal con 2 decimales)
- Se eliminaron los campos `created_at` y `updated_at`
- El precio es **requerido** al crear una comida
- Estructura nueva de `MealOut`:
  ```json
  {
    "id": 1,
    "nombre": "Pasta a la Carbonara",
    "precio": 8.50,
    "categories": [
      {"id": 1, "nombre": "Rápida"}
    ]
  }
  ```

## Interfaz Web - Características

### 🗓️ **Calendario**
- Muestra **dos semanas**: actual y próxima
- Cada día tiene **dos tarjetas**: Almuerzo 🍽️ y Cena 🍽️
- **Marcado visual** del día actual (con borde rosa y badge "HOY")
- Cada comida muestra el **nombre y precio** en la tarjeta

### ➕ **Agregar Comidas**
1. Haz clic en una tarjeta de comida (almuerzo o cena)
2. Se abre un modal con todas las recetas disponibles
3. Haz clic en "Asignar" en la receta deseada
4. Se actualiza el calendario automáticamente

### ✏️ **Crear Nueva Receta**
Desde la barra lateral:
1. Haz clic en **"+ Nueva Receta"**
2. Ingresa el nombre y precio
3. Selecciona categorías (opcional)
4. Haz clic en "Crear Receta"

### ⚙️ **Gestionar Categorías**
Desde la barra lateral:
1. Haz clic en **"⚙️ Categorías"**
2. Nuevo apartado para **agregar categorías**
3. Lista de categorías existentes con opción de **eliminar**

### 📊 **Panel de Resumen**
Muestra en la barra lateral:
- Total de recetas disponibles
- Total de categorías
- **Costo total de la semana actual** (suma de almuerzo + cena)

## Cómo Usar la Web

### Requisitos
1. La API debe estar ejecutándose en `http://localhost:8000`
2. Abre el archivo `index.html` en un navegador
3. La API Key ya está configurada (`homeapi_default_key_2024`)

### Flujo Típico

1. **Primero: Crear Categorías** (opcional, ya existen predefinidas)
   - Abre "Gestionar Categorías"
   - Agrega las que necesites

2. **Segundo: Crear Recetas**
   - Haz clic en "+ Nueva Receta"
   - Llena datos: nombre, precio, categorías
   - Confirma

3. **Tercero: Planificar Semana**
   - Haz clic en una tarjeta de almuerzo o cena
   - Selecciona la receta del modal
   - La comida aparece en el calendario

4. **Eliminar Comidas**
   - Haz clic en la "×" dentro de la tarjeta de comida
   - La comida se elimina de ese día

## Diseño Visual

### Paleta de Colores Pastel ✨
- **Rosa Pastel** (#FFB3D9): Principal, botones, acentos
- **Azul Pastel** (#B3D9FF): Secundario, información
- **Verde Pastel** (#B3FFB3): Éxito, confirmación
- **Amarillo Pastel** (#FFFFB3): Advertencias suaves
- **Púrpura Pastel** (#D9B3FF): Acentos adicionales
- **Durazno Pastel** (#FFD9B3): Alternativo

### Responsive
- ✅ Diseño completamente responsive
- ✅ Funciona en desktop, tablet y móvil
- ✅ Grid adaptable (de 1 a 7 columnas según pantalla)

## API Endpoints Actualizados

### Categorías
```
GET    /categories              → Lista todas
POST   /categories              → Crear (solo nombre)
GET    /categories/{id}         → Obtener una
PUT    /categories/{id}         → Actualizar (solo nombre)
DELETE /categories/{id}         → Eliminar
```

### Comidas
```
GET    /meals                   → Lista todas (con precio)
POST   /meals                   → Crear (nombre, precio, categorías)
GET    /meals/{id}              → Obtener una
PUT    /meals/{id}              → Actualizar (nombre, precio, categorías)
DELETE /meals/{id}              → Eliminar
GET    /meals/category/{cat_id} → Por categoría
```

### Menú Diario
```
GET       /daily-menu               → Listar
POST      /daily-menu               → Crear
GET       /daily-menu/{id}          → Obtener
PUT       /daily-menu/{id}          → Actualizar
DELETE    /daily-menu/{id}          → Eliminar
GET       /daily-menu/mes/{mes}/año/{año}  → Por mes/año
```

## Ejemplos de Requests

### Crear Categoría
```bash
curl -X POST http://localhost:8000/categories \
  -H "X-API-Key: homeapi_default_key_2024" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Dieta"}'
```

### Crear Receta con Precio
```bash
curl -X POST http://localhost:8000/meals \
  -H "X-API-Key: homeapi_default_key_2024" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Ensalada César",
    "precio": 6.99,
    "category_ids": [3]
  }'
```

### Crear Menú Diario
```bash
curl -X POST http://localhost:8000/daily-menu \
  -H "X-API-Key: homeapi_default_key_2024" \
  -H "Content-Type: application/json" \
  -d '{
    "mes": 4,
    "año": 2026,
    "dia": 11,
    "meal_lunch_id": 1,
    "meal_dinner_id": 2
  }'
```

## Notas Importantes

- ⚠️ Al eliminar una categoría, las recetas mantienen su asignación pero la categoría desaparece
- ⚠️ Al eliminar una receta, se elimina de todos los días del menú
- ✅ El precio se calcula automáticamente en el frontend
- ✅ Se puede reutilizar la misma receta múltiples veces en diferentes días
- ✅ Los datos persisten en la base de datos SQLite

## Próximas Mejoras Sugeridas

1. Editar recetas existentes desde el web
2. Duplicar menú semanal
3. Exportar menú a PDF
4. Vista de recetas populares
5. Buscar recetas por categoría
6. Historial de cambios

---

¡Disfruta planificando tu menú semanal! 🍽️📅
