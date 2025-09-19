# DOMINIO
import uuid
from typing import Optional
from datetime import datetime, timezone

class Token:
    """ Representa un token de acceso en el dominio de autenticación.
    Encapsula las propiedades y reglas de negocio básicas de un token.    
    Responsabilidades:
    - Encapsular datos del token
    - Validar reglas de negocio (campos requeridos, expiración)
    - Proporcionar comportamiento del dominio (is_expired)
    """

    def __init__(self, token_id: str, user_id: str, access_token: str, expires_at: datetime):
        """
            token_id (str): El identificador único del token.
            user_id (str): El identificador del usuario al que pertenece el token.
            access_token (str): El valor del token de acceso.
            expires_at (datetime): La fecha y hora de expiración del token.
        """
        # Validación de campos requeridos
        if not token_id or not user_id or not access_token or not expires_at:
            raise ValueError("Todos los campos del token son obligatorios.")
        
        # Validación de fecha de expiración
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("La fecha de expiración debe ser futura.")

        # Asignación de atributos privados (encapsulamiento)
        self._id = token_id
        self._user_id = user_id
        self._access_token = access_token
        self._expires_at = expires_at

    # Propiedades de solo lectura para encapsulamiento
    @property
    def id(self) -> str:
        """ Obtiene el ID del token."""
        return self._id

    @property
    def user_id(self) -> str:
        """ Obtiene el ID del usuario."""
        return self._user_id

    @property
    def access_token(self) -> str:
        """ Obtiene el valor del token de acceso."""
        return self._access_token

    @property
    def expires_at(self) -> datetime:
        """ Obtiene la fecha de expiración del token."""
        return self._expires_at


    def is_expired(self) -> bool:
        """
        Verifica si el token ha expirado según la hora actual UTC.
        Regla de negocio: Comparación con tiempo actual para determinar validez.
        """
        
        # Obtener 'ahora'
        now = datetime.now(timezone.utc)
        
        # Obtener la fecha de expiración del token
        expires_at = self._expires_at

        # --- LÓGICA DE NORMALIZACIÓN ---
        # Si `expires_at` es naive, asumimos que está en UTC y lo convertimos a aware
        if expires_at.tzinfo is None:
            # Es naive, lo convertimos a aware asumiendo UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # Ahora ambos `now` y `expires_at` son aware y se pueden comparar
        return expires_at <= now


    def __eq__(self, other) -> bool:
        """
        Compara dos tokens por su ID para facilitar testing y comparaciones.
        Returns: bool: True si ambos tokens tienen el mismo ID
        """
        if not isinstance(other, Token):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        """ Representación del objeto Token para debugging. """
        return f"<Token(id='{self.id}', user_id='{self.user_id}', expires_at='{self.expires_at}')>"



# Rol en la Arquitectura
# Dominio puro: No tiene dependencias externas
# Reglas de negocio: Validaciones y comportamiento del token
# Encapsulamiento: Atributos privados con propiedades públicas
# Inmutabilidad implícita: No hay setters, el estado se establece en construcción