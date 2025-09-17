# app/auth/infrastructure/persistence/database.py
"""
Módulo de configuración de la base de datos para el contexto de autenticación (auth).
Este módulo define la conexión a la base de datos, la sesión y la base declarativa
para los modelos de SQLAlchemy específicos del contexto auth.
También incluye la lógica para crear las tablas definidas en los modelos de auth.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- Configuración de la Base de Datos ---
# En una implementación real, estas URLs vendrían de variables de entorno
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")
# Para simplificar y alinearse con docker-compose.yml, usamos directamente la URL
# Nota: En docker-compose.yml definimos: DATABASE_URL: postgresql://myapp_user:myapp_password@db:5432/myapp_db
# Aquí la usamos directamente, pero en producción se recomienda usar variables de entorno.
# Se comparte la misma BD que users para este ejemplo.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myapp_user:myapp_password@db:5432/myapp_db")

# --- Creación del "engine" ---
# El engine es el punto de entrada para cualquier conexión a la BD.
# El parámetro `echo=True` es útil para desarrollo, muestra las SQL queries en la consola.
# En producción, se recomienda `echo=False`.
engine = create_engine(DATABASE_URL, echo=True) # Echo para ver queries en logs

# --- Creación de la "Base" declarativa ---
# Esta es la base para definir modelos SQLAlchemy.
# Es crucial que esta sea la MISMA instancia de Base usada por users
# para que ambos contextos compartan el metadata y las tablas se creen correctamente.
# Por lo tanto, la importamos desde el database.py de users.
# Si auth tuviera su propia BD, crearíamos una Base aquí.
try:
    # Intentamos importar Base desde users para compartir el metadata
    print("[DEBUG] Intentando importar Base desde users.infrastructure.persistence.database...")
    from app.users.infrastructure.persistence.database import Base
    print("[DEBUG] Base importada exitosamente desde users.infrastructure.persistence.database")
except ImportError as ie:
    # Si no se puede importar (por ejemplo, estructura diferente), creamos una local.
    # Esto NO es lo recomendado si comparten BD, pero lo dejamos como fallback.
    print(f"[WARNING] No se pudo importar Base desde users (ImportError: {ie}). Creando Base local para auth.")
    Base = declarative_base()
except ModuleNotFoundError as mnfe:
     print(f"[ERROR CRITICO] No se encontró el modulo al intentar importar Base desde users (ModuleNotFoundError: {mnfe}).")
     raise # Relanzar para detener la ejecución si es un error de modulo no encontrado
except Exception as e:
     print(f"[ERROR INESPERADO] Error al intentar importar Base desde users: {e}")
     raise

# --- Creación de la fábrica de sesiones ---
# sessionmaker crea una clase fábrica preconfigurada para crear nuevas Session instancias.
# `autocommit=False` significa que no se hará commit automáticamente, debemos hacerlo explícitamente.
# `autoflush=False` evita que se haga flush automáticamente antes de ciertas operaciones de query.
# `bind=engine` asocia esta fábrica con el engine que creamos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session() -> Session:
    """
    Generador de dependencias para obtener una sesión de base de datos.
    Este es un patrón común en aplicaciones FastAPI para obtener una sesión
    por solicitud de manera segura.
    
    Yields:
        Session: Una sesión de SQLAlchemy.
    """
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def create_tables():
    """
    Crea todas las tablas definidas en los modelos que heredan de Base.
    Esto se basa en las definiciones de los modelos SQLAlchemy.
    Es crucial llamar a esta función para asegurar que las tablas existan
    antes de que los consumidores intenten usarlas.
    """
    # Importamos todos los modelos aquí PARA QUE Base los conozca
    # Es crucial que este import suceda ANTES de Base.metadata.create_all()
    # para que el metadata sepa qué tablas debe crear.
    try:
        from .auth_model import TokenModel # Asegúrate de que este import sea correcto
        print(f"[DEBUG] Modelo TokenModel importado. Base.metadata.tables: {list(Base.metadata.tables.keys())}")
        
        # Ahora crea las tablas que aún no existen en la BD
        # Se basa en las definiciones de los modelos que heredan de Base.
        tables_before = list(Base.metadata.tables.keys())
        print(f"[DEBUG] Tablas antes de create_all: {tables_before}")
        
        Base.metadata.create_all(bind=engine)
        
        tables_after = list(Base.metadata.tables.keys())
        print(f"[DEBUG] Tablas después de create_all: {tables_after}")
        print("[INFO] Tablas de auth creadas (o ya existían).")
        
    except Exception as e:
        print(f"[ERROR] Fallo al crear tablas para auth: {e}")
        raise # Relanzar la excepción para que el error se propague

# --- Notas sobre la implementación ---
# 1. `DATABASE_URL`: La URL de conexión. Se comparte con users en este ejemplo.
# 2. `create_engine`: Crea el objeto engine que gestiona la conexión a la BD.
# 3. `declarative_base()`: Se importa desde users para compartir el metadata global.
#    Si auth tuviera BD separada, se crearía una Base local aquí.
# 4. `sessionmaker`: Crea una fábrica de sesiones configurada.
# 5. `get_db_session`: Un generador (generator function) que es idiomático en FastAPI
#    para manejar la creación y cierre de recursos por solicitud. Útil si auth tuviera endpoints de consulta directa.
# 6. `create_tables`: Función auxiliar para crear las tablas en la BD.
#    Es útil para inicializar la BD, pero en producción se usa Alembic para migraciones.
# 7. Dependencias: Este archivo depende completamente de SQLAlchemy.
# 8. Punto de entrada para la BD de auth: Centraliza la configuración de la BD
#    para el contexto de `auth`.
# 9. Compatibilidad con users: Al compartir `Base`, se asegura que las tablas
#    de ambos contextos se gestionen correctamente dentro de la misma BD.