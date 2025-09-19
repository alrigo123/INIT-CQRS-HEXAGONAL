# SCHEMAS (ESQUEMAS DE PYDANTIC)
from pydantic import BaseModel, EmailStr, Field
from typing import Optional 


# --- Esquemas para Solicitudes (Requests) ---
class LoginRequest(BaseModel):
    """
    Esquema para validar los datos de entrada al iniciar sesión.
    
    PATRÓN DE DISEÑO: Data Transfer Object (DTO)
    Se usa para transferir datos entre la API y la capa de aplicación.
    """
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")
    password: str = Field(..., description="La contraseña del usuario.")

    class Config:
        schema_extra = {
            "example": {
                "email": "ana.garcia@example.com",
                "password": "unacontrasegura123"
            }
        }

class ValidateTokenRequest(BaseModel):
    """ Esquema para validar los datos de entrada al validar un token. """
    access_token: str = Field(..., description="El token de acceso a validar.")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

# --- Esquemas para Respuestas (Responses) ---
# Estos esquemas se usan para estructurar y serializar los datos que se envían como respuesta HTTP.

class LoginResponse(BaseModel):
    """ Esquema para estructurar los datos de salida al iniciar sesión. """
    access_token: str = Field(..., description="El token de acceso generado.")
    token_type: str = Field("bearer", description="Tipo de token.")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

class ValidateTokenResponse(BaseModel):
    """ Esquema para estructurar los datos de salida al validar un token. """
    is_valid: bool = Field(..., description="Indica si el token es válido.")
    user_id: Optional[str] = Field(None, description="El ID del usuario asociado al token.")
    expires_at: Optional[str] = Field(None, description="Fecha de expiración del token (ISO 8601).")

    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "user_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
                "expires_at": "2023-10-27T12:00:00Z"
            }
        }
        
        

# --- Notas sobre la implementación ---
# `BaseModel` de Pydantic: La clase base para todos los esquemas.
# Proporciona validación, serialización y documentación automática.
# Separación de Requests y Responses: Mantiene interfaces claras y permite evoluciones independientes.
# in lógica de negocio: Solo definen estructura y validación.