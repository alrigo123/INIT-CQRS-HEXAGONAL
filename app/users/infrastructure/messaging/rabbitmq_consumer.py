# app/users/infrastructure/messaging/rabbitmq_consumer.py
import json
import pika
import traceback
import time
import os # Para obtener variables de entorno

# Importamos el comando que vamos a consumir
from ...application.commands.create_user_command import CreateUserCommand

# Importamos el handler que procesará el comando
# Nota: En una implementación más avanzada, esto podría ser inyectado.
from ...application.commands.handlers import handle_create_user

# Importamos dependencias necesarias para el handler
# (En una implementación real, estas vendrían de un sistema de inyección de dependencias)
from ...infrastructure.persistence.database import SessionLocal, create_tables
from ...infrastructure.persistence.repositories import SQLAlchemyUserRepository

# Para simular el hashing de contraseña (en una implementación real, usar una librería como passlib)
import hashlib

from pika.exceptions import AMQPConnectionError

# --- Configuración de RabbitMQ ---
# Alineada con el publisher y docker-compose.yml
# Se recomienda usar variables de entorno en lugar de valores fijos
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
USER_COMMANDS_QUEUE = "user_commands"


def dummy_hash_password(password: str) -> str:
    """
    Función de ejemplo para hashear una contraseña.
    En una implementación real, usar una librería segura como passlib.
    """
    # Usamos hashlib para una simulación básica. No es seguro para producción.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def process_create_user_command(command_data: dict):
    """
    Procesa un comando CreateUserCommand deserializado.
    Esta función orquesta la obtención de dependencias y la ejecución del handler.
    """
    print(f"[.] Processing CreateUserCommand for '{command_data['name']}'")

    # 1. Crear el objeto comando desde los datos deserializados
    command = CreateUserCommand(
        name=command_data["name"],
        email=command_data["email"],
        password=command_data["password"],
    )

    # 2. Obtener dependencias necesarias para el handler
    # En una arquitectura más avanzada, esto vendría de un contenedor de inyección de dependencias.
    db_session = SessionLocal()
    user_repository = SQLAlchemyUserRepository(db_session)
    hash_password_fn = dummy_hash_password  # O una función real de hashing

    try:
        # 3. Invocar al handler de aplicación
        # Pasamos el comando y las dependencias inyectadas
        user_id = handle_create_user(command, user_repository, hash_password_fn)
        print(f"[.] Successfully created user with ID: {user_id}")
    except Exception as e:
        # Manejar errores del handler (validaciones, problemas de BD, etc.)
        print(f"[!] Error processing CreateUserCommand: {e}")
        traceback.print_exc()  # Para debugging
        # En un sistema real, podrías reencolar el mensaje, enviarlo a una cola de dead-letter, etc.
    finally:
        # 4. Cerrar la sesión de la base de datos
        db_session.close()


# --- Importante: La definición de 'callback' debe estar ANTES de 'start_consuming' ---
def callback(ch, method, properties, body):
    """
    Función callback que se ejecuta cada vez que se recibe un mensaje de RabbitMQ.
    
    Args:
        ch: Canal de comunicación.
        method: Información sobre el método de entrega.
        properties: Propiedades del mensaje.
        body: Cuerpo del mensaje (los datos).
    """
    try:
        # 1. Decodificar el cuerpo del mensaje (de bytes a string)
        message_str = body.decode('utf-8')
        print(f"[x] Received raw message: {message_str}")

        # 2. Deserializar el mensaje de JSON a un diccionario de Python
        message_data = json.loads(message_str)

        # 3. Determinar el tipo de comando y procesarlo
        command_type = message_data.get("type")
        command_data = message_data.get("data")

        if command_type == "CreateUserCommand" and command_data:
            # Corrección: pasar command_data, no command_
            process_create_user_command(command_data)
        else:
            print(f"[!] Unknown command type or missing data: {command_type}")

        # 4. Enviar ACK manualmente para confirmar que el mensaje fue procesado
        # Esto es importante para la resiliencia de RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        print(f"[!] Failed to decode JSON: {e}")
        # Es importante rechazar (reject) o enviar a una cola de dead-letter mensajes no válidos
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        print(f"[!] Error in callback: {e}")
        traceback.print_exc()
        # Rechazar el mensaje. requeue=False lo manda a una cola de dead-letter si está configurada.
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming():
    """
    Inicia el consumidor de comandos de RabbitMQ.
    Se conecta a la cola y comienza a escuchar mensajes.
    """
    # Asegurarse de que las tablas de la BD existen
    create_tables()

    # --- Nueva lógica de conexión con reintentos ---
    max_retries = 5
    retry_delay = 5  # segundos

    for attempt in range(1, max_retries + 1):
        try:
            print(
                f"[.] Intentando conectar a RabbitMQ (Intento {attempt}/{max_retries})..."
            )
            # 1. Conectarse a RabbitMQ
            # Usar la variable de entorno RABBITMQ_URL
            parameters = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            print("[.] Conexión a RabbitMQ establecida.")
            break  # Si la conexión es exitosa, salimos del bucle
        except AMQPConnectionError as e:
            print(f"[!] Error de conexión a RabbitMQ (Intento {attempt}): {e}")
            if attempt < max_retries:
                print(f"[.] Esperando {retry_delay} segundos antes de reintentar...")
                time.sleep(retry_delay)
            else:
                print("[!] Todos los intentos de conexión a RabbitMQ fallaron.")
                raise  # Relanzar la excepción si se agotaron los reintentos
        except Exception as e:
            print(f"[!] Error inesperado al conectar a RabbitMQ: {e}")
            raise  # Relanzar cualquier otro error inesperado

    # 2. Declarar la cola (por si acaso el publisher aún no la ha creado)
    channel.queue_declare(queue=USER_COMMANDS_QUEUE, durable=True)

    # 3. Configurar la calidad de servicio
    channel.basic_qos(prefetch_count=1)

    # 4. Configurar el consumidor
    # Ahora 'callback' está definido antes, por lo que esta línea funcionará
    channel.basic_consume(
        queue=USER_COMMANDS_QUEUE, on_message_callback=callback, auto_ack=False
    )

    print("[*] Waiting for messages. To exit press CTRL+C")
    try:
        # 5. Comenzar a consumir mensajes
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[-] Stopping consumer...")
        channel.stop_consuming()
        connection.close()

# --- Notas sobre la implementación ---
# 1. `pika`: Librería cliente de RabbitMQ.
# 2. Importaciones: Importa comandos, handlers y dependencias de infraestructura.
# 3. `dummy_hash_password`: Simulación de hashing. En producción, usar librerías seguras.
# 4. `process_create_user_command`: Función auxiliar que orquesta la ejecución del handler
#    con sus dependencias inyectadas manualmente.
# 5. `callback`: La función principal que Pika llama al recibir un mensaje.
#    - Decodifica y deserializa el mensaje.
#    - Determina el tipo de comando.
#    - Llama al procesador específico.
#    - Envía ACK/NACK según el resultado.
# 6. `start_consuming`: Función principal para iniciar el bucle de consumo.
#    - Crea tablas si no existen.
#    - Se conecta a RabbitMQ.
#    - Declara la cola.
#    - Configura QoS.
#    - Registra el callback.
#    - Inicia el consumo.
# 7. Manejo de ACK/NACK: Crucial para la resiliencia. ACK confirma éxito, NACK maneja errores.
# 8. `basic_qos(prefetch_count=1)`: Evita sobrecarga del consumidor.
# 9. Inyección de Dependencias Manual: Las dependencias (repo, hasher) se crean dentro
#    de `process_create_user_command`. En una arquitectura avanzada, se usaría un contenedor DI.
# 10. Manejo de Errores: Se capturan y manejan errores de deserialización y procesamiento.
# 11. Proceso Independiente: Este script está diseñado para ejecutarse como un worker separado.