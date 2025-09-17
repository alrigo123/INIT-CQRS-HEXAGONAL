# app/auth/application/commands/handlers.py
import uuid
from typing import Callable
# Importamos el modelo de dominio de auth
from ...domain.models import Token
from ...domain.repositories import TokenRepository

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
