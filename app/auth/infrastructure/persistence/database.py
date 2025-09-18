# app/auth/infrastructure/persistence/database.py
"""
Módulo de configuración de la base de datos para el contexto de autenticación (auth).
Este módulo define la conexión a la base de datos, la sesión y la base declarativa
para los modelos de SQLAlchemy específicos del contexto auth.
También incluye la lógica para crear las tablas definidas en los modelos de auth.
"""
import os
from sqlalchemy import create_engine
# Importamos declarative_base por si necesitamos crear una local
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- Configuración de la Base de Datos ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myapp_user:myapp_password@db:5432/myapp_db")

# --- Creación del "engine" ---
engine = create_engine(DATABASE_URL, echo=True)

# --- Inicialización de Base ---
# Inicializamos Base como None. Se intentará importar o crear.
Base = None

# --- Intento de importar Base desde users ---
try:
    # Intentamos importar Base desde users para compartir el metadata
    print("[DEBUG] Intentando importar Base desde users.infrastructure.persistence.database...")
    from app.users.infrastructure.persistence.database import Base as UsersBase
    Base = UsersBase
    print("[DEBUG] Base importada exitosamente desde users.infrastructure.persistence.database")
except ImportError as ie:
    print(f"[WARNING] No se pudo importar Base desde users (ImportError: {ie}). Creando Base local para auth.")
    Base = declarative_base()
except ModuleNotFoundError as mnfe:
    print(f"[ERROR CRITICO] No se encontró el modulo al intentar importar Base desde users (ModuleNotFoundError: {mnfe}).")
    # No relanzamos inmediatamente, intentamos crear una local
    Base = declarative_base()
    # O podrías relanzar si prefieres que falle aquí: raise
except Exception as e:
    print(f"[ERROR INESPERADO] Error al intentar importar Base desde users: {e}. Creando Base local para auth.")
    Base = declarative_base()
    # O podrías relanzar si prefieres que falle aquí: raise

# --- Verificación final de Base ---
if Base is None:
    print("[ERROR CRITICO] Base no se pudo definir correctamente.")
    raise RuntimeError("No se pudo establecer la instancia de Base para SQLAlchemy en auth.")

# --- Creación de la fábrica de sesiones ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session() -> Session:
    """
    Generador de dependencias para obtener una sesión de base de datos.
    """
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def create_tables():
    """
    Crea todas las tablas definidas en los modelos que heredan de Base.
    """
    try:
        # Importamos el modelo para que se registre en Base.metadata
        from .auth_model import TokenModel
        print(f"[DEBUG] Modelo TokenModel importado para create_tables. Tablas conocidas: {list(Base.metadata.tables.keys())}")

        tables_before = list(Base.metadata.tables.keys())
        print(f"[DEBUG] Tablas antes de create_all: {tables_before}")

        # Crea las tablas que aún no existen
        Base.metadata.create_all(bind=engine)

        tables_after = list(Base.metadata.tables.keys())
        print(f"[DEBUG] Tablas después de create_all: {tables_after}")
        print("[INFO] Tablas de auth creadas (o ya existían).")

    except Exception as e:
        print(f"[ERROR] Fallo al crear tablas para auth: {e}")
        raise

# --- Notas sobre la implementación ---
# 1. Se inicializa `Base = None` para tener un punto de control.
# 2. El bloque `try...except` maneja diferentes tipos de errores de importación.
# 3. Se crea una `Base` local (`declarative_base()`) como fallback en varios casos de error.
# 4. Se agrega una verificación final `if Base is None` para asegurar que siempre haya una `Base`.
# 5. La importación del modelo en `create_tables` sigue siendo crucial.