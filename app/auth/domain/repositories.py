# Puerto de Persistencia
from .models import Token
from typing import Optional
from abc import ABC, abstractmethod

class TokenRepository(ABC):  # ← Esto define el contrato
    """
    Interfaz abstracta para el repositorio de Tokens.
    Define los métodos que cualquier implementación de persistencia
    de tokens debe proporcionar. Es un PUERTO de entrada/salida de datos.
    """

    @abstractmethod
    def save(self, token: Token) -> None:
        """
        Guarda un token en el repositorio.
        Este método representa una operación de escritura en el sistema de persistencia.
        """
        pass

    @abstractmethod
    def find_by_access_token(self, access_token: str) -> Optional[Token]:
        """
        Busca un token por su valor de acceso.
        Returns: Optional[Token]: La instancia del Token si se encuentra, None en caso contrario.
        Lectura que permite recuperar tokens por su valor.
        """
        pass

    @abstractmethod
    def delete(self, token_id: str) -> bool:
        """
        Elimina un token por su ID.
        Returns: bool: True si el token fue eliminado, False si no se encontró.
        Escritura que modifica el estado del repositorio.
        """
        pass


# Rol en la Arquitectura:
# Puerto (Port): Define qué operaciones necesita el dominio para persistir datos
# Abstracción: Interface que cualquier adaptador puede implementar
# Inversión de dependencias: El dominio depende de abstracciones, no de implementaciones
# Separación de preocupaciones: Dominio define QUÉ necesita, infraestructura define CÓMO lo hace