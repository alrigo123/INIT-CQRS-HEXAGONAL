# RABBITMQ PUBLISHER (ADAPTADOR SECUNDARIO)
# Esta capa implementa un adaptador para publicar mensajes en RabbitMQ.
# Es un ADAPTADOR SECUNDARIO en Arquitectura Hexagonal.
# Se encarga de las interacciones con el sistema externo de mensajería.

import json # Para serializar mensajes
import pika # Cliente de RabbitMQ
import os # Para acceder a variables de entorno
from typing import Any, Dict # Para anotaciones de tipo

# --- Configuración de RabbitMQ ---
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
# Nombre de la cola donde se publicarán los comandos/eventos de autenticación
AUTH_COMMANDS_QUEUE = 'auth_commands'

class RabbitMQAuthPublisher:
    """
    Adaptador de infraestructura para publicar comandos/eventos de autenticación en RabbitMQ.
    Esta clase encapsula la lógica específica de Pika y RabbitMQ
    para enviar mensajes a una cola.
    """

    def __init__(self, rabbitmq_url: str = RABBITMQ_URL):
        """ Inicializa el publicador con la URL de RabbitMQ. """
        self.rabbitmq_url = rabbitmq_url
        # Atributos para la conexión y el canal, inicializados como None
        self._connection = None
        self._channel = None

    def _connect(self):
        """
        Establece la conexión y el canal con RabbitMQ si no están ya creados.
        Método privado (por convención, con `_`).
        """
        # Verifica si la conexión no existe o está cerrada
        if not self._connection or self._connection.is_closed:
            # Crea los parámetros de conexión desde la URL
            parameters = pika.URLParameters(self.rabbitmq_url)
            # Establece la conexión bloqueante
            self._connection = pika.BlockingConnection(parameters)
            # Crea un canal de comunicación
            self._channel = self._connection.channel()
            # Declara la cola para asegurarse de que existe (idempotente)
            self._channel.queue_declare(queue=AUTH_COMMANDS_QUEUE, durable=True)


    def publish_command(self, command_type: str, command_data: Dict[str, Any]):
        """ Publica un comando/evento genérico en la cola de RabbitMQ. """
        try:
            # Asegura que la conexión esté activa
            self._connect()

            # Crea un diccionario con el tipo y los datos del comando
            message_dict = {
                "type": command_type,
                "data": command_data
            }
            # Serializa el diccionario a una cadena JSON
            message_body = json.dumps(message_dict)

            # Publica el mensaje en la cola
            self._channel.basic_publish(
                exchange='', # Exchange por defecto (direct)
                routing_key=AUTH_COMMANDS_QUEUE, # Cola destino
                body=message_body, # Contenido del mensaje
                properties=pika.BasicProperties(
                    delivery_mode=2, # Hacer el mensaje persistente
                )
            )
            print(f"[x] Sent {command_type}")

        except pika.exceptions.AMQPConnectionError as e:
            # Maneja errores específicos de conexión
            print(f"Error de conexión a RabbitMQ: {e}")
            raise RuntimeError(f"No se pudo conectar a RabbitMQ: {e}") from e
        except Exception as e:
            # Maneja cualquier otro error
            print(f"Error al publicar el mensaje en RabbitMQ: {e}")
            raise RuntimeError(f"Error al publicar el comando/evento en RabbitMQ: {e}") from e


    def close(self):
        """
        Cierra la conexión con RabbitMQ.
        Método para liberar recursos.
        """
        # Verifica que la conexión exista y no esté ya cerrada
        if self._connection and not self._connection.is_closed:
            self._connection.close()

# --- Notas sobre la implementación ---
# `AUTH_COMMANDS_QUEUE`: Cola específica para comandos/eventos de `auth`.
#    Facilita el enrutamiento y el consumo específico por contexto.
# Manejo de errores: Captura y relanza excepciones con mensajes más descriptivos.
# Persistencia de mensajes: Los mensajes se guardan en disco para no perderlos.
# Lazy Initialization: La conexión se crea solo cuando se necesita.