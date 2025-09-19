# app/users/infrastructure/messaging/rabbitmq_consumer.py
import json
import pika
import traceback
import time
import os
from typing import Dict, Any
import bcrypt

# Importamos el comando que vamos a consumir
# Este es el comando que este consumidor sabe procesar
from ...application.commands.create_user_command import CreateUserCommand

# Importamos el handler que procesará el comando
# Este es el handler de aplicación que ejecutará la lógica de negocio
from ...application.commands.handlers import handle_create_user

# Importamos dependencias necesarias para el handler
# Estas son las implementaciones concretas de infraestructura que el handler necesita
from ...infrastructure.persistence.database import SessionLocal, create_tables
from ...infrastructure.persistence.repositories import SQLAlchemyUserRepository

# Para simular el hashing de contraseña (en una implementación real, usar una librería como bcrypt)
# ADVERTENCIA: hashlib no es seguro para passwords en producción
import hashlib

# Para manejar errores específicos de conexión de RabbitMQ
from pika.exceptions import AMQPConnectionError

# --- Configuración de RabbitMQ ---
# Alineada con el publisher y docker-compose.yml
# Se recomienda usar variables de entorno en lugar de valores fijos
# MEJORA SUGERIDA: Mover a variables de entorno para diferentes ambientes
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
USER_COMMANDS_QUEUE = "user_commands"

# --- NUEVA FUNCIÓN SEGURA PARA HASHEAR ---
def secure_hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    """
    try:
        # bcrypt.gensalt() genera un salt aleatorio automáticamente
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Devolvemos como string para poder serializar/deserializar fácilmente
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"[!] Error al hashear contraseña con bcrypt: {e}")
        raise RuntimeError(f"Error al hashear la contraseña: {e}") from e
# --- FIN NUEVA FUNCIÓN ---

def process_create_user_command(command_data: Dict[str, Any]):
    """
    Procesa un comando CreateUserCommand deserializado.
    
    Esta función orquesta la obtención de dependencias y la ejecución del handler.
    Es el punto de entrada para procesar comandos recibidos de la cola.
    
    PATRÓN DE DISEÑO: Orquestador (Orchestrator Pattern)
    Este método coordina la creación de dependencias y ejecución del handler.

    Args:
        command_data (dict): Datos del comando deserializados desde JSON
    """
    print(f"[.] Processing CreateUserCommand for '{command_data['name']}'")
    
     # --- CAMBIO CLAVE: HASHEAR LA CONTRASEÑA AQUÍ ---
    try:
        plain_password = command_data["password"]
        # Usamos la nueva función segura
        hashed_password = secure_hash_password(plain_password)
        print(f"[.] Contraseña hasheada para el usuario '{command_data['name']}'.")
    except Exception as e:
        print(f"[!] Error al hashear la contraseña antes de crear el comando: {e}")
        # Manejar el error: log, enviar a dead-letter, etc. Por ahora, simplemente retornamos.
        return
    # --- FIN CAMBIO CLAVE ---

    # 1. Crear el objeto comando desde los datos deserializados
    # Reconstruimos el comando del dominio a partir de los datos recibidos
    command = CreateUserCommand(
        name=command_data["name"],
        email=command_data["email"],
        password=hashed_password,
    )

    # 2. Obtener dependencias necesarias para el handler
    # En una arquitectura más avanzada, esto vendría de un contenedor de inyección de dependencias.
    # Aquí creamos las dependencias manualmente siguiendo el principio de inversión de dependencias
    
    # Obtener una sesión de base de datos del pool
    db_session = SessionLocal()
    
    # Crear el repositorio con la sesión (adaptador concreto de persistencia)
    user_repository = SQLAlchemyUserRepository(db_session)
    
     # Creamos una función "dummy" para pasar al handler.
    # El handler espera una función que hashea, pero la contraseña ya está hasheada.
    def pass_through_hashed_password(pwd: str) -> str:
        # Simplemente devuelve la contraseña que recibe (que ya es el hash)
        return pwd
    
    # Función para hashear contraseñas (adaptador concreto de seguridad)
    # MEJORA SUGERIDA: Usar implementación real de hashing seguro
    hash_password_fn = pass_through_hashed_password

    try:
        # 3. Invocar al handler de aplicación
        # Pasamos el comando y las dependencias inyectadas
        # Este es el punto donde se ejecuta la lógica de negocio
        user_id = handle_create_user(command, user_repository)
        print(f"[.] Successfully created user with ID: {user_id}")
    except Exception as e:
        # Manejar errores del handler (validaciones, problemas de BD, etc.)
        print(f"[!] Error processing CreateUserCommand: {e}")
        # Para debugging detallado en desarrollo
        traceback.print_exc()
        # En un sistema real, podrías reencolar el mensaje, enviarlo a una cola de dead-letter, etc.
        # MEJORA SUGERIDA: Implementar dead-letter exchanges para manejo de errores
    finally:
        # 4. Cerrar la sesión de la base de datos
        # Es crucial cerrar sesiones para liberar conexiones del pool
        db_session.close()

def callback(ch, method, properties, body):
    """
    Función callback que se ejecuta cada vez que se recibe un mensaje de RabbitMQ.
    
    Este es el punto de entrada principal para el consumidor de mensajes.
    Se ejecuta automáticamente cuando RabbitMQ entrega un mensaje a este consumidor.
    
    PATRÓN DE DISEÑO: Callback/Event Handler
    Se registra como manejador de eventos para mensajes de RabbitMQ.

    Args:
        ch: Canal de comunicación con RabbitMQ
        method: Información sobre el método de entrega del mensaje
        properties: Propiedades del mensaje (headers, delivery mode, etc.)
        body: Cuerpo del mensaje (los datos en bytes)
    """
    try:
        # 1. Decodificar el cuerpo del mensaje (de bytes a string)
        # Los mensajes llegan como bytes y deben convertirse a string para procesar
        message_str = body.decode('utf-8')
        print(f"[x] Received raw message: {message_str}")

        # 2. Deserializar el mensaje de JSON a un diccionario de Python
        # Convertimos el JSON recibido en estructura de datos Python
        message_data = json.loads(message_str)

        # 3. Determinar el tipo de comando y procesarlo
        # Extraemos el tipo de comando y los datos del mensaje
        command_type = message_data.get("type")
        command_data = message_data.get("data")

        # Procesamos solo los comandos que conocemos
        if command_type == "CreateUserCommand":
            # Corrección: pasar command_data, no command_ (había un error tipográfico)
            process_create_user_command(command_data)
        else:
            # Manejar comandos desconocidos o mensajes mal formados
            print(f"[!] Unknown command type or missing  {command_type}")
            # MEJORA SUGERIDA: Enviar a dead-letter queue para análisis posterior

        # 4. Enviar ACK manualmente para confirmar que el mensaje fue procesado
        # Esto es importante para la resiliencia de RabbitMQ
        # Sin ACK, el mensaje se reenviaría si este consumidor falla
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        # Manejar errores de deserialización (JSON mal formado)
        print(f"[!] Failed to decode JSON: {e}")
        # Es importante rechazar (reject) o enviar a una cola de dead-letter mensajes no válidos
        # requeue=False evita que el mensaje se reenvíe infinitamente
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        # MEJORA SUGERIDA: Implementar dead-letter exchange para mensajes inválidos
    except Exception as e:
        # Manejar cualquier otro error inesperado
        print(f"[!] Error in callback: {e}")
        traceback.print_exc()  # Para debugging
        # Rechazar el mensaje. requeue=False lo manda a dead-letter si está configurada
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_consuming():
    """
    Inicia el consumidor de comandos de RabbitMQ.
    
    Este método configura y arranca el bucle principal de consumo de mensajes.
    Es el punto de entrada para ejecutar este worker como proceso independiente.
    
    PATRÓN DE DISEÑO: Worker Pattern
    Se ejecuta como proceso independiente que consume mensajes continuamente.
    """
    # Asegurarse de que las tablas de la BD existen
    # Esto es útil para asegurar que la infraestructura esté lista
    create_tables()

    # --- Nueva lógica de conexión con reintentos ---
    # Implementamos resiliencia con reintentos de conexión
    max_retries = 5  # Número máximo de intentos de conexión
    retry_delay = 5  # Segundos entre reintentos

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
    # Aseguramos que la cola exista antes de consumir mensajes
    channel.queue_declare(queue=USER_COMMANDS_QUEUE, durable=True)

    # 3. Configurar la calidad de servicio
    # prefetch_count=1 limita a 1 mensaje no confirmado por consumidor
    # Esto evita que un consumidor se sobrecargue con mensajes
    channel.basic_qos(prefetch_count=1)

    # 4. Configurar el consumidor
    # Registramos nuestra función callback para manejar mensajes entrantes
    channel.basic_consume(
        queue=USER_COMMANDS_QUEUE, 
        on_message_callback=callback, 
        auto_ack=False  # Desactivamos auto-ack para control manual
    )

    print("[*] Waiting for messages. To exit press CTRL+C")
    try:
        # 5. Comenzar a consumir mensajes
        # Este método bloquea y continúa hasta que se interrumpa
        channel.start_consuming()
    except KeyboardInterrupt:
        # Manejar interrupción manual (Ctrl+C)
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

# Rol en la Arquitectura
# Adaptador de mensajería: Consume comandos de colas y los procesa
# Deserialización: Convierte mensajes JSON a comandos del dominio
# Orquestación: Coordina ejecución de handlers con sus dependencias
# Resiliencia: Maneja reconexiones y errores de procesamiento
# Implementación CQRS: Procesa comandos de manera asíncrona
# Worker independiente: Se ejecuta como proceso separado del API