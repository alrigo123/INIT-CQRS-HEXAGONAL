# app/users/domain/repositories.py
from abc import ABC, abstractmethod
from typing import Optional

# Importamos la entidad de dominio User
from .models import User

class UserRepository(ABC):
    """
    Interfaz abstracta para el repositorio de Usuarios.
    
    Esta es una ABSTRACCIÓN que define qué operaciones de persistencia
    necesita el dominio de usuarios, sin especificar cómo se implementan.
    
    PATRÓN DE DISEÑO: Repository Pattern (Patrón Repositorio)
    PATRÓN DE DISEÑO: Interface Segregation (Segregación de Interfaces)
    
    ARQUITECTURA: Puerto secundario en Arquitectura Hexagonal
    El dominio define la interfaz, la infraestructura la implementa.
    
    PRINCIPIO SOLID: Inversión de Dependencias
    El dominio depende de abstracciones, no de implementaciones concretas.
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
            
        MEJORA SUGERIDA: Definir excepciones específicas de dominio para errores de persistencia
        """
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Obtiene un usuario por su ID.

        Args:
            user_id (str): El identificador único del usuario.

        Returns:
            User | None: La instancia del User si se encuentra, None en caso contrario.
            
        MEJORA SUGERIDA: Considerar sobrecargas para diferentes tipos de ID
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