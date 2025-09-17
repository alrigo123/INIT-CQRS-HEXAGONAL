# app/auth/infrastructure/messaging/start_consumer.py
"""
Script para iniciar el consumidor de comandos de RabbitMQ para el contexto 'auth'.
Este script se ejecuta como un proceso independiente.
"""

# Importamos la función principal del consumidor
from .rabbitmq_consumer import start_consuming_auth
# --- Importamos create_tables ---
from ..persistence.database import create_tables # <--- Añade esta línea

if __name__ == "__main__":
    print("[*] Iniciando el consumidor de comandos de RabbitMQ para 'auth'...")
    try:
        # --- Llama a create_tables() ANTES de iniciar el consumo ---
        print("[.] Creando tablas (si no existen)...")
        create_tables() # <--- Añade esta línea
        print("[.] Tablas creadas (o ya existían).")
        # -------------------
        start_consuming_auth()
    except KeyboardInterrupt:
        print("\n[-] Consumidor de 'auth' detenido manualmente.")
    except Exception as e:
        print(f"[!] Error fatal en el consumidor de 'auth': {e}")
        # En un entorno de producción, aquí se podría agregar logging
        # y lógica de reintento o notificación de fallo crítico.
        # Para depuración, puedes añadir:
        # import traceback
        # traceback.print_exc()
