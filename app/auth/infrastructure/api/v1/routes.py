# API ROUTES (ENDPOINTS DE FASTAPI)
# ADAPTADOR PRIMARIO en Arquitectura Hexagonal.

# IMPORTS
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated

# Importa los DTOs para validar entrada y estructurar salida
from .schemas import ( LoginRequest,LoginResponse,ValidateTokenRequest,ValidateTokenResponse )

# Importamos las interfaces del dominio (puertos)
from app.users.domain.repositories import UserRepository 
from app.auth.domain.repositories import TokenRepository 

# Importaciones para Login
from ....application.commands.login_command import LoginCommand
from ....application.commands.handlers import handle_login_user, secure_verify_password, generate_access_token, calculate_expires_at

# --- Importaciones para Validación de Token ---
from ....application.queries.validate_token_query import ValidateTokenQuery
from ....application.queries.handlers import handle_validate_token

# Importamos las dependencias del contenedor DI compartido
from app.shared.di_container import get_user_repository, get_token_repository

# Creamos el router de FastAPI para este contexto
router = APIRouter(
    prefix="/auth", # Prefijo para todas las rutas definidas aquí
    tags=["auth"], # Etiqueta para agrupar en la documentación
    responses={404: {"description": "Not found"}}, # Respuesta por defecto para 404
)

# --- ENDPOINTS (RUTAS DE LA API) ---
@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(
    login_request: LoginRequest, # Pydantic valida la entrada
    # Inyectamos las dependencias a través del contenedor
    user_repo: Annotated[UserRepository, Depends(get_user_repository)], # <-- INTERFACE
    token_repo: Annotated[TokenRepository, Depends(get_token_repository)], # <-- INTERFACE
):
    """ Endpoint para iniciar sesión de un usuario. """
    
    try:
        # Crear el comando LoginCommand (DTO de aplicación)
        command = LoginCommand(
            email=login_request.email, password=login_request.password
        )

        # Llamar al handler de aplicación
        # Se pasan las dependencias (interfaces) y funciones auxiliares necesarias.
        access_token = handle_login_user(
            command=command,
            user_repository=user_repo, # <-- Interfaz inyectada
            token_repository=token_repo, # <-- Interfaz inyectada
            verify_password_fn=secure_verify_password, # Función auxiliar inyectada
            generate_token_fn=generate_access_token, # Función auxiliar inyectada
            calculate_expires_fn=calculate_expires_at, # Función auxiliar inyectada
        )

        # Devolver la respuesta estructurada
        return LoginResponse(access_token=access_token, token_type="bearer")
    except ValueError as e:
        # Credenciales inválidas (error del cliente)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        # Error interno del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el login: {e}",
        )


@router.post(
    "/validate-token",
    response_model=ValidateTokenResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_token(
    token_request: ValidateTokenRequest, # Pydantic valida la entrada
    # Inyecta el repositorio de tokens a través del contenedor
    token_repo: Annotated[TokenRepository, Depends(get_token_repository)], # <-- INTERFACE
):
    """ Endpoint para validar un token de acceso. """
    try:
        # Crear la consulta ValidateTokenQuery (DTO de aplicación)
        query = ValidateTokenQuery(access_token=token_request.access_token)

        # Llamar al handler de aplicación
        # Pasamos la interfaz inyectada.
        result = handle_validate_token(query=query, token_repository=token_repo) # <-- Interfaz

        # Devolver la respuesta estructurada
        if result and result.get("is_valid"):
            return ValidateTokenResponse(
                is_valid=True,
                user_id=result["user_id"],
                expires_at=result["expires_at"],
            )
        else:
            return ValidateTokenResponse(is_valid=False, user_id=None, expires_at=None)
    except Exception as e:
        # Error interno del servidor
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al validar el token: {e}",
        )




# Rol en la Arquitectura
# Adaptador de entrada: Convierte requests HTTP en acciones del sistema.
# Implementación CQRS: Separa comandos (POST /login) de consultas (POST /validate-token).
# Orquestación: Coordina adaptadores de persistencia a través de interfaces.
# Validación y serialización: Usa Pydantic para estructurar datos.