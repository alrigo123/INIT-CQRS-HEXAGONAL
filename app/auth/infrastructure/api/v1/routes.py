# API ROUTES (ENDPOINTS DE FASTAPI)
# ADAPTADOR PRIMARIO en Arquitectura Hexagonal.

# IMPORTS
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated

# Importa los DTOs para validar entrada y estructurar salida
from .schemas import ( LoginRequest,LoginResponse,ValidateTokenRequest,ValidateTokenResponse )

# Importamos las interfaces del dominio (puertos)
from app.users.domain.repositories import UserRepository # <-- INTERFACE
from app.auth.domain.repositories import TokenRepository # <-- INTERFACE

# Importaciones para Login
from ....application.commands.login_command import LoginCommand
from ....application.commands.handlers import handle_login_user, secure_verify_password, generate_access_token, calculate_expires_at

# --- Importaciones para Validación de Token ---
# Importa la consulta y su handler
from ....application.queries.validate_token_query import ValidateTokenQuery
from ....application.queries.handlers import handle_validate_token

# *** NUEVO: Importamos las dependencias del contenedor DI compartido ***
# *** ESTO REEMPLAZA las importaciones directas de infraestructura ***
from app.shared.di_container import get_user_repository, get_token_repository

# Creamos el router de FastAPI para este contexto
router = APIRouter(
    prefix="/auth", # Prefijo para todas las rutas definidas aquí
    tags=["auth"], # Etiqueta para agrupar en la documentación
    responses={404: {"description": "Not found"}}, # Respuesta por defecto para 404
)

# *** ELIMINADO: Todas las funciones `get_...` anteriores que hacían importaciones directas. ***

# --- ENDPOINTS (RUTAS DE LA API) ---

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(
    login_request: LoginRequest, # Pydantic valida la entrada
    # Inyectamos las dependencias a través del contenedor
    user_repo: Annotated[UserRepository, Depends(get_user_repository)], # <-- INTERFACE
    token_repo: Annotated[TokenRepository, Depends(get_token_repository)], # <-- INTERFACE
):
    """
    Endpoint para iniciar sesión de un usuario.
    
    ARQUITECTURA: Adaptador Primario en Arquitectura Hexagonal
    Recibe una petición HTTP, la transforma en un comando y lo delega.
    *** MEJORA: Ahora depende de interfaces inyectadas, no de implementaciones concretas. ***
    """
    # *** SECCION MODIFICADA ***
    # Desempaquetado de `repos` eliminado.
    # `user_repo` y `token_repo` se inyectan directamente como interfaces.

    try:
        # 1. Crear el comando LoginCommand (DTO de aplicación)
        command = LoginCommand(
            email=login_request.email, password=login_request.password
        )

        # 2. Llamar al handler de aplicación
        # Se pasan las dependencias (interfaces) y funciones auxiliares necesarias.
        access_token = handle_login_user(
            command=command,
            user_repository=user_repo, # <-- Interfaz inyectada
            token_repository=token_repo, # <-- Interfaz inyectada
            verify_password_fn=secure_verify_password, # Función auxiliar inyectada
            generate_token_fn=generate_access_token, # Función auxiliar inyectada
            calculate_expires_fn=calculate_expires_at, # Función auxiliar inyectada
        )

        # 3. Devolver la respuesta estructurada
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
    """
    Endpoint para validar un token de acceso.
    
    ARQUITECTURA: Adaptador Primario en Arquitectura Hexagonal
    Recibe una petición HTTP, la transforma en una consulta y lo delega.
    *** MEJORA: Ahora depende de la interfaz inyectada, no de la implementación concreta. ***
    """
    try:
        # 1. Crear la consulta ValidateTokenQuery (DTO de aplicación)
        query = ValidateTokenQuery(access_token=token_request.access_token)

        # 2. Llamar al handler de aplicación
        # Pasamos la interfaz inyectada.
        result = handle_validate_token(query=query, token_repository=token_repo) # <-- Interfaz

        # 3. Devolver la respuesta estructurada
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

# --- Notas sobre la implementación ---
# 1. Se eliminaron las funciones duplicadas `login_user` y `validate_token` que estaban simuladas.
# 2. Se eliminaron todas las referencias a RegisterUser.
# 3. Se corrigieron las importaciones faltantes y se eliminaron las innecesarias.
# 4. *** MODIFICADO: Se eliminaron todas las funciones `get_...` anteriores. ***
# 5. Se mantuvo el manejo de errores con `HTTPException`.
# 6. Se eliminaron las funciones auxiliares duplicadas (dummy_verify_password, etc.)
#    ya que se importan directamente del handler.
# 7. Se eliminó el bloque `finally: pass` innecesario.
# 8. *** MODIFICADO: Se eliminó la dependencia compleja `get_user_and_token_repositories`. ***
# 9. *** MODIFICADO: Se eliminaron `get_auth_db_session`, `get_token_repository` específicas. ***
# 10. *** MEJORA: Las dependencias ahora se obtienen del `di_container`, eliminando importaciones directas. ***
#     Esto mejora significativamente el desacoplamiento y cumple con el punto 7 del PDF.

# Rol en la Arquitectura
# Adaptador de entrada: Convierte requests HTTP en acciones del sistema.
# Implementación CQRS: Separa comandos (POST /login) de consultas (POST /validate-token).
# Orquestación: Coordina adaptadores de persistencia a través de interfaces.
# Validación y serialización: Usa Pydantic para estructurar datos.
# *** MEJORA CLAVE: Cumple con el punto 7 del PDF sobre Inyección de Dependencias. ***
