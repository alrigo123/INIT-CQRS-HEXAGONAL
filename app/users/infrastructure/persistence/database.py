# app/users/infrastructure/persistence/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- Configuración de Base de Datos ---
# URL de conexión a PostgreSQL
# MEJORA SUGERIDA: Usar variables de entorno para diferentes ambientes
# MEJORA SUGERIDA: No hardcodear credenciales en el código
DATABASE_URL = "postgresql://myapp_user:myapp_password@db:5432/myapp_db"

# Crear el motor de SQLAlchemy
# echo=True muestra todas las consultas SQL en consola (útil para debugging)
# En producción, considerar echo=False para mejor performance
engine = create_engine(DATABASE_URL, echo=True)

# --- Definición centralizada de Base ---
# Esta es la ÚNICA definición de Base en este contexto
# Todas las tablas heredarán de esta clase base
Base = declarative_base()

# Crear el sessionmaker
# autocommit=False: No hacer commit automático (control manual)
# autoflush=False: No hacer flush automático (control manual)
# bind=engine: Asociar con el motor de base de datos creado
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session() -> Session:
    """
    Generador que proporciona sesiones de base de datos.
    
    PATRÓN DE DISEÑO: Dependency Injection con Generadores
    FastAPI puede inyectar automáticamente estas sesiones en endpoints.
    
    Uso típico:
    def endpoint(db: Session = Depends(get_db_session)):
        # usar db aquí
        pass
    """
    # Crear una nueva sesión del pool
    db_session = SessionLocal()
    try:
        # Yield permite que FastAPI use la sesión
        yield db_session
    finally:
        # Asegurar que la sesión se cierre siempre
        # Esto libera la conexión de vuelta al pool
        db_session.close()

def create_tables():
    """
    Crea todas las tablas definidas en los modelos que heredan de Base.
    
    Este método asegura que la estructura de la base de datos
    esté sincronizada con los modelos definidos.
    
    MEJORA SUGERIDA: Usar migraciones (Alembic) en lugar de create_all
    en entornos de producción para mejor control de cambios.
    """
    # Importamos todos los modelos aquí PARA QUE Base los conozca
    # Es crucial que este import suceda ANTES de Base.metadata.create_all()
    try:
        from .user_model import UserModel
        print(f"[DEBUG] Modelo UserModel importado. Base.metadata.tables: {list(Base.metadata.tables.keys())}")
        # Ahora crea las tablas
        tables_before = list(Base.metadata.tables.keys())
        print(f"[DEBUG] Tablas antes de create_all: {tables_before}")
        Base.metadata.create_all(bind=engine)
        tables_after = list(Base.metadata.tables.keys())
        print(f"[DEBUG] Tablas después de create_all: {tables_after}")
        print("[INFO] Tablas creadas (o ya existían).")
    except Exception as e:
        print(f"[ERROR] Fallo al crear tablas: {e}")
        raise

# Exportamos elementos importantes para que otros módulos puedan importarlos
__all__ = ['Base', 'engine', 'SessionLocal', 'get_db_session', 'create_tables']

# Rol en la Arquitectura
# Adaptador de persistencia: Configura conexión con base de datos PostgreSQL
# Gestión de sesiones: Proporciona mecanismos para manejar transacciones
# Configuración centralizada: Única fuente de verdad para conexión a BD
# Inyección de dependencias: Facilita la inyección de sesiones en endpoints
# Resiliencia: Configura pool de conexiones para mejor performance