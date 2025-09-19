# RABBITMQ CONSUMER (ADAPTADOR PRIMARIO)
# Esta capa implementa un adaptador para consumir mensajes de RabbitMQ.
# Es un ADAPTADOR PRIMARIO en Arquitectura Hexagonal.
# Se encarga de recibir comandos/eventos y orquestar su procesamiento.

import json # Para deserializar mensajes
import pika # Cliente de RabbitMQ
import traceback # Para imprimir trazas de error detalladas
import time # Para implementar reintentos
import os # Para acceder a variables de entorno
from pika.exceptions import AMQPConnectionError # Para manejar errores específicos de conexión

# Importamos las dependencias de auth
# *** MEJORA FUTURA: Estas importaciones directas rompen la arquitectura.
# Idealmente, se inyectarían adaptadores configurados externamente.
from app.auth.infrastructure.persistence.database import SessionLocal as AuthSessionLocal, create_tables
from app.auth.infrastructure.persistence.repositories import SQLAlchemyTokenRepository

# Para simular la generación de tokens
# *** MEJORA FUTURA: Estas funciones deberían estar en infraestructura o ser inyectadas ***
import secrets
from datetime import datetime, timedelta

# --- Configuración de RabbitMQ ---
# Se usa una variable de entorno para la configuración.
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
AUTH_COMMANDS_QUEUE = "auth_commands" # Cola para comandos/eventos específicos de auth

# --- Funciones auxiliares ---
# *** MEJORA FUTURA: Mover a un módulo de servicios de infraestructura ***
def generate_access_token() -> str:
    """Genera un token de acceso."""
    return secrets.token_urlsafe(32)

def calculate_expires_at(hours: int = 1) -> datetime:
    """Calcula la fecha de expiración."""
    return datetime.utcnow() + timedelta(hours=hours)

# --- Lógica de procesamiento de mensajes ---
# *** MEJORA: Este consumidor actualmente no procesa ningún comando específico de auth.
# Se mantiene como base para futuros comandos o eventos como `UserLoggedIn`.

def dummy_command_processor(command_data: dict):
    """
    Procesador de ejemplo para comandos genéricos.
    En una implementación real, aquí iría la lógica para procesar comandos específicos.
    Por ahora, solo imprime el comando recibido.
    """
    print(f"[.] Procesando comando genérico con datos: {command_data}")

def callback(ch, method, properties, body):
    """
    Función callback que se ejecuta cada vez que se recibe un mensaje de RabbitMQ.
    
    PATRÓN DE DISEÑO: Callback
    Función que se pasa como argumento para ser llamada cuando ocurre un evento.
    
    ARQUITECTURA: Adaptador Primario en Arquitectura Hexagonal
    Recibe un mensaje externo (RabbitMQ) y lo convierte en una acción interna.
    """
    try:
        # Decodifica el cuerpo del mensaje de bytes a string
        message_str = body.decode('utf-8')
        print(f"[x] Received raw message: {message_str}")
        # Deserializa el string JSON a un diccionario de Python
        message_data = json.loads(message_str)
        # Extrae el tipo de comando y los datos
        command_type = message_data.get("type")
        command_data = message_data.get("data")

        # Procesa el comando según su tipo
        # *** ACTUALIZADO: Eliminada la lógica de RegisterUserCommand ***
        if command_type and command_data:
            # *** MEJORA: En lugar de if/else, se podría usar un diccionario de handlers ***
            print(f"[.] Recibido comando de tipo '{command_type}'. Procesando...")
            # Llama a un procesador genérico o específico si existiera
            dummy_command_processor(command_data)
            print(f"[.] Comando '{command_type}' procesado.")
        else:
            print(f"[!] Unknown command type or missing data in message: {message_data}")

        # Enviar ACK manualmente para confirmar que el mensaje fue procesado
        # Esto es crucial para la fiabilidad de los mensajes.
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        # Si el mensaje no es JSON válido, lo rechazamos y no lo reencolamos
        print(f"[!] Failed to decode JSON: {e}")
        # Rechaza el mensaje sin reencolarlo (se pierde)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        # Si ocurre un error inesperado, lo rechazamos y no lo reencolamos
        print(f"[!] Error in callback while processing message: {e}")
        traceback.print_exc()
        # Rechaza el mensaje sin reencolarlo (se pierde)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_consuming_auth():
    """
    Inicia el consumidor de comandos/eventos de RabbitMQ para el contexto 'auth'.
    
    PATRÓN DE DISEÑO: Service Layer (capa de servicio de infraestructura)
    Orquesta la conexión y el consumo de mensajes.
    
    ARQUITECTURA: Adaptador Primario en Arquitectura Hexagonal
    Punto de entrada para eventos externos dirigidos a este contexto.
    """
    # Asegurarse de que las tablas de la BD de auth existen
    # *** PROBLEMA: Importación directa ***
    create_tables()

    # --- Lógica de conexión con reintentos ---
    max_retries = 5
    retry_delay = 5  # segundos

    # Bucle de reintentos para conectar a RabbitMQ
    connection = None
    channel = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[.] Intentando conectar a RabbitMQ para 'auth' (Intento {attempt}/{max_retries})...")
            parameters = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            print("[.] Conexión a RabbitMQ para 'auth' establecida.")
            break # Salir del bucle si la conexión es exitosa
        except AMQPConnectionError as e:
            print(f"[!] Error de conexión a RabbitMQ para 'auth' (Intento {attempt}): {e}")
            if attempt < max_retries:
                print(f"[.] Esperando {retry_delay} segundos antes de reintentar...")
                time.sleep(retry_delay)
            else:
                print("[!] Todos los intentos de conexión a RabbitMQ para 'auth' fallaron.")
                # Lanzar la excepción para que el script principal pueda manejarla
                raise 
        except Exception as e:
            print(f"[!] Error inesperado al conectar a RabbitMQ para 'auth': {e}")
            raise # Lanzar cualquier otro error inesperado

    if not connection or not channel:
        print("[ERROR] No se pudo establecer conexión con RabbitMQ para 'auth'.")
        return # Salir si no hay conexión

    try:
        # Declara la cola (idempotente)
        channel.queue_declare(queue=AUTH_COMMANDS_QUEUE, durable=True)
        # Configura el QoS para procesar un mensaje a la vez
        channel.basic_qos(prefetch_count=1)
        # Registra la función callback para consumir mensajes
        channel.basic_consume(queue=AUTH_COMMANDS_QUEUE, on_message_callback=callback, auto_ack=False)

        print('[*] Waiting for auth commands/events. To exit press CTRL+C')
        # Inicia el bucle de consumo de mensajes
        channel.start_consuming()
        
    except KeyboardInterrupt:
        print("\n[-] Stopping auth consumer (KeyboardInterrupt)...")
    except Exception as e:
        print(f"[!] Error inesperado en el consumidor de 'auth': {e}")
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
                print("[-] Conexión a RabbitMQ para 'auth' cerrada.")
            except Exception as e:
                print(f"[!] Error al cerrar la conexión: {e}")

# --- Notas sobre la implementación ---
# 1. Se eliminó toda la lógica relacionada con `RegisterUserCommand`.
# 2. Se eliminó la función `create_user_in_users_context` que rompía la arquitectura.
# 3. Se eliminó la función `process_register_user_command`.
# 4. Se mantuvieron las funciones auxiliares de infraestructura (`generate_access_token`).
# 5. Se actualizó el `callback` para no procesar `RegisterUserCommand`.
# 6. Se mejoró el manejo de errores y cierre de recursos en `start_consuming_auth`.
# 7. *** PROBLEMA PENDIENTE: Importaciones directas de infraestructura.
# 8. *** MEJORA FUTURA: Implementar procesadores específicos para comandos/eventos reales de `auth`.