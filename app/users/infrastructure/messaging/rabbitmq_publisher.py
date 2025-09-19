import json
import pika
from typing import Any, Dict

from ...application.commands.create_user_command import CreateUserCommand # Comando de aplicación que queremos enviar a través de mensajes

# --- Configuración de RabbitMQ ---
RABBITMQ_URL = "amqp://myapp_user:myapp_password@rabbitmq:5672/"

# Nombre de la cola donde se publicarán los comandos de creación de usuario
USER_COMMANDS_QUEUE = 'user_commands'

class RabbitMQPublisher:
    """
    Adaptador de infraestructura para publicar comandos en RabbitMQ.
    Implementa el patrón de mensajería para comunicación asíncrona entre servicios. 
    Publica comandos del dominio como mensajes JSON en colas.
    """

    def __init__(self, rabbitmq_url: str = RABBITMQ_URL):
        """
        Inicializa el publicador con la URL de RabbitMQ.
        """
        # Almacenamos la URL de conexión
        self.rabbitmq_url = rabbitmq_url
        # Inicializamos las conexiones como None
        self._connection = None
        self._channel = None


    def _connect(self):
        """
        Establece la conexión y el canal con RabbitMQ si no están ya creados.
        Este método solo crea la conexión cuando realmente se necesita, evitando conexiones innecesarias.
        """
        # Verificamos si ya tenemos una conexión válida
        if not self._connection or self._connection.is_closed:
            parameters = pika.URLParameters(self.rabbitmq_url) # pika.URLParameters parsea la URL y configura los parámetros
            # Establecer la conexión bloqueante con RabbitMQ
            self._connection = pika.BlockingConnection(parameters) # BlockingConnection bloquea el thread hasta completar operaciones
            # Crear un canal de comunicación sobre la conexión
            self._channel = self._connection.channel()
            
            # Declarar la cola para asegurarse de que existe
            self._channel.queue_declare(queue=USER_COMMANDS_QUEUE, durable=True) # durable=True hace que la cola sobreviva a reinicios del broker


    def publish_create_user(self, command: CreateUserCommand):
        """
        Publica un comando CreateUserCommand en la cola de RabbitMQ.
        Este método implementa la serialización y publicación de comandos.
        Convierte comandos del dominio en mensajes JSON para transporte.
        """
        try:
            # Conectarse a RabbitMQ
            self._connect()

            # Convertimos el dataclass a un diccionario y luego a JSON (proceso de serialización)
            command_dict = {
                # Identificador del tipo de comando para que el consumidor sepa qué procesar
                "type": "CreateUserCommand",
                # Los datos del comando
                "data": {
                    "name": command.name,
                    "email": command.email,
                    "password": command.password,
                    "user_id": command.user_id
                }
            }
            
            # Convertir a string JSON
            message_body = json.dumps(command_dict)

            # Publicar el mensaje en la cola
            self._channel.basic_publish(
                exchange='',                      # Exchange por defecto (direct)
                routing_key=USER_COMMANDS_QUEUE,  # Nombre de la cola destino
                body=message_body,                # Contenido del mensaje (JSON serializado)
                properties=pika.BasicProperties(
                    delivery_mode=2, # Persistente, Se guarda en disco y sobrevive reinicios del broker
                )
            )
            # Para debugging y monitoreo
            print(f"[x] Sent CreateUserCommand for '{command.name}'")

        except pika.exceptions.AMQPConnectionError as e:
            # Manejar errores específicos de conexión a RabbitMQ
            print(f"Error de conexión a RabbitMQ: {e}")
            raise RuntimeError(f"No se pudo conectar a RabbitMQ: {e}") from e
        except Exception as e:
            # Manejar otros errores de publicación (serialización, red, etc.)
            print(f"Error al publicar el mensaje en RabbitMQ: {e}")
            raise RuntimeError(f"Error al publicar el comando en RabbitMQ: {e}") from e

    def close(self):
        """
        Cierra la conexión con RabbitMQ.
        Es importante cerrar conexiones para liberar recursos del sistema y del broker de mensajes.
        """
        # Verificar que la conexión exista y no esté ya cerrada
        if self._connection and not self._connection.is_closed:
            self._connection.close()

# --- Notas sobre la implementación ---
# `pika`: Librería cliente de RabbitMQ para Python.
# `USER_COMMANDS_QUEUE`: Nombre de la cola. Es importante que el consumidor use el mismo nombre.
# Independencia del Dominio/Aplicación: Este publisher solo conoce el comando, no la lógica de negocio ni el handler. Solo sabe cómo enviarlo.
# Adaptador de Infraestructura: Conecta la aplicación con RabbitMQ.

# Rol en la Arquitectura
# Adaptador de mensajería: Publica comandos del dominio a colas de mensajes
# Serialización: Convierte comandos a JSON para transporte asíncrono
# Persistencia de mensajes: Configura mensajes y colas como durables para resiliencia
# Desacoplamiento: Permite comunicación asíncrona entre servicios
# Implementación CQRS: Facilita el procesamiento asíncrono de comandos