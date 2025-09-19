import re
from typing import Optional

class InvalidEmailError(Exception):
    """ Excepción lanzada cuando un email no es válido. """
    pass

class WeakPasswordError(Exception):
    """ Excepción lanzada cuando una contraseña no cumple con los criterios mínimos. """
    pass

class User:
    """
    Representa un Usuario en el dominio.
    Esta clase encapsula las propiedades y reglas de negocio básicas de un usuario.
    Es una ENTIDAD del dominio con identidad única e igualdad por ID.
    """

    def __init__(self, user_id: str, name: str, email: str, hashed_password: str):
        """
        Inicializa un nuevo Usuario.
        Raises:
            InvalidEmailError: Si el email no es válido.
            WeakPasswordError: Si la contraseña no cumple con los criterios.
        """
        # Regla de negocio Validación de email antes de crear la entidad
        if not self._is_valid_email(email):
            raise InvalidEmailError(f"El email '{email}' no es válido.")
        
        # Almacenar los atributos como propiedades privadas
        self._id = user_id
        self._name = name
        self._email = email.lower()
        self._hashed_password = hashed_password

    @property
    def id(self) -> str:
        """ Obtiene el ID del usuario. """
        return self._id

    @property
    def name(self) -> str:
        """ Obtiene el nombre del usuario. """
        return self._name

    @name.setter
    def name(self, value: str):
        """ Establece el nombre del usuario.
        VALIDACIÓN DE NEGOCIO: El nombre no puede estar vacío.
        Raises: ValueError: Si el nombre está vacío o solo espacios
        """
        # Validación básica de nombre no vacío
        if not value or not value.strip():
            raise ValueError("El nombre no puede estar vacío.")
        # Almacenar el nombre limpio de espacios
        self._name = value.strip()

    @property
    def email(self) -> str:
        """ Obtiene el email del usuario. """
        return self._email

    @property
    def hashed_password(self) -> str:
        """ Obtiene la contraseña hasheada del usuario. """
        return self._hashed_password


    def _is_valid_email(self, email: str) -> bool:
        """ Valida si un email tiene un formato básico correcto.
        REGLA DE NEGOCIO: Validación de formato de email.
        Esta lógica pertenece al dominio porque es una regla del negocio.
        Returns: bool: True si es válido, False si no
        """
        
        # Expresión regular básica para validar email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


    def __eq__(self, other) -> bool:
        """ Compara dos usuarios por su ID """
        if not isinstance(other, User):
            return False
        # Comparar por ID (identidad única)
        return self.id == other.id


    def __repr__(self) -> str:
        """ Representación del objeto User para debugging. """
        return f"<User(id='{self.id}', name='{self.name}', email='{self.email}')>"

# --- Notas sobre la implementación ---
# Excepciones personalizadas: Creamos `InvalidEmailError` para encapsular errores
#    específicos del dominio. Esto es parte de las buenas prácticas.
# Propiedades (`@property`): Usamos getters para encapsular el acceso a los atributos.
# Setters con validación: El setter de `name` incluye una validación básica.
# `_is_valid_email`: Método interno para validar el email. Mantiene la lógica de negocio
#    dentro del dominio.
# `__eq__` y `__repr__`: Métodos mágicos para facilitar comparaciones y debugging.

# Rol en la Arquitectura
# Entidad de dominio: Representa un concepto central del negocio con identidad única
# Reglas de negocio: Contiene validaciones y comportamiento específico del usuario
# Independencia: No tiene dependencias externas, solo lógica de negocio pura
# Lenguaje ubicuo: Usa términos del dominio (InvalidEmailError, WeakPasswordError)
# Inmutabilidad parcial: ID es inmutable, otros atributos tienen setters controlados