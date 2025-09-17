# app/auth/infrastructure/messaging/rabbitmq_consumer.py
import json
import pika
import traceback
import time
import os
from pika.exceptions import AMQPConnectionError
# Importamos el comando que vamos a consumir
from ...application.commands.register_user_command import RegisterUserCommand
# Importamos dependencias necesarias para el handler
from ....users.infrastructure.persistence.database import SessionLocal as UsersSessionLocal
from ....users.infrastructure.persistence.repositories import SQLAlchemyUserRepository as UsersSQLAlchemyUserRepository
# Importamos las dependencias de auth
from ...infrastructure.persistence.database import SessionLocal as AuthSessionLocal, create_tables
from ...infrastructure.persistence.repositories import SQLAlchemyTokenRepository
# Para simular el hashing de contraseña y generar tokens
import hashlib
import secrets
from datetime import datetime, timedelta

# --- Configuración de RabbitMQ ---
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
AUTH_COMMANDS_QUEUE = "auth_commands"

# --- Funciones auxiliares ---
def dummy_hash_password(password: str) -> str:
    """Función de ejemplo para hashear una contraseña."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_access_token() -> str:
    """Genera un token de acceso."""
    return secrets.token_urlsafe(32)

def calculate_expires_at(hours: int = 1) -> datetime:
    """Calcula la fecha de expiración."""
    return datetime.utcnow() + timedelta(hours=hours)

# --- Función auxiliar para interactuar con users ---
def create_user_in_users_context(name: str, email: str, hashed_password: str) -> str:
    """
    Crea un usuario en el contexto 'users' usando su repositorio directamente.
    Retorna el ID del usuario creado.
    """
    db_session = UsersSessionLocal()
    user_repository = UsersSQLAlchemyUserRepository(db_session)
    
    # Importamos el modelo de dominio de users
    from ....users.domain.models import User
    import uuid
    user_id = str(uuid.uuid4())
    
    try:
        # Creamos la entidad de dominio User de users
        user = User(
            user_id=user_id,
            name=name,
            email=email,
            hashed_password=hashed_password
        )
        # Guardamos usando el repositorio de users
        user_repository.save(user)
        print(f"[.] Usuario creado en contexto 'users' con ID: {user_id}")
        return user_id
    except Exception as e:
        print(f"[!] Error al crear usuario en contexto 'users': {e}")
        traceback.print_exc()
        raise
    finally:
        db_session.close()

def process_register_user_command(command_data: dict):
    """
    Procesa un comando RegisterUserCommand deserializado.
    """
    print(f"[.] Processing RegisterUserCommand for '{command_data['name']}'")

    # 1. Hashear la contraseña para users
    try:
        hashed_password_for_users = dummy_hash_password(command_data['password'])
    except Exception as e:
        print(f"[!] Error al hashear la contraseña para users: {e}")
        traceback.print_exc()
        return

    # 2. Crear el usuario en el contexto 'users'
    user_id = None
    try:
        user_id = create_user_in_users_context(
            name=command_data['name'],
            email=command_data['email'],
            hashed_password=hashed_password_for_users
        )
        if not user_id:
            raise RuntimeError("La creación del usuario en 'users' no devolvió un ID válido.")
    except Exception as e:
        print(f"[!] Error al crear usuario en contexto 'users': {e}")
        traceback.print_exc()
        return

    # 3. Proceder con la lógica de auth (crear token)
    auth_db_session = AuthSessionLocal()
    token_repository = SQLAlchemyTokenRepository(auth_db_session)
    
    # Importamos el handler corregido
    from ...application.commands.handlers import handle_register_user_for_auth_context

    try:
        # 4. Invocar al handler de aplicación de auth CORREGIDO
        access_token = handle_register_user_for_auth_context(
            user_id=user_id,
            user_email=command_data['email'],
            token_repository=token_repository,
            generate_token_fn=generate_access_token,
            calculate_expires_fn=calculate_expires_at
        )
        print(f"[.] Successfully registered user and created token. Access Token: {access_token[:10]}...")
    except Exception as e:
        print(f"[!] Error processing RegisterUserCommand in auth context: {e}")
        traceback.print_exc()
    finally:
        # Cerrar la sesión de la base de datos de auth
        auth_db_session.close()

def callback(ch, method, properties, body):
    """
    Función callback que se ejecuta cada vez que se recibe un mensaje de RabbitMQ.
    """
    try:
        message_str = body.decode('utf-8')
        print(f"[x] Received raw message: {message_str}")
        message_data = json.loads(message_str)
        command_type = message_data.get("type")
        command_data = message_data.get("data")

        if command_type == "RegisterUserCommand" and command_data:
            process_register_user_command(command_data)
        else:
            print(f"[!] Unknown command type or missing data: {command_type}")

        # Enviar ACK manualmente
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        print(f"[!] Failed to decode JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        print(f"[!] Error in callback: {e}")
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_consuming_auth():
    """
    Inicia el consumidor de comandos de RabbitMQ para el contexto 'auth'.
    """
    # Asegurarse de que las tablas de la BD de auth existen
    create_tables()

    # --- Lógica de conexión con reintentos ---
    max_retries = 5
    retry_delay = 5  # segundos

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[.] Intentando conectar a RabbitMQ para 'auth' (Intento {attempt}/{max_retries})...")
            parameters = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            print("[.] Conexión a RabbitMQ para 'auth' establecida.")
            break
        except AMQPConnectionError as e:
            print(f"[!] Error de conexión a RabbitMQ para 'auth' (Intento {attempt}): {e}")
            if attempt < max_retries:
                print(f"[.] Esperando {retry_delay} segundos antes de reintentar...")
                time.sleep(retry_delay)
            else:
                print("[!] Todos los intentos de conexión a RabbitMQ para 'auth' fallaron.")
                raise
        except Exception as e:
            print(f"[!] Error inesperado al conectar a RabbitMQ para 'auth': {e}")
            raise

    channel.queue_declare(queue=AUTH_COMMANDS_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=AUTH_COMMANDS_QUEUE, on_message_callback=callback, auto_ack=False)

    print('[*] Waiting for auth commands. To exit press CTRL+C')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[-] Stopping auth consumer...")
        channel.stop_consuming()
        connection.close()
