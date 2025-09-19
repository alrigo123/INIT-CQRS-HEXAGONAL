import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- Configuración de Base de Datos ---
DATABASE_URL = "postgresql://myapp_user:myapp_password@db:5432/myapp_db"  # URL de conexión a PostgreSQL
engine = create_engine(DATABASE_URL, echo=True)  # Crear el motor de SQLAlchemy

# --- Definición centralizada de Base ---
# Todas las tablas heredarán de esta clase base
Base = declarative_base()

# Crear el sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """ Generador que proporciona sesiones de base de datos. """
    db_session = SessionLocal() # Crear una nueva sesión del pool
    try:
        yield db_session # Permite que FastAPI use la sesión

    finally:
        # Asegurar que la sesión se cierre siempre
        db_session.close()


def create_tables():
    """
    Crea todas las tablas definidas en los modelos que heredan de Base.
    Este método asegura que la estructura de la base de datos
    esté sincronizada con los modelos definidos.
    """
    try:
        from .user_model import UserModel # Importamos el modelo
        print(f"[DEBUG] Modelo UserModel importado. Base.metadata.tables: {list(Base.metadata.tables.keys())}")
        tables_before = list(Base.metadata.tables.keys()) # Crea las tablas
        print(f"[DEBUG] Tablas antes de create_all: {tables_before}")
        Base.metadata.create_all(bind=engine)
        tables_after = list(Base.metadata.tables.keys())
        print(f"[DEBUG] Tablas después de create_all: {tables_after}")
        print("[INFO] Tablas creadas (o ya existían).")
    except Exception as e:
        print(f"[ERROR] Fallo al crear tablas: {e}")
        raise


# Exportamos elementos importantes para que otros módulos puedan importarlos
__all__ = ["Base", "engine", "SessionLocal", "get_db_session", "create_tables"]

# Rol en la Arquitectura
# Adaptador de persistencia: Configura conexión con base de datos PostgreSQL
# Gestión de sesiones: Proporciona mecanismos para manejar transacciones
# Configuración centralizada: Única fuente de verdad para conexión a BD
# Inyección de dependencias: Facilita la inyección de sesiones en endpoints
# Resiliencia: Configura pool de conexiones para mejor performance
