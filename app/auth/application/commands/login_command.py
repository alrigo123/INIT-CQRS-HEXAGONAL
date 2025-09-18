# app/auth/application/commands/login_command.py
from dataclasses import dataclass

@dataclass(frozen=True)
class LoginCommand:
    """
    Comando para iniciar sesión de un usuario.
    Este comando encapsula los datos necesarios para la operación de login.
    Es inmutable y se puede serializar fácilmente.
    
    Atributos:
        email (str): El correo electrónico del usuario.
        password (str): La contraseña en texto plano del usuario.
        otp_code (Optional[str]): Código OTP para 2FA (opcional).
    """
    email: str
    password: str
    otp_code: str | None = None # Para futura implementación de 2FA

# --- Notas sobre la implementación ---
# 1. `@dataclass(frozen=True)`: Hace que el objeto sea inmutable.
# 2. Atributos simples: Solo contiene los datos necesarios para el login.
# 3. `otp_code` opcional: Preparado para extensión futura.
# 4. Independiente: Pertenece a la capa de Aplicación de `auth`.