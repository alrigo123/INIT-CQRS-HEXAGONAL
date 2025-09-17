# app/users/infrastructure/persistence/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "postgresql://myapp_user:myapp_password@db:5432/myapp_db"

engine = create_engine(DATABASE_URL, echo=True)

# --- Definición centralizada de Base ---
# Esta es la ÚNICA definición de Base en este contexto
Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session() -> Session:
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def create_tables():
    """
    Crea todas las tablas definidas en los modelos que heredan de Base.
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

# Exportamos Base para que user_model.py pueda importarla
__all__ = ['Base', 'engine', 'SessionLocal', 'get_db_session', 'create_tables']