import uuid
from typing import Callable
from typing import Optional

# Importamos el comando que vamos a manejar
from .create_user_command import CreateUserCommand

# Importamos la entidad de dominio y el repositorio (interfaz)
from ...domain.models import User
from ...domain.repositories import UserRepository

def handle_create_user(
    command: CreateUserCommand,
    user_repository: UserRepository,
) -> str:
    """
    Handler para el comando CreateUserCommand.
    Este handler ORQUESTA la ejecución de la operación de creación de usuario.
    Coordina entre el comando de entrada, las dependencias y el dominio.
    Returns: str: El ID del usuario creado.
    Raises:
        ValueError: Si hay errores en validación o creación de entidad.
        RuntimeError: Si hay errores de persistencia.
    """
    
    # Asigna un ID único para el nuevo usuario
    user_id = command.user_id if command.user_id else str(uuid.uuid4())

    hashed_password = command.password # Contraseña hasheada
    
    # Crear la entidad de dominio User
    try:
        user = User(
            user_id=user_id,
            name=command.name,
            email=command.email,
            hashed_password=hashed_password
        )
    except Exception as e:  # Captura excepciones del dominio (InvalidEmailError, etc.)
        raise ValueError(f"Error al crear la entidad de usuario: {e}")

    # Guardar el usuario usando el repositorio inyectado
    try:
        user_repository.save(user)
    except Exception as e:
        # Manejar errores de persistencia (por ejemplo, email duplicado en BD)
        raise RuntimeError(f"Error al guardar el usuario en el repositorio: {e}")

    # Retornar el ID del usuario creado
    return user_id



# --- Notas sobre la implementación ---
# Independencia: Este handler no importa módulos de infraestructura directamente.
#    Depende de abstracciones (UserRepository) que se resuelven en la capa de infraestructura.

# Rol en la Arquitectura
# Handler CQRS: Procesa comandos y orquesta la lógica de aplicación
# Orquestación: Coordina entre comandos, dominio e infraestructura
# Inyección de dependencias: Recibe colaboradores externos
# Manejo de cross-cutting concerns: Hashing, generación de IDs
# Traducción: Convierte intenciones en acciones concretas
# Lógica de aplicación: Coordina flujo sin incluir lógica de negocio del dominio