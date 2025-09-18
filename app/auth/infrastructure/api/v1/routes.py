# app/auth/infrastructure/api/v1/routes.py
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
# --- Importaciones de Esquemas ---
from .schemas import RegisterUserRequest, RegisterUserResponse, LoginRequest, LoginResponse, ValidateTokenRequest, ValidateTokenResponse

# --- Importaciones para Registro ---
from ...messaging.rabbitmq_publisher import RabbitMQAuthPublisher

# --- Importaciones para Login ---
from ....application.commands.login_command import LoginCommand
from ....application.commands.handlers import handle_login_user
# Importamos repositorios (necesarios para el handler)
from app.users.infrastructure.persistence.database import SessionLocal as UsersSessionLocal
from app.users.infrastructure.persistence.repositories import SQLAlchemyUserRepository as UsersSQLAlchemyUserRepository
from app.auth.infrastructure.persistence.database import SessionLocal as AuthSessionLocal
from app.auth.infrastructure.persistence.repositories import SQLAlchemyTokenRepository as AuthSQLAlchemyTokenRepository

# --- Importaciones para Validación de Token ---
from ....application.queries.validate_token_query import ValidateTokenQuery
from ....application.queries.handlers import handle_validate_token
# Para la dependencia de validación de token
from sqlalchemy.orm import Session

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

def get_user_and_token_repositories():
    """
    Dependencia para obtener las instancias de los repositorios de users y auth.
    """
    # Sesiones de BD
    users_db_session = UsersSessionLocal()
    auth_db_session = AuthSessionLocal()
    
    # Repositorios
    user_repository = UsersSQLAlchemyUserRepository(users_db_session)
    token_repository = AuthSQLAlchemyTokenRepository(auth_db_session)
    
    try:
        yield user_repository, token_repository
    finally:
        users_db_session.close()
        auth_db_session.close()

def get_auth_db_session() -> Session:
    """Dependencia para obtener una sesión de la BD de auth."""
    db_session = AuthSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

def get_token_repository(db_session: Session = Depends(get_auth_db_session)) -> AuthSQLAlchemyTokenRepository:
    """Dependencia para obtener el repositorio de tokens."""
    return AuthSQLAlchemyTokenRepository(db_session)

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
async def login_user(
    login_request: LoginRequest,
    repos: Annotated[tuple, Depends(get_user_and_token_repositories)]
):
    """
    Endpoint para iniciar sesión de un usuario.
    """
    user_repository, token_repository = repos
    
    try:
        # 1. Crear el comando LoginCommand
        command = LoginCommand(
            email=login_request.email,
            password=login_request.password
        )
        
        # 2. Llamar al handler de aplicación
        access_token = handle_login_user(
            command=command,
            user_repository=user_repository,
            token_repository=token_repository
        )
        
        # 3. Devolver la respuesta
        return LoginResponse(
            access_token=access_token,
            token_type="bearer"
        )
    except ValueError as e:
        # Credenciales inválidas
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) # Detail ya es una cadena, no necesitas str(e) si e ya lo es
        )
    except Exception as e:
        # Error interno
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el login: {e}"
        )

@router.post("/validate-token", response_model=ValidateTokenResponse, status_code=status.HTTP_200_OK)
async def validate_token(
    token_request: ValidateTokenRequest,
    token_repo: Annotated[AuthSQLAlchemyTokenRepository, Depends(get_token_repository)] # Usamos la dependencia específica
):
    """
    Endpoint para validar un token de acceso.
    """
    try:
        # 1. Crear la consulta ValidateTokenQuery
        query = ValidateTokenQuery(access_token=token_request.access_token)
        
        # 2. Llamar al handler de aplicación
        result = handle_validate_token(query=query, token_repository=token_repo)
        
        # 3. Devolver la respuesta
        if result and result.get("is_valid"):
            return ValidateTokenResponse(
                is_valid=True,
                user_id=result["user_id"],
                expires_at=result["expires_at"]
            )
        else:
            return ValidateTokenResponse(
                is_valid=False,
                user_id=None,
                expires_at=None
            )
    except Exception as e:
        # Error interno
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al validar el token: {e}"
        )
    # finally:
    #     # Las sesiones se cierran automáticamente por la dependencia `get_token_repository`
    #     pass # Se puede eliminar este bloque

# --- Notas sobre la implementación ---
# 1. Se eliminaron las funciones duplicadas `login_user` y `validate_token` que estaban simuladas.
# 2. Se corrigieron las importaciones faltantes.
# 3. Se usó `Depends` con funciones dependencia dedicadas en lugar de lambdas para `validate_token`.
# 4. Se eliminó el bloque `finally: pass` innecesario en `validate_token`.
# 5. Se mantuvo el manejo de errores con `HTTPException`.
# 6. Se reutilizó la lógica de dependencias existente (`get_user_and_token_repositories`) para `login`.
# 7. Se crearon nuevas dependencias específicas (`get_auth_db_session`, `get_token_repository`) para `validate-token`.