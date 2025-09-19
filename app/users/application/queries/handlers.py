# app/users/application/queries/handlers.py
from typing import Optional
from .get_user_query import GetUserQuery
from ...domain.models import User
from ...domain.repositories import UserRepository
# Opcional: Definir una excepción específica para cuando el usuario no se encuentra
# class UserNotFoundError(Exception): pass

def handle_get_user(
    query: GetUserQuery,
    user_repository: UserRepository
) -> Optional[User]:
    """
    Handler para el query GetUserQuery.
    
    PATRÓN DE DISEÑO: Query Handler (CQRS)
    
    Args:
        query (GetUserQuery): El query con el ID del usuario.
        user_repository (UserRepository): El repositorio inyectado para acceder a los datos.
        
    Returns:
        Optional[User]: La entidad User si se encuentra, None en caso contrario.
    """
    # El handler simplemente delega la búsqueda al repositorio.
    # La lógica de negocio central está en el dominio/repositorio.
    return user_repository.get_by_id(query.user_id)
