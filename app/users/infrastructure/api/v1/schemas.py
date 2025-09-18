# app/users/infrastructure/api/v1/schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# --- Esquemas para Solicitudes (Requests) ---

class UserCreateRequest(BaseModel):
    """
    Esquema para validar los datos de entrada al crear un usuario.
    Este modelo define qué campos se esperan y sus validaciones en el endpoint POST /users.
    """
    # El nombre del usuario. Debe tener al menos 1 caracter.
    # Field(...) indica que es requerido, min_length=1 valida longitud mínima
    name: str = Field(..., min_length=1, description="El nombre del usuario.")
    
    # El correo electrónico. Usamos EmailStr para validación automática de formato de email.
    # Pydantic validará automáticamente que tenga formato de email válido
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")
    
    # La contraseña. Debe tener al menos 8 caracteres para cierta seguridad básica.
    # En una implementación real, podrías tener reglas más complejas como mayúsculas, números, etc.
    password: str = Field(..., min_length=8, description="La contraseña del usuario (mínimo 8 caracteres).")

    class Config:
        # Ejemplo de datos para la documentación automática de FastAPI (Swagger/OpenAPI)
        # Esto aparece en la interfaz de Swagger para mostrar cómo se ve una request válida
        schema_extra = {
            "example": {
                "name": "Juan Pérez",
                "email": "juan.perez@example.com",
                "password": "unacontrasegura123"
            }
        }

# --- Esquemas para Respuestas (Responses) ---

class UserResponse(BaseModel):
    """
    Esquema para estructurar los datos de salida cuando se devuelve información de un usuario.
    Este modelo define cómo se verá la respuesta del endpoint GET /users/{user_id}.
    """
    # El ID del usuario. Lo devolvemos como string para consistencia.
    id: str = Field(..., description="El identificador único del usuario.")
    
    # El nombre del usuario.
    name: str = Field(..., description="El nombre del usuario.")
    
    # El correo electrónico del usuario.
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")
    
    # Nota: created_at está comentado porque no lo usamos en este ejemplo básico
    # pero sería útil incluirlo en una implementación real

    class Config:
        # Ejemplo de datos para la documentación automática
        # Muestra cómo se verá una respuesta exitosa en Swagger
        schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
                "name": "Juan Pérez",
                "email": "juan.perez@example.com",
            }
        }

# Rol en la Arquitectura
# Adaptador de presentación: Valida y estructura datos de entrada/salida HTTP
# Separación de concerns: Esquemas independientes para requests y responses
# Validación automática: Pydantic valida datos antes de llegar a la lógica de negocio
# Documentación OpenAPI: Genera especificación automática para Swagger