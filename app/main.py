# APP
from fastapi import FastAPI

# ROUTES
from .users.infrastructure.api.v1.routes import router as users_router
from .auth.infrastructure.api.v1.routes import router as auth_router

# Importamos la función para crear tablas de la BD
from .users.infrastructure.persistence.database import create_tables


# --- Creación de la instancia de la aplicación ---
app = FastAPI(title="INIT Backend Hexagonal CQRS")

# --- Eventos de Ciclo de Vida ---
@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación.
    """
    print("Iniciando la aplicación...")
    # Crear las tablas en la base de datos si no existen
    create_tables()
    print("Aplicación iniciada. Tablas creadas (si no existían).")

# --- Inclusión de Routers ---

# Incluimos el router de users v1 bajo un prefijo de API
# Esto significa que los endpoints definidos en users_router
# estarán disponibles en /api/v1/users/...
app.include_router(users_router, prefix="/api/v1")
# Incluimos el router de auth v1
app.include_router(auth_router, prefix="/api/v1")

# --- Rutas de prueba o health check (opcional) ---


@app.get("/")
async def root():
    """
    Endpoint raíz para verificar que la API está funcionando.
    """
    return {
        "message": "¡Bienvenido a la API Backend Hexagonal CQRS Clenad code y SOLID y ahora Rabbit!",
        "version": "1.0.1",
    }


@app.get("/health")
async def health_check():
    """
    Endpoint de health check básico.
    """
    return {"status": "ok"}


# --- Notas sobre la implementación ---
# 1. `FastAPI()`: Crea la instancia principal de la aplicación.
# 2. Parámetros de `FastAPI`: title, description, version mejoran la documentación automática.
# 3. `@app.on_event("startup")`: Decorador para ejecutar código al iniciar la app.
#    `create_tables()` se llama aquí para asegurar que la BD esté lista.
# 4. `app.include_router()`: Método para incluir routers de diferentes módulos/contexts.
#    El `prefix="/api/v1"` agrupa todos los endpoints de users bajo /api/v1/.
# 5. `users_router`: El router definido en `routes.py`. Se le da un alias `router` al importarlo.
# 6. Endpoints raíz y de health check: Útiles para monitoreo y verificación básica.
# 7. Independencia: Este archivo no contiene lógica de negocio, solo ensambla componentes.
# 8. Punto de entrada: `uvicorn app.main:app --host 0.0.0.0 --port 8000` apunta a `app` en este módulo.
