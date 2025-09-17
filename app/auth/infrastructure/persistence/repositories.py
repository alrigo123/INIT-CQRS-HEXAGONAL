# app/auth/infrastructure/persistence/repositories.py
from sqlalchemy.orm import Session
from typing import Optional
from ...domain.repositories import TokenRepository
from ...domain.models import Token
from .auth_model import TokenModel

class SQLAlchemyTokenRepository(TokenRepository):
    """
    Implementación concreta del TokenRepository usando SQLAlchemy.
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

    def save(self, token: Token) -> None:
        """
        Guarda un token en la base de datos.

        Args:
            token (Token): La instancia de Token del dominio a guardar.
        """
        token_model = TokenModel(
            id=token.id,
            user_id=token.user_id,
            access_token=token.access_token,
            expires_at=token.expires_at,
            # created_at se establece por defecto en el modelo
        )
        
        self._db_session.add(token_model)
        try:
            self._db_session.commit()
        except Exception as e:
            self._db_session.rollback()
            raise RuntimeError(f"Error al guardar el token en la base de datos: {e}") from e

    def find_by_access_token(self, access_token: str) -> Optional[Token]:
        """
        Busca un token por su valor de acceso desde la base de datos.

        Args:
            access_token (str): El valor del token de acceso.

        Returns:
            Optional[Token]: La instancia del Token del dominio si se encuentra, None en caso contrario.
        """
        token_model: TokenModel = self._db_session.query(TokenModel).filter(TokenModel.access_token == access_token).first()
        
        if not token_model:
            return None
            
        token_domain = Token(
            token_id=str(token_model.id),
            user_id=str(token_model.user_id),
            access_token=token_model.access_token,
            expires_at=token_model.expires_at
        )
        
        return token_domain

    def delete(self, token_id: str) -> bool:
        """
        Elimina un token por su ID desde la base de datos.

        Args:
            token_id (str): El identificador único del token.

        Returns:
            bool: True si el token fue eliminado, False si no se encontró.
        """
        token_model: TokenModel = self._db_session.query(TokenModel).filter(TokenModel.id == token_id).first()
        
        if not token_model:
            return False
            
        self._db_session.delete(token_model)
        try:
            self._db_session.commit()
            return True
        except Exception as e:
            self._db_session.rollback()
            raise RuntimeError(f"Error al eliminar el token de la base de datos: {e}") from e

# --- Notas sobre la implementación ---
# 1. Herencia: `SQLAlchemyTokenRepository` hereda de `TokenRepository`.
# 2. Inyección de Dependencias: Recibe una `Session` de SQLAlchemy en el constructor.
# 3. Traducción entre capas:
#    - `save`: Convierte `Token` (dominio) -> `TokenModel` (SQLAlchemy) -> BD.
#    - `find_by_access_token`: Convierte BD -> `TokenModel` (SQLAlchemy) -> `Token` (dominio).
#    - `delete`: Busca y elimina `TokenModel` en BD.
# 4. Uso de SQLAlchemy: Utiliza la sesión para queries y persistir cambios.
# 5. Manejo de Excepciones: Captura errores de la BD y los maneja adecuadamente.