# app/users/application/commands/handlers.py
import uuid
from typing import Callable
# Importamos el comando que vamos a manejar
from .create_user_command import CreateUserCommand
# Importamos la entidad de dominio y el repositorio (interfaz)
from ...domain.models import User # , InvalidEmailError, WeakPasswordError
from ...domain.repositories import UserRepository

# Para hashear la contraseña (esto requerirá una dependencia, lo manejaremos con inyección)
# En una implementación real, este servicio podría ser inyectado
# from ...domain.services import PasswordHasher

def handle_create_user(
    command: CreateUserCommand,
    user_repository: UserRepository,
    # Ejemplo de inyección de dependencia para un servicio
    # password_hasher: PasswordHasher 
    # O una función simple para hashear
    hash_password_fn: Callable[[str], str]
) -> str:
    """
    Handler para el comando CreateUserCommand.
    Procesa la solicitud de creación de un nuevo usuario.

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
        # Puede lanzar excepciones definidas en el dominio o aplicación
        # InvalidEmailError: Si el email del comando no es válido.
        # WeakPasswordError: Si la contraseña no cumple con los criterios.
        # Otras excepciones de infraestructura (por ejemplo, si el email ya existe).
    """
    # 1. (Opcional) Validaciones adicionales a nivel de aplicación
    #    Las básicas ya se harán en el modelo de dominio al crear el User.
    #    Aquí podrías validar unicidad de email, etc., si es necesario antes de crear.

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
    except Exception as e: # Captura excepciones del dominio (InvalidEmailError, etc.)
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