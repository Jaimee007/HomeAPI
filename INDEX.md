# 📚 HomeAPI - Índice de Documentación

Bienvenido a **HomeAPI**, tu gestor de menú semanal. Aquí encontrarás todo lo que necesitas.

---

## 🚀 Quiero Empezar Ahora

### Opción A: La Más Rápida (5 minutos)
👉 **Lee:** [QUICK_START.md](QUICK_START.md)

```powershell
.\run-api.ps1
```

Luego abre: `file:///c:/Git/HomeAPI/index.html`

### Opción B: Hacer Doble Click (Aún Más Rápido)
👉 Haz doble click en: **START.bat**

El script automáticamente:
- Instala dependencias
- Ejecuta la API
- Abre la web en tu navegador

---

## 📖 Documentación Detallada

### Para Usuarios
- **[QUICK_START.md](QUICK_START.md)** - Cómo empezar rápidamente
- **[SETUP_LOCAL.md](SETUP_LOCAL.md)** - Guía completa de instalación y desarrollo local
- **[FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)** - Cómo usar la interfaz web

### Para Desarrolladores
- **[README.md](README.md)** - Documentación de la API con instrucciones Docker
- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Estado actual del proyecto
- **[API_EXAMPLES.md](API_EXAMPLES.md)** - Ejemplos de requests a la API

---

## 🎯 Casos de Uso Comunes

### "Quiero probar todo en mi PC"
👉 [QUICK_START.md](QUICK_START.md) → Sección "Opción Más Fácil"

### "Quiero entender cómo funciona"
👉 [SETUP_LOCAL.md](SETUP_LOCAL.md) → Lee todo

### "Tengo un error"
👉 [SETUP_LOCAL.md](SETUP_LOCAL.md) → Sección "Solucionar Problemas"

### "Quiero desplegar a producción"
👉 [SETUP_LOCAL.md](SETUP_LOCAL.md) → Sección "Cuando estés listo para producción"

### "Quiero usar la API desde otro programa"
👉 [SETUP_LOCAL.md](SETUP_LOCAL.md) → Sección "Testear la API"

---

## 📁 Estructura del Proyecto

```
HomeAPI/
├── 📄 index.html                    ← WEB (abre en navegador)
├── 
├── 📂 app/                          ← BACKEND (API FastAPI)
│   ├── main.py
│   ├── schemas.py
│   ├── crud.py
│   ├── db.py
│   └── routers/
│       ├── categories.py
│       ├── meals.py
│       └── daily_menu.py
│
├── 📂 data/
│   └── home_menu.db                 ← Base de datos SQLite
│
├── requirements.txt                 ← Dependencias Python
├── Dockerfile                       ← Para Docker
├── docker-compose.yml               ← Orquestación Docker
├── run-api.ps1                      ← Script PowerShell de inicio
├── START.bat                        ← Doble click para iniciar
├── venv/                            ← Entorno virtual (se crea automáticamente)
│
└── 📚 DOCUMENTACIÓN
    ├── README.md
    ├── QUICK_START.md               ← COMIENZA AQUÍ
    ├── SETUP_LOCAL.md
    ├── FRONTEND_GUIDE.md
    ├── SETUP_COMPLETE.md
    ├── API_EXAMPLES.md
    └── INDEX.md                     ← Este archivo
```

---

## 🔧 Requisitos

- **Windows 10/11** (el proyecto usa scripts .bat/.ps1)
- **Python 3.11+** (se descargará automáticamente si no lo tienes)
- **Navegador moderno** (Chrome, Firefox, Edge, Safari)
- **Conexión a internet** (para la primera instalación)

Para Docker:
- **Docker Desktop** (opcional, para producción)

---

## 💡 Preguntas Frecuentes

### P: ¿Dónde guarda los datos?
R: En `data/home_menu.db` (base de datos SQLite local)

### P: ¿Puedo cambiar la API Key?
R: Sí, edita `app/main.py` o `index.html`. Lee [SETUP_LOCAL.md](SETUP_LOCAL.md) para más detalles.

### P: ¿Cómo despliego a producción?
R: Lee [SETUP_LOCAL.md](SETUP_LOCAL.md) → Sección "Cuando estés listo para producción"

### P: ¿La web se conectará automáticamente a homeapi.beadpaws.es?
R: Sí, el `index.html` detecta automáticamente si estás en localhost o en producción.

### P: ¿Puedo usar la API desde otra aplicación?
R: Sí, la API está en `http://localhost:8000` (dev) o `https://homeapi.beadpaws.es` (prod)

### P: ¿Dónde está la documentación de la API?
R: En `http://localhost:8000/docs` (Swagger interactivo)

---

## 🚀 Pasos Rápidos

```bash
# 1. Abre PowerShell en la carpeta HomeAPI
cd c:\Git\HomeAPI

# 2. Ejecuta la API
.\run-api.ps1

# 3. Abre el navegador
# file:///c:/Git/HomeAPI/index.html

# 4. ¡Empieza a planificar tu menú!
```

---

## 📞 Soporte

Si algo no funciona:
1. Lee [SETUP_LOCAL.md](SETUP_LOCAL.md) → Sección "Solucionar Problemas"
2. Verifica que `http://localhost:8000/docs` esté accesible
3. Comprueba los logs en la ventana de PowerShell

---

## 📝 Notas de Desarrollo

**Última actualización:** Abril 11, 2026

**Versión:** 2.0

**Cambios principales:**
- ✅ Agregado campo `precio` a comidas
- ✅ Eliminada descripción de categorías
- ✅ Eliminados timestamps de comidas
- ✅ Interfaz web completa con calendario
- ✅ Detección automática de URL de API

**Próximas mejoras:**
- [ ] Editar recetas existentes
- [ ] Duplicar menú semanal
- [ ] Exportar a PDF
- [ ] Búsqueda avanzada
- [ ] Sincronización en la nube

---

## ✨ ¡Listo!

**Comienza aquí:** [QUICK_START.md](QUICK_START.md)

O haz doble click en **START.bat** para hacerlo todo automáticamente.

¡Disfruta organizando tu menú semanal! 🍽️📅
