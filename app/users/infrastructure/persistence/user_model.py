# app/users/infrastructure/persistence/user_model.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
# --- Importar Base desde database.py ---
# Esta es la clave: usamos la MISMA Base definida en database.py
from .database import Base

class UserModel(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<UserModel(id='{self.id}', name='{self.name}', email='{self.email}')>"