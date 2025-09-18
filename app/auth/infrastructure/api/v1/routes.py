# API ROUTES (ENDPOINTS DE FASTAPI)
# Esta capa expone los endpoints HTTP de la API.
# Se encarga de recibir peticiones, delegar al handler de aplicación y devolver respuestas.
# Es un ADAPTADOR de entrada en Arquitectura Hexagonal.

from fastapi import APIRouter, HTTPException, status, Depends # FastAPI
from typing import Annotated # Para anotaciones de tipo más limpias

# --- Importaciones de Esquemas ---
# Importa los DTOs para validar entrada y estructurar salida
from .schemas import (
    RegisterUserRequest,
    RegisterUserResponse,
    LoginRequest,
    LoginResponse,
    ValidateTokenRequest,
    ValidateTokenResponse,
)

# --- Importaciones para Registro ---
# Importa el publicador para enviar comandos a RabbitMQ
from ...messaging.rabbitmq_publisher import RabbitMQAuthPublisher

# --- Importaciones para Login ---
# Importa el comando y su handler
from ....application.commands.login_command import LoginCommand
from ....application.commands.handlers import handle_login_user

# Importamos repositorios (necesarios para el handler)
# *** ESTAS IMPORTACIONES ROMPEN LA ARQUITECTURA ***
# Importan directamente de `users.infrastructure` y `auth.infrastructure`
# Esto crea un acoplamiento fuerte. Se debería usar inyección de dependencias.
# *** VER ANÁLISIS DETALLADO MÁS ABAJO ***

# --- Importaciones para Validación de Token ---
# Importa la consulta y su handler
from ....application.queries.validate_token_query import ValidateTokenQuery
from ....application.queries.handlers import handle_validate_token


from app.auth.domain.repositories import TokenRepository # <-- Importación corregida

# Para la dependencia de validación de token
from sqlalchemy.orm import Session

# Creamos el router de FastAPI para este contexto
router = APIRouter(
    prefix="/auth", # Prefijo para todas las rutas definidas aquí
    tags=["auth"], # Etiqueta para agrupar en la documentación
    responses={404: {"description": "Not found"}}, # Respuesta por defecto para 404
)

# *** FUNCIONES AUXILIARES ***
# *** ESTAS FUNCIONES TAMBIÉN DEBERÍAN ESTAR EN INFRAESTRUCTURA ***
# Se usan para inyectar lógica de negocio simulada (hashing, generación de tokens)
import hashlib
import secrets
from datetime import datetime, timedelta

def dummy_verify_password(plain_password: str, hashed_password: str) -> bool:
    """Función de ejemplo para verificar una contraseña contra un hash."""
    plain_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return plain_hash == hashed_password

def dummy_hash_password(password: str) -> str:
    """Función de ejemplo para hashear una contraseña."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def generate_access_token() -> str:
    """Genera un token de acceso seguro."""
    return secrets.token_urlsafe(32)

def calculate_expires_at(hours: int = 1) -> datetime:
    """Calcula la fecha de expiración."""
    return datetime.utcnow() + timedelta(hours=hours)

# --- DEPENDENCIAS DE FASTAPI ---
# Son funciones que se inyectan en los endpoints usando `Depends()`.
# Gestionan recursos como conexiones a BD o instancias de servicios.

def get_rabbitmq_auth_publisher():
    """
    Dependencia para obtener una instancia del publicador de comandos de auth.
    
    PATRÓN DE DISEÑO: Dependency Injection (Inyección de Dependencias)
    FastAPI lo usa para gestionar el ciclo de vida de recursos.
    """
    publisher = RabbitMQAuthPublisher()
    try:
        yield publisher
    finally:
        # Se ejecuta después de que el endpoint termina
        publisher.close() # Cierra la conexión a RabbitMQ

def get_user_and_token_repositories():
    """
    Dependencia para obtener las instancias de los repositorios de users y auth.
    *** ESTA DEPENDENCIA TIENE PROBLEMAS DE ARQUITECTURA ***
    """
    # *** PROBLEMA 1: Importaciones directas de infraestructura ***
    # Importa directamente de `users.infrastructure` y `auth.infrastructure`
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
    user_repository = UsersSQLAlchemyUserRepository(users_db_session)
    token_repository = AuthSQLAlchemyTokenRepository(auth_db_session)

    try:
        # *** PROBLEMA 2: Devuelve una tupla, no interfaces ***
        # El handler espera `UserRepository`, pero recibe `SQLAlchemyUserRepository`
        # Aunque técnicamente funciona por herencia, rompe el principio de abstracción.
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
) -> TokenRepository: # *** PROBLEMA: Devuelve implementación concreta ***
    """Dependencia para obtener el repositorio de tokens."""
    # *** PROBLEMA: Importación directa de infraestructura ***
    from app.auth.infrastructure.persistence.repositories import SQLAlchemyTokenRepository # <-- Importación corregida
    return SQLAlchemyTokenRepository(db_session)

# --- ENDPOINTS (RUTAS DE LA API) ---

@router.post(
    "/register",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_request: RegisterUserRequest, # Pydantic valida la entrada
    publisher: Annotated[RabbitMQAuthPublisher, Depends(get_rabbitmq_auth_publisher)],
):
    """
    Endpoint para registrar un nuevo usuario.
    *** ESTE ENDPOINT DEBE SER REVISADO ***
    """
    try:
        # 1. Crear el comando RegisterUserCommand
        # *** PROBLEMA: Se crea un diccionario en lugar del comando real ***
        # Esto es inconsistente con el uso de `LoginCommand` en `/login`.
        command_data = {
            "name": user_request.name,
            "email": user_request.email,
            "password": user_request.password,
        }

        # 2. Publicar el comando en RabbitMQ
        # *** PROBLEMA: Se publica un diccionario, no un objeto comando ***
        # El consumidor tendrá que reconstruir el comando desde el diccionario.
        publisher.publish_command("RegisterUserCommand", command_data)

        # 3. Devolver una respuesta.
        return RegisterUserResponse(
            message="Registro iniciado. El usuario se creará en breve.",
            access_token="pending_token_creation",  # Indicador de que está en proceso
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud de registro: {e}",
        )

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(
    login_request: LoginRequest, # Pydantic valida la entrada
    # Inyecta las dependencias (repositorios)
    repos: Annotated[tuple, Depends(get_user_and_token_repositories)],
):
    """
    Endpoint para iniciar sesión de un usuario.
    """
    # Desempaqueta las dependencias inyectadas
    user_repository, token_repository = repos

    try:
        # 1. Crear el comando LoginCommand (DTO de aplicación)
        command = LoginCommand(
            email=login_request.email, password=login_request.password
        )

        # 2. Llamar al handler de aplicación
        # *** INYECCIÓN DE DEPENDENCIAS CORRECTA ***
        # Se pasan las dependencias y funciones necesarias.
        access_token = handle_login_user(
            command=command,
            user_repository=user_repository, # Adaptador concreto inyectado
            token_repository=token_repository, # Adaptador concreto inyectado
            verify_password_fn=dummy_verify_password, # Función auxiliar inyectada
            # hash_password_fn=dummy_hash_password, # <- ELIMINADO (no se necesita para login)
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
    # Inyecta el repositorio de tokens
    token_repo: Annotated[
        TokenRepository, Depends(get_token_repository)
    ],
):
    """
    Endpoint para validar un token de acceso.
    """
    try:
        # 1. Crear la consulta ValidateTokenQuery (DTO de aplicación)
        query = ValidateTokenQuery(access_token=token_request.access_token)

        # 2. Llamar al handler de aplicación
        result = handle_validate_token(query=query, token_repository=token_repo)

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
# 2. Se corrigieron las importaciones faltantes.
# 3. Se usó `Depends` con funciones dependencia dedicadas en lugar de lambdas.
# 4. Se eliminó el bloque `finally: pass` innecesario.
# 5. Se mantuvo el manejo de errores con `HTTPException`.
# 6. Se reutilizó la lógica de dependencias existente (`get_user_and_token_repositories`) para `login`.
# 7. Se crearon nuevas dependencias específicas (`get_auth_db_session`, `get_token_repository`) para `validate-token`.