from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

# Importamos Base desde la infraestructura compartida
from app.users.infrastructure.persistence.database import Base

class TokenModel(Base):
    """
    Modelo de SQLAlchemy para la tabla 'tokens' en el contexto de autenticación.
    Este modelo es un adaptador que mapea la entidad de dominio Token
    a una tabla en la base de datos relacional.
    """
    __tablename__ = 'tokens'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False) # FK implícita
    access_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<TokenModel(id='{self.id}', user_id='{self.user_id}', expires_at='{self.expires_at}')>"



# --- Notas sobre la implementación ---
# 1. `Base`: Reutilizamos la Base de users para estar en la misma metadata.
# 2. `__tablename__`: Nombre de la tabla en la BD.
# 3. `Column`, `String`, `DateTime`, `UUID`: Tipos de datos de SQLAlchemy.
# 4. `primary_key=True`: Define la clave primaria.
# 5. `unique=True` y `index=True` en `access_token`: Para búsquedas rápidas y unicidad.
# 6. `nullable=False`: Campos obligatorios.
# 7. `default=`: Valor por defecto para `created_at`.
# 8. Sin lógica de negocio: Solo mapeo de datos.