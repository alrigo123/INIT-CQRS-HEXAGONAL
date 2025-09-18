# app/users/infrastructure/persistence/user_model.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

# --- Importar Base desde database.py ---
# Esta es la clave: usamos la MISMA Base definida en database.py
# Esto asegura que todos los modelos compartan el mismo metadata
from .database import Base

class UserModel(Base):
    """
    Modelo de SQLAlchemy para la tabla 'users' en el contexto de usuarios.
    
    Este modelo es un ADAPTADOR que mapea la entidad de dominio User
    a una tabla en la base de datos relacional.
    
    PATRÓN DE DISEÑO: Data Transfer Object (DTO) / Active Record
    Actúa como puente entre el modelo de dominio y la base de datos.
    
    ARQUITECTURA: Parte de la capa de infraestructura
    Específicamente el adaptador de persistencia.
    """
    
    # Nombre de la tabla en la base de datos
    # Este es el nombre físico que tendrá la tabla
    __tablename__ = 'users'

    # Columnas de la tabla
    # Cada atributo se convierte en una columna en la BD
    
    # ID del usuario como UUID
    # UUID(as_uuid=True) permite usar objetos uuid.UUID en Python
    # primary_key=True: Define esta columna como clave primaria
    # default=uuid.uuid4: Genera automáticamente un UUID nuevo para cada registro
    # MEJORA SUGERIDA: Considerar usar UUID nativo de PostgreSQL para mejor performance
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Nombre del usuario
    # String(255): VARCHAR(255) en PostgreSQL
    # nullable=False: No permite valores NULL (campo obligatorio)
    name = Column(String(255), nullable=False)
    
    # Email del usuario
    # unique=True: Crea constraint UNIQUE en la BD
    # nullable=False: Campo obligatorio
    # index=True: Crea índice automático para búsquedas rápidas
    # MEJORA SUGERIDA: Considerar índice compuesto si hay búsquedas por múltiples campos
    email = Column(String(255), unique=True, nullable=False, index=True)
    
    # Contraseña hasheada
    # Almacenamos solo el hash, nunca la contraseña en texto plano
    # nullable=False: Campo obligatorio
    hashed_password = Column(String(255), nullable=False)
    
    # Fecha de creación
    # default=datetime.utcnow: Valor por defecto es la fecha/hora actual
    # nullable=False: Campo obligatorio
    # MEJORA SUGERIDA: Considerar campo updated_at para auditoría
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        """
        Representación en string del objeto para debugging.
        """
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

# Rol en la Arquitectura
# Modelo de persistencia: Adaptador que mapea entidades de dominio a tablas
# Sin lógica de negocio: Solo estructura y constraints de la base de datos
# Tipos específicos: Utiliza UUID, DateTime y otros tipos de PostgreSQL
# Índices y constraints: Optimiza búsquedas y garantiza integridad
# Adaptador de infraestructura: Conecta dominio con base de datos relacional