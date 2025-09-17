# app/auth/infrastructure/api/v1/routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from .schemas import RegisterUserRequest, RegisterUserResponse, LoginRequest, LoginResponse, ValidateTokenRequest, ValidateTokenResponse
# Importamos el publisher
from ...messaging.rabbitmq_publisher import RabbitMQAuthPublisher
import uuid # Para generar un ID temporal si es necesario

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

# --- Dependencias ---
def get_rabbitmq_auth_publisher():
    """
    Dependencia para obtener una instancia del publicador de comandos de auth.
    """
    publisher = RabbitMQAuthPublisher()
    try:
        yield publisher
    finally:
        publisher.close()

# --- Endpoints ---

@router.post("/register", response_model=RegisterUserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_request: RegisterUserRequest,
    publisher: Annotated[RabbitMQAuthPublisher, Depends(get_rabbitmq_auth_publisher)]
):
    """
    Endpoint para registrar un nuevo usuario.
    """
    try:
        # 1. Crear el comando RegisterUserCommand
        command_data = {
            "name": user_request.name,
            "email": user_request.email,
            "password": user_request.password
        }
        
        # 2. Publicar el comando en RabbitMQ
        publisher.publish_command("RegisterUserCommand", command_data)
        
        # 3. Devolver una respuesta.
        # Nota: Como es asíncrono, no tenemos el token real todavía.
        # En una implementación más completa, podrías:
        # - Generar un ID de operación y devolverlo.
        # - Usar websockets para notificar cuando se cree.
        # - Implementar un endpoint para consultar el estado de la operación.
        return RegisterUserResponse(
            message="Registro iniciado. El usuario se creará en breve.",
            access_token="pending_token_creation" # Indicador de que está en proceso
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud de registro: {e}"
        )

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(login_request: LoginRequest):
    """
    Endpoint para iniciar sesión de un usuario.
    """
    # Este endpoint necesita implementar la lógica:
    # 1. Validar credenciales (email, password)
    # 2. Si son válidas, generar un nuevo token
    # 3. Guardar el token
    # 4. Devolver el token
    # Por ahora, devolvemos una respuesta simulada.
    # TODO: Implementar lógica real de login
    return LoginResponse(
        access_token="token_de_login_simulado",
        token_type="bearer"
    )

@router.post("/validate-token", response_model=ValidateTokenResponse, status_code=status.HTTP_200_OK)
async def validate_token(token_request: ValidateTokenRequest):
    """
    Endpoint para validar un token de acceso.
    """
    # Este endpoint necesita implementar la lógica:
    # 1. Crear ValidateTokenQuery
    # 2. Llamar al handler
    # 3. Devolver el resultado
    # Por ahora, devolvemos una respuesta simulada.
    # TODO: Implementar lógica real de validación
    return ValidateTokenResponse(
        is_valid=True,
        user_id="user_id_simulado",
        expires_at="2025-12-31T23:59:59Z"
    )

# --- Notas sobre la implementación ---
# 1. `Depends(get_rabbitmq_auth_publisher)`: Inyecta el publisher.
# 2. `publish_command`: Publica el comando `RegisterUserCommand`.
# 3. Manejo de errores con `HTTPException`.
# 4. El endpoint `register` ahora interactúa con RabbitMQ.
# 5. `login` y `validate-token` siguen simulados, se pueden implementar después.