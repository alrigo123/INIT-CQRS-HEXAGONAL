# QUERY HANDLER SERVICE
"""
Esta capa contiene la lógica para procesar consultas (Queries).
Los handlers de consultas se enfocan en leer datos y aplicar lógica de presentación o validación.
Son diferentes de los handlers de comandos, que cambian el estado del sistema.
"""

from typing import Optional, Dict, Any # Tipos para anotaciones
from .validate_token_query import ValidateTokenQuery # Importa la consulta
from ...domain.models import Token # Importa el modelo de dominio
from ...domain.repositories import TokenRepository # Importa el puerto/repositorio

def handle_validate_token(
    query: ValidateTokenQuery,
    token_repository: TokenRepository
) -> Optional[Dict[str, Any]]:
    """
    Handler para la consulta ValidateTokenQuery.
    Procesa la solicitud de validación de un token de acceso.
    Returns: Optional[Dict[str, Any]]: Un diccionario con información del usuario si el token es válido,
                                  None si el token no es válido o ha expirado.
    """
    try:
        # Buscar el token en el repositorio del dominio `auth`
        token: Token = token_repository.find_by_access_token(query.access_token)

        # Verificar si el token existe
        if not token:
            return None # Token no encontrado FALLA

        # Verificar si el token ha expirado usando la lógica del dominio
        # El método `is_expired` encapsula una regla de negocio del modelo `Token`.
        if token.is_expired():
            return None # Token expirado

        # Si el token es válido, devolver información del usuario
        return {
            "is_valid": True, # Indicador explícito de validez
            "user_id": token.user_id, # ID del usuario asociado
            "expires_at": token.expires_at.isoformat() if token.expires_at else None # Fecha en formato estándar
        }

    except Exception as e:
        # Manejar errores de búsqueda o de procesamiento
        print(f"[!] Error al validar el token: {e}")
        # Relanzar como un error de aplicación más genérico.
        raise RuntimeError(f"Error al validar el token: {e}") from e



# --- Notas sobre la implementación ---
# 1. Inyección de Dependencias: Recibe el repositorio como parámetro.
#    Esto permite cambiar la implementación (en memoria, SQL, Redis) sin modificar el handler.
# 2. Lógica de consulta: Busca y valida el token.
#    Se enfoca en leer datos y aplicar reglas de negocio simples.
# 3. Manejo de Excepciones: Captura errores de búsqueda.
#    Distingue entre un resultado "no encontrado" (None) y un error interno (RuntimeError).
# 4. Validación de negocio: Usa el método `is_expired()` del modelo de dominio.
#    La lógica de negocio vive en el dominio, no en el handler.
# 5. Retorno de datos: Devuelve un diccionario simple, no una entidad de dominio.
#    Esto evita acoplamiento y facilita la serialización (por ejemplo, a JSON).
# 6. Lenguaje Ubicuo: Usa términos del dominio (token, user_id, expires_at).