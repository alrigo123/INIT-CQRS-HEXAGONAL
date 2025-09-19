"""
Script para iniciar el consumidor de comandos de RabbitMQ.
Este script se ejecuta como un proceso independiente para escuchar y procesar mensajes de la cola de comandos de usuarios.
"""

import json
import pika
import traceback

# Importamos la función principal del consumidor
from .rabbitmq_consumer import start_consuming

if __name__ == "__main__":
    print("[*] Iniciando el consumidor de comandos de RabbitMQ para 'users'...")
    try:
        # Llamamos a la función que inicia el bucle de consumo
        start_consuming()
    except KeyboardInterrupt:
        print("\n[-] Consumidor detenido manualmente.")
    except Exception as e:
        # Imprime el mensaje de error y el traceback completo
        print(f"[!] Error fatal en el consumidor: {e}")
        traceback.print_exc()