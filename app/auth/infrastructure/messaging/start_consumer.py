# START CONSUMER SCRIPT
# Este es un script ejecutable que inicia el consumidor de RabbitMQ.
# Es el punto de entrada para ejecutar el adaptador de consumo como un proceso independiente.

"""
Script para iniciar el consumidor de comandos de RabbitMQ para el contexto 'auth'.
Este script se ejecuta como un proceso independiente.
"""

# Importamos la función principal del consumidor
from .rabbitmq_consumer import start_consuming_auth


if __name__ == "__main__":
    # Punto de entrada del script
    print("[*] Iniciando el consumidor de comandos de RabbitMQ para 'auth'...")
    try:
        # Llama a la función principal que inicia el consumo
        start_consuming_auth()
    except KeyboardInterrupt:
        # Maneja la interrupción por teclado (Ctrl+C)
        print("\n[-] Consumidor de 'auth' detenido manualmente.")
    except Exception as e:
        # Maneja cualquier otro error fatal
        print(f"[!] Error fatal en el consumidor de 'auth': {e}")
