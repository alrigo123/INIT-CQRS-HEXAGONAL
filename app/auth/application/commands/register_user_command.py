# COMMAND
from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterUserCommand:
    """
    Comando para registrar un nuevo usuario en el contexto de autenticación.

    - Inmutable
    - Solo datos necesarios para registro
    - Representa la intención de crear una nueva cuenta.

    Responsabilidad:
    - Transportar datos de registro desde interfaz hasta handler
    - Mantener separación de contextos (auth vs users) (Bounded Contexts)
    """

    name: str
    email: str
    password: str # Contraseña en texto plano


# --- Notas importantes ---
# 1. Contexto separado: Aunque hay usuarios, auth tiene su propio contexto
# 2. Contraseña en texto plano: El handler se encarga de hashearla
# 3. Independiente: Pertenece a la capa de Aplicación de `auth`.
