# app/users/application/commands/create_user_command.py
from dataclasses import dataclass
from typing import Optional # Asegúrate de tener esta importación

@dataclass(frozen=True)  # frozen=True hace que el objeto sea inmutable
class CreateUserCommand:
    """
    Comando para crear un nuevo usuario.
    
    Este comando representa una INTENCIÓN de escritura en el sistema.
    Es un objeto de transferencia de datos (DTO) que encapsula los datos
    necesarios para la operación de creación.
    
    PATRÓN DE DISEÑO: Command Pattern (Patrón Comando)
    PATRÓN DE DISEÑO: Data Transfer Object (DTO)
    
    ARQUITECTURA: Parte de la capa de Aplicación en CQRS
    Representa un comando de escritura que se puede serializar y enviar.
    
    INMUTABILIDAD: frozen=True garantiza que el comando no cambie después de crearlo.
    Esto es importante para la consistencia y para mensajería.
    """
    
    # Atributos del comando - solo datos necesarios para la operación
    name: str
    email: str
    password: str
    user_id: Optional[str] = None # Hacerlo opcional es buena práctica

# --- Notas sobre la implementación ---
# 1. `@dataclass`: Es una forma concisa de crear clases que principalmente 
#    almacenan datos. Genera automáticamente `__init__`, `__repr__`, `__eq__`, etc.
# 2. `frozen=True`: Hace que la instancia sea inmutable después de su creación.
#    Esto es una buena práctica para objetos comando/consulta, ya que representan
#    una solicitud específica en un momento dado.
# 3. Atributos simples: Solo contiene los datos necesarios. No incluye lógica de negocio.
# 4. Contraseña en texto plano: El comando lleva la contraseña tal como se recibe.
#    La responsabilidad de hashearla recae en la capa de aplicación o infraestructura.
# 5. Independiente: Este comando no depende de frameworks ni de la capa de dominio.
#    Pertenece a la capa de Aplicación.

# Rol en la Arquitectura
# Comando CQRS: Representa una intención de escritura en el sistema
# Transporte de datos: Solo contiene datos necesarios para la operación
# Inmutabilidad: frozen=True garantiza que el comando no cambie
# Serialización: Fácilmente convertible a JSON para mensajería
# Separación de concerns: Comandos separados de la lógica de negocio