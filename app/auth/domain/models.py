# app/auth/domain/models.py
import uuid
from datetime import datetime, timedelta
from typing import Optional

class Token:
    """
    Representa un token de acceso en el dominio de autenticación.
    Esta clase encapsula las propiedades y reglas de negocio básicas de un token.
    Es independiente de frameworks, bases de datos o mecanismos de persistencia.
    """

    def __init__(self, token_id: str, user_id: str, access_token: str, expires_at: datetime):
        """
        Inicializa un nuevo Token.

        Args:
            token_id (str): El identificador único del token.
            user_id (str): El identificador del usuario al que pertenece el token.
            access_token (str): El valor del token de acceso.
            expires_at (datetime): La fecha y hora de expiración del token.
        """
        if not token_id or not user_id or not access_token or not expires_at:
            raise ValueError("Todos los campos del token son obligatorios.")
        if expires_at <= datetime.utcnow():
            raise ValueError("La fecha de expiración debe ser futura.")

        self._id = token_id
        self._user_id = user_id
        self._access_token = access_token
        self._expires_at = expires_at

    @property
    def id(self) -> str:
        """Obtiene el ID del token."""
        return self._id

    @property
    def user_id(self) -> str:
        """Obtiene el ID del usuario."""
        return self._user_id

    @property
    def access_token(self) -> str:
        """Obtiene el valor del token de acceso."""
        return self._access_token

    @property
    def expires_at(self) -> datetime:
        """Obtiene la fecha de expiración del token."""
        return self._expires_at

    def is_expired(self) -> bool:
        """
        Verifica si el token ha expirado.

        Returns:
            bool: True si el token ha expirado, False en caso contrario.
        """
        return datetime.utcnow() >= self._expires_at

    def __eq__(self, other) -> bool:
        """Compara dos tokens por su ID."""
        if not isinstance(other, Token):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        """Representación del objeto Token."""
        return f"<Token(id='{self.id}', user_id='{self.user_id}', expires_at='{self.expires_at}')>"

# --- Notas sobre la implementación ---
# 1. `token_id`, `user_id`, `access_token`, `expires_at`: Propiedades esenciales.
# 2. Validaciones en `__init__`: Verifica que los datos sean válidos.
# 3. `is_expired()`: Método de negocio para verificar la validez del token.
# 4. Propiedades (`@property`): Para encapsular el acceso a los atributos.
# 5. `__eq__` y `__repr__`: Métodos mágicos para facilitar comparaciones y debugging.
# 6. Independencia: Código Python puro, sin dependencias externas.