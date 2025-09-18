# HANDLER SERVICE
"""
Esta capa contiene la lógica de coordinación entre:
- Comandos (intenciones de usuario)
- Modelos de dominio (reglas de negocio)
- Repositorios (puertos de persistencia)
- Servicios externos (inyectados como funciones)

Principios aplicados:
- Inyección de dependencias
- Separación de responsabilidades
- Manejo de errores específico
- Independencia de frameworks
"""

import uuid
from typing import Callable, TYPE_CHECKING
from datetime import datetime

# Importamos modelos y repositorios de dominio
from app.users.domain.repositories import UserRepository
from ...domain.repositories import TokenRepository
from ...domain.models import Token

# Importamos comandos de aplicación
from ...application.commands.login_command import LoginCommand
from ...application.commands.register_user_command import RegisterUserCommand

def handle_register_user_for_auth_context(
    user_id: str,
    user_email: str,
    token_repository: TokenRepository,
    generate_token_fn: Callable[[], str],
    calculate_expires_fn: Callable[[int], datetime]
) -> str:
    """
    Handler para la lógica de registro en el contexto de auth.
    
    CASO DE USO: Generar token de acceso para usuario ya creado en otro contexto.
    
    Flujo:
    1. Recibe datos del usuario ya creado
    2. Genera token de acceso usando función inyectada
    3. Calcula expiración usando función inyectada
    4. Crea entidad Token (dominio)
    5. Guarda token usando repositorio (puerto)
    6. Retorna token generado
    
    Args:
        user_id (str): ID del usuario ya creado
        user_email (str): Email del usuario
        token_repository (TokenRepository): Puerto para persistencia
        generate_token_fn (Callable): Función para generar tokens
        calculate_expires_fn (Callable): Función para calcular expiración
        
    Returns:
        str: Token de acceso generado
        
    Raises:
        ValueError: Si hay error en generación de token
        RuntimeError: Si hay error en persistencia
    """
    try:
        print(f"[Handler] Generando token para usuario {user_id} ({user_email})")

        # 1. Generar token de acceso
        access_token = generate_token_fn()
        if not access_token:
            raise ValueError("La función de generación de tokens devolvió un valor vacío.")

        # 2. Calcular fecha de expiración
        expires_at = calculate_expires_fn(1)  # Expira en 1 hora

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


def handle_login_user(
    command: LoginCommand,
    user_repository: UserRepository,
    token_repository: TokenRepository,
    verify_password_fn: Callable[[str, str], bool] = None,
    hash_password_fn: Callable[[str], str] = None,
    generate_token_fn: Callable[[], str] = None,
    calculate_expires_fn: Callable[[int], datetime] = None
):
    """
    Handler para el comando LoginCommand.
    
    CASO DE USO PRINCIPAL: Autenticar usuario y generar token de acceso.
    
    Flujo completo:
    1. Busca usuario por email (cross-context: users domain)
    2. Verifica contraseña usando función inyectada
    3. Genera nuevo token usando función inyectada
    4. Calcula expiración usando función inyectada
    5. Crea entidad Token (dominio)
    6. Guarda token usando repositorio (puerto)
    7. Retorna token generado
    
    Args:
        command (LoginCommand): Comando con credenciales
        user_repository (UserRepository): Puerto para buscar usuarios
        token_repository (TokenRepository): Puerto para guardar tokens
        verify_password_fn (Callable): Función para verificar passwords
        hash_password_fn (Callable): Función para hashear passwords
        generate_token_fn (Callable): Función para generar tokens
        calculate_expires_fn (Callable): Función para calcular expiración
        
    Returns:
        str: Token de acceso generado si login exitoso
        
    Raises:
        ValueError: Si credenciales inválidas
        RuntimeError: Si error en persistencia o búsqueda
    """
    # 1. Buscar el usuario por email
    try:
        user = user_repository.get_by_email(command.email)
    except Exception as e:
        raise RuntimeError(f"Error al buscar el usuario en el repositorio: {e}") from e

    # 2. Verificar si el usuario existe (seguridad: mensaje genérico)
    if not user:
        raise ValueError("Credenciales inválidas.")

    # 3. Verificar la contraseña
    try:
        if not verify_password_fn(command.password, user.hashed_password):
            raise ValueError("Credenciales inválidas.")
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error al verificar la contraseña: {e}") from e

    # 4. Generar token de acceso
    try:
        access_token = generate_token_fn()
    except Exception as e:
        raise RuntimeError(f"Error al generar el token de acceso: {e}") from e

    # 5. Calcular expiración
    try:
        expires_at = calculate_expires_fn(1)  # Expira en 1 hora
    except Exception as e:
        raise RuntimeError(f"Error al calcular la expiración del token: {e}") from e

    # 6. Crear entidad de dominio Token
    token_id = str(uuid.uuid4())
    token = Token(
        token_id=token_id,
        user_id=user.id,
        access_token=access_token,
        expires_at=expires_at
    )

    # 7. Guardar token usando repositorio
    try:
        token_repository.save(token)
    except Exception as e:
        raise RuntimeError(f"Error al guardar el token en el repositorio: {e}") from e

    # 8. Retornar token generado
    return access_token


# --- Funciones auxiliares (simulaciones, en producción usar librerías reales) ---

def dummy_verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Función de ejemplo para verificar una contraseña contra un hash.
    En producción usar librerías seguras como passlib, bcrypt, argon2.
    """
    import hashlib
    plain_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return plain_hash == hashed_password

def dummy_hash_password(password: str) -> str:
    """Función de ejemplo para hashear una contraseña."""
    import hashlib
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_access_token() -> str:
    """Genera un token de acceso seguro."""
    import secrets
    return secrets.token_urlsafe(32)

def calculate_expires_at(hours: int = 1) -> datetime:
    """Calcula la fecha de expiración."""
    from datetime import datetime, timedelta
    return datetime.utcnow() + timedelta(hours=hours)

# --- Notas sobre la implementación ---
# 1. Inyección de Dependencias: Recibe repositorios y funciones como parámetros.
# 2. Lógica de aplicación: Orquesta la validación de credenciales y la creación del token.
# 3. Manejo de Excepciones: Captura y maneja errores de búsqueda, verificación y persistencia.
# 4. Seguridad: No revela si el email existe o no.
# 5. Independencia: Este handler no importa módulos de infraestructura directamente.