# APP
from fastapi import FastAPI

# ROUTES
from .users.infrastructure.api.v1.routes import router as users_router
from .auth.infrastructure.api.v1.routes import router as auth_router

# Importamos la función para crear tablas de la BD
from .users.infrastructure.persistence.database import create_tables as users_create_tables
from .auth.infrastructure.persistence.database import create_tables as auth_create_tables

app = FastAPI(title="INIT Backend Hexagonal CQRS") # Creación de la instancia de la aplicación

# --- Evento de Ciclo de Vida ---
@app.on_event("startup")
async def startup_event():
    """ Evento que se ejecuta al iniciar la aplicación. """
    print("Iniciando la aplicación...")
    # Crear las tablas en la base de datos si no existen
    users_create_tables()
    auth_create_tables()
    print("Aplicación iniciada. Tablas creadas (si no existían).")

# --- Inclusión de Routers Endpoints ---
app.include_router(users_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

# --- Endpoints utilitarios (health / root) ---
@app.get("/")
async def root():
    """ Endpoint raíz para verificar que la API está funcionando. """
    return { "message": "¡Bienvenido a INIT Backend Hexagonal CQRS Clenad code y SOLID y ahora Rabbit!" }

@app.get("/health")
async def health_check():
    """ Endpoint de health check básico. """
    return {"status": "ok"}


# --- Notas sobre la implementación ---
# Independencia: Este archivo no contiene lógica de negocio, solo ensambla componentes.