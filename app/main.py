# app/main.py
from fastapi import FastAPI
# Importamos el router de users v1
from .users.infrastructure.api.v1.routes import router as users_router
# Importamos la función para crear tablas de la BD
from .users.infrastructure.persistence.database import create_tables


# Importamos el router de auth v1
from .auth.infrastructure.api.v1.routes import router as auth_router

# --- Creación de la instancia de la aplicación ---
app = FastAPI(
    title="Backend Hexagonal CQRS API",
    description="API de ejemplo siguiendo Arquitectura Hexagonal y CQRS con FastAPI, SQLAlchemy y RabbitMQ.",
    version="1.0.0",
    # openapi_url="/api/v1/openapi.json" # Puedes personalizar la ruta de la especificación OpenAPI
)

# --- Eventos de Ciclo de Vida ---

@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación.
    Ideal para inicializaciones que deben ocurrir una sola vez.
    """
    print("Iniciando la aplicación...")
    # Crear las tablas en la base de datos si no existen
    # Nota: En producción, se recomienda usar Alembic para migraciones.
    create_tables()
    print("Aplicación iniciada. Tablas creadas (si no existían).")

# @app.on_event("shutdown")
# async def shutdown_event():
#     """
#     Evento que se ejecuta al detener la aplicación.
#     Ideal para limpiar recursos.
#     """
#     print("Deteniendo la aplicación...")
#     # Aquí se podrían cerrar conexiones, limpiar caches, etc.
#     print("Aplicación detenida.")

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
    return {"message": "¡Bienvenido a la API Backend Hexagonal CQRS Clenad code y SOLID y ahora Rabbit!", "version": "1.0.1"}

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