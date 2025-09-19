# SQLALCHEMY TOKEN REPOSITORY (ADAPTADOR CONCRETO)
# Esta capa implementa el puerto `TokenRepository` definido en el dominio.
# Es un ADAPTADOR SECUNDARIO en Arquitectura Hexagonal.
# Traduce las operaciones del dominio a operaciones específicas de SQLAlchemy.

from sqlalchemy.orm import Session # Para tipar la sesión
from typing import Optional # Para retornos opcionales
# Importa el puerto (interfaz) del dominio
from ...domain.repositories import TokenRepository
# Importa la entidad de dominio
from ...domain.models import Token
# Importa el modelo de SQLAlchemy (adaptador)
from .auth_model import TokenModel
from datetime import timezone
from datetime import datetime

class SQLAlchemyTokenRepository(TokenRepository):
    """
    Implementación concreta del TokenRepository usando SQLAlchemy.
    Esta clase adapta las operaciones del dominio a las operaciones
    específicas de la base de datos mediante SQLAlchemy.

    PATRÓN DE DISEÑO: Adapter (Adaptador)
    Convierte la interfaz del dominio (`TokenRepository`) en una interfaz compatible
    con la infraestructura (SQLAlchemy).

    ARQUITECTURA: Adaptador Secundario en Arquitectura Hexagonal
    Implementa un puerto definido por el dominio.
    """

    def __init__(self, db_session: Session):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            db_session (Session): La sesión activa de SQLAlchemy para interactuar con la BD.

        PATRÓN DE DISEÑO: Constructor
        Inicializa el estado del objeto con sus dependencias.
        """
        self._db_session = db_session

    def save(self, token: Token) -> None:
        """
        Guarda un token en la base de datos.

        Args:
            token (Token): La instancia de Token del dominio a guardar.

        PATRÓN DE DISEÑO: Data Transfer Object (DTO) - Conversión
        Conviierte un objeto de dominio en un objeto de persistencia.
        """
        # Crea una instancia del modelo de SQLAlchemy a partir del dominio
        token_model = TokenModel(
            id=token.id,
            user_id=token.user_id,
            access_token=token.access_token,
            expires_at=token.expires_at,
            # expires_at=token.expires_at,
            # created_at se establece por defecto en el modelo
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

        Args:
            access_token (str): El valor del token de acceso.

        Returns:
            Optional[Token]: La instancia del Token del dominio si se encuentra, None en caso contrario.

        PATRÓN DE DISEÑO: Data Transfer Object (DTO) - Conversión
        Convierte un objeto de persistencia en un objeto de dominio.
        """
        # Realiza la consulta usando SQLAlchemy
        token_model: TokenModel = self._db_session.query(TokenModel).filter(TokenModel.access_token == access_token).first()

        # Si no se encuentra, retorna None
        if not token_model:
            return None

                # *** MODIFICACIÓN CRUCIAL ***

        # expires_at_aware = datetime.fromisoformat(token_model.expires_at.isoformat())  # Esto crea un datetime aware
        expires_at_aware = token_model.expires_at.replace(tzinfo=timezone.utc)

        # Si se encuentra, crea y retorna una instancia del dominio
        token_domain = Token(
            token_id=str(token_model.id),
            user_id=str(token_model.user_id),
            access_token=token_model.access_token,
            # expires_at=token_model.expires_at,
            expires_at=expires_at_aware
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
# 1. Herencia: `SQLAlchemyTokenRepository` hereda de `TokenRepository`.
#    Cumple con el contrato definido por el puerto del dominio.
# 2. Inyección de Dependencias: Recibe una `Session` de SQLAlchemy en el constructor.
#    Permite que el repositorio sea fácil de testear y configurar.
# 3. Traducción entre capas:
#    - `save`: Convierte `Token` (dominio) -> `TokenModel` (SQLAlchemy) -> BD.
#    - `find_by_access_token`: Convierte BD -> `TokenModel` (SQLAlchemy) -> `Token` (dominio).
#    - `delete`: Busca y elimina `TokenModel` en BD.
#    Esta traducción es el corazón del patrón Adaptador.
# 4. Uso de SQLAlchemy: Utiliza la sesión para queries y persistir cambios.
#    Se adhiere a las prácticas comunes de SQLAlchemy.
# 5. Manejo de Excepciones: Captura errores de la BD, hace rollback y relanza
#    como excepciones del dominio o aplicación (`RuntimeError`).
#    *** MEJORA: Definir excepciones específicas de dominio para errores de persistencia. ***
# 6. Transaccionalidad: Usa `commit` y `rollback` para garantizar la integridad.
# 7. Sin lógica de negocio: Solo se encarga de la persistencia.
#    Respeta el principio de separación de capas.