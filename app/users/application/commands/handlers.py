# app/users/application/commands/handlers.py
import uuid
from typing import Callable
from typing import Optional  # Para tipos opcionales

# Importamos el comando que vamos a manejar
from .create_user_command import CreateUserCommand

# Importamos la entidad de dominio y el repositorio (interfaz)
from ...domain.models import User
from ...domain.repositories import UserRepository

def handle_create_user(
    command: CreateUserCommand,
    user_repository: UserRepository,
    hash_password_fn: Callable[[str], str]
) -> str:
    """
    Handler para el comando CreateUserCommand.
    
    Este handler ORQUESTA la ejecución de la operación de creación de usuario.
    Coordina entre el comando de entrada, las dependencias y el dominio.
    
    PATRÓN DE DISEÑO: Command Handler (Manejador de Comandos)
    PATRÓN DE DISEÑO: Orchestration Pattern (Patrón de Orquestación)
    
    ARQUITECTURA: Parte de la capa de Aplicación en CQRS
    Procesa comandos y coordina la lógica de aplicación.
    
    INYECCIÓN DE DEPENDENCIAS: Recibe todas las dependencias necesarias
    Esto facilita testing y separación de concerns.

    Este handler encapsula la lógica de aplicación:
    1. Toma el comando con los datos del usuario.
    2. (Opcional) Realiza validaciones adicionales a nivel de aplicación.
    3. Hashea la contraseña proporcionada en el comando.
    4. Crea una instancia de la entidad de dominio User.
    5. Guarda la entidad usando el repositorio inyectado.

    Args:
        command (CreateUserCommand): El comando que contiene los datos del nuevo usuario.
        user_repository (UserRepository): El repositorio inyectado para persistir el usuario.
        hash_password_fn (Callable[[str], str]): Función inyectada para hashear contraseñas.

    Returns:
        str: El ID del usuario creado.

    Raises:
        ValueError: Si hay errores en validación o creación de entidad.
        RuntimeError: Si hay errores de persistencia.
        
    MEJORA SUGERIDA: Definir excepciones específicas de aplicación
    MEJORA SUGERIDA: Agregar logging para auditoría
    """
    
    # 1. (Opcional) Validaciones adicionales a nivel de aplicación
    # Las básicas ya se harán en el modelo de dominio al crear el User.
    # Aquí podrías validar unicidad de email, etc., si es necesario antes de crear.
    # MEJORA SUGERIDA: Validar unicidad de email antes de crear la entidad

    # 2. Hashear la contraseña
    # En una implementación más robusta, podrías inyectar un servicio PasswordHasher
    # hashed_password = password_hasher.hash(command.password)
    # Para simplificar ahora, asumimos que hash_password_fn es una función válida
    try:
        hashed_password = hash_password_fn(command.password)
    except Exception as e:
        # Manejar errores de hashing (por ejemplo, contraseña demasiado corta)
        # Podrías lanzar una excepción específica de aplicación
        raise ValueError(f"Error al hashear la contraseña: {e}")

    # 3. Generar un ID único para el nuevo usuario
    # Usamos uuid4 para generar un ID único. En la BD podría ser un UUID o auto-incremental.
    # Este ID se genera en la capa de aplicación, no en el dominio
    user_id = str(uuid.uuid4())

    # 4. Crear la entidad de dominio User
    # El modelo de dominio validará el email y otros datos.
    try:
        user = User(
            user_id=user_id,
            name=command.name,
            email=command.email,
            hashed_password=hashed_password
        )
    except Exception as e:  # Captura excepciones del dominio (InvalidEmailError, etc.)
        # Podrías relanzar la excepción o envolverla en una excepción de aplicación
        raise ValueError(f"Error al crear la entidad de usuario: {e}")

    # 5. Guardar el usuario usando el repositorio inyectado
    # Este es el punto donde la capa de aplicación interactúa con el dominio/infraestructura
    try:
        user_repository.save(user)
    except Exception as e:
        # Manejar errores de persistencia (por ejemplo, email duplicado en BD)
        # Podrías lanzar una excepción específica de aplicación
        raise RuntimeError(f"Error al guardar el usuario en el repositorio: {e}")

    # 6. Retornar el ID del usuario creado
    # El ID generado se devuelve para que el llamador pueda usarlo
    return user_id

# --- Notas sobre la implementación ---
# 1. Función en lugar de Clase: Para simplificar, usamos una función. En proyectos más grandes,
#    es común tener una clase `CreateUserCommandHandler` con un método `handle`.
# 2. Inyección de Dependencias: Recibimos `user_repository` y `hash_password_fn` como parámetros.
#    Esto permite usar mocks en pruebas y desacopla la lógica de aplicación de implementaciones concretas.
# 3. Manejo de Excepciones: Se capturan y manejan excepciones de dominio y posibles errores
#    de infraestructura (hashing, persistencia).
# 4. Valor de Retorno: Devolvemos el ID del usuario creado. En otros casos, podría no devolver nada (None)
#    o devolver un DTO con información básica.
# 5. Validaciones: Las validaciones centrales están en el modelo de dominio `User`.
#    Aquí se pueden hacer validaciones adicionales a nivel de aplicación si es necesario.
# 6. Independencia: Este handler no importa módulos de infraestructura directamente.
#    Depende de abstracciones (UserRepository) que se resuelven en la capa de infraestructura.

# Rol en la Arquitectura
# Handler CQRS: Procesa comandos y orquesta la lógica de aplicación
# Orquestación: Coordina entre comandos, dominio e infraestructura
# Inyección de dependencias: Recibe colaboradores externos
# Manejo de cross-cutting concerns: Hashing, generación de IDs
# Traducción: Convierte intenciones en acciones concretas
# Lógica de aplicación: Coordina flujo sin incluir lógica de negocio del dominio