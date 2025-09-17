# app/auth/infrastructure/messaging/rabbitmq_publisher.py
import json
import pika
import os
from typing import Any, Dict

# --- Configuración de RabbitMQ ---
# Alineada con docker-compose.yml
# Se recomienda usar variables de entorno
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
# Nombre de la cola donde se publicarán los comandos de autenticación
AUTH_COMMANDS_QUEUE = 'auth_commands'

class RabbitMQAuthPublisher:
    """
    Adaptador de infraestructura para publicar comandos de autenticación en RabbitMQ.
    Esta clase encapsula la lógica específica de Pika y RabbitMQ
    para enviar mensajes a una cola.
    """

    def __init__(self, rabbitmq_url: str = RABBITMQ_URL):
        """
        Inicializa el publicador con la URL de RabbitMQ.

        Args:
            rabbitmq_url (str): La URL de conexión a RabbitMQ.
        """
        self.rabbitmq_url = rabbitmq_url
        self._connection = None
        self._channel = None

    def _connect(self):
        """Establece la conexión y el canal con RabbitMQ si no están ya creados."""
        if not self._connection or self._connection.is_closed:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            # Declarar la cola para asegurarse de que existe
            self._channel.queue_declare(queue=AUTH_COMMANDS_QUEUE, durable=True)

    def publish_command(self, command_type: str, command_data: Dict[str, Any]):
        """
        Publica un comando genérico en la cola de RabbitMQ.

        Args:
            command_type (str): El tipo de comando (ej: "RegisterUserCommand").
            command_data (Dict[str, Any]): Los datos del comando.
        """
        try:
            self._connect()

            message_dict = {
                "type": command_type,
                "data": command_data
            }
            message_body = json.dumps(message_dict)

            self._channel.basic_publish(
                exchange='',
                routing_key=AUTH_COMMANDS_QUEUE,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2, # Hacer el mensaje persistente
                )
            )
            print(f"[x] Sent {command_type}")

        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error de conexión a RabbitMQ: {e}")
            raise RuntimeError(f"No se pudo conectar a RabbitMQ: {e}") from e
        except Exception as e:
            print(f"Error al publicar el mensaje en RabbitMQ: {e}")
            raise RuntimeError(f"Error al publicar el comando en RabbitMQ: {e}") from e

    def close(self):
        """Cierra la conexión con RabbitMQ."""
        if self._connection and not self._connection.is_closed:
            self._connection.close()

# --- Notas sobre la implementación ---
# 1. Similar al publisher de `users`, pero con una cola diferente.
# 2. `publish_command`: Método genérico para publicar cualquier comando de `auth`.
# 3. `AUTH_COMMANDS_QUEUE`: Cola específica para comandos de `auth`.
# 4. Uso de variables de entorno para la configuración.