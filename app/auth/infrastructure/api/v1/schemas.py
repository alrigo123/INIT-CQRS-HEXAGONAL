# app/auth/infrastructure/api/v1/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# --- Esquemas para Solicitudes (Requests) ---

class RegisterUserRequest(BaseModel):
    """
    Esquema para validar los datos de entrada al registrar un usuario.
    """
    name: str = Field(..., min_length=1, description="El nombre del usuario.")
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")
    password: str = Field(..., min_length=8, description="La contraseña del usuario (mínimo 8 caracteres).")

    class Config:
        schema_extra = {
            "example": {
                "name": "Ana García",
                "email": "ana.garcia@example.com",
                "password": "unacontrasegura123"
            }
        }

class LoginRequest(BaseModel):
    """
    Esquema para validar los datos de entrada al iniciar sesión.
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
    """
    Esquema para validar los datos de entrada al validar un token.
    """
    access_token: str = Field(..., description="El token de acceso a validar.")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

# --- Esquemas para Respuestas (Responses) ---

class RegisterUserResponse(BaseModel):
    """
    Esquema para estructurar los datos de salida al registrar un usuario.
    """
    message: str = Field(..., description="Mensaje de confirmación.")
    access_token: str = Field(..., description="El token de acceso generado.")

    class Config:
        schema_extra = {
            "example": {
                "message": "Usuario registrado exitosamente.",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

class LoginResponse(BaseModel):
    """
    Esquema para estructurar los datos de salida al iniciar sesión.
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
# 2. `EmailStr` de Pydantic: Valida automáticamente el formato del email.
# 3. `Field`: Permite agregar validaciones, descripciones y metadatos.
# 4. `...` en Field: Indica que el campo es obligatorio.
# 5. `min_length`: Una validación básica de longitud.
# 6. `class Config`: Para ejemplos en la documentación automática.
# 7. Separación de Requests y Responses: Buena práctica.
# 8. Sin lógica de negocio: Solo definen estructura y validación.