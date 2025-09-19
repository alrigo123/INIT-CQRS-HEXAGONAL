# SQLALCHEMY TOKEN REPOSITORY (ADAPTADOR CONCRETO)
# Esta capa implementa el puerto `TokenRepository` definido en el dominio.

from sqlalchemy.orm import Session # Para tipar la sesión
from typing import Optional # Para retornos opcionales
from datetime import timezone
from datetime import datetime

# Importa el puerto (interfaz) del dominio
from ...domain.repositories import TokenRepository

# Importa la entidad de dominio
from ...domain.models import Token

# Importa el modelo de SQLAlchemy (adaptador)
from .auth_model import TokenModel

class SQLAlchemyTokenRepository(TokenRepository):
    """
    Implementación concreta del TokenRepository usando SQLAlchemy.
    Esta clase adapta las operaciones del dominio a las operaciones
    específicas de la base de datos mediante SQLAlchemy.
    """

    def __init__(self, db_session: Session):
        """ Inicializa el repositorio con una sesión de SQLAlchemy. """
        self._db_session = db_session

    def save(self, token: Token) -> None:
        """ Guarda un token en la base de datos. """
        # Crea una instancia del modelo de SQLAlchemy a partir del dominio
        token_model = TokenModel(
            id=token.id,
            user_id=token.user_id,
            access_token=token.access_token,
            expires_at=token.expires_at
        )

        # Añade el modelo a la sesión
        self._db_session.add(token_model)
        try:
            # Intenta hacer commit de la transacción
            self._db_session.commit()
        except Exception as e:
            # Si hay un error, hace rollback y relanza la excepción
            self._db_session.rollback()
            raise RuntimeError(f"Error al guardar el token en la base de datos: {e}") from e


    def find_by_access_token(self, access_token: str) -> Optional[Token]:
        """ 
        Busca un token por su valor de acceso desde la base de datos.
        Returns: Optional[Token]: La instancia del Token del dominio si se encuentra, None en caso contrario.
        """
        # Realiza la consulta usando SQLAlchemy
        token_model: TokenModel = self._db_session.query(TokenModel).filter(TokenModel.access_token == access_token).first()

        # Si no se encuentra, retorna None
        if not token_model:
            return None

        # Esto crea un datetime aware para evitar errores con el formato de la DB
        expires_at_aware = token_model.expires_at.replace(tzinfo=timezone.utc)

        # Si se encuentra, crea y retorna una instancia del dominio
        token_domain = Token(
            token_id=str(token_model.id),
            user_id=str(token_model.user_id),
            access_token=token_model.access_token,
            expires_at=expires_at_aware
        )

        return token_domain


    def delete(self, token_id: str) -> bool:
        """
        Elimina un token por su ID desde la base de datos.
        Returns: bool: True si el token fue eliminado, False si no se encontró.
        """
        # Busca el modelo por ID
        token_model: TokenModel = self._db_session.query(TokenModel).filter(TokenModel.id == token_id).first()

        # Si no se encuentra, retorna False
        if not token_model:
            return False

        # Si se encuentra, lo elimina de la sesión
        self._db_session.delete(token_model)
        try:
            # Intenta hacer commit de la transacción
            self._db_session.commit()
            return True # Retorna True si se eliminó con éxito
        except Exception as e:
            # Si hay un error, hace rollback y relanza la excepción
            self._db_session.rollback()
            raise RuntimeError(f"Error al eliminar el token de la base de datos: {e}") from e


# --- Notas sobre la implementación ---
# Herencia: `SQLAlchemyTokenRepository` hereda de `TokenRepository`.
#    Cumple con el contrato definido por el puerto del dominio.
# Inyección de Dependencias: Recibe una `Session` de SQLAlchemy en el constructor.
#    Permite que el repositorio sea fácil de testear y configurar.
#  entre capas:
#    - `save`: Convierte `Token` (dominio) -> `TokenModel` (SQLAlchemy) -> BD.
#    - `find_by_access_token`: Convierte BD -> `TokenModel` (SQLAlchemy) -> `Token` (dominio).
#    - `delete`: Busca y elimina `TokenModel` en BD.
#    Esta traducción es el corazón del patrón Adaptador.
# Uso de SQLAlchemy: Utiliza la sesión para queries y persistir cambios.
#    Se adhiere a las prácticas comunes de SQLAlchemy.
# Sin lógica de negocio: Solo se encarga de la persistencia.
#    Respeta el principio de separación de capas.