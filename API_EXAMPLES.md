"""
EJEMPLOS DE USO - HomeAPI desde Frontend

Este archivo muestra cómo hacer llamadas a la API desde un frontend JavaScript/React
"""

# ============================================
# CONFIGURACIÓN (en tu frontend)
# ============================================

API_URL = "http://localhost:8000"
API_KEY = "homeapi_default_key_2024"  # La misma clave que en docker-compose.yml

# Headers por defecto
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}


# ============================================
# 1. GESTIÓN DE CATEGORÍAS
# ============================================

# Obtener todas las categorías
async def obtener_categorias():
    response = await fetch(f"{API_URL}/categories", {
        method: "GET",
        headers
    })
    return await response.json()

# Crear una nueva categoría
async def crear_categoria(nombre, descripcion=None):
    response = await fetch(f"{API_URL}/categories", {
        method: "POST",
        headers,
        body: JSON.stringify({
            nombre,
            descripcion
        })
    })
    return await response.json()

# Actualizar categoría
async def actualizar_categoria(category_id, nombre=None, descripcion=None):
    response = await fetch(f"{API_URL}/categories/{category_id}", {
        method: "PUT",
        headers,
        body: JSON.stringify({
            nombre,
            descripcion
        })
    })
    return await response.json()

# Eliminar categoría
async def eliminar_categoria(category_id):
    response = await fetch(f"{API_URL}/categories/{category_id}", {
        method: "DELETE",
        headers
    })
    return response.ok


# ============================================
# 2. GESTIÓN DE COMIDAS
# ============================================

# Obtener todas las comidas
async def obtener_comidas():
    response = await fetch(f"{API_URL}/meals", {
        method: "GET",
        headers
    })
    return await response.json()

# Crear una nueva comida
async def crear_comida(nombre, descripcion=None, category_ids=[]):
    response = await fetch(f"{API_URL}/meals", {
        method: "POST",
        headers,
        body: JSON.stringify({
            nombre,
            descripcion,
            category_ids
        })
    })
    return await response.json()

# Actualizar comida
async def actualizar_comida(meal_id, nombre=None, descripcion=None, category_ids=None):
    body = {}
    if nombre: body['nombre'] = nombre
    if descripcion is not None: body['descripcion'] = descripcion
    if category_ids is not None: body['category_ids'] = category_ids
    
    response = await fetch(f"{API_URL}/meals/{meal_id}", {
        method: "PUT",
        headers,
        body: JSON.stringify(body)
    })
    return await response.json()

# Eliminar comida
async def eliminar_comida(meal_id):
    response = await fetch(f"{API_URL}/meals/{meal_id}", {
        method: "DELETE",
        headers
    })
    return response.ok

# Obtener comidas de una categoría específica
async def obtener_comidas_por_categoria(category_id):
    response = await fetch(f"{API_URL}/meals/category/{category_id}", {
        method: "GET",
        headers
    })
    return await response.json()


# ============================================
# 3. GESTIÓN DE MENÚ DIARIO
# ============================================

# Obtener menú completo
async def obtener_menu_completo():
    response = await fetch(f"{API_URL}/menu", {
        method: "GET",
        headers
    })
    return await response.json()

# Obtener menú de un mes específico
async def obtener_menu_mes(mes, año):
    response = await fetch(
        f"{API_URL}/menu?mes={mes}&año={año}",
        {
            method: "GET",
            headers
        }
    )
    return await response.json()

# Crear asignación para un día (comida y cena)
async def asignar_comidas_dia(mes, año, dia, meal_lunch_id=None, meal_dinner_id=None):
    response = await fetch(f"{API_URL}/menu", {
        method: "POST",
        headers,
        body: JSON.stringify({
            mes,
            año,
            dia,
            meal_lunch_id,
            meal_dinner_id
        })
    })
    return await response.json()

# Actualizar comidas de un día
async def actualizar_menu_dia(daily_menu_id, meal_lunch_id=None, meal_dinner_id=None):
    body = {}
    if meal_lunch_id is not None: body['meal_lunch_id'] = meal_lunch_id
    if meal_dinner_id is not None: body['meal_dinner_id'] = meal_dinner_id
    
    response = await fetch(f"{API_URL}/menu/{daily_menu_id}", {
        method: "PUT",
        headers,
        body: JSON.stringify(body)
    })
    return await response.json()

# Eliminar asignación de un día
async def eliminar_menu_dia(daily_menu_id):
    response = await fetch(f"{API_URL}/menu/{daily_menu_id}", {
        method: "DELETE",
        headers
    })
    return response.ok


# ============================================
# EJEMPLO DE USO COMPLETO (en JavaScript/React)
# ============================================

"""
// Ejemplo 1: Obtener todas las categorías
const categorias = await obtener_categorias();
console.log('Categorías:', categorias);

// Ejemplo 2: Crear una nueva comida
const nuevaComida = await crear_comida(
    nombre="Ensalada César",
    descripcion="Ensalada fresca con pollo",
    category_ids=[1, 3]  // Saludable + Rápida
);
console.log('Comida creada:', nuevaComida);

// Ejemplo 3: Obtener comidas saludables (categoría 1)
const comidasSaludables = await obtener_comidas_por_categoria(1);
console.log('Comidas saludables:', comidasSaludables);

// Ejemplo 4: Asignar comidas a un día
const menuDia = await asignar_comidas_dia(
    mes=4,
    año=2026,
    dia=10,
    meal_lunch_id=1,   // ID de la comida de almuerzo
    meal_dinner_id=2   // ID de la comida de cena
);
console.log('Menú del día:', menuDia);

// Ejemplo 5: Obtener menú completo de abril 2026
const menuMes = await obtener_menu_mes(4, 2026);
console.log('Menú de abril:', menuMes);

// Ejemplo 6: Actualizar comidas de un día
const menuActualizado = await actualizar_menu_dia(
    daily_menu_id=1,
    meal_lunch_id=3,  // Nueva comida
    meal_dinner_id=4  // Nueva cena
);
console.log('Menú actualizado:', menuActualizado);

// Ejemplo 7: Eliminar comida
const eliminado = await eliminar_comida(1);
console.log('¿Comida eliminada?:', eliminado);
"""

# ============================================
# ESTRUCTURA DE RESPUESTA
# ============================================

# Categoría (CategoryOut)
categoria_ejemplo = {
    "id": 1,
    "nombre": "Saludable",
    "descripcion": "Comidas bajas en calorías y nutritivas",
    "created_at": "2026-04-10T10:30:00"
}

# Comida (MealOut)
comida_ejemplo = {
    "id": 1,
    "nombre": "Pollo al horno",
    "descripcion": "Pechuga de pollo al horno con limón",
    "categories": [
        {
            "id": 1,
            "nombre": "Saludable",
            "descripcion": "Comidas bajas en calorías y nutritivas",
            "created_at": "2026-04-10T10:30:00"
        },
        {
            "id": 5,
            "nombre": "Carnes",
            "descripcion": "Platos con carne",
            "created_at": "2026-04-10T10:30:00"
        }
    ],
    "created_at": "2026-04-10T10:30:00",
    "updated_at": "2026-04-10T10:30:00"
}

# Menú Diario (DailyMenuOut)
menu_dia_ejemplo = {
    "id": 1,
    "mes": 4,
    "año": 2026,
    "dia": 10,
    "meal_lunch": comida_ejemplo,
    "meal_dinner": {
        "id": 2,
        "nombre": "Pasta Carbonara",
        "descripcion": "Pasta italiana con salsa de huevo y bacon",
        "categories": [
            {
                "id": 3,
                "nombre": "Vegetariana",
                "descripcion": "Comidas sin carne",
                "created_at": "2026-04-10T10:30:00"
            }
        ],
        "created_at": "2026-04-10T10:30:00",
        "updated_at": "2026-04-10T10:30:00"
    },
    "created_at": "2026-04-10T10:30:00",
    "updated_at": "2026-04-10T10:30:00"
}

# ============================================
# CÓDIGOS DE RESPUESTA HTTP
# ============================================

# Exitosas:
# 200 OK - Operación exitosa (GET, PUT, etc.)
# 201 Created - Recurso creado (POST)
# 204 No Content - Operación exitosa sin contenido (DELETE)

# Errores:
# 400 Bad Request - Datos inválidos o categoría/comida duplicada
# 401 Unauthorized - API Key inválida o no proporcionada
# 404 Not Found - Recurso no encontrado
# 500 Internal Server Error - Error del servidor
