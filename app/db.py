import sqlite3
from contextlib import contextmanager
import os
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "home_menu.db"
DB_PATH = Path(os.getenv("DB_PATH", DEFAULT_DB))


def init_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    
    # Tabla de categorías
    cur.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de comidas
    cur.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de relación entre comidas y categorías (muchos a muchos)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS meal_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            UNIQUE(meal_id, category_id)
        )
    ''')
    
    # Tabla de menú diario (asignación de comidas a días)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS daily_menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes INTEGER NOT NULL,
            año INTEGER NOT NULL,
            dia INTEGER NOT NULL,
            meal_lunch_id INTEGER,
            meal_dinner_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meal_lunch_id) REFERENCES meals(id) ON DELETE SET NULL,
            FOREIGN KEY (meal_dinner_id) REFERENCES meals(id) ON DELETE SET NULL,
            UNIQUE(mes, año, dia)
        )
    ''')
    
    # Insertar categorías predefinidas
    cur.execute('SELECT COUNT(*) FROM categories')
    if cur.fetchone()[0] == 0:
        default_categories = [
            ('Saludable', 'Comidas bajas en calorías y nutritivas'),
            ('Rápida', 'Comidas que se preparan rápidamente'),
            ('Vegetariana', 'Comidas sin carne'),
            ('Postres', 'Postres y dulces'),
            ('Carnes', 'Platos con carne'),
            ('Pescado', 'Platos con pescado'),
        ]
        cur.executemany('INSERT INTO categories (nombre, descripcion) VALUES (?, ?)', default_categories)
    
    conn.commit()
    conn.close()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
