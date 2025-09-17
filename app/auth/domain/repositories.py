# app/auth/domain/repositories.py
from abc import ABC, abstractmethod
from typing import Optional
from .models import Token

class TokenRepository(ABC):
    """
    Interfaz abstracta para el repositorio de Tokens.
    Define los métodos que cualquier implementación de persistencia de tokens
    debe proporcionar. Esta interfaz pertenece al dominio y no debe tener
    dependencias externas.
    """

    @abstractmethod
    def save(self, token: Token) -> None:
        """
        Guarda un token en el repositorio.

        Args:
            token (Token): La instancia de Token a guardar.
        """
        pass

    @abstractmethod
    def find_by_access_token(self, access_token: str) -> Optional[Token]:
        """
        Busca un token por su valor de acceso.

        Args:
            access_token (str): El valor del token de acceso.

        Returns:
            Optional[Token]: La instancia del Token si se encuentra, None en caso contrario.
        """
        pass

    @abstractmethod
    def delete(self, token_id: str) -> bool:
        """
        Elimina un token por su ID.

        Args:
            token_id (str): El identificador único del token.

        Returns:
            bool: True si el token fue eliminado, False si no se encontró.
        """
        pass

# --- Notas sobre la implementación ---
# 1. Herencia de ABC: Hace que esta clase sea abstracta.
# 2. @abstractmethod: Marca los métodos que deben ser implementados por las subclases.
# 3. Dependencia del dominio: Solo importa `Token` desde el mismo dominio.
# 4. Tipo de retorno `Optional[Token]`: Indica que la operación puede no encontrar el token.
# 5. Sin lógica de implementación: Este archivo no sabe ni cómo se conecta a una BD.