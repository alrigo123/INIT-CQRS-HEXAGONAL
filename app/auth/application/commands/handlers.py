# HANDLER SERVICE
"""
Esta capa contiene la lógica de coordinación entre:
- Comandos (intenciones de usuario)
- Modelos de dominio (reglas de negocio)
- Repositorios (puertos de persistencia)
- Servicios externos (inyectados como funciones)

Los handlers son los "casos de uso" en una arquitectura limpia.
Orquestan el flujo de una operación específica.

Principios aplicados:
- Inyección de dependencias (reciben dependencias como parámetros)
- Separación de responsabilidades (cada handler hace una cosa)
- Manejo de errores específico (capturan y relanzan excepciones adecuadas)
- Independencia de frameworks (no importan FastAPI, SQLAlchemy, etc.)
- Alta cohesión, bajo acoplamiento

PATRÓN DE DISEÑO: Use Case Interactor (del Clean Architecture)
PATRÓN DE DISEÑO: Dependency Injection (Inyección de Dependencias)
"""

import uuid
from typing import Callable, TYPE_CHECKING
from datetime import datetime

# Importamos modelos y repositorios de dominio
# Importamos desde `users` porque necesitamos verificar usuarios existentes
from app.users.domain.repositories import UserRepository
# Importamos del propio dominio `auth`
from ...domain.repositories import TokenRepository
from ...domain.models import Token

# Importamos comandos de aplicación
# *** ELIMINAR ESTA LÍNEA ***
# from ...application.commands.register_user_command import RegisterUserCommand
# Importamos el comando de login
from ...application.commands.login_command import LoginCommand

# *** ELIMINAR ESTA FUNCIÓN ***
# def handle_register_user_for_auth_context(...): ...

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
        user_repository (UserRepository): Puerto para buscar usuarios (desde contexto `users`)
        token_repository (TokenRepository): Puerto para guardar tokens (desde contexto `auth`)
        verify_password_fn (Callable): Función para verificar passwords (inyectada)
        generate_token_fn (Callable): Función para generar tokens (inyectada)
        calculate_expires_fn (Callable): Función para calcular expiración (inyectada)
        
    Returns:
        str: Token de acceso generado si login exitoso
        
    Raises:
        ValueError: Si credenciales inválidas (mensaje genérico por seguridad)
        RuntimeError: Si hay un error interno (búsqueda, verificación, persistencia)
        
    PATRÓN DE DISEÑO: Transaction Script (para este caso de uso simple)
    PATRÓN DE DISEÑO: Service Layer (capa de servicio de aplicación)
    """
    # 1. Buscar el usuario por email en el repositorio del contexto `users`
    try:
        user = user_repository.get_by_email(command.email)
    except Exception as e:
        # Error interno al buscar el usuario
        raise RuntimeError(f"Error al buscar el usuario en el repositorio: {e}") from e

    # 2. Verificar si el usuario existe (seguridad: mensaje genérico)
    # Si no existe, se lanza el mismo error que si la contraseña es incorrecta
    # para evitar revelar si un email está registrado.
    if not user:
        raise ValueError("Credenciales inválidas.")

    # 3. Verificar la contraseña usando la función inyectada
    try:
        # Se asume que `user.hashed_password` existe en el modelo de `users`
        if not verify_password_fn(command.password, user.hashed_password):
            raise ValueError("Credenciales inválidas.")
    except ValueError:
        # Relanzar el error de credenciales inválidas
        raise
    except Exception as e:
        # Error interno al verificar la contraseña
        raise RuntimeError(f"Error al verificar la contraseña: {e}") from e

    # 4. Generar token de acceso usando la función inyectada
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

    # 5. Calcular expiración usando la función inyectada
    try:
        expires_at = calculate_expires_fn(1)  # Expira en 1 hora
    except Exception as e:
        # Error interno al calcular la expiración
        raise RuntimeError(f"Error al calcular la expiración del token: {e}") from e

    # 6. Crear la entidad de dominio Token
    # Esta es la parte donde se aplica la lógica de negocio del dominio `auth`
    token_id = str(uuid.uuid4()) # Generamos un ID único para el token
    token = Token(
        token_id=token_id,
        user_id=user.id, # ID del usuario autenticado
        access_token=access_token, # Token generado
        expires_at=expires_at # Fecha de expiración calculada
    )

    # 7. Guardar el token usando el repositorio del contexto `auth`
    try:
        token_repository.save(token)
    except Exception as e:
        # Error interno al guardar el token
        raise RuntimeError(f"Error al guardar el token en el repositorio: {e}") from e

    # 8. Retornar el token generado al cliente
    return access_token


# --- Funciones auxiliares (simulaciones, en producción usar librerías reales) ---
# Estas funciones deben estar en la capa de infraestructura y ser inyectadas.

def dummy_verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Función de ejemplo para verificar una contraseña contra un hash.
    *** EN PRODUCCIÓN: Usar librerías seguras como passlib, bcrypt, argon2. ***
    
    Args:
        plain_password (str): Contraseña en texto plano.
        hashed_password (str): Contraseña hasheada almacenada.
        
    Returns:
        bool: True si coinciden, False en caso contrario.
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
#    Esto permite cambiar la implementación sin modificar el handler.
# 2. Lógica de aplicación: Orquesta la validación de credenciales y la creación del token.
# 3. Manejo de Excepciones: Captura y maneja errores de búsqueda, verificación y persistencia.
#    Distingue entre errores del cliente (ValueError) y errores del servidor (RuntimeError).
# 4. Seguridad: No revela si el email existe o no. Mensajes de error genéricos.
# 5. Independencia: Este handler no importa módulos de infraestructura directamente.
#    Las implementaciones concretas se inyectan desde fuera.
# 6. Lenguaje Ubicuo: Usa términos del dominio (login, token, user, repository).