# app/shared/di_container.py
"""
Contenedor de Inyección de Dependencias para la aplicación.

Este módulo es el núcleo del sistema de Inyección de Dependencias (DI).
Su función principal es centralizar la creación y resolución de dependencias 
concretas de infraestructura (adaptadores) que implementan
las interfaces definidas en el dominio (puertos).

PATRÓN DE DISEÑO: Service Locator (Variante simple de Contenedor DI)
ARQUITECTURA: Facilita la Inversión de Dependencias en Arquitectura Hexagonal
"""

# --- Importaciones de Interfaces del Dominio (Puertos) ---
# Abstracciones que define el dominio/core de la aplicación.
# Los adaptadores primarios dependerán de estas interfaces, no de implementaciones.
from app.users.domain.repositories import UserRepository
from app.auth.domain.repositories import TokenRepository

# --- Importaciones de Implementaciones Concretas (Adaptadores de Infraestructura) ---
# El objetivo es que ningún otro archivo del proyecto tenga que importar directamente
from app.users.infrastructure.persistence.repositories import SQLAlchemyUserRepository
from app.auth.infrastructure.persistence.repositories import SQLAlchemyTokenRepository
from app.users.infrastructure.persistence.database import SessionLocal as UsersSessionLocal
from app.auth.infrastructure.persistence.database import SessionLocal as AuthSessionLocal

# Importamos otras dependencias concretas si es necesario (ej: publisher)
from app.users.infrastructure.messaging.rabbitmq_publisher import RabbitMQPublisher

# --- Fábricas de Dependencias ---
# Estas funciones son las encargadas de crear las INSTANCIAS CONCRETAS de los adaptadores.

def create_user_repository() -> UserRepository:
    """
    Fábrica para crear una instancia de UserRepository.
    Retorna un adaptador concreto.
    """
    # Creamos la sesión específica del contexto 'users'
    db_session = UsersSessionLocal()
    # Creamos el adaptador concreto, pasándole la sesión
    repo = SQLAlchemyUserRepository(db_session)
    return repo

def create_token_repository() -> TokenRepository:
    """
    Fábrica para crear una instancia de TokenRepository.
    Retorna un adaptador concreto.
    """
    db_session = AuthSessionLocal()
    repo = SQLAlchemyTokenRepository(db_session)
    return repo

def create_rabbitmq_publisher() -> RabbitMQPublisher:
    """
    Fábrica para crear una instancia de RabbitMQPublisher.
    """
    # El publisher no necesita una sesión, solo su propia configuración
    publisher = RabbitMQPublisher()
    return publisher

# --- Registro del Contenedor ---
# Un diccionario simple que actúa como registro.
_DEPENDENCY_REGISTRY = {
    "user_repository": create_user_repository,
    "token_repository": create_token_repository,
    "rabbitmq_publisher": create_rabbitmq_publisher
}


def get_dependency(dependency_name: str):
    """
    Obtiene una dependencia por su nombre lógico.
    Esta es la función central que resuelve una solicitud de dependencia.
    Busca en el registro `_DEPENDENCY_REGISTRY` la fábrica correspondiente
    y la ejecuta para crear la instancia concreta.
    Returns: La instancia de la dependencia creada por su fábrica.
    Raises: ValueError: Si el nombre de la dependencia no se encuentra en el registro.
                    Esto ayuda a detectar errores de configuración temprano.
    """
    factory = _DEPENDENCY_REGISTRY.get(dependency_name)
    if not factory:
        raise ValueError(f"Dependencia '{dependency_name}' no registrada en el contenedor DI.")
    # Llamamos a la fábrica para crear y devolver la instancia
    return factory()


# --- Alias para Facilitar el Uso con FastAPI ---
# Estos alias son funciones de conveniencia que simplemente llaman a `get_dependency`
# con un nombre específico. Son cruciales para la integración con FastAPI.
# FastAPI usa `Depends(get_user_repository)` para inyectar la dependencia.
# El tipado (`-> UserRepository`) ayuda a FastAPI a entender qué tipo de objeto se inyecta.

def get_user_repository() -> UserRepository:
    """
    Alias tipado para obtener UserRepository.
    Este es el punto de entrada principal para que los adaptadores primarios
    (como endpoints de FastAPI) soliciten un repositorio de usuarios.
    Uso en FastAPI: user_repo: Annotated[UserRepository, Depends(get_user_repository)]
    """
    return get_dependency("user_repository")


def get_token_repository() -> TokenRepository:
    """
    Alias tipado para obtener TokenRepository.
    Punto de entrada para que los adaptadores primarios soliciten un repositorio de tokens.
    Uso en FastAPI: token_repo: Annotated[TokenRepository, Depends(get_token_repository)]
    """
    return get_dependency("token_repository")


def get_rabbitmq_publisher() -> RabbitMQPublisher:
    """
    Alias tipado para obtener RabbitMQPublisher.
    Punto de entrada para que los adaptadores primarios soliciten un publicador de mensajes.
    Uso en FastAPI: publisher: Annotated[RabbitMQPublisher, Depends(get_rabbitmq_publisher)]
    """
    return get_dependency("rabbitmq_publisher")



# --- Notas sobre la implementación ---
# 1. Centralización: Todas las importaciones de infraestructura están aquí.
# 2. Desacoplamiento: Los adaptadores primarios no importan módulos de infraestructura.
# 3. Tipado: Los alias proporcionan tipado estático para herramientas como FastAPI.
# 4. Escalabilidad: Añadir nuevas dependencias es fácil.
# 5. Testing: Se puede reemplazar _DEPENDENCY_REGISTRY para inyectar mocks.

# Rol en la Arquitectura
# Facilitador de Inyección de Dependencias: Punto central para resolver dependencias.
# Desacoplador: Elimina importaciones directas en adaptadores primarios.
# Cumplimiento de PDF: Satisface el punto 7 sobre inyección de dependencias.
# Mejora de Mantenibilidad: Cambios en infraestructura solo afectan este archivo.
