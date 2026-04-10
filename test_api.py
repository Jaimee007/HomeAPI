#!/usr/bin/env python3
"""
Script de test para validar la estructura y funcionalidad básica de HomeAPI
"""

import sys
sys.path.insert(0, '.')

def test_imports():
    """Verificar que todos los módulos se pueden importar correctamente"""
    print("[OK] Probando imports...")
    try:
        from app.db import init_database, get_conn
        print("  [OK] db.py OK")
        
        from app.schemas import MealIn, MealOut, CategoryIn, CategoryOut, DailyMenuIn, DailyMenuOut
        print("  [OK] schemas.py OK")
        
        from app import crud
        print("  [OK] crud.py OK")
        
        from app.main import app
        print("  [OK] main.py OK")
        
        from app.routers import categories, meals, daily_menu
        print("  [OK] routers OK")
        
        return True
    except Exception as e:
        print(f"  [ERROR] Error en imports: {e}")
        return False


def test_database():
    """Verificar que la base de datos se inicializa correctamente"""
    print("\n[OK] Probando base de datos...")
    try:
        from app.db import init_database, get_conn
        
        # Inicializar BD
        init_database()
        print("  [OK] init_database() OK")
        
        # Verificar conexión
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM categories')
            count = cur.fetchone()[0]
            print(f"  [OK] Conexion OK ({count} categorias por defecto)")
        
        return True
    except Exception as e:
        print(f"  [ERROR] Error en base de datos: {e}")
        return False


def test_crud():
    """Verificar operaciones CRUD basicas"""
    print("\n[OK] Probando operaciones CRUD...")
    try:
        from app import crud
        
        # Test: Obtener categorias
        cats = crud.listar_categorias()
        print(f"  [OK] crud.listar_categorias() - {len(cats)} categorias encontradas")
        
        # Test: Crear comida
        meal = crud.crear_comida("Comida Test", "Descripcion test", [1])
        print(f"  [OK] crud.crear_comida() - ID: {meal['id']}")
        
        # Test: Obtener comida
        retrieved = crud.obtener_comida(meal['id'])
        assert retrieved['nombre'] == "Comida Test"
        print(f"  [OK] crud.obtener_comida() - Nombre: {retrieved['nombre']}")
        
        # Test: Actualizar comida
        updated = crud.actualizar_comida(meal['id'], nombre="Comida Actualizada")
        assert updated['nombre'] == "Comida Actualizada"
        print(f"  [OK] crud.actualizar_comida() - Nuevo nombre: {updated['nombre']}")
        
        # Test: Crear menu diario
        menu = crud.crear_dia_menu(4, 2026, 10, meal['id'], meal['id'])
        print(f"  [OK] crud.crear_dia_menu() - ID: {menu['id']}")
        
        # Test: Eliminar comida
        deleted = crud.eliminar_comida(meal['id'])
        assert deleted == True
        print(f"  [OK] crud.eliminar_comida() - Eliminado correctamente")
        
        return True
    except Exception as e:
        print(f"  [ERROR] Error en CRUD: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api():
    """Verificar que la API de FastAPI esta configurada correctamente"""
    print("\n[OK] Probando configuracion de API...")
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test: Endpoint raiz
        response = client.get("/")
        assert response.status_code == 200, f"Status esperado 200, obtuve {response.status_code}"
        print(f"  [OK] GET / - Status: 200")
        
        # Test: Autenticacion con API Key correcta
        response = client.get("/categories", headers={"X-API-Key": "homeapi_default_key_2024"})
        assert response.status_code == 200, f"Status esperado 200, obtuve {response.status_code}"
        print(f"  [OK] Autenticacion - Con API Key: 200")
        
        # Test: Crear categoria (requiere API Key)
        response = client.post(
            "/categories",
            json={"nombre": "Test Category", "descripcion": "Test"},
            headers={"X-API-Key": "homeapi_default_key_2024"}
        )
        assert response.status_code == 201, f"Status esperado 201, obtuve {response.status_code}"
        print(f"  [OK] POST /categories - Status: 201")
        
        # Test: Docs
        response = client.get("/docs")
        assert response.status_code == 200, f"Status esperado 200, obtuve {response.status_code}"
        print(f"  [OK] GET /docs - Status: 200")
        
        return True
    except Exception as e:
        print(f"  [ERROR] Error en API: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 50)
    print("PRUEBA DE INTEGRIDAD - HomeAPI")
    print("=" * 50)
    
    results = [
        ("Imports", test_imports()),
        ("Base de Datos", test_database()),
        ("CRUD", test_crud()),
        ("API FastAPI", test_api()),
    ]
    
    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n[OK] Todas las pruebas pasaron correctamente.")
        print("\nProximos pasos:")
        print("  1. docker-compose up -d")
        print("  2. Acceder a http://localhost:8000/docs")
        print("  3. Usar header: X-API-Key: homeapi_default_key_2024")
    else:
        print("\n[ERROR] Algunas pruebas fallaron. Revisar errores arriba.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
