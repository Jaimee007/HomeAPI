import sqlite3
from contextlib import contextmanager
import os
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "home_menu.db"
DB_PATH = Path(os.getenv("DB_PATH", DEFAULT_DB))


def _create_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _create_connection()
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

    # Tabla de ingredientes
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
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

    # Tabla de relación entre comidas e ingredientes
    cur.execute('''
        CREATE TABLE IF NOT EXISTS meal_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_id INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            spec TEXT,
            FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
            UNIQUE(meal_id, ingredient_id)
        )
    ''')

    # Tabla de pasos de receta
    cur.execute('''
        CREATE TABLE IF NOT EXISTS meal_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL,
            texto TEXT NOT NULL,
            FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE,
            UNIQUE(meal_id, step_order)
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
    
    # Tabla de eventos publicados en Google Calendar.
    # Se indexa por fecha + franja (no por daily_menu_id) para que el mapeo
    # sobreviva al borrado y recreacion de la fila de daily_menu.
    cur.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes INTEGER NOT NULL,
            año INTEGER NOT NULL,
            dia INTEGER NOT NULL,
            slot TEXT NOT NULL,
            google_event_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(mes, año, dia, slot)
        )
    ''')

    # Cola de sincronizacion (outbox). Cada fila dice "esta fecha/franja esta
    # sucia", no que operacion hacer: el worker relee el estado actual y decide
    # crear, actualizar o borrar. Asi es idempotente y se puede reintentar.
    cur.execute('''
        CREATE TABLE IF NOT EXISTS calendar_sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes INTEGER NOT NULL,
            año INTEGER NOT NULL,
            dia INTEGER NOT NULL,
            slot TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            next_attempt_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(mes, año, dia, slot)
        )
    ''')

    # Insertar categorías predefinidas
    cur.execute('SELECT COUNT(*) FROM categories')
    if cur.fetchone()[0] == 0:
        default_categories = [
            ('Saludable',),
            ('Rápida',),
            ('Vegetariana',),
            ('Postres',),
            ('Carnes',),
            ('Pescado',),
        ]
        cur.executemany('INSERT INTO categories (nombre) VALUES (?)', default_categories)
    
    conn.commit()
    conn.close()


@contextmanager
def get_conn():
    conn = _create_connection()
    try:
        yield conn
    finally:
        conn.close()
