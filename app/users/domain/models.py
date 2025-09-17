import re
from typing import Optional
# Nota: Usar str para el ID es una forma simple de mantener independencia.

class InvalidEmailError(Exception):
    """Excepción lanzada cuando un email no es válido."""
    pass

class WeakPasswordError(Exception):
    """Excepción lanzada cuando una contraseña no cumple con los criterios mínimos."""
    pass

class User:
    """
    Representa un Usuario en el dominio.
    Esta clase encapsula las propiedades y reglas de negocio básicas de un usuario.
    Es independiente de frameworks, bases de datos o mecanismos de persistencia.
    """

    def __init__(self, user_id: str, name: str, email: str, hashed_password: str):
        """
        Inicializa un nuevo Usuario.

        Args:
            user_id (str): El identificador único del usuario.
            name (str): El nombre del usuario.
            email (str): El correo electrónico del usuario.
            hashed_password (str): La contraseña del usuario, ya hasheada.
        
        Raises:
            InvalidEmailError: Si el email no es válido.
            WeakPasswordError: Si la contraseña no cumple con los criterios.
            # Nota: En una implementación real, hashed_password debería ser validado
            # por la capa de aplicación o infraestructura que lo genera.
        """
        if not self._is_valid_email(email):
            raise InvalidEmailError(f"El email '{email}' no es válido.")
        # Nota: Validar la contraseña hasheada aquí no es típico,
        # ya que la validación y hashing ocurren antes de crear el dominio.
        # Pero podemos asumir que hashed_password ya es seguro.
        
        self._id = user_id
        self._name = name
        self._email = email.lower() # Normalizar email
        self._hashed_password = hashed_password

    @property
    def id(self) -> str:
        """Obtiene el ID del usuario."""
        return self._id

    @property
    def name(self) -> str:
        """Obtiene el nombre del usuario."""
        return self._name

    @name.setter
    def name(self, value: str):
        """Establece el nombre del usuario."""
        if not value or not value.strip():
            raise ValueError("El nombre no puede estar vacío.")
        self._name = value.strip()

    @property
    def email(self) -> str:
        """Obtiene el email del usuario."""
        return self._email

    @property
    def hashed_password(self) -> str:
        """Obtiene la contraseña hasheada del usuario."""
        return self._hashed_password

    def _is_valid_email(self, email: str) -> bool:
        """
        Valida si un email tiene un formato básico correcto.
        Esta es una validación simple. En producción, podría ser más robusta.
        """
        # Expresión regular básica para validar email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def __eq__(self, other) -> bool:
        """Compara dos usuarios por su ID."""
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        """Representación del objeto User."""
        return f"<User(id='{self.id}', name='{self.name}', email='{self.email}')>"

# --- Notas sobre la implementación ---
# 1. `user_id` como `str`: Mantenemos la simplicidad. En la infraestructura (SQLAlchemy)
#    podríamos usar UUID o Integer, pero el dominio lo trata como un identificador opaco.
# 2. Excepciones personalizadas: Creamos `InvalidEmailError` para encapsular errores
#    específicos del dominio. Esto es parte de las buenas prácticas.
# 3. Propiedades (`@property`): Usamos getters para encapsular el acceso a los atributos.
# 4. Setters con validación: El setter de `name` incluye una validación básica.
# 5. `_is_valid_email`: Método interno para validar el email. Mantiene la lógica de negocio
#    dentro del dominio.
# 6. `__eq__` y `__repr__`: Métodos mágicos para facilitar comparaciones y debugging.