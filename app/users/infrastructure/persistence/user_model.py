from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

# --- Importar Base desde database.py ---
# Usamos la MISMA Base definida en database.py
from .database import Base

class UserModel(Base):
    """
    Modelo de SQLAlchemy para la tabla 'users' en el contexto de usuarios.
    Este modelo es un ADAPTADOR que mapea la entidad de dominio User
    a una tabla en la base de datos relacional.
    """

    # Nombre de la tabla en la base de datos
    __tablename__ = 'users'

    # Columnas de la tabla
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        """
        Representación en string del objeto para debugging.
        """
        return f"<UserModel(id='{self.id}', name='{self.name}', email='{self.email}')>"

# --- Notas sobre la implementación ---
# `Base`: Importada desde `database.py` para compartir el metadata global.
# Sin lógica de negocio: Solo mapeo de datos.
# `__repr__`: Método para facilitar debugging.

# Rol en la Arquitectura
# Modelo de persistencia: Adaptador que mapea entidades de dominio a tablas
# Sin lógica de negocio: Solo estructura y constraints de la base de datos
# Tipos específicos: Utiliza UUID, DateTime y otros tipos de PostgreSQL
# Índices y constraints: Optimiza búsquedas y garantiza integridad
# Adaptador de infraestructura: Conecta dominio con base de datos relacional