# app/users/infrastructure/messaging/rabbitmq_publisher.py
import json
import pika
from typing import Any, Dict
# Importamos el comando específico que vamos a publicar
# En una implementación más genérica, podrías tener una interfaz base para comandos
from ...application.commands.create_user_command import CreateUserCommand

# --- Configuración de RabbitMQ ---
# En una implementación real, estas configuraciones vendrían de variables de entorno
# RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
# Para simplificar y alinearse con docker-compose.yml, usamos directamente la URL
# Nota: En docker-compose.yml definimos: RABBITMQ_URL: amqp://myapp_user:myapp_password@rabbitmq:5672/
# Aquí la usamos directamente, pero en producción se recomienda usar variables de entorno.
RABBITMQ_URL = "amqp://myapp_user:myapp_password@rabbitmq:5672/"

# Nombre de la cola donde se publicarán los comandos de creación de usuario
USER_COMMANDS_QUEUE = 'user_commands'

class RabbitMQPublisher:
    """
    Adaptador de infraestructura para publicar comandos en RabbitMQ.
    Esta clase encapsula la lógica específica de Pika y RabbitMQ
    para enviar mensajes a una cola.
    """

    def __init__(self, rabbitmq_url: str = RABBITMQ_URL):
        """
        Inicializa el publicador con la URL de RabbitMQ.

        Args:
            rabbitmq_url (str): La URL de conexión a RabbitMQ.
                                En producción, debería venir de variables de entorno.
        """
        self.rabbitmq_url = rabbitmq_url
        self._connection = None
        self._channel = None

    def _connect(self):
        """Establece la conexión y el canal con RabbitMQ si no están ya creados."""
        if not self._connection or self._connection.is_closed:
            # Crear la conexión
            parameters = pika.URLParameters(self.rabbitmq_url)
            self._connection = pika.BlockingConnection(parameters)
            # Crear el canal
            self._channel = self._connection.channel()
            # Declarar la cola para asegurarse de que existe
            # durable=True hace que la cola sobreviva a reinicios del broker
            self._channel.queue_declare(queue=USER_COMMANDS_QUEUE, durable=True)

    def publish_create_user(self, command: CreateUserCommand):
        """
        Publica un comando CreateUserCommand en la cola de RabbitMQ.

        Args:
            command (CreateUserCommand): El comando a publicar.
        """
        try:
            # 1. Conectarse a RabbitMQ (si no lo está ya)
            self._connect()

            # 2. Serializar el comando a un formato que se pueda enviar (por ejemplo, JSON)
            # Convertimos el dataclass a un diccionario y luego a JSON
            command_dict = {
                "type": "CreateUserCommand", # Identificador del tipo de comando
                "data": {
                    "name": command.name,
                    "email": command.email,
                    "password": command.password # En producción, considera no enviar la pass en texto plano
                }
            }
            message_body = json.dumps(command_dict)

            # 3. Publicar el mensaje en la cola
            # exchange='' significa usar el exchange por defecto (direct exchange)
            # routing_key es el nombre de la cola cuando se usa el exchange por defecto
            # properties con delivery_mode=2 hace que el mensaje sea persistente
            self._channel.basic_publish(
                exchange='',
                routing_key=USER_COMMANDS_QUEUE,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2, # Hacer el mensaje persistente
                )
            )
            print(f"[x] Sent CreateUserCommand for '{command.name}'") # Para debugging

        except pika.exceptions.AMQPConnectionError as e:
            # Manejar errores de conexión
            print(f"Error de conexión a RabbitMQ: {e}")
            raise RuntimeError(f"No se pudo conectar a RabbitMQ: {e}") from e
        except Exception as e:
            # Manejar otros errores de publicación
            print(f"Error al publicar el mensaje en RabbitMQ: {e}")
            raise RuntimeError(f"Error al publicar el comando en RabbitMQ: {e}") from e

    def close(self):
        """Cierra la conexión con RabbitMQ."""
        if self._connection and not self._connection.is_closed:
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