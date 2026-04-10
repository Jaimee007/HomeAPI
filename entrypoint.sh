#!/usr/bin/env bash
set -e

DATA_DIR="/data"
DB_FILE="$DATA_DIR/home_menu.db"

mkdir -p "$DATA_DIR"
# Ajusta propietario si quieres ejecutar como UID 1000 dentro del contenedor
chown -R 1000:1000 "$DATA_DIR" || true
chmod -R 755 "$DATA_DIR" || true

# Opcional: crear DB vacía si no existe (la app también puede hacerlo)
if [ ! -f "$DB_FILE" ]; then
  touch "$DB_FILE"
  chown 1000:1000 "$DB_FILE" || true
fi

exec "$@"
