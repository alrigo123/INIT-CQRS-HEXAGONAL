# app/shared/di_container.py
"""
Contenedor de Inyección de Dependencias para la aplicación.

Este módulo centraliza la configuración y creación de adaptadores concretos
(infraestructura) que implementan las interfaces (puertos) definidas en el dominio.
Los adaptadores primarios (endpoints, consumidores) solicitarán dependencias
a través de este contenedor, eliminando la necesidad de importaciones directas
de módulos de infraestructura dentro de ellos.

Esto mejora el desacoplamiento y facilita el testing y el mantenimiento,
cumpliendo con el punto 7 del PDF de la prueba técnica.

PATRÓN DE DISEÑO: Service Locator (Variante simple de Contenedor DI)
ARQUITECTURA: Facilita la Inversión de Dependencias en Arquitectura Hexagonal
"""

# Importamos las interfaces (puertos) del dominio
from app.users.domain.repositories import UserRepository
from app.auth.domain.repositories import TokenRepository

# Importamos las implementaciones concretas (adaptadores) de la infraestructura
# *** ESTAS SON LAS ÚNICAS IMPORTACIONES DIRECTAS DE INFRAESTRUCTURA EN TODO EL PROYECTO ***
# *** Y ESTÁN CONCENTRADAS AQUÍ ***
from app.users.infrastructure.persistence.repositories import SQLAlchemyUserRepository
from app.auth.infrastructure.persistence.repositories import SQLAlchemyTokenRepository
from app.users.infrastructure.persistence.database import SessionLocal as UsersSessionLocal
from app.auth.infrastructure.persistence.database import SessionLocal as AuthSessionLocal

# Importamos otras dependencias concretas si es necesario (ej: publisher)
from app.users.infrastructure.messaging.rabbitmq_publisher import RabbitMQPublisher

# --- Fábricas de Dependencias ---
# Estas funciones encapsulan la lógica de creación de adaptadores concretos.

def create_user_repository() -> UserRepository:
    """
    Fábrica para crear una instancia de UserRepository.
    Retorna un adaptador concreto.
    """
    # Creamos la sesión (en una implementación más avanzada, la sesión podría ser una dependencia inyectada)
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

# --- Contenedor Simple ---
# Un diccionario que mapea un "nombre" o "tipo" de dependencia a su fábrica.
# En una implementación más avanzada, esto podría ser una clase con métodos más complejos.
_DEPENDENCY_REGISTRY = {
    "user_repository": create_user_repository,
    "token_repository": create_token_repository,
    "rabbitmq_publisher": create_rabbitmq_publisher,
    # Se pueden añadir más dependencias aquí
}

def get_dependency(dependency_name: str):
    """
    Obtiene una dependencia por su nombre.
    
    Args:
        dependency_name (str): El nombre de la dependencia a obtener 
                               (debe coincidir con una clave en _DEPENDENCY_REGISTRY).
                               
    Returns:
        La instancia de la dependencia creada por su fábrica.
        
    Raises:
        ValueError: Si el nombre de la dependencia no se encuentra en el registro.
    """
    factory = _DEPENDENCY_REGISTRY.get(dependency_name)
    if not factory:
        raise ValueError(f"Dependencia '{dependency_name}' no registrada en el contenedor DI.")
    # Llamamos a la fábrica para crear y devolver la instancia
    return factory()

# --- Alias para facilitar el tipado y el uso en Depends() ---
# Creamos alias que simplemente llaman a get_dependency con un nombre específico.
# Esto hace que el uso en Depends() sea más limpio y tipado.

def get_user_repository() -> UserRepository:
    """
    Alias tipado para obtener UserRepository.
    
    Uso en FastAPI:
        user_repo: Annotated[UserRepository, Depends(get_user_repository)]
    """
    return get_dependency("user_repository")

def get_token_repository() -> TokenRepository:
    """
    Alias tipado para obtener TokenRepository.
    
    Uso en FastAPI:
        token_repo: Annotated[TokenRepository, Depends(get_token_repository)]
    """
    return get_dependency("token_repository")

def get_rabbitmq_publisher() -> RabbitMQPublisher:
    """
    Alias tipado para obtener RabbitMQPublisher.
    
    Uso en FastAPI:
        publisher: Annotated[RabbitMQPublisher, Depends(get_rabbitmq_publisher)]
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
