# app/auth/application/queries/handlers.py
from typing import Optional
from .validate_token_query import ValidateTokenQuery
from ...domain.models import Token
from ...domain.repositories import TokenRepository

def handle_validate_token(
    query: ValidateTokenQuery,
    token_repository: TokenRepository
) -> Optional[dict]:
    """
    Handler para la consulta ValidateTokenQuery.
    Procesa la solicitud de validación de un token de acceso.

    Args:
        query (ValidateTokenQuery): La consulta que contiene el token a validar.
        token_repository (TokenRepository): El repositorio inyectado para buscar el token.

    Returns:
        Optional[dict]: Un diccionario con información del usuario si el token es válido,
                        None si el token no es válido o ha expirado.
    """
    # 1. Buscar el token en el repositorio
    try:
        token: Token = token_repository.find_by_access_token(query.access_token)
    except Exception as e:
        # Manejar errores de búsqueda (por ejemplo, problemas de conexión a BD)
        raise RuntimeError(f"Error al buscar el token en el repositorio: {e}")

    # 2. Verificar si el token existe
    if not token:
        return None # Token no encontrado

    # 3. Verificar si el token ha expirado
    if token.is_expired():
        # Opcionalmente, podrías eliminar el token expirado
        # token_repository.delete(token.id)
        return None # Token expirado

    # 4. Si el token es válido, devolver información del usuario
    # En una implementación real, podrías buscar información adicional del usuario
    # usando el user_id del token.
    return {
        "user_id": token.user_id,
        "is_valid": True,
        "expires_at": token.expires_at.isoformat()
    }

# --- Notas sobre la implementación ---
# 1. Inyección de Dependencias: Recibe el repositorio como parámetro.
# 2. Lógica de consulta: Busca y valida el token.
# 3. Manejo de Excepciones: Captura errores de búsqueda.
# 4. Validación de negocio: Usa el método `is_expired()` del modelo de dominio.
# 5. Retorno de datos: Devuelve un diccionario simple, no una entidad de dominio.