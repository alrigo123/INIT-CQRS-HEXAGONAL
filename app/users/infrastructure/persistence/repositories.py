# PUERTO SECUNDARIO
from sqlalchemy.orm import Session
from typing import Optional

# Importamos la interfaz del repositorio del dominio
from ...domain.repositories import UserRepository # ABSTRACCIÓN
# Importamos la entidad de dominio
from ...domain.models import User # MODELO DE DOMINIO
# Importamos el modelo de SQLAlchemy
from .user_model import UserModel #ADAPTADOR

class SQLAlchemyUserRepository(UserRepository):
    """
    Implementación concreta del UserRepository usando SQLAlchemy.
    Esta clase es un ADAPTADOR que implementa la interfaz abstracta UserRepository
    usando SQLAlchemy como tecnología de persistencia específica.
    """

    def __init__(self, db_session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.
        La sesión se inyecta para facilitar testing y separación de concerns.
        """
        # Almacenamos la sesión inyectada para usarla en las operaciones
        self._db_session = db_session


    def save(self, user: User) -> None:
        """
        Guarda un usuario en la base de datos.
        IMPLEMENTACIÓN DEL PUERTO SECUNDARIO: Traduce del modelo de dominio al modelo de persistencia.
        Raises: RuntimeError: Si hay un error al guardar el usuario en la base de datos.
        """
 
        # Traducción entre capas: dominio -> persistencia
        user_model = UserModel(
            id=user.id,  # El ID ya fue generado en el handler
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            # created_at se establece por defecto en el modelo
        )
        
        # Agregar el modelo a la sesión de SQLAlchemy
        self._db_session.add(user_model)
        
        # Commit para persistir los cambios en la BD
        try:
            self._db_session.commit()
        except Exception as e:
            # Rollback en caso de error
            self._db_session.rollback()
            # Relanzar la excepción
            raise RuntimeError(f"Error al guardar el usuario en la base de datos: {e}") from e


    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por su ID desde la base de datos.
        IMPLEMENTACIÓN DEL PUERTO SECUNDARIO: Traduce del modelo de persistencia al modelo de dominio.
        Returns: Optional[User]: La instancia del User del dominio si se encuentra, None en caso contrario.
        """
        # Buscar el UserModel en la BD usando la sesión de SQLAlchemy
        user_model: UserModel = self._db_session.query(UserModel).filter(UserModel.id == user_id).first() # UserModel (modelo de persistencia)

        # Si no se encuentra, devolver None
        if not user_model:
            return None

        # Si se encuentra, traducir el UserModel al User del dominio:  persistencia -> dominio
        user_domain = User(
            user_id=str(user_model.id),  # Convertir UUID a str
            name=user_model.name,
            email=user_model.email,
            hashed_password=user_model.hashed_password
        )

        return user_domain


    def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su correo electrónico.
        Returns: Optional[User]: La instancia del User del dominio si se encuentra, None en caso contrario.
        """
        # Buscar el UserModel en la BD usando la sesión de SQLAlchemy
        user_model: Optional[UserModel] = self._db_session.query(UserModel).filter(UserModel.email == email).first()

        # Si no se encuentra, devolver None
        if not user_model:
            return None

        # Si se encuentra, traducir el UserModel al User del dominio
        user_domain = User(
            user_id=str(user_model.id),
            name=user_model.name,
            email=user_model.email,
            hashed_password=user_model.hashed_password
        )

        return user_domain

# --- Notas sobre la implementación ---
# Herencia: `SQLAlchemyUserRepository` hereda de `UserRepository` (del dominio).
# Inyección de Dependencias: Recibe una `Session` de SQLAlchemy en el constructor.
# Traducción entre capas:
#    - `save`: Convierte `User` (dominio) -> `UserModel` (SQLAlchemy) -> BD.
#    - `get_by_id`: Convierte BD -> `UserModel` (SQLAlchemy) -> `User` (dominio).
# SQLAlchemy Utiliza la sesión para queries (`query`, `filter`, `first`) y para persistir cambios (`add`, `commit`, `rollback`).
# Manejo de Excepciones: Captura errores de la BD y los maneja adecuadamente: (rollback, relanzar como excepción de aplicación).
# Dependencias de Infraestructura: Esta clase DEPENDE de SQLAlchemy y UserModel. El dominio NO debe conocer estas dependencias.
# Arquitectura Hexagonal: El dominio define la interfaz, la infraestructura la implementa. El dominio usa la abstracción.

# Rol en la Arquitectura
# Implementación concreta: Adaptador que cumple el contrato UserRepository
# Traducción entre capas: Convierte entre User (dominio) y UserModel (persistencia)
# Manejo de transacciones: Commit/rollback para garantizar consistencia
# Inyección de dependencias: Recibe sesión de BD para facilitar testing
# Adaptador de infraestructura: Conecta dominio con tecnología específica (SQLAlchemy)