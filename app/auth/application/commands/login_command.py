# COMMAND
from dataclasses import dataclass


@dataclass(frozen=True)
class LoginCommand:
    """
    Comando para iniciar sesión de un usuario.
    Este comando encapsula los datos necesarios para la operación de login.

    - Es inmutable (@dataclass(frozen=True))
    - Solo contiene datos, no lógica
    - Representa una acción que el usuario quiere realizar

    Responsabilidad:
    - Transportar datos de login desde la interfaz hasta el handler
    - Actuar como DTO en la capa de aplicación
    """

    email: str
    password: str
    otp_code: str | None = None  # Código OTP para 2FA (opcional) / FUTURO


# --- Rol en la Arquitectura ---
# 1. CQRS Pattern: Comando que representa una intención de escritura
# 2. Application Layer: Pertenece a la capa de aplicación
# 3. Serialización: Fácil de convertir a/desde JSON para APIs
# 4. Independiente: Pertenece a la capa de Aplicación de `auth`.
