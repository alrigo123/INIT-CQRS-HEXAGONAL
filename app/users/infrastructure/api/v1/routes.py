# app/users/infrastructure/api/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated  # Para FastAPI >= 0.95
import uuid

# Importamos los esquemas Pydantic para validación de requests/responses
from .schemas import UserCreateRequest, UserResponse

# Importamos el adaptador de mensajería para publicar comandos
# Este es un adaptador de infraestructura que nos permite enviar mensajes a RabbitMQ
from ...messaging.rabbitmq_publisher import RabbitMQPublisher

# Importamos el repositorio y la base de datos para las consultas directas
# Estos son adaptadores de infraestructura para acceso a datos
from ...persistence.repositories import SQLAlchemyUserRepository
from ...persistence.database import get_db_session

# Importamos el comando de aplicación y el modelo de dominio
# Estos son elementos del núcleo de nuestra aplicación
from ....application.commands.create_user_command import CreateUserCommand
from ....domain.models import User

# Para manejar sesiones de SQLAlchemy (ORM para base de datos)
from sqlalchemy.orm import Session

# Crear un router de FastAPI para este módulo
# Este router se montará en main.py bajo un prefijo (por ejemplo, /api/v1/users)
# tags=["users"] aparece en la documentación Swagger para agrupar endpoints
router = APIRouter(
    prefix="/users",
    tags=["users"],  # Etiqueta para la documentación
    responses={404: {"description": "Not found"}},  # Respuestas por defecto
)

# --- Dependencias ---
# Estas funciones facilitan la inyección de dependencias en los endpoints.
# FastAPI usa Depends() para inyectar estas dependencias automáticamente

def get_rabbitmq_publisher():
    """
    Dependencia para obtener una instancia del publicador de RabbitMQ.
    Esta es una dependencia que maneja el ciclo de vida del publisher.
    En una implementación más avanzada, esto podría venir de un contenedor DI.
    """
    # Creamos una nueva instancia del publisher para cada request
    # En producción, podrías querer un singleton o un pool de conexiones
    publisher = RabbitMQPublisher()
    try:
        # yield permite que FastAPI use el publisher y luego ejecute el finally
        yield publisher
    finally:
        # Asegurarse de cerrar la conexión cuando termina el request
        # Esto es importante para liberar recursos
        publisher.close()

# --- Endpoints ---

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_request: UserCreateRequest,
    publisher: Annotated[RabbitMQPublisher, Depends(get_rabbitmq_publisher)],
):
    """
    Endpoint para crear un nuevo usuario.
    
    IMPLEMENTACIÓN CQRS - COMANDO (ESCRITURA):
    Este endpoint recibe una solicitud con los datos del usuario,
    crea un comando CreateUserCommand y lo publica en RabbitMQ
    para ser procesado de forma asíncrona por un consumidor.
    
    Flujo:
    1. Validación automática con UserCreateRequest
    2. Creación de comando CreateUserCommand
    3. Publicación a cola de mensajes (RabbitMQ)
    4. Respuesta inmediata (asíncrono)

    Args:
        user_request (UserCreateRequest): Los datos del usuario a crear.
        publisher (RabbitMQPublisher): El publicador de comandos inyectado.

    Returns:
        UserResponse: Una respuesta indicando que el proceso ha comenzado.
    """
    # 1. Crear el comando a partir de los datos de la solicitud
    # Convertimos los datos validados del request en un comando del dominio
    command = CreateUserCommand(
        name=user_request.name, 
        email=user_request.email, 
        password=user_request.password
    )

    try:
        # 2. Publicar el comando en RabbitMQ
        # El publisher se encarga de serializar y enviar el comando a la cola
        # Esta es la separación CQRS: escribimos a través de comandos
        publisher.publish_create_user(command)

        # 3. Devolver una respuesta.
        # Nota: Como es asíncrono, no tenemos el ID real del usuario todavía.
        # En una implementación más completa, podrías:
        # - Generar un ID temporal y devolverlo.
        # - Usar websockets para notificar al cliente cuando se cree.
        # - Implementar un endpoint para consultar el estado de la operación.
        return UserResponse(
            id="processing",  # Indicador de que está en proceso
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
    db_session: Annotated[Session, Depends(get_db_session)]
):
    """
    Endpoint para obtener información de un usuario por su ID.
    
    IMPLEMENTACIÓN CQRS - CONSULTA (LECTURA):
    Este endpoint realiza una consulta directa al repositorio
    para obtener los datos del usuario solicitado.
    
    Flujo:
    1. Validación del ID (UUID)
    2. Obtención del repositorio con sesión de BD
    3. Consulta directa a la base de datos
    4. Conversión a respuesta

    Args:
        user_id (str): El identificador único del usuario.
        db_session (Session): La sesión de base de datos inyectada.

    Returns:
        UserResponse: La información del usuario solicitado.
    """
    # 1. Convertir el ID de string a UUID
    # Validamos que el ID tenga formato UUID válido
    try:
        user_id_uuid = uuid.UUID(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ID del usuario debe ser un UUID válido. Error: {e}",
        )

    # 2. Obtener el repositorio, inyectando la sesión de la BD
    # Creamos una instancia del repositorio con la sesión de base de datos
    user_repository = SQLAlchemyUserRepository(db_session)

    try:
        # 3. Usar el repositorio para obtener el usuario por ID
        # Esta es la separación CQRS: leemos directamente del repositorio
        user_domain: User = user_repository.get_by_id(str(user_id_uuid))

        # 4. Verificar si el usuario fue encontrado
        if not user_domain:
            # Si no se encuentra, lanzamos 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado.",
            )

        # 5. Convertir la entidad de dominio a un esquema de respuesta
        # Transformamos el modelo de dominio en una respuesta HTTP
        user_response = UserResponse(
            id=user_domain.id, 
            name=user_domain.name, 
            email=user_domain.email
        )

        return user_response

    except HTTPException:
        # Relanzar la excepción HTTP si ya fue lanzada
        raise
    except Exception as e:
        # Manejar errores inesperados de la BD o del repositorio
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el usuario: {e}",
        )

# --- Notas sobre la implementación ---
# 1. `APIRouter`: Permite agrupar rutas relacionadas. Se incluye en main.py.
# 2. `Depends`: Mecanismo de inyección de dependencias de FastAPI.
# 3. `Annotated`: Sintaxis moderna de Python/FastAPI para tipar dependencias.
# 4. `UserCreateRequest` y `UserResponse`: Esquemas Pydantic para validar y estructurar datos.
# 5. `get_rabbitmq_publisher`: Una dependencia personalizada que maneja la creación y cierre del publisher.
# 6. `get_db_session`: La dependencia del generador de sesiones de BD definida en database.py.
# 7. `@router.post("/")`: Define el endpoint POST para /users (relativo al prefijo /api/v1/users).
# 8. `@router.get("/{user_id}")`: Define el endpoint GET para /users/{user_id}.
# 9. `response_model`: Especifica el esquema de la respuesta, lo que permite validación y documentación automática.
# 10. `status_code`: Define el código HTTP de éxito para la operación.
# 11. Manejo de errores con `HTTPException`: FastAPI lo convierte automáticamente en respuestas HTTP.
# 12. Asincronía: Los endpoints son funciones `async`, aprovechando las capacidades de FastAPI.
# 13. Separación CQRS clara:
#     - POST /users -> Crea comando -> Publica en RabbitMQ (Escritura).
#     - GET /users/{id} -> Consulta directa al repositorio (Lectura).
# 14. Adaptadores: Usa RabbitMQPublisher y SQLAlchemyUserRepository como adaptadores de infraestructura.
# 15. Independencia del dominio: Este archivo no importa la lógica del handler directamente.
#     La comunicación es a través de comandos/repositorios.

# Rol en la Arquitectura
# Adaptador de entrada: Convierte requests HTTP en acciones del sistema
# Implementación CQRS: Separa comandos (POST) de consultas (GET)
# Orquestación: Coordina adaptadores de mensajería y persistencia
# Validación y serialización: Usa Pydantic para estructurar datos