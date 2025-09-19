# app/users/infrastructure/api/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated  # Para FastAPI >= 0.95
import uuid

# Importamos los esquemas Pydantic para validación de requests/responses
from .schemas import UserCreateRequest, UserResponse

# Importamos las interfaces del dominio (puertos) y modelos
# Estos son elementos del núcleo de nuestra aplicación
from ....domain.repositories import UserRepository # <-- INTERFACE
from ....domain.models import User

# Importamos comandos, queries y handlers
from ....application.commands.create_user_command import CreateUserCommand
from ....application.queries.get_user_query import GetUserQuery
from ....application.queries.handlers import handle_get_user

# *** NUEVO: Importamos las dependencias del contenedor DI compartido ***
# *** ESTO REEMPLAZA las importaciones directas de infraestructura ***
from app.shared.di_container import get_user_repository, get_rabbitmq_publisher, RabbitMQPublisher

# Crear un router de FastAPI para este módulo
# Este router se montará en main.py bajo un prefijo (por ejemplo, /api/v1/users)
# tags=["users"] aparece en la documentación Swagger para agrupar endpoints
router = APIRouter(
    prefix="/users",
    tags=["users"],  # Etiqueta para la documentación
    responses={404: {"description": "Not found"}},  # Respuestas por defecto
)

# --- Endpoints ---
# *** AHORA DEPENDEMOS DE LAS INTERFACES Y DEL CONTENEDOR ***

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_request: UserCreateRequest,
    # Inyectamos el publisher a través del contenedor
    publisher: Annotated[RabbitMQPublisher, Depends(get_rabbitmq_publisher)], # <-- DEL CONTENEDOR
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

    user_id = str(uuid.uuid4())  # Generar ID aquí

    # 1. Crear el comando a partir de los datos de la solicitud
    # Convertimos los datos validados del request en un comando del dominio
    command = CreateUserCommand(
        name=user_request.name,
        email=user_request.email,
        password=user_request.password,
        user_id=user_id,
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
            id=user_id,  # Indicador de que está en proceso
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
    # Inyectamos el repositorio a través del contenedor
    user_repo: Annotated[UserRepository, Depends(get_user_repository)], # <-- INTERFACE desde contenedor
    # En una implementación más avanzada con DI container, inyectarías el handler directamente
    # en lugar de crear el repo aquí.
):
    """
    Endpoint para obtener información de un usuario por su ID.

    IMPLEMENTACIÓN CQRS - CONSULTA (LECTURA):
    Este endpoint crea un query, un handler y lo ejecuta para obtener los datos.
    Flujo:
    1. Validación del ID (UUID)
    2. Creación del query GetUserQuery
    3. *** ELIMINADO: Obtención manual del repositorio ***
    4. Ejecución del handler de consulta (lógica de aplicación)
    5. Conversión a respuesta

    Args:
        user_id (str): El identificador único del usuario.
        user_repo (UserRepository): El repositorio de usuarios inyectado (interfaz).

    Returns:
        UserResponse: La información del usuario solicitado.
    """
    # 1. Convertir el ID de string a UUID (validación)
    try:
        user_id_uuid = uuid.UUID(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El ID del usuario debe ser un UUID válido. Error: {e}",
        )

    # 2. Crear el objeto Query
    query = GetUserQuery(user_id=str(user_id_uuid))

    # *** SECCION MODIFICADA ***
    # 3. ELIMINADO: Obtener el repositorio manualmente.
    #    Ahora se inyecta directamente como `user_repo: UserRepository`.

    try:
        # 4. Ejecutar el handler de consulta (lógica de aplicación)
        # Este es el cambio clave: usamos el handler en lugar de llamar directamente al repo
        # y pasamos la interfaz inyectada.
        user_domain: User = handle_get_user(query, user_repo) # <-- Pasamos la interfaz

        # 5. Verificar si el usuario fue encontrado
        if not user_domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado.",
            )

        # 6. Convertir la entidad de dominio a un esquema de respuesta
        user_response = UserResponse(
            id=user_domain.id, name=user_domain.name, email=user_domain.email
        )

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
# 1. `APIRouter`: Permite agrupar rutas relacionadas. Se incluye en main.py.
# 2. `Depends`: Mecanismo de inyección de dependencias de FastAPI.
# 3. `Annotated`: Sintaxis moderna de Python/FastAPI para tipar dependencias.
# 4. `UserCreateRequest` y `UserResponse`: Esquemas Pydantic para validar y estructurar datos.
# 5. *** MODIFICADO: `get_rabbitmq_publisher` se obtiene ahora del `di_container`. ***
# 6. *** ELIMINADO: `get_db_session` ya no se usa directamente aquí. ***
# 7. `@router.post("/")`: Define el endpoint POST para /users (relativo al prefijo /api/v1/users).
# 8. `@router.get("/{user_id}")`: Define el endpoint GET para /users/{user_id}.
# 9. `response_model`: Especifica el esquema de la respuesta, lo que permite validación y documentación automática.
# 10. `status_code`: Define el código HTTP de éxito para la operación.
# 11. Manejo de errores con `HTTPException`: FastAPI lo convierte automáticamente en respuestas HTTP.
# 12. Asincronía: Los endpoints son funciones `async`, aprovechando las capacidades de FastAPI.
# 13. Separación CQRS clara:
#     - POST /users -> Crea comando -> Publica en RabbitMQ (Escritura).
#     - GET /users/{id} -> Consulta directa al handler/repositorio (Lectura).
# 14. *** MODIFICADO: Adaptadores: Ahora se obtienen a través del `di_container`, no se importan directamente. ***
# 15. Independencia del dominio: Este archivo no importa la lógica del handler directamente.
#     La comunicación es a través de comandos/queries y handlers, que operan con interfaces.

# Rol en la Arquitectura
# Adaptador de entrada: Convierte requests HTTP en acciones del sistema
# Implementación CQRS: Separa comandos (POST) de consultas (GET)
# Orquestación: Coordina adaptadores de mensajería y persistencia
# Validación y serialización: Usa Pydantic para estructurar datos
# *** MEJORA: Desacoplado de infraestructura mediante inyección de dependencias centralizada. ***
