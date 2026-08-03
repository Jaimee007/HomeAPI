from .db import get_conn
import sqlite3
from typing import List, Optional, Dict, Any


def _normalize_spec(spec: Optional[str]) -> Optional[str]:
    if spec is None:
        return None
    normalized = spec.strip()
    return normalized if normalized else None


def _merge_specs(existing: Optional[str], new_spec: Optional[str]) -> Optional[str]:
    existing = _normalize_spec(existing)
    new_spec = _normalize_spec(new_spec)
    if existing and new_spec:
        existing_parts = [part.strip() for part in existing.split('/') if part.strip()]
        new_parts = [part.strip() for part in new_spec.split('/') if part.strip()]
        for part in new_parts:
            if part not in existing_parts:
                existing_parts.append(part)
        return ' / '.join(existing_parts)
    return existing or new_spec


def _upsert_meal_ingredient(cur, meal_id: int, ingredient_id: int, spec: Optional[str]):
    cur.execute(
        'SELECT spec FROM meal_ingredients WHERE meal_id = ? AND ingredient_id = ?',
        (meal_id, ingredient_id)
    )
    row = cur.fetchone()
    if row is None:
        cur.execute(
            'INSERT INTO meal_ingredients (meal_id, ingredient_id, spec) VALUES (?, ?, ?)',
            (meal_id, ingredient_id, _normalize_spec(spec))
        )
        return

    combined_spec = _merge_specs(row['spec'], spec)
    if combined_spec != row['spec']:
        cur.execute(
            'UPDATE meal_ingredients SET spec = ? WHERE meal_id = ? AND ingredient_id = ?',
            (combined_spec, meal_id, ingredient_id)
        )


# ==================== CATEGORÍAS ====================
def crear_categoria(nombre: str) -> Dict[str, Any]:
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO categories (nombre) VALUES (?)',
                (nombre,)
            )
            conn.commit()
            cur.execute('SELECT id, nombre FROM categories WHERE id = ?', (cur.lastrowid,))
            return dict(cur.fetchone())
        except sqlite3.IntegrityError:
            raise ValueError(f"Categoría '{nombre}' ya existe")


def listar_categorias() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre FROM categories ORDER BY nombre')
        return [dict(r) for r in cur.fetchall()]


def obtener_categoria(category_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre FROM categories WHERE id = ?', (category_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def actualizar_categoria(category_id: int, nombre: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM categories WHERE id = ?', (category_id,))
        if not cur.fetchone():
            return None
        
        if nombre:
            try:
                cur.execute('UPDATE categories SET nombre = ? WHERE id = ?', (nombre, category_id))
            except sqlite3.IntegrityError:
                raise ValueError(f"Categoria '{nombre}' ya existe")
        
        conn.commit()
        return obtener_categoria(category_id)


def eliminar_categoria(category_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        return cur.rowcount > 0


# ==================== INGREDIENTES ====================
def crear_ingrediente(nombre: str) -> Dict[str, Any]:
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO ingredients (nombre) VALUES (?)',
                (nombre,)
            )
            conn.commit()
            cur.execute('SELECT id, nombre FROM ingredients WHERE id = ?', (cur.lastrowid,))
            return dict(cur.fetchone())
        except sqlite3.IntegrityError:
            raise ValueError(f"Ingrediente '{nombre}' ya existe")


def listar_ingredientes() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre FROM ingredients ORDER BY nombre')
        return [dict(r) for r in cur.fetchall()]


def obtener_ingrediente(ingredient_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre FROM ingredients WHERE id = ?', (ingredient_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def actualizar_ingrediente(ingredient_id: int, nombre: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM ingredients WHERE id = ?', (ingredient_id,))
        if not cur.fetchone():
            return None
        try:
            cur.execute('UPDATE ingredients SET nombre = ? WHERE id = ?', (nombre, ingredient_id))
            conn.commit()
            return obtener_ingrediente(ingredient_id)
        except sqlite3.IntegrityError:
            raise ValueError(f"Ingrediente '{nombre}' ya existe")


def eliminar_ingrediente(ingredient_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM ingredients WHERE id = ?', (ingredient_id,))
        conn.commit()
        return cur.rowcount > 0


# ==================== COMIDAS ====================

def _attach_meal_details(cur, meal: Dict[str, Any]) -> Dict[str, Any]:
    cur.execute('''
        SELECT c.id, c.nombre
        FROM categories c
        JOIN meal_categories mc ON c.id = mc.category_id
        WHERE mc.meal_id = ?
    ''', (meal['id'],))
    meal['categories'] = [dict(row) for row in cur.fetchall()]

    cur.execute('''
        SELECT i.id AS ingredient_id, i.nombre, mi.spec
        FROM ingredients i
        JOIN meal_ingredients mi ON i.id = mi.ingredient_id
        WHERE mi.meal_id = ?
        ORDER BY i.nombre
    ''', (meal['id'],))
    meal['ingredients'] = [dict(row) for row in cur.fetchall()]
    return meal


def crear_comida(nombre: str, category_ids: List[int], ingredient_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO meals (nombre) VALUES (?)',
            (nombre,)
        )
        conn.commit()
        meal_id = cur.lastrowid

        for cat_id in category_ids:
            cur.execute(
                'INSERT OR IGNORE INTO meal_categories (meal_id, category_id) VALUES (?, ?)',
                (meal_id, cat_id)
            )

        ingredient_map: Dict[int, Optional[str]] = {}
        for entry in ingredient_entries:
            ingredient_id = entry.get('ingredient_id')
            if not ingredient_id:
                continue
            ingredient_map[ingredient_id] = _merge_specs(ingredient_map.get(ingredient_id), entry.get('spec'))

        for ingredient_id, spec in ingredient_map.items():
            _upsert_meal_ingredient(cur, meal_id, ingredient_id, spec)

        conn.commit()
        return obtener_comida(meal_id)


def listar_comidas() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre FROM meals ORDER BY nombre')
        meals = [dict(r) for r in cur.fetchall()]
        for meal in meals:
            _attach_meal_details(cur, meal)
        return meals


def obtener_comida(meal_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre FROM meals WHERE id = ?', (meal_id,))
        row = cur.fetchone()
        if not row:
            return None
        meal = dict(row)
        _attach_meal_details(cur, meal)
        return meal


def actualizar_comida(meal_id: int, nombre: Optional[str] = None, category_ids: Optional[List[int]] = None, ingredient_entries: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM meals WHERE id = ?', (meal_id,))
        if not cur.fetchone():
            return None

        if nombre:
            cur.execute('UPDATE meals SET nombre = ? WHERE id = ?', (nombre, meal_id))

        if category_ids is not None:
            cur.execute('DELETE FROM meal_categories WHERE meal_id = ?', (meal_id,))
            for cat_id in category_ids:
                cur.execute(
                    'INSERT OR IGNORE INTO meal_categories (meal_id, category_id) VALUES (?, ?)',
                    (meal_id, cat_id)
                )

        if ingredient_entries is not None:
            cur.execute('DELETE FROM meal_ingredients WHERE meal_id = ?', (meal_id,))
            ingredient_map: Dict[int, Optional[str]] = {}
            for entry in ingredient_entries:
                ingredient_id = entry.get('ingredient_id')
                if not ingredient_id:
                    continue
                ingredient_map[ingredient_id] = _merge_specs(ingredient_map.get(ingredient_id), entry.get('spec'))

            for ingredient_id, spec in ingredient_map.items():
                _upsert_meal_ingredient(cur, meal_id, ingredient_id, spec)

        conn.commit()
        return obtener_comida(meal_id)


def eliminar_comida(meal_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM meals WHERE id = ?', (meal_id,))
        conn.commit()
        return cur.rowcount > 0


def obtener_comidas_por_categoria(category_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT m.id, m.nombre
            FROM meals m
            JOIN meal_categories mc ON m.id = mc.meal_id
            WHERE mc.category_id = ?
            ORDER BY m.nombre
        ''', (category_id,))
        meals = [dict(row) for row in cur.fetchall()]
        for meal in meals:
            _attach_meal_details(cur, meal)
        return meals


# ==================== MENÚ DIARIO ====================
def crear_dia_menu(mes: int, año: int, dia: int, meal_lunch_id: Optional[int], meal_dinner_id: Optional[int]) -> Dict[str, Any]:
    with get_conn() as conn:
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO daily_menu (mes, año, dia, meal_lunch_id, meal_dinner_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (mes, año, dia, meal_lunch_id, meal_dinner_id))
            conn.commit()
            return obtener_dia_menu(cur.lastrowid)
        except sqlite3.IntegrityError:
            raise ValueError(f"Ya existe un menú para {dia}/{mes}/{año}")


def listar_menu(mes: Optional[int] = None, año: Optional[int] = None) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        if mes and año:
            cur.execute('''
                SELECT id, mes, año, dia, meal_lunch_id, meal_dinner_id, created_at, updated_at
                FROM daily_menu
                WHERE mes = ? AND año = ?
                ORDER BY año, mes, dia
            ''', (mes, año))
        else:
            cur.execute('''
                SELECT id, mes, año, dia, meal_lunch_id, meal_dinner_id, created_at, updated_at
                FROM daily_menu
                ORDER BY año, mes, dia
            ''')
        
        menus = [dict(row) for row in cur.fetchall()]
        
        # Obtener comidas para cada día
        for menu in menus:
            meal_lunch = obtener_comida(menu['meal_lunch_id']) if menu['meal_lunch_id'] else None
            meal_dinner = obtener_comida(menu['meal_dinner_id']) if menu['meal_dinner_id'] else None
            menu['meal_lunch'] = meal_lunch
            menu['meal_dinner'] = meal_dinner
        
        return menus


def obtener_dia_menu(daily_menu_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, mes, año, dia, meal_lunch_id, meal_dinner_id, created_at, updated_at
            FROM daily_menu
            WHERE id = ?
        ''', (daily_menu_id,))
        row = cur.fetchone()
        if not row:
            return None
        
        menu = dict(row)
        menu['meal_lunch'] = obtener_comida(menu['meal_lunch_id']) if menu['meal_lunch_id'] else None
        menu['meal_dinner'] = obtener_comida(menu['meal_dinner_id']) if menu['meal_dinner_id'] else None
        
        return menu


def actualizar_dia_menu(daily_menu_id: int, meal_lunch_id: Optional[int] = None, meal_dinner_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM daily_menu WHERE id = ?', (daily_menu_id,))
        if not cur.fetchone():
            return None
        
        # Actualizar ambos campos en una sola query, permitiendo valores null
        cur.execute('''UPDATE daily_menu 
                     SET meal_lunch_id = ?, meal_dinner_id = ?, updated_at = CURRENT_TIMESTAMP 
                     WHERE id = ?''', 
                   (meal_lunch_id, meal_dinner_id, daily_menu_id))
        
        conn.commit()
        return obtener_dia_menu(daily_menu_id)


def eliminar_dia_menu(daily_menu_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM daily_menu WHERE id = ?', (daily_menu_id,))
        conn.commit()
        return cur.rowcount > 0
