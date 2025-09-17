# app/auth/application/commands/register_user_command.py
from dataclasses import dataclass

@dataclass(frozen=True)
class RegisterUserCommand:
    """
    Comando para registrar un nuevo usuario en el contexto de autenticación.
    Este comando encapsula los datos necesarios para la operación de registro.
    Es inmutable y se puede serializar fácilmente.
    
    Atributos:
        name (str): El nombre del usuario.
        email (str): El correo electrónico del usuario.
        password (str): La contraseña en texto plano del usuario.
    """
    name: str
    email: str
    password: str

# --- Notas sobre la implementación ---
# 1. `@dataclass(frozen=True)`: Hace que el objeto sea inmutable.
# 2. Atributos simples: Solo contiene los datos necesarios.
# 3. Contraseña en texto plano: El comando lleva la contraseña tal como se recibe.
# 4. Independiente: Pertenece a la capa de Aplicación de `auth`.