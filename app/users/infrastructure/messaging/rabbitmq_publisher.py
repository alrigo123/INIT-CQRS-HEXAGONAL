# app/users/infrastructure/messaging/rabbitmq_publisher.py
import json
import pika
from typing import Any, Dict

# Importamos el comando específico que vamos a publicar
# Este es el comando de aplicación que queremos enviar a través de mensajes
from ...application.commands.create_user_command import CreateUserCommand

# --- Configuración de RabbitMQ ---
# En una implementación real, estas configuraciones vendrían de variables de entorno
# Esta URL debe coincidir con la configuración de tu docker-compose.yml
RABBITMQ_URL = "amqp://myapp_user:myapp_password@rabbitmq:5672/"

# Nombre de la cola donde se publicarán los comandos de creación de usuario
# Es crucial que consumidores y publicadores usen el mismo nombre de cola
USER_COMMANDS_QUEUE = 'user_commands'

class RabbitMQPublisher:
    """
    Adaptador de infraestructura para publicar comandos en RabbitMQ.
    
    Este adaptador implementa el patrón de mensajería para comunicación asíncrona
    entre servicios. Publica comandos del dominio como mensajes JSON en colas.
    
    PATRÓN DE DISEÑO: Adaptador (Adapter Pattern)
    ARQUITECTURA: Parte de la capa de infraestructura en Arquitectura Hexagonal
    MENSAJERÍA: Implementa publicador en sistema de colas RabbitMQ
    """

    def __init__(self, rabbitmq_url: str = RABBITMQ_URL):
        """
        Inicializa el publicador con la URL de RabbitMQ.

        Args:
            rabbitmq_url (str): La URL de conexión a RabbitMQ.
                                En producción, debería venir de variables de entorno.
                                
        MEJORA SUGERIDA: Usar variables de entorno en lugar de URL hardcoded
        """
        # Almacenamos la URL de conexión para usarla cuando se necesite conectar
        self.rabbitmq_url = rabbitmq_url
        # Inicializamos las conexiones como None, se crearán cuando se necesiten
        self._connection = None
        self._channel = None

    def _connect(self):
        """
        Establece la conexión y el canal con RabbitMQ si no están ya creados.
        
        PATRÓN DE DISEÑO: Lazy Initialization (Inicialización Perezosa)
        Este método solo crea la conexión cuando realmente se necesita,
        evitando conexiones innecesarias.
        """
        # Verificamos si ya tenemos una conexión válida
        if not self._connection or self._connection.is_closed:
            # Crear los parámetros de conexión usando la URL configurada
            # pika.URLParameters parsea la URL y configura los parámetros automáticamente
            parameters = pika.URLParameters(self.rabbitmq_url)
            
            # Establecer la conexión bloqueante con RabbitMQ
            # BlockingConnection es simple pero bloquea el thread hasta completar operaciones
            self._connection = pika.BlockingConnection(parameters)
            
            # Crear un canal de comunicación sobre la conexión
            # Los canales son "lightweight connections" que comparten la misma conexión TCP
            self._channel = self._connection.channel()
            
            # Declarar la cola para asegurarse de que existe
            # durable=True hace que la cola sobreviva a reinicios del broker
            # Esto es importante para no perder mensajes si RabbitMQ se reinicia
            self._channel.queue_declare(queue=USER_COMMANDS_QUEUE, durable=True)

    def publish_create_user(self, command: CreateUserCommand):
        """
        Publica un comando CreateUserCommand en la cola de RabbitMQ.
        
        Este método implementa la serialización y publicación de comandos.
        Convierte comandos del dominio en mensajes JSON para transporte.

        Args:
            command (CreateUserCommand): El comando a publicar.
            
        MEJORA SUGERIDA: No enviar passwords en texto plano por colas
        MEJORA SUGERIDA: Agregar logging para auditoría de mensajes
        """
        try:
            # 1. Conectarse a RabbitMQ (si no lo está ya)
            # El método _connect maneja la inicialización perezosa
            self._connect()

            # 2. Serializar el comando a un formato que se pueda enviar (por ejemplo, JSON)
            # Convertimos el dataclass a un diccionario y luego a JSON
            # Este es el proceso de serialización para transporte por mensajes
            command_dict = {
                # Identificador del tipo de comando para que el consumidor sepa qué procesar
                "type": "CreateUserCommand",
                # Los datos reales del comando
                "data": {
                    "name": command.name,
                    "email": command.email,
                    # ADVERTENCIA DE SEGURIDAD: Enviar password en texto plano por colas
                    # no es recomendable. Considerar hashing previo o tokens temporales.
                    "password": command.password
                }
            }
            # Convertir el diccionario a string JSON para enviarlo como mensaje
            message_body = json.dumps(command_dict)

            # 3. Publicar el mensaje en la cola
            # exchange='' significa usar el exchange por defecto (direct exchange)
            # routing_key es el nombre de la cola cuando se usa el exchange por defecto
            # properties con delivery_mode=2 hace que el mensaje sea persistente
            self._channel.basic_publish(
                exchange='',  # Exchange por defecto (direct)
                routing_key=USER_COMMANDS_QUEUE,  # Nombre de la cola destino
                body=message_body,  # Contenido del mensaje (JSON serializado)
                properties=pika.BasicProperties(
                    # delivery_mode=2 hace que el mensaje sea persistente
                    # Se guarda en disco y sobrevive reinicios del broker
                    delivery_mode=2,
                )
            )
            # Para debugging y monitoreo
            print(f"[x] Sent CreateUserCommand for '{command.name}'")

        except pika.exceptions.AMQPConnectionError as e:
            # Manejar errores específicos de conexión a RabbitMQ
            # AMQPConnectionError ocurre cuando no se puede establecer conexión
            print(f"Error de conexión a RabbitMQ: {e}")
            raise RuntimeError(f"No se pudo conectar a RabbitMQ: {e}") from e
        except Exception as e:
            # Manejar otros errores de publicación (serialización, red, etc.)
            print(f"Error al publicar el mensaje en RabbitMQ: {e}")
            raise RuntimeError(f"Error al publicar el comando en RabbitMQ: {e}") from e

    def close(self):
        """
        Cierra la conexión con RabbitMQ.
        
        Es importante cerrar conexiones para liberar recursos del sistema
        y del broker de mensajes.
        """
        # Verificar que la conexión exista y no esté ya cerrada
        if self._connection and not self._connection.is_closed:
            # Cerrar la conexión liberará todos los recursos asociados
            self._connection.close()

# --- Notas sobre la implementación ---
# 1. `pika`: Librería cliente de RabbitMQ para Python.
# 2. `RABBITMQ_URL`: URL de conexión. Alineada con docker-compose.yml.
# 3. `USER_COMMANDS_QUEUE`: Nombre de la cola. Es importante que el consumidor use el mismo nombre.
# 4. `_connect()`: Método interno para gestionar la conexión y declaración de la cola.
# 5. `publish_create_user()`: Método público para publicar el comando específico.
# 6. Serialización: Se convierte el comando a JSON. Es crucial para enviarlo como string.
# 7. `queue_declare(durable=True)`: Hace que la cola sea persistente.
# 8. `basic_publish` con `delivery_mode=2`: Hace que el mensaje sea persistente.
# 9. Manejo de Excepciones: Se capturan errores específicos de Pika y otros errores generales.
# 10. `close()`: Método para cerrar recursos, importante para liberar conexiones.
# 11. Independencia del Dominio/Aplicación: Este publisher solo conoce el comando,
#     no la lógica de negocio ni el handler. Solo sabe cómo enviarlo.
# 12. Adaptador de Infraestructura: Conecta la aplicación con RabbitMQ.

# Rol en la Arquitectura
# Adaptador de mensajería: Publica comandos del dominio a colas de mensajes
# Serialización: Convierte comandos a JSON para transporte asíncrono
# Persistencia de mensajes: Configura mensajes y colas como durables para resiliencia
# Desacoplamiento: Permite comunicación asíncrona entre servicios
# Implementación CQRS: Facilita el procesamiento asíncrono de comandos