# app/users/application/queries/get_user_query.py
from dataclasses import dataclass

@dataclass(frozen=True)
class GetUserQuery:
    """
    Query para obtener la información de un usuario por su ID.
    
    PATRÓN DE DISEÑO: Query Pattern (CQRS)
    PATRÓN DE DISEÑO: Data Transfer Object (DTO)
    """
    user_id: str
