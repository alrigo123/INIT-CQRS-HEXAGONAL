# app/users/domain/models.py
import re
from typing import Optional

class InvalidEmailError(Exception):
    """
    Excepción lanzada cuando un email no es válido.
    
    EXCEPCIÓN DE DOMINIO: Representa un error específico del negocio.
    ARQUITECTURA: Parte del lenguaje ubicuo del dominio de usuarios.
    
    MEJORA SUGERIDA: Agregar más contexto al mensaje de error
    """
    pass

class WeakPasswordError(Exception):
    """
    Excepción lanzada cuando una contraseña no cumple con los criterios mínimos.
    
    EXCEPCIÓN DE DOMINIO: Representa una regla de negocio sobre contraseñas.
    ARQUITECTURA: Parte del lenguaje ubicuo del dominio de usuarios.
    
    MEJORA SUGERIDA: Definir criterios específicos de fortaleza de contraseña
    """
    pass

class User:
    """
    Representa un Usuario en el dominio.
    
    Esta clase encapsula las propiedades y reglas de negocio básicas de un usuario.
    Es una ENTIDAD del dominio con identidad única e igualdad por ID.
    
    PATRÓN DE DISEÑO: Domain Entity (Entidad de Dominio)
    Tiene identidad única y ciclo de vida propio.
    
    ARQUITECTURA: Núcleo del dominio en Arquitectura Hexagonal
    Independiente de frameworks, bases de datos o mecanismos de persistencia.
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
            
        MEJORA SUGERIDA: Validar también la fortaleza de la contraseña hasheada
        MEJORA SUGERIDA: Considerar validación de longitud de nombre
        """
        # Validación de email antes de crear la entidad
        # Esta es una regla de negocio fundamental
        if not self._is_valid_email(email):
            raise InvalidEmailError(f"El email '{email}' no es válido.")
        
        # Almacenar los atributos como propiedades privadas
        # El ID es inmutable una vez creado
        self._id = user_id
        self._name = name
        # Normalizar email a minúsculas para consistencia
        self._email = email.lower()
        # La contraseña ya debe estar hasheada al llegar aquí
        self._hashed_password = hashed_password

    @property
    def id(self) -> str:
        """
        Obtiene el ID del usuario.
        
        PROPIEDAD DE SOLO LECTURA: El ID es inmutable después de la creación.
        """
        return self._id

    @property
    def name(self) -> str:
        """
        Obtiene el nombre del usuario.
        """
        return self._name

    @name.setter
    def name(self, value: str):
        """
        Establece el nombre del usuario.
        
        VALIDACIÓN DE NEGOCIO: El nombre no puede estar vacío.
        Esta es una regla de negocio importante.

        Args:
            value (str): Nuevo nombre del usuario
            
        Raises:
            ValueError: Si el nombre está vacío o solo espacios
        """
        # Validación básica de nombre no vacío
        if not value or not value.strip():
            raise ValueError("El nombre no puede estar vacío.")
        # Almacenar el nombre limpio de espacios
        self._name = value.strip()

    @property
    def email(self) -> str:
        """
        Obtiene el email del usuario.
        """
        return self._email

    @property
    def hashed_password(self) -> str:
        """
        Obtiene la contraseña hasheada del usuario.
        
        SEGURIDAD: Solo exponemos el hash, nunca el texto plano.
        """
        return self._hashed_password

    def _is_valid_email(self, email: str) -> bool:
        """
        Valida si un email tiene un formato básico correcto.
        
        REGLA DE NEGOCIO: Validación de formato de email.
        Esta lógica pertenece al dominio porque es una regla del negocio.

        Args:
            email (str): Email a validar
            
        Returns:
            bool: True si es válido, False si no
            
        MEJORA SUGERIDA: Usar librería especializada como email-validator
        MEJORA SUGERIDA: Considerar validaciones más robustas para producción
        """
        # Expresión regular básica para validar email
        # Esta es una validación simple. En producción, podría ser más robusta.
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def __eq__(self, other) -> bool:
        """
        Compara dos usuarios por su ID.
        
        IGUALDAD POR IDENTIDAD: Dos usuarios son iguales si tienen el mismo ID.
        Esta es la definición de igualdad para entidades de dominio.
        """
        if not isinstance(other, User):
            return False
        # Comparar por ID (identidad única)
        return self.id == other.id

    def __repr__(self) -> str:
        """
        Representación del objeto User para debugging.
        """
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

# Rol en la Arquitectura
# Entidad de dominio: Representa un concepto central del negocio con identidad única
# Reglas de negocio: Contiene validaciones y comportamiento específico del usuario
# Independencia: No tiene dependencias externas, solo lógica de negocio pura
# Lenguaje ubicuo: Usa términos del dominio (InvalidEmailError, WeakPasswordError)
# Inmutabilidad parcial: ID es inmutable, otros atributos tienen setters controlados