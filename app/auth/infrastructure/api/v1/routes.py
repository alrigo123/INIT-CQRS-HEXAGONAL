# API ROUTES (ENDPOINTS DE FASTAPI)
# Esta capa expone los endpoints HTTP de la API.
# Se encarga de recibir peticiones, delegar al handler de aplicación y devolver respuestas.
# Es un ADAPTADOR PRIMARIO en Arquitectura Hexagonal.

from fastapi import APIRouter, HTTPException, status, Depends # FastAPI
from typing import Annotated # Para anotaciones de tipo más limpias

# --- Importaciones de Esquemas ---
# Importa los DTOs para validar entrada y estructurar salida
# *** ELIMINADO: RegisterUserRequest, RegisterUserResponse ***
from .schemas import (
    LoginRequest,
    LoginResponse,
    ValidateTokenRequest,
    ValidateTokenResponse,
)

# --- Importaciones para Login ---
# Importa el comando y su handler
from ....application.commands.login_command import LoginCommand
from ....application.commands.handlers import handle_login_user, secure_verify_password, generate_access_token, calculate_expires_at # <-- Ahora

# Importamos el puerto del dominio para anotaciones de tipo
from app.users.domain.repositories import UserRepository
from app.auth.domain.repositories import TokenRepository

# --- Importaciones para Validación de Token ---
# Importa la consulta y su handler
from ....application.queries.validate_token_query import ValidateTokenQuery
from ....application.queries.handlers import handle_validate_token

# Para la dependencia de validación de token
from sqlalchemy.orm import Session

# Creamos el router de FastAPI para este contexto
router = APIRouter(
    prefix="/auth", # Prefijo para todas las rutas definidas aquí
    tags=["auth"], # Etiqueta para agrupar en la documentación
    responses={404: {"description": "Not found"}}, # Respuesta por defecto para 404
)

# --- DEPENDENCIAS DE FASTAPI ---
# Son funciones que se inyectan en los endpoints usando `Depends()`.
# Gestionan recursos como conexiones a BD o instancias de servicios.
# *** MEJORA: Estas dependencias aún importan infraestructura directamente.
# Idealmente, estas crearían adaptadores y devolverían interfaces (puertos).

def get_user_and_token_repositories():
    """
    Dependencia para obtener las instancias de los repositorios de users y auth.
    *** ESTA DEPENDENCIA TIENE PROBLEMAS DE ARQUITECTURA ***
    Importa directamente implementaciones concretas de infraestructura.
    Idealmente, esto estaría en un módulo de configuración/inyección de dependencias.
    """
    # *** PROBLEMA: Importaciones directas de infraestructura ***
    from app.users.infrastructure.persistence.database import (
        SessionLocal as UsersSessionLocal,
    )
    from app.users.infrastructure.persistence.repositories import (
        SQLAlchemyUserRepository as UsersSQLAlchemyUserRepository,
    )
    from app.auth.infrastructure.persistence.database import (
        SessionLocal as AuthSessionLocal,
    )
    from app.auth.infrastructure.persistence.repositories import (
        SQLAlchemyTokenRepository as AuthSQLAlchemyTokenRepository,
    )
    
    # Sesiones de BD
    users_db_session = UsersSessionLocal()
    auth_db_session = AuthSessionLocal()

    # Repositorios (adaptadores concretos)
    # *** PROBLEMA: Devuelve implementaciones concretas ***
    # El handler espera las interfaces `UserRepository` y `TokenRepository`.
    user_repository = UsersSQLAlchemyUserRepository(users_db_session)
    token_repository = AuthSQLAlchemyTokenRepository(auth_db_session)

    try:
        # Devuelve una tupla de los adaptadores concretos
        yield user_repository, token_repository
    finally:
        users_db_session.close()
        auth_db_session.close()

def get_auth_db_session() -> Session:
    """Dependencia para obtener una sesión de la BD de auth."""
    # *** PROBLEMA: Importación directa de infraestructura ***
    from app.auth.infrastructure.persistence.database import SessionLocal as AuthSessionLocal
    
    db_session = AuthSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def get_token_repository(
    db_session: Session = Depends(get_auth_db_session),
) -> TokenRepository: # Anotamos con la interfaz
    """Dependencia para obtener el repositorio de tokens."""
    # *** PROBLEMA: Importación directa de infraestructura ***
    from app.auth.infrastructure.persistence.repositories import SQLAlchemyTokenRepository
    # Retorna una instancia del adaptador concreto
    return SQLAlchemyTokenRepository(db_session)

# --- ENDPOINTS (RUTAS DE LA API) ---

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(
    login_request: LoginRequest, # Pydantic valida la entrada
    # Inyecta las dependencias (adaptadores concretos)
    repos: Annotated[tuple, Depends(get_user_and_token_repositories)],
):
    """
    Endpoint para iniciar sesión de un usuario.
    
    ARQUITECTURA: Adaptador Primario en Arquitectura Hexagonal
    Recibe una petición HTTP, la transforma en un comando y lo delega.
    """
    # Desempaqueta las dependencias inyectadas (adaptadores concretos)
    # Aunque se anoten como UserRepository y TokenRepository, son las implementaciones concretas.
    user_repository: UserRepository
    token_repository: TokenRepository
    user_repository, token_repository = repos

    try:
        # 1. Crear el comando LoginCommand (DTO de aplicación)
        command = LoginCommand(
            email=login_request.email, password=login_request.password
        )

        # 2. Llamar al handler de aplicación
        # Se pasan las dependencias (adaptadores) y funciones auxiliares necesarias.
        access_token = handle_login_user(
            command=command,
            user_repository=user_repository, # Adaptador concreto inyectado
            token_repository=token_repository, # Adaptador concreto inyectado
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
    # Inyecta el repositorio de tokens (adaptador concreto)
    token_repo: Annotated[
        TokenRepository, Depends(get_token_repository) # Anotado con la interfaz
    ],
):
    """
    Endpoint para validar un token de acceso.
    
    ARQUITECTURA: Adaptador Primario en Arquitectura Hexagonal
    Recibe una petición HTTP, la transforma en una consulta y lo delega.
    """
    try:
        # 1. Crear la consulta ValidateTokenQuery (DTO de aplicación)
        query = ValidateTokenQuery(access_token=token_request.access_token)

        # 2. Llamar al handler de aplicación
        result = handle_validate_token(query=query, token_repository=token_repo) # Adaptador concreto

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
# 4. Se usó `Depends` con funciones dependencia dedicadas.
# 5. Se mantuvo el manejo de errores con `HTTPException`.
# 6. Se eliminaron las funciones auxiliares duplicadas (dummy_verify_password, etc.)
#    ya que se importan directamente del handler.
# 7. Se eliminó el bloque `finally: pass` innecesario.
# 8. Se reutilizó la lógica de dependencias existente (`get_user_and_token_repositories`) para `login`.
# 9. Se crearon nuevas dependencias específicas (`get_auth_db_session`, `get_token_repository`) para `validate-token`.
# 10. *** PROBLEMA PENDIENTE: Las dependencias importan directamente de infraestructura.
#     Esto se puede mejorar creando un módulo de inyección de dependencias centralizado.