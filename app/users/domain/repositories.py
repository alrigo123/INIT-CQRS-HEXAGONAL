from abc import ABC, abstractmethod
from typing import Optional

# Importamos la entidad de dominio User
from .models import User

class UserRepository(ABC):
    """
    Interfaz abstracta para el repositorio de Usuarios.
    Esta es una ABSTRACCIÓN que define qué operaciones de persistencia
    necesita el dominio de usuarios, sin especificar cómo se implementan.
    """

    @abstractmethod
    def save(self, user: User) -> None:
        """ Guarda un usuario en el repositorio. """
        pass


    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        Returns: User | None: La instancia del User si se encuentra, None en caso contrario.
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

# Rol en la Arquitectura
# Puerto secundario: Interfaz que el dominio define para interactuar con infraestructura
# Inversión de dependencias: El dominio no depende de implementaciones concretas
# Contrato claro: Define qué operaciones de persistencia necesita el dominio
# Abstracción: Oculta los detalles de cómo se implementa la persistencia
# Lenguaje ubicuo: Usa términos del dominio en la definición de operaciones