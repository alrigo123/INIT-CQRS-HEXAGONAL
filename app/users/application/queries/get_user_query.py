from dataclasses import dataclass

@dataclass(frozen=True)
class GetUserQuery:
    """ Query para obtener la información de un usuario por su ID. """
    user_id: str
