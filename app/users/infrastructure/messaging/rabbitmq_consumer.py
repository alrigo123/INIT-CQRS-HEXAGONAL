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
# *** ACTUALIZADO ***: Asegúrate de importar el handler CORRECTO (el actualizado)
from ...application.commands.handlers import handle_create_user

# *** NUEVO ***: Importamos el DI Container para obtener dependencias
# *** ESTO REEMPLAZA las importaciones directas de SessionLocal y SQLAlchemyUserRepository ***
from app.shared.di_container import get_user_repository
# Importamos la interfaz para el tipado y claridad
from app.users.domain.repositories import UserRepository

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
    *** IMPLEMENTACIÓN SEGURA ***
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

    # 1. Crear el comando a partir de los datos deserializados
    # Reconstruimos el comando del dominio a partir de los datos recibidos
    # *** ACTUALIZADO ***: Usamos la contraseña hasheada
    command = CreateUserCommand(
        name=command_data["name"],
        email=command_data["email"],
        password=hashed_password, # <-- AHORA ES EL HASH
        user_id=command_data.get("user_id") # Incluimos user_id si está presente
    )

    # *** MODIFICADO ***: Obtener dependencias del DI Container
    # En lugar de crear manualmente SessionLocal y SQLAlchemyUserRepository,
    # obtenemos directamente la interfaz UserRepository del contenedor.
    try:
        # *** NUEVO ***: Usar el contenedor DI para obtener UserRepository
        user_repository: UserRepository = get_user_repository() # <-- DEL CONTENEDOR
        print("[.] UserRepository obtenido del DI container.")
    except Exception as e:
        print(f"[!] Error al obtener UserRepository del DI container: {e}")
        # Manejar error de inicialización de dependencias
        return # O podrías relanzar como RuntimeException

    # *** ELIMINADO ***: Ya no creamos db_session ni SQLAlchemyUserRepository aquí.
    # *** ELIMINADO ***: Ya no creamos hash_password_fn aquí.

    try:
        # *** MODIFICADO ***: Invocar al handler de aplicación
        # Pasamos el comando y las dependencias inyectadas
        # *** ACTUALIZADO ***: Ya no pasamos hash_password_fn
        user_id = handle_create_user(command, user_repository) # <-- INYECTADO
        print(f"[.] Successfully created user with ID: {user_id}")
    except Exception as e:
        # Manejar errores del handler (validaciones, problemas de BD, etc.)
        print(f"[!] Error processing CreateUserCommand: {e}")
        # Para debugging detallado en desarrollo
        traceback.print_exc()
        # En un sistema real, podrías reencolar el mensaje, enviarlo a una cola de dead-letter, etc.
        # MEJORA SUGERIDA: Implementar dead-letter exchanges para manejo de errores
    # finally:
        # *** ELIMINADO ***: Ya no cerramos la sesión aquí.
        # La gestión del ciclo de vida de la sesión (abrir/cerrar) ahora es responsabilidad
        # del adaptador concreto (SQLAlchemyUserRepository) o del contenedor DI.
        # El contenedor debería encargarse de cerrar la sesión cuando sea apropiado,
        # por ejemplo, usando un generador o un mecanismo de scoped session.
        # Por ahora, asumimos que el repositorio maneja su sesión internamente
        # o que el contenedor la cierra correctamente después de usarla.

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
            # *** ACTUALIZADO ***: Llamamos a la función procesadora actualizada
            process_create_user_command(command_data)
        else:
            # Manejar comandos desconocidos o mensajes mal formados
            print(f"[!] Unknown command type or missing data in message: {message_data}")
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
    # *** MEJORA SUGERIDA ***: Mover create_tables a un lugar centralizado o usar Alembic
    # Importa la función create_tables para asegurar que las tablas existen
    from ...infrastructure.persistence.database import create_tables
    create_tables()

    
    # --- Nueva lógica de conexión con reintentos ---
    # Implementamos resiliencia con reintentos de conexión
    max_retries = 5  # Número máximo de intentos de conexión
    retry_delay = 5  # Segundos entre reintentos

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
        # 2. Declarar la cola (por si acaso el publisher aún no la ha creado)
        # Aseguramos que la cola exista antes de consumir mensajes
        channel.queue_declare(queue=USER_COMMANDS_QUEUE, durable=True)

        # 3. Configurar la calidad de servicio
        # prefetch_count=1 limita a 1 mensaje no confirmado por consumidor
        # Esto evita que un consumidor se sobrecargue con mensajes
        channel.basic_qos(prefetch_count=1)

        # 4. Configurar el consumidor
        # Registramos nuestra función callback para manejar mensajes entrantes
        channel.basic_consume(queue=USER_COMMANDS_QUEUE, on_message_callback=callback, auto_ack=False)

        print('[*] Waiting for messages. To exit press CTRL+C')
        # 5. Comenzar a consumir mensajes
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

# --- CAMBIOS REALIZADOS PARA INTEGRAR EL DI CONTAINER ---
# *** NUEVO ***: Importación de `get_user_repository` desde `app.shared.di_container`.
# *** NUEVO ***: Importación de la interfaz `UserRepository` para tipado.
# *** ELIMINADO ***: Importación directa de `SessionLocal` (de `database.py`).
# *** ELIMINADO ***: Importación directa de `SQLAlchemyUserRepository` (de `repositories.py`).
# *** MODIFICADO ***: `process_create_user_command`:
#     - *** ELIMINADO ***: Creación manual de `db_session = SessionLocal()`.
#     - *** ELIMINADO ***: Creación manual de `user_repository = SQLAlchemyUserRepository(db_session)`.
#     - *** NUEVO ***: Obtención de `UserRepository` desde el `di_container` usando `get_user_repository()`.
#     - *** ELIMINADO ***: Creación manual de `hash_password_fn`.
#     - *** MODIFICADO ***: Llamada a `handle_create_user` ahora recibe solo el comando y el repositorio inyectado.
#     - *** ELIMINADO ***: Bloque `finally` para cerrar `db_session` manualmente.
# *** BENEFICIO ***: El consumidor ahora depende de la interfaz `UserRepository`, no de la implementación concreta.
#                   Esto cumple con el Principio de Inversión de Dependencias y desacopla este adaptador
#                   de los detalles de la infraestructura (SQLAlchemy).
# *** BENEFICIO ***: Centraliza la creación de dependencias en `app/shared/di_container.py`.