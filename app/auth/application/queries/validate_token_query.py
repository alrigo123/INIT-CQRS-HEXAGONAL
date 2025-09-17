# app/auth/application/queries/validate_token_query.py
from dataclasses import dataclass

@dataclass(frozen=True)
class ValidateTokenQuery:
    """
    Consulta para validar un token de acceso.
    Este comando encapsula los datos necesarios para la operación de validación.
    Es inmutable y se puede serializar fácilmente.
    
    Atributos:
        access_token (str): El valor del token de acceso a validar.
    """
    access_token: str

# --- Notas sobre la implementación ---
# 1. `@dataclass(frozen=True)`: Hace que el objeto sea inmutable.
# 2. Atributo simple: Solo contiene el token a validar.
# 3. Independiente: Pertenece a la capa de Aplicación de `auth`.