from .db import get_conn
import sqlite3
from typing import List, Optional, Dict, Any


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


# ==================== COMIDAS ====================
def crear_comida(nombre: str, precio: float, category_ids: List[int]) -> Dict[str, Any]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO meals (nombre, precio) VALUES (?, ?)',
            (nombre, precio)
        )
        conn.commit()
        meal_id = cur.lastrowid
        
        # Añadir categorías
        for cat_id in category_ids:
            cur.execute(
                'INSERT OR IGNORE INTO meal_categories (meal_id, category_id) VALUES (?, ?)',
                (meal_id, cat_id)
            )
        conn.commit()
        
        return obtener_comida(meal_id)


def listar_comidas() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre, precio FROM meals ORDER BY nombre')
        meals = [dict(r) for r in cur.fetchall()]
        
        # Obtener categorías para cada comida
        for meal in meals:
            cur.execute('''
                SELECT c.id, c.nombre
                FROM categories c
                JOIN meal_categories mc ON c.id = mc.category_id
                WHERE mc.meal_id = ?
            ''', (meal['id'],))
            meal['categories'] = [dict(row) for row in cur.fetchall()]
        
        return meals


def obtener_comida(meal_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, nombre, precio FROM meals WHERE id = ?', (meal_id,))
        row = cur.fetchone()
        if not row:
            return None
        
        meal = dict(row)
        cur.execute('''
            SELECT c.id, c.nombre
            FROM categories c
            JOIN meal_categories mc ON c.id = mc.category_id
            WHERE mc.meal_id = ?
        ''', (meal_id,))
        meal['categories'] = [dict(row) for row in cur.fetchall()]
        
        return meal


def actualizar_comida(meal_id: int, nombre: Optional[str] = None, precio: Optional[float] = None, category_ids: Optional[List[int]] = None) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT id FROM meals WHERE id = ?', (meal_id,))
        if not cur.fetchone():
            return None
        
        if nombre:
            cur.execute('UPDATE meals SET nombre = ? WHERE id = ?', (nombre, meal_id))
        
        if precio is not None:
            cur.execute('UPDATE meals SET precio = ? WHERE id = ?', (precio, meal_id))
        
        if category_ids is not None:
            # Eliminar categorías existentes
            cur.execute('DELETE FROM meal_categories WHERE meal_id = ?', (meal_id,))
            # Añadir nuevas categorías
            for cat_id in category_ids:
                cur.execute(
                    'INSERT OR IGNORE INTO meal_categories (meal_id, category_id) VALUES (?, ?)',
                    (meal_id, cat_id)
                )
        
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
            SELECT m.id, m.nombre, m.precio
            FROM meals m
            JOIN meal_categories mc ON m.id = mc.meal_id
            WHERE mc.category_id = ?
            ORDER BY m.nombre
        ''', (category_id,))
        meals = [dict(row) for row in cur.fetchall()]
        
        # Obtener categorías para cada comida
        for meal in meals:
            cur.execute('''
                SELECT c.id, c.nombre
                FROM categories c
                JOIN meal_categories mc ON c.id = mc.category_id
                WHERE mc.meal_id = ?
            ''', (meal['id'],))
            meal['categories'] = [dict(row) for row in cur.fetchall()]
        
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
