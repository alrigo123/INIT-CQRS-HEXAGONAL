from typing import Optional
from .get_user_query import GetUserQuery
from ...domain.models import User
from ...domain.repositories import UserRepository

def handle_get_user(
    query: GetUserQuery,
    user_repository: UserRepository
) -> Optional[User]:
    """
    Handler para el query GetUserQuery.
    Returns: Optional[User]: La entidad User si se encuentra, None en caso contrario.
    """
    # El handler simplemente delega la búsqueda al repositorio.
    return user_repository.get_by_id(query.user_id)
