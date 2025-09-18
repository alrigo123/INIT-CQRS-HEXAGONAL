# app/users/infrastructure/persistence/repositories.py
from sqlalchemy.orm import Session
from typing import Optional

# Importamos la interfaz del repositorio del dominio
# Esta es la ABSTRACCIÓN que implementamos
from ...domain.repositories import UserRepository

# Importamos la entidad de dominio
# Este es el MODELO DE DOMINIO que manipulamos
from ...domain.models import User

# Importamos el modelo de SQLAlchemy
# Este es el ADAPTADOR de persistencia específico
from .user_model import UserModel

class SQLAlchemyUserRepository(UserRepository):
    """
    Implementación concreta del UserRepository usando SQLAlchemy.
    
    Esta clase es un ADAPTADOR que implementa la interfaz abstracta UserRepository
    usando SQLAlchemy como tecnología de persistencia específica.
    
    PATRÓN DE DISEÑO: Adapter Pattern (Patrón Adaptador)
    Convierte la interfaz del dominio en una interfaz compatible con SQLAlchemy.
    
    ARQUITECTURA: Adaptador de infraestructura en Arquitectura Hexagonal
    Implementa el puerto secundario definido en el dominio.
    """

    def __init__(self, db_session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            db_session (Session): La sesión activa de SQLAlchemy para interactuar con la BD.
            
        PATRÓN DE DISEÑO: Dependency Injection
        La sesión se inyecta para facilitar testing y separación de concerns.
        """
        # Almacenamos la sesión inyectada para usarla en las operaciones
        self._db_session = db_session

    def save(self, user: User) -> None:
        """
        Guarda un usuario en la base de datos.
        
        IMPLEMENTACIÓN DEL PUERTO SECUNDARIO:
        Traduce del modelo de dominio al modelo de persistencia.

        Args:
            user (User): La instancia de User del dominio a guardar.

        Raises:
            RuntimeError: Si hay un error al guardar el usuario en la base de datos.
        """
        # 1. Traducir la entidad de dominio User al modelo de infraestructura UserModel
        # Esta es la traducción entre capas: dominio -> persistencia
        user_model = UserModel(
            id=user.id,  # El ID ya fue generado en el handler
            name=user.name,
            email=user.email,
            hashed_password=user.hashed_password,
            # created_at se establece por defecto en el modelo
        )
        
        # 2. Agregar el modelo a la sesión de SQLAlchemy
        # Esto programa la inserción para cuando se haga commit
        self._db_session.add(user_model)
        
        # 3. Hacer commit para persistir los cambios en la BD
        try:
            self._db_session.commit()
        except Exception as e:
            # Es importante hacer rollback en caso de error
            # Esto deshace cualquier cambio pendiente en la sesión
            self._db_session.rollback()
            # Relanzar la excepción o envolverla en una excepción de aplicación
            # MEJORA SUGERIDA: Lanzar excepción específica de aplicación
            raise RuntimeError(f"Error al guardar el usuario en la base de datos: {e}") from e

    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por su ID desde la base de datos.
        
        IMPLEMENTACIÓN DEL PUERTO SECUNDARIO:
        Traduce del modelo de persistencia al modelo de dominio.

        Args:
            user_id (str): El identificador único del usuario.

        Returns:
            Optional[User]: La instancia del User del dominio si se encuentra, None en caso contrario.
        """
        # 1. Buscar el UserModel en la BD usando la sesión de SQLAlchemy
        # Usamos UserModel aqui (modelo de persistencia)
        user_model: UserModel = self._db_session.query(UserModel).filter(UserModel.id == user_id).first()
        
        # 2. Si no se encuentra, devolver None
        if not user_model:
            return None
            
        # 3. Si se encuentra, traducir el UserModel al User del dominio
        # Esta es la traducción entre capas: persistencia -> dominio
        user_domain = User(
            user_id=str(user_model.id),  # Convertir UUID a str si es necesario
            name=user_model.name,
            email=user_model.email,
            hashed_password=user_model.hashed_password
            # created_at no se pasa tipicamente, pero si se necesita:
            # created_at=user_model.created_at
        )
        
        return user_domain

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su correo electrónico.

        Args:
            email (str): El correo electrónico del usuario.

        Returns:
            Optional[User]: La instancia del User del dominio si se encuentra, None en caso contrario.
        """
        # 1. Buscar el UserModel en la BD usando la sesión de SQLAlchemy
        # Usamos UserModel aqui, NO User (el de dominio)
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
        )
        
        return user_domain

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

# Rol en la Arquitectura
# Implementación concreta: Adaptador que cumple el contrato UserRepository
# Traducción entre capas: Convierte entre User (dominio) y UserModel (persistencia)
# Manejo de transacciones: Commit/rollback para garantizar consistencia
# Inyección de dependencias: Recibe sesión de BD para facilitar testing
# Adaptador de infraestructura: Conecta dominio con tecnología específica (SQLAlchemy)