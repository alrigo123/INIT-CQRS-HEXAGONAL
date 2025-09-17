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
    name: str = Field(..., min_length=1, description="El nombre del usuario.")
    
    # El correo electrónico. Usamos EmailStr para validación automática de formato de email.
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")
    
    # La contraseña. Debe tener al menos 8 caracteres para cierta seguridad básica.
    # En una implementación real, podrías tener reglas más complejas.
    password: str = Field(..., min_length=8, description="La contraseña del usuario (mínimo 8 caracteres).")

    class Config:
        # Ejemplo de datos para la documentación automática de FastAPI (Swagger/OpenAPI)
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
    # El ID del usuario. Lo devolvemos como string.
    id: str = Field(..., description="El identificador único del usuario.")
    
    # El nombre del usuario.
    name: str = Field(..., description="El nombre del usuario.")
    
    # El correo electrónico del usuario.
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")
    
    # Fecha de creación. Opcional en la respuesta básica, pero útil.
    # created_at: datetime # Se puede incluir si se desea

    class Config:
        # Ejemplo de datos para la documentación automática
        schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
                "name": "Juan Pérez",
                "email": "juan.perez@example.com",
                # "created_at": "2023-10-27T10:00:00Z"
            }
        }

# --- Esquemas para Comandos/Eventos Internos (Opcional, pero útil para claridad) ---

# class UserCreatedEvent(BaseModel):
#     """
#     Esquema para representar un evento interno de usuario creado.
#     Puede ser útil si se publican eventos adicionales.
#     """
#     user_id: str
#     name: str
#     email: str

# --- Notas sobre la implementación ---
# 1. `BaseModel` de Pydantic: La clase base para todos los esquemas.
# 2. `EmailStr` de Pydantic: Un tipo especial que valida automáticamente el formato del email.
#    Requiere que 'email-validator' esté instalado (incluido en requirements.txt).
# 3. `Field`: Permite agregar validaciones, descripciones y metadatos.
# 4. `...` en Field: Indica que el campo es obligatorio.
# 5. `min_length`: Una validación básica de longitud.
# 6. `class Config`: Se usa para configurar el comportamiento del modelo.
#    `schema_extra` es útil para la documentación automática de FastAPI.
# 7. Separación de Requests y Responses: Es una buena práctica tener esquemas separados
#    para lo que entra y lo que sale, permitiendo evolucionarlos independientemente.
# 8. Sin lógica de negocio: Estos esquemas solo definen estructura y validación.
# 9. Independientes del dominio: No importan ni User ni CreateUserCommand directamente.
#    La conversión se hace en el controlador/route.