# app/users/infrastructure/persistence/repositories.py
from sqlalchemy.orm import Session
from typing import Optional
# Importamos la interfaz del repositorio del dominio
from ...domain.repositories import UserRepository
# Importamos la entidad de dominio
from ...domain.models import User
# Importamos el modelo de SQLAlchemy
from .user_model import UserModel # <- Asegurate de importar UserModel

class SQLAlchemyUserRepository(UserRepository):
    """
    Implementación concreta del UserRepository usando SQLAlchemy.
    Esta clase adapta las operaciones del dominio a las operaciones
    específicas de la base de datos mediante SQLAlchemy.
    """

    def __init__(self, db_session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            db_session (Session): La sesión activa de SQLAlchemy para interactuar con la BD.
        """
        self._db_session = db_session

    def save(self, user: User) -> None:
        """
        Guarda un usuario en la base de datos.

        Args:
            user (User): La instancia de User del dominio a guardar.

        Raises:
            RuntimeError: Si hay un error al guardar el usuario en la base de datos.
        """
        # 1. Traducir la entidad de dominio User al modelo de infraestructura UserModel
        user_model = UserModel(
            id=user.id, # El ID ya fue generado en el handler
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            # created_at se establece por defecto en el modelo
        )
        
        # 2. Agregar el modelo a la sesión de SQLAlchemy
        self._db_session.add(user_model)
        
        # 3. Hacer commit para persistir los cambios en la BD
        try:
            self._db_session.commit()
        except Exception as e:
            # Es importante hacer rollback en caso de error
            self._db_session.rollback()
            # Relanzar la excepción o envolverla en una excepción de aplicación
            raise RuntimeError(f"Error al guardar el usuario en la base de datos: {e}") from e

    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por su ID desde la base de datos.

        Args:
            user_id (str): El identificador único del usuario.

        Returns:
            Optional[User]: La instancia del User del dominio si se encuentra, None en caso contrario.
        """
        # 1. Buscar el UserModel en la BD usando la sesión de SQLAlchemy
        # Usamos UserModel aqui
        user_model: UserModel = self._db_session.query(UserModel).filter(UserModel.id == user_id).first()
        
        # 2. Si no se encuentra, devolver None
        if not user_model:
            return None
            
        # 3. Si se encuentra, traducir el UserModel al User del dominio
        user_domain = User(
            user_id=str(user_model.id), # Convertir UUID a str si es necesario
            name=user_model.name,
            email=user_model.email,
            hashed_password=user_model.hashed_password
            # created_at no se pasa tipicamente, pero si se necesita:
            # created_at=user_model.created_at
        )
        
        return user_domain

    # --- METODO CORREGIDO ---
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su correo electrónico.

        Args:
            email (str): El correo electrónico del usuario.

        Returns:
            Optional[User]: La instancia del User del dominio si se encuentra, None en caso contrario.
        """
        # 1. Buscar el UserModel en la BD usando la sesión de SQLAlchemy
        #    Usamos UserModel aqui, NO User (el de dominio)
        user_model: Optional[UserModel] = self._db_session.query(UserModel).filter(UserModel.email == email).first()
        
        # 2. Si no se encuentra, devolver None
        if not user_model:
            return None
            
        # 3. Si se encuentra, traducir el UserModel al User del dominio
        user_domain = User(
            user_id=str(user_model.id),
            name=user_model.name,
            email=user_model.email,
            hashed_password=user_model.hashed_password
            # created_at=user_model.created_at (si es necesario)
        )
        
        return user_domain
    # --- FIN DEL METODO CORREGIDO ---

    # Se pueden implementar más métodos definidos en la interfaz UserRepository
    # ...

# --- Notas sobre la implementación ---
# 1. Herencia: `SQLAlchemyUserRepository` hereda de `UserRepository` (del dominio).
# 2. Inyección de Dependencias: Recibe una `Session` de SQLAlchemy en el constructor.
# 3. Traducción entre capas:
#    - `save`: Convierte `User` (dominio) -> `UserModel` (SQLAlchemy) -> BD.
#    - `get_by_id`: Convierte BD -> `UserModel` (SQLAlchemy) -> `User` (dominio).
#    - `get_by_email` (CORREGIDO): Convierte BD -> `UserModel` (SQLAlchemy) -> `User` (dominio).
# 4. Uso de SQLAlchemy: Utiliza la sesión para queries (`query`, `filter`, `first`)
#    y para persistir cambios (`add`, `commit`, `rollback`).
# 5. Manejo de Excepciones: Captura errores de la BD y los maneja adecuadamente.
# 6. Dependencias de Infraestructura: Esta clase DEPENDE de SQLAlchemy y UserModel.
# 7. Cumple con Arquitectura Hexagonal: El dominio define la interfaz,
#    la infraestructura la implementa. El dominio usa la abstracción.

    # Se pueden implementar más métodos definidos en la interfaz UserRepository
    # Por ejemplo:
    # def find_by_email(self, email: str) -> Optional[User]:
    #     user_model = self._db_session.query(UserModel).filter(UserModel.email == email).first()
    #     if not user_model:
    #         return None
    #     return User(...) # Convertir UserModel a User
    
    
    # def delete(self, user_id: str) -> None:
    #     """Elimina un usuario por su ID."""
    #     try:
    #         user = self._db_session.query(User).filter(User.id == user_id).first()
    #         if user:
    #             self._db_session.delete(user)
    #             self._db_session.commit()
    #         else:
    #             raise ValueError(f"No se encontró el usuario con ID: {user_id}")
    #     except Exception as e:
    #         self._db_session.rollback()
    #         raise RuntimeError(f"Error al eliminar el usuario: {e}") from e

    # def update(self, user: User) -> None:
    #     """Actualiza un usuario existente."""
    #     try:
    #         self._db_session.merge(user)
    #         self._db_session.commit()
    #     except Exception as e:
    #         self._db_session.rollback()
    #         raise RuntimeError(f"Error al actualizar el usuario: {e}") from e

# --- Notas sobre la implementación ---
# 1. Herencia: `SQLAlchemyUserRepository` hereda de `UserRepository` (del dominio).
#    Esto cumple con el contrato definido en la interfaz abstracta.
# 2. Inyección de Dependencias: Recibe una `Session` de SQLAlchemy en el constructor.
#    Esto permite usar diferentes sesiones (reales, mock, etc.) y facilita las pruebas.
# 3. Traducción entre capas:
#    - `save`: Convierte `User` (dominio) -> `UserModel` (SQLAlchemy) -> BD.
#    - `get_by_id`: Convierte BD -> `UserModel` (SQLAlchemy) -> `User` (dominio).
# 4. Uso de SQLAlchemy: Utiliza la sesión para queries (`query`, `filter`, `first`)
#    y para persistir cambios (`add`, `commit`, `rollback`).
# 5. Manejo de Excepciones: Captura errores de la BD y los maneja adecuadamente
#    (rollback, relanzar como excepción de aplicación).
# 6. Dependencias de Infraestructura: Esta clase DEPENDE de SQLAlchemy y UserModel.
#    El dominio NO debe conocer estas dependencias.
# 7. Cumple con Arquitectura Hexagonal: El dominio define la interfaz,
#    la infraestructura la implementa. El dominio usa la abstracción.