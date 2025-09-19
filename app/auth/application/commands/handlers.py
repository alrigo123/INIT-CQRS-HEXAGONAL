# HANDLER SERVICE
"""
Esta capa contiene la lógica de coordinación entre:
- Comandos (intenciones de usuario)
- Modelos de dominio (reglas de negocio)
- Repositorios (puertos de persistencia)
- Servicios externos (inyectados como funciones)

Los handlers son los "casos de uso" en una arquitectura limpia.
Orquestan el flujo de una operación específica.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable
import bcrypt

# Importamos modelos y repositorios de dominio
from app.users.domain.repositories import UserRepository

# Importamos del propio dominio `auth`
from app.auth.domain.repositories import TokenRepository
from app.auth.domain.models import Token

# Importamos comandos de aplicación
from .login_command import LoginCommand

def handle_login_user(
    command: LoginCommand,
    user_repository: UserRepository,
    token_repository: TokenRepository,
    verify_password_fn: Callable[[str, str], bool],
    generate_token_fn: Callable[[], str],
    calculate_expires_fn: Callable[[int], datetime]
):
    """
    Handler para el comando LoginCommand.
    CASO DE USO PRINCIPAL: Autenticar usuario y generar token de acceso.
    Returns: str: Token de acceso generado si login exitoso
    Raises:
        ValueError: Si credenciales inválidas (mensaje genérico por seguridad)
        RuntimeError: Si hay un error interno (búsqueda, verificación, persistencia)
    """
    # Buscar el usuario por email en el repositorio del contexto `users`
    try:
        user = user_repository.get_by_email(command.email)
    except Exception as e:
        # Error interno al buscar el usuario
        raise RuntimeError(f"Error al buscar el usuario en el repositorio: {e}") from e

    # Verificar si el usuario existe (seguridad: mensaje genérico)
    if not user:
        raise ValueError("Credenciales inválidas.")

    # Verificar la contraseña usando la función inyectada
    try:
        if not verify_password_fn(command.password, user.hashed_password):
            raise ValueError("Credenciales inválidas.")
    except ValueError:
        # Relanzar el error de credenciales inválidas
        raise
    except Exception as e:
        # Error interno al verificar la contraseña
        raise RuntimeError(f"Error al verificar la contraseña: {e}") from e

    # Generar token de acceso usando la función inyectada
    try:
        access_token = generate_token_fn()
        if not access_token:
             raise RuntimeError("La función de generación de tokens devolvió un valor vacío.")
    except RuntimeError:
         # Relanzar errores específicos de generación
         raise
    except Exception as e:
        # Error interno al generar el token
        raise RuntimeError(f"Error al generar el token de acceso: {e}") from e

    # Calcular expiración usando la función inyectada
    try:
        expires_at = calculate_expires_fn(1)  # Expira en 1 hora
        print(f"[DEBUG] expires_at creado: {expires_at}, tzinfo: {expires_at.tzinfo}") # Para depurar
    except Exception as e:
        # Error interno al calcular la expiración
        raise RuntimeError(f"Error al calcular la expiración del token: {e}") from e

    # Crear la entidad de dominio Token
    # Esta es la parte donde se aplica la lógica de negocio del dominio `auth`
    token_id = str(uuid.uuid4()) # Generamos un ID único para el token
    token = Token(
        token_id=token_id,
        user_id=user.id, # ID del usuario autenticado
        access_token=access_token, # Token generado
        expires_at=expires_at # Fecha de expiración calculada
    )

    # Guardar el token usando el repositorio del contexto `auth`
    try:
        token_repository.save(token)
    except Exception as e:
        # Error interno al guardar el token
        raise RuntimeError(f"Error al guardar el token en el repositorio: {e}") from e

    # Retornar el token generado al cliente
    return access_token


# --- Funciones auxiliares ---
def secure_verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña contra un hash usando bcrypt.
    *** IMPLEMENTACIÓN SEGURA ***
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print(f"[!] Error al verificar contraseña con bcrypt: {e}")
        # Devolver False en caso de error interno para no romper el flujo
        return False


def generate_access_token() -> str:
    """ Genera un token de acceso seguro. """
    import secrets
    return secrets.token_urlsafe(32)


def calculate_expires_at(hours: int = 1) -> datetime:
    """ Calcula la fecha de expiración. """
    from datetime import datetime, timedelta
    return datetime.now(timezone.utc) + timedelta(hours=hours)




# --- Notas sobre la implementación ---
# 1. Inyección de Dependencias: Recibe repositorios y funciones como parámetros.
#    Esto permite cambiar la implementación sin modificar el handler.
# 2. Lógica de aplicación: Orquesta la validación de credenciales y la creación del token.
# 3. Manejo de Excepciones: Captura y maneja errores de búsqueda, verificación y persistencia.
#    Distingue entre errores del cliente (ValueError) y errores del servidor (RuntimeError).
# 4. Seguridad: No revela si el email existe o no. Mensajes de error genéricos.
# 5. Independencia: Este handler no importa módulos de infraestructura directamente.
#    Las implementaciones concretas se inyectan desde fuera.
# 6. Lenguaje Ubicuo: Usa términos del dominio (login, token, user, repository).