from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import os

from .db import init_database
from .routers import categories, meals, daily_menu

# Inicializar base de datos
init_database()

app = FastAPI(
    title="Home API - Gestor de Menú Semanal",
    description="API para gestionar comidas, cenas y menú semanal",
    version="1.0.0"
)

# API Key para autenticación (puede ser modificada por variable de entorno)
API_KEY = os.getenv("API_KEY", "homeapi_default_key_2024")


# Middleware de autenticación por API Key
class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Endpoints públicos que no requieren autenticación
        public_endpoints = ["/docs", "/openapi.json", "/redoc", "/"]
        
        if any(request.url.path.startswith(endpoint) for endpoint in public_endpoints):
            return await call_next(request)
        
        # Verificar API Key
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key invalida o no proporcionada",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return await call_next(request)


# Configurar middleware
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(categories.router)
app.include_router(meals.router)
app.include_router(daily_menu.router)


@app.get("/", tags=["root"])
def root():
    """Endpoint raíz de la API"""
    return {
        "mensaje": "Bienvenido a Home API - Gestor de Menú Semanal",
        "documentacion": "/docs",
        "version": "1.0.0"
    }
