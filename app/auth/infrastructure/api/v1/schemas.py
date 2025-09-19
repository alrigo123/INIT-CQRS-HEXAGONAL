# SCHEMAS (ESQUEMAS DE PYDANTIC)
# Esta capa define los modelos de datos para la API.
# Se encarga de la validación de entrada (requests) y la serialización de salida (responses).
# Son independientes del dominio y pertenecen a la infraestructura (API).

from pydantic import BaseModel, EmailStr, Field # Pydantic para validación y serialización
from typing import Optional # Para campos opcionales
from datetime import datetime # Para tipos de fecha

# --- Esquemas para Solicitudes (Requests) ---
# Estos esquemas se usan para validar y parsear los datos que llegan en las peticiones HTTP.

class LoginRequest(BaseModel):
    """
    Esquema para validar los datos de entrada al iniciar sesión.
    
    PATRÓN DE DISEÑO: Data Transfer Object (DTO)
    Se usa para transferir datos entre la API y la capa de aplicación.
    """
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")
    password: str = Field(..., description="La contraseña del usuario.")

    class Config:
        # Configuración para la documentación automática de FastAPI
        schema_extra = {
            "example": {
                "email": "ana.garcia@example.com",
                "password": "unacontrasegura123"
            }
        }

class ValidateTokenRequest(BaseModel):
    """
    Esquema para validar los datos de entrada al validar un token.
    
    PATRÓN DE DISEÑO: Data Transfer Object (DTO)
    """
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
    """
    Esquema para estructurar los datos de salida al iniciar sesión.
    
    PATRÓN DE DISEÑO: Data Transfer Object (DTO)
    """
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
    """
    Esquema para estructurar los datos de salida al validar un token.
    
    PATRÓN DE DISEÑO: Data Transfer Object (DTO)
    """
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
# 1. `BaseModel` de Pydantic: La clase base para todos los esquemas.
#    Proporciona validación, serialización y documentación automática.
# 2. `EmailStr` de Pydantic: Valida automáticamente el formato del email.
#    Requiere `email-validator` instalado.
# 3. `Field`: Permite agregar validaciones, descripciones y metadatos.
#    Mejora la documentación y la experiencia del desarrollador.
# 4. `...` en Field: Indica que el campo es obligatorio.
# 5. `class Config`: Para ejemplos en la documentación automática (Swagger/OpenAPI).
# 6. Separación de Requests y Responses: Buena práctica.
#    Mantiene interfaces claras y permite evoluciones independientes.
# 7. Sin lógica de negocio: Solo definen estructura y validación.
#    La lógica pertenece a los handlers de aplicación.
# 8. Lenguaje Ubicuo: Nombres claros y descriptivos.
# 9. Tipado fuerte: Ayuda a prevenir errores y mejora el autocompletado.