# app/users/application/commands/create_user_command.py
from dataclasses import dataclass

@dataclass(frozen=True) # frozen=True hace que el objeto sea inmutable
class CreateUserCommand:
    """
    Comando para crear un nuevo usuario.
    Este comando encapsula los datos necesarios para la operación de creación.
    Es inmutable y se puede serializar fácilmente para ser enviado a través de colas de mensajes como RabbitMQ.
    
    Atributos:
        name (str): El nombre del usuario.
        email (str): El correo electrónico del usuario.
        password (str): La contraseña en texto plano del usuario (será hasheada en la capa de aplicación o infraestructura).
    """
    name: str
    email: str
    password: str

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