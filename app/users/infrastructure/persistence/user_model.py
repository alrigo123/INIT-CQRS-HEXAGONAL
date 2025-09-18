# app/users/infrastructure/persistence/user_model.py
# Eliminamos la importacion no usada
# from sqlalchemy import Column, String, DateTime, UUID # Linea eliminada
from sqlalchemy import Column, String, DateTime # UUID viene de postgresql
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
# --- Importar Base desde database.py ---
# Esta es la clave: usamos la MISMA Base definida en database.py
from .database import Base
# Eliminamos la importacion no usada
# from app.users.domain.models import User as DomainUser # Linea eliminada

class UserModel(Base):
    """
    Modelo de SQLAlchemy para la tabla 'users' en el contexto de usuarios.
    Este modelo es un adaptador que mapea la entidad de dominio User
    a una tabla en la base de datos relacional.
    """
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserModel(id='{self.id}', name='{self.name}', email='{self.email}')>"

# --- Notas sobre la implementación ---
# 1. `Base`: Importada desde `database.py` para compartir el metadata global.
# 2. `__tablename__`: Nombre de la tabla en la BD.
# 3. `Column`, `String`, `DateTime`, `UUID`: Tipos de datos de SQLAlchemy.
# 4. `primary_key=True`: Define la clave primaria.
# 5. `unique=True` y `index=True` en `email`: Para unicidad y búsquedas rápidas.
# 6. `nullable=False`: Campos obligatorios.
# 7. `default=`: Valor por defecto para `created_at` y `id`.
# 8. Sin lógica de negocio: Solo mapeo de datos.
# 9. `__repr__`: Método mágico para facilitar debugging.