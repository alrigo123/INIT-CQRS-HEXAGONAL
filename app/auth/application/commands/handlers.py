import uuid
from typing import Callable, TYPE_CHECKING
from sqlalchemy.orm import Session
# Importamos el comando que vamos a manejar
from ...application.commands.login_command import LoginCommand
# Importamos las excepciones del dominio que podrían ser lanzadas
from ....users.domain.models import InvalidEmailError
# Importamos las interfaces para el repositorio
from ....users.domain.repositories import UserRepository
from ...domain.repositories import TokenRepository
# Importamos el modelo de dominio Token
from ...domain.models import Token

def handle_register_user_for_auth_context(
    user_id: str,
    user_email: str,
    token_repository: TokenRepository,
    generate_token_fn: Callable[[], str],
    calculate_expires_fn: Callable[[int], 'datetime']
) -> str:
    """
    Handler para la lógica de registro en el contexto de auth.
    Se enfoca únicamente en generar y guardar el token de acceso
    para un usuario que ya ha sido creado en el contexto 'users'.

    Args:
        user_id (str): El ID del usuario ya creado en el contexto 'users'.
        user_email (str): El email del usuario.
        token_repository (TokenRepository): Repositorio inyectado para persistir el token.
        generate_token_fn (Callable[[], str]): Función inyectada para generar tokens.
        calculate_expires_fn (Callable[[int], datetime]): Función inyectada para calcular expiración.

    Returns:
        str: El token de acceso generado para el usuario.
        
    Raises:
        ValueError: Si hay un error en la generación del token.
        RuntimeError: Si hay un error al guardar el token en el repositorio.
    """
    try:
        print(f"[Handler] Generando token para usuario {user_id} ({user_email})")

        # 1. Generar token de acceso
        access_token = generate_token_fn()
        if not access_token:
             raise ValueError("La función de generación de tokens devolvió un valor vacío.")

        # 2. Calcular fecha de expiración
        expires_at = calculate_expires_fn(1) # Expira en 1 hora

        # 3. Crear la entidad de dominio Token
        token_id = str(uuid.uuid4())
        token = Token(
            token_id=token_id,
            user_id=user_id,
            access_token=access_token,
            expires_at=expires_at
        )

        # 4. Guardar el token usando el repositorio inyectado
        token_repository.save(token)
        
        print(f"[Handler] Token creado y guardado para el usuario {user_id}")

        # 5. Retornar el token de acceso generado
        return access_token

    except ValueError as ve:
        # Relanzar errores de valor directamente
        raise ve
    except Exception as e:
        # Manejar errores de persistencia u otros
        raise RuntimeError(f"Error al procesar el registro de usuario en auth: {e}") from e

# --- Funciones auxiliares (simulaciones, en producción usar librerías reales) ---
def dummy_verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Función de ejemplo para verificar una contraseña contra un hash.
    En una implementación real, usar una librería segura como passlib.
    """
    import hashlib
    # Hasheamos la contraseña plana con el mismo método usado para guardarla
    plain_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return plain_hash == hashed_password

# --- Funciones auxiliares (simulaciones, en producción usar librerías reales) ---
def dummy_verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Función de ejemplo para verificar una contraseña contra un hash.
    En una implementación real, usar una librería segura como passlib.
    """
    import hashlib
    # Hasheamos la contraseña plana con el mismo método usado para guardarla
    plain_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return plain_hash == hashed_password

def dummy_hash_password(password: str) -> str:
    """Función de ejemplo para hashear una contraseña."""
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_access_token() -> str:
    """Genera un token de acceso."""
    import secrets
    return secrets.token_urlsafe(32)

def calculate_expires_at(hours: int = 1) -> 'datetime':
    """Calcula la fecha de expiración."""
    from datetime import datetime, timedelta
    return datetime.utcnow() + timedelta(hours=hours)

def handle_login_user(
    command: LoginCommand,
    user_repository: UserRepository,
    token_repository: TokenRepository,
    verify_password_fn: Callable[[str, str], bool] = dummy_verify_password,
    hash_password_fn: Callable[[str], str] = dummy_hash_password,
    generate_token_fn: Callable[[], str] = generate_access_token,
    calculate_expires_fn: Callable[[int], 'datetime'] = calculate_expires_at
):
    """
    Handler para el comando LoginCommand.
    Procesa la solicitud de inicio de sesión de un usuario.

    Este handler encapsula la lógica de aplicación:
    1. Busca al usuario por email usando el repositorio de users.
    2. Verifica la contraseña proporcionada contra la almacenada (hasheada).
    3. Si las credenciales son válidas, genera un nuevo token de acceso.
    4. Guarda el token usando el repositorio de auth.

    Args:
        command (LoginCommand): El comando que contiene las credenciales del usuario.
        user_repository (UserRepository): El repositorio inyectado para buscar el usuario.
        token_repository (TokenRepository): El repositorio inyectado para guardar el token.
        verify_password_fn (Callable): Función inyectada para verificar contraseñas.
        hash_password_fn (Callable): Función inyectada para hashear contraseñas (si se necesita regenerar algo).
        generate_token_fn (Callable): Función inyectada para generar tokens.
        calculate_expires_fn (Callable): Función inyectada para calcular expiración.

    Returns:
        str: El token de acceso generado si el login es exitoso.

    Raises:
        ValueError: Si las credenciales son inválidas.
        RuntimeError: Si hay un error al guardar el token en la base de datos.
    """
    # 1. Buscar el usuario por email
    try:
        user = user_repository.get_by_email(command.email)
    except Exception as e:
        # Manejar errores de búsqueda (por ejemplo, problemas de conexión a BD)
        raise RuntimeError(f"Error al buscar el usuario en el repositorio: {e}") from e

    # 2. Verificar si el usuario existe
    if not user:
        # Es una buena práctica no revelar si el email existe o no por motivos de seguridad
        raise ValueError("Credenciales inválidas.")

    # 3. Verificar la contraseña
    try:
        if not verify_password_fn(command.password, user.hashed_password):
            raise ValueError("Credenciales inválidas.")
    except ValueError:
        # Relanzar credenciales inválidas
        raise
    except Exception as e:
        # Manejar errores inesperados de verificación
        raise RuntimeError(f"Error al verificar la contraseña: {e}") from e

    # 4. Si las credenciales son válidas, generar un nuevo token de acceso
    try:
        access_token = generate_token_fn()
    except Exception as e:
        raise RuntimeError(f"Error al generar el token de acceso: {e}") from e

    # 5. Calcular la fecha de expiración
    try:
        expires_at = calculate_expires_fn(1) # Expira en 1 hora
    except Exception as e:
        raise RuntimeError(f"Error al calcular la expiración del token: {e}") from e

    # 6. Crear la entidad de dominio Token
    token_id = str(uuid.uuid4())
    token = Token(
        token_id=token_id,
        user_id=user.id,
        access_token=access_token,
        expires_at=expires_at
    )

    # 7. Guardar el token usando el repositorio inyectado
    try:
        token_repository.save(token)
    except Exception as e:
        raise RuntimeError(f"Error al guardar el token en el repositorio: {e}") from e

    # 8. Retornar el token de acceso generado
    return access_token

# --- Notas sobre la implementación ---
# 1. Inyección de Dependencias: Recibe repositorios y funciones como parámetros.
# 2. Lógica de aplicación: Orquesta la validación de credenciales y la creación del token.
# 3. Manejo de Excepciones: Captura y maneja errores de búsqueda, verificación y persistencia.
# 4. Seguridad: No revela si el email existe o no.
# 5. Independencia: Este handler no importa módulos de infraestructura directamente.