from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
import uuid

# Importamos los esquemas Pydantic para validación de requests/responses
from .schemas import UserCreateRequest, UserResponse

# Importamos las interfaces del dominio (puertos) y modelos
from ....domain.repositories import UserRepository # <-- INTERFACE
from ....domain.models import User

# Importamos comandos, queries y handlers
from ....application.commands.create_user_command import CreateUserCommand
from ....application.queries.get_user_query import GetUserQuery
from ....application.queries.handlers import handle_get_user

# Importamos las dependencias del contenedor DI compartido
from app.shared.di_container import get_user_repository, get_rabbitmq_publisher, RabbitMQPublisher

# Crear un router de FastAPI para este módulo
router = APIRouter(
    prefix="/users",
    tags=["users"],  # Etiqueta para la documentación
    responses={404: {"description": "Not found"}},  # Respuestas por defecto
)

# --- Endpoints ---
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_request: UserCreateRequest,
    # Inyectamos el publisher a través del contenedor
    publisher: Annotated[RabbitMQPublisher, Depends(get_rabbitmq_publisher)], # DI
):
    """
    Endpoint para crear un nuevo usuario.
    IMPLEMENTACIÓN CQRS - COMANDO (ESCRITURA):
    Este endpoint recibe una solicitud con los datos del usuario,
    crea un comando CreateUserCommand y lo publica en RabbitMQ
    para ser procesado de forma asíncrona por un consumidor.
    Returns: UserResponse: Una respuesta indicando que el proceso ha comenzado.
    """

    user_id = str(uuid.uuid4())  # Generar ID

    # Convertimos los datos validados del request en un comando del dominio
    command = CreateUserCommand(
        name=user_request.name,
        email=user_request.email,
        password=user_request.password,
        user_id=user_id,
    )

    try:
        # Publicar el comando en RabbitMQ
        # El publisher se encarga de serializar y enviar el comando a la cola
        publisher.publish_create_user(command)

        # Devolver una respuesta.
        return UserResponse(
            id=user_id, 
            name=user_request.name,
            email=user_request.email,
        )
    except Exception as e:
        # Manejar errores de publicación
        # Convertimos excepciones técnicas en respuestas HTTP apropiadas
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud de creación de usuario: {e}",
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)], # DI
):
    """
    Endpoint para obtener información de un usuario por su ID.
    IMPLEMENTACIÓN CQRS - CONSULTA (LECTURA):
    Este endpoint crea un query, un handler y lo ejecuta para obtener los datos.
    Returns: UserResponse: La información del usuario solicitado.
    """
    # Convertir el ID de string a UUID (validación)
    try:
        user_id_uuid = uuid.UUID(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ID del usuario debe ser un UUID válido. Error: {e}",
        )

    # Crear el objeto Query
    query = GetUserQuery(user_id=str(user_id_uuid))

    try:
        # Ejecutar el handler de consulta (lógica de aplicación)
        user_domain: User = handle_get_user(query, user_repo) # DI

        # Verificar si el usuario fue encontrado
        if not user_domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado.",
            )

        # Convertir la entidad de dominio a un esquema de respuesta
        user_response = UserResponse(id=user_domain.id, name=user_domain.name, email=user_domain.email)
        return user_response

    except HTTPException:
        # Relanzar la excepción HTTP si ya fue lanzada
        raise
    except Exception as e:
        # Manejar errores inesperados del handler o del repositorio
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el usuario: {e}",
        )


# --- Notas sobre la implementación ---

# Rol en la Arquitectura
# Adaptador de entrada: Convierte requests HTTP en acciones del sistema
# Implementación CQRS: Separa comandos (POST) de consultas (GET)
# Orquestación: Coordina adaptadores de mensajería y persistencia
# Validación y serialización: Usa Pydantic para estructurar datos
# Desacoplado de infraestructura mediante inyección de dependencias centralizada.
