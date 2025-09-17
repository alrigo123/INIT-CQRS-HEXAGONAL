# app/users/domain/repositories.py
from abc import ABC, abstractmethod
# Importamos la entidad de dominio User
from .models import User

class UserRepository(ABC):
    """
    Interfaz abstracta para el repositorio de Usuarios.
    Define los métodos que cualquier implementación de persistencia de usuarios
    debe proporcionar. Esta interfaz pertenece al dominio y no debe tener
    dependencias externas.
    """

    @abstractmethod
    def save(self, user: User) -> None:
        """
        Guarda un usuario en el repositorio.

        Args:
            user (User): La instancia de User a guardar.

        Raises:
            # Puede lanzar excepciones específicas definidas en el dominio
            # o dejárselas a la implementación concreta.
        """
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: # Usamos Union[User, None] si < Python 3.10
        """
        Obtiene un usuario por su ID.

        Args:
            user_id (str): El identificador único del usuario.

        Returns:
            User | None: La instancia del User si se encuentra, None en caso contrario.
        """
        pass

    # Se pueden agregar más métodos abstractos aquí si el dominio los requiere
    # Por ejemplo:
    # @abstractmethod
    # def find_by_email(self, email: str) -> User | None:
    #     pass

# --- Notas sobre la implementación ---
# 1. Herencia de ABC: Hace que esta clase sea abstracta.
# 2. @abstractmethod: Marca los métodos que deben ser implementados por las subclases.
# 3. Dependencia del dominio: Solo importa `User` desde el mismo dominio.
# 4. Tipo de retorno `User | None`: Indica que la operación puede no encontrar el usuario.
# 5. Sin lógica de implementación: Este archivo no sabe ni cómo se conecta a una BD.