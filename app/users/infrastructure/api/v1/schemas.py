# SCHEMAS (ESQUEMAS DE PYDANTIC)
from pydantic import BaseModel, EmailStr, Field


# --- Esquemas para Solicitudes (Requests) ---
class UserCreateRequest(BaseModel):
    """ Esquema para validar los datos de entrada al crear un usuario. """
    
    # Field(...) indica que es requerido, min_length=1 valida longitud mínima
    name: str = Field(..., min_length=1, description="El nombre del usuario.")
    
    # Pydantic valida automáticamente que tenga formato de email válido
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")
    
    # La contraseña. Debe tener al menos 8 caracteres para cierta seguridad básica.
    password: str = Field(..., min_length=8, description="La contraseña del usuario (mínimo 8 caracteres).")

    class Config:
        # Ejemplo de datos en la interfaz de Swagger para mostrar cómo se ve una request válida
        schema_extra = {
            "example": {
                "name": "Juan Pérez",
                "email": "juan.perez@example.com",
                "password": "unacontrasegura123"
            }
        }


# --- Esquemas para Respuestas (Responses) ---
class UserResponse(BaseModel):
    """ Este modelo define cómo se verá la respuesta del endpoint GET /users/{user_id}. """
   
    id: str = Field(..., description="El identificador único del usuario.")
    name: str = Field(..., description="El nombre del usuario.")
    email: EmailStr = Field(..., description="El correo electrónico del usuario.")

    class Config:
        # Ejemplo de datos para la documentación automática
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