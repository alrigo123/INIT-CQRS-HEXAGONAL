import json
import pika
import traceback
import time
import os
import bcrypt
from typing import Dict, Any

# Para manejar errores específicos de conexión de RabbitMQ
from pika.exceptions import AMQPConnectionError

# Importamos el comando que vamos a consumir
from ...application.commands.create_user_command import CreateUserCommand

# Importamos el handler que procesará el comando
from ...application.commands.handlers import handle_create_user

# Importamos la interfaz para el tipado y claridad
from app.users.domain.repositories import UserRepository

# Importamos el DI Container para obtener dependencias
from app.shared.di_container import get_user_repository

# Importa la función create_tables para asegurar que las tablas existen
from ...infrastructure.persistence.database import create_tables


# --- Configuración de RabbitMQ ---
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

# Nombre de la cola que consumira los comandos de creación de usuario
USER_COMMANDS_QUEUE = "user_commands"

# FUNCIÓN SEGURA DE HASHEO ---
def secure_hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    *** IMPLEMENTACIÓN SEGURA ***
    """
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8') # String para poder serializar/deserializar fácilmente
    except Exception as e:
        print(f"[!] Error al hashear contraseña con bcrypt: {e}")
        raise RuntimeError(f"Error al hashear la contraseña: {e}") from e


def process_create_user_command(command_data: Dict[str, Any]):
    """
    Procesa un comando CreateUserCommand deserializado.
    Esta función orquesta la obtención de dependencias y la ejecución del handler.
    Es el punto de entrada para procesar comandos recibidos de la cola.
    """
    print(f"[.] Processing CreateUserCommand for '{command_data['name']}'")
    
    try:
        plain_password = command_data["password"]
        hashed_password = secure_hash_password(plain_password) # Llamar a la funcion de hasheo
        print(f"[.] Contraseña hasheada para el usuario '{command_data['name']}'.")
    except Exception as e:
        print(f"[!] Error al hashear la contraseña antes de crear el comando: {e}")
        return

    # Crear el comando a partir de los datos deserializados
    command = CreateUserCommand(
        name=command_data["name"],
        email=command_data["email"],
        password=hashed_password,
        user_id=command_data.get("user_id")
    )

    # Obtenemos directamente la interfaz UserRepository del contenedor DI.
    try:
        user_repository: UserRepository = get_user_repository() # INYECCION DEL CONTENEDORD DI
        print("[.] UserRepository obtenido del DI container.")
    except Exception as e:
        print(f"[!] Error al obtener UserRepository del DI container: {e}")
        return
    
    try:
        # Invocar al handler de aplicación
        user_id = handle_create_user(command, user_repository) # INYECCION DEL HANDLER
        print(f"[.] Successfully created user with ID: {user_id}")
    except Exception as e:
        print(f"[!] Error processing CreateUserCommand: {e}")
        traceback.print_exc()


def callback(ch, method, properties, body):
    """
    Función callback que se ejecuta cada vez que se recibe un mensaje de RabbitMQ.
    Este es el punto de entrada principal para el consumidor de mensajes.
    Se ejecuta automáticamente cuando RabbitMQ entrega un mensaje a este consumidor.
    """
    try:
        # Decodificar el cuerpo del mensaje (de bytes a string)
        message_str = body.decode('utf-8')
        print(f"[x] Received raw message: {message_str}")

        # Deserializar el mensaje de JSON a un diccionario de Python
        message_data = json.loads(message_str)

        # Determinar el tipo de comando y procesarlo
        command_type = message_data.get("type")
        command_data = message_data.get("data")

        # Procesamos solo los comandos que conocemos
        if command_type == "CreateUserCommand":
            process_create_user_command(command_data)
        else:
            # Manejar comandos desconocidos o mensajes mal formados
            print(f"[!] Unknown command type or missing data in message: {message_data}")

        # Enviar ACK manualmente para confirmar que el mensaje fue procesado
        # Esto es importante para la resiliencia de RabbitMQ
        # Sin ACK, el mensaje se reenviaría si este consumidor falla
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        # Manejar errores de deserialización (JSON mal formado)
        print(f"[!] Failed to decode JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # requeue=False evita que el mensaje se reenvíe infinitamente
    except Exception as e:
        # Manejar cualquier otro error inesperado
        print(f"[!] Error in callback: {e}")
        traceback.print_exc()  # Para debugging
        # Rechazar el mensaje. 
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # requeue=False lo manda a dead-letter si está configurada


def start_consuming():
    """
    Inicia el consumidor de comandos de RabbitMQ.
    Este método configura y arranca el bucle principal de consumo de mensajes.
    Es el punto de entrada para ejecutar este worker como proceso independiente.
    PATRÓN DE DISEÑO: Worker Pattern Se ejecuta como proceso independiente que consume mensajes continuamente.
    """
    
    # Llamamos al metodo de crear tablas
    create_tables()
    
    # --- Lógica de conexión con reintentos ---
    # Resiliencia con reintentos de conexión
    max_retries = 5  # Número máximo de intentos de conexión
    retry_delay = 5  # Segundos entre reintentos

    # Inicializamos las variables de conexión y canal fuera del bucle para poder usarlas después
    connection = None
    channel = None
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[.] Intentando conectar a RabbitMQ (Intento {attempt}/{max_retries})...")
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
                # Lanzar la excepción para que el script principal pueda manejarla
                raise 
        except Exception as e:
            print(f"[!] Error inesperado al conectar a RabbitMQ: {e}")
            raise  # Lanzar cualquier otro error inesperado

    if not connection or not channel:
        print("[ERROR] No se pudo establecer conexión con RabbitMQ.")
        return # Salir si no hay conexión

    try:
        # Declarar la cola (por si el publisher aún no la ha creado)
        # Aseguramos que la cola exista antes de consumir mensajes
        channel.queue_declare(queue=USER_COMMANDS_QUEUE, durable=True)

        # Configurar la calidad de servicio
        channel.basic_qos(prefetch_count=1) # Esto evita que un consumidor se sobrecargue con mensajes

        # Configurar el consumidor
        # Registramos nuestra función callback para manejar mensajes entrantes
        channel.basic_consume(queue=USER_COMMANDS_QUEUE, on_message_callback=callback, auto_ack=False)
        
        print('[*] Waiting for messages. To exit press CTRL+C')
        
        # Comenzar a consumir mensajes
        # Este método bloquea y continúa hasta que se interrumpa
        channel.start_consuming()
        
    except KeyboardInterrupt:
        # Manejar interrupción manual (Ctrl+C)
        print("[-] Stopping consumer...")
        channel.stop_consuming()
        connection.close()
    except Exception as e:
        print(f"[!] Error inesperado en el consumidor: {e}")
        traceback.print_exc()
    finally:
        # Asegura que los recursos se cierren correctamente
        if channel and not channel.is_closed:
            try:
                channel.stop_consuming()
            except Exception as e:
                print(f"[!] Error al detener el consumo: {e}")
        if connection and not connection.is_closed:
            try:
                connection.close()
                print("[-] Conexión a RabbitMQ cerrada.")
            except Exception as e:
                print(f"[!] Error al cerrar la conexión: {e}")

# --- Notas sobre la implementación ---
# `callback`: La función principal que Pika llama al recibir un mensaje.
#    - Decodifica y deserializa el mensaje.
#    - Determina el tipo de comando.
#    - Llama al procesador específico.
#    - Envía ACK/NACK según el resultado.
# `start_consuming`: Función principal para iniciar el bucle de consumo.
#    - Crea tablas si no existen.
#    - Se conecta a RabbitMQ.
#    - Declara la cola.
#    - Configura QoS.
#    - Registra el callback.
#    - Inicia el consumo.
# Manejo de ACK/NACK: Crucial para la resiliencia. ACK confirma éxito, NACK maneja errores.

# Rol en la Arquitectura
# Adaptador de mensajería: Consume comandos de colas y los procesa
# Deserialización: Convierte mensajes JSON a comandos del dominio
# Orquestación: Coordina ejecución de handlers con sus dependencias
# Resiliencia: Maneja reconexiones y errores de procesamiento
# Implementación CQRS: Procesa comandos de manera asíncrona
# Worker independiente: Se ejecuta como proceso separado del API