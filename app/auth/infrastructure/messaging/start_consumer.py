# START CONSUMER SCRIPT
# Este es un script ejecutable que inicia el consumidor de RabbitMQ.
# Es el punto de entrada para ejecutar el adaptador de consumo como un proceso independiente.

"""
Script para iniciar el consumidor de comandos de RabbitMQ para el contexto 'auth'.
Este script se ejecuta como un proceso independiente.
"""

# Importamos la función principal del consumidor
# Esta es la función que orquesta todo el proceso de consumo.
from .rabbitmq_consumer import start_consuming_auth

# --- Importamos create_tables ---
# *** PROBLEMA: Importación directa de infraestructura ***
# from ..persistence.database import create_tables # <--- Añade esta línea

if __name__ == "__main__":
    # Punto de entrada del script
    print("[*] Iniciando el consumidor de comandos de RabbitMQ para 'auth'...")
    try:
        # --- Llama a create_tables() ANTES de iniciar el consumo ---
        # print("[.] Creando tablas (si no existen)...")
        # create_tables() # <--- Añade esta línea
        # print("[.] Tablas creadas (o ya existían).")
        # -------------------
        # Llama a la función principal que inicia el consumo
        start_consuming_auth()
    except KeyboardInterrupt:
        # Maneja la interrupción por teclado (Ctrl+C)
        print("\n[-] Consumidor de 'auth' detenido manualmente.")
    except Exception as e:
        # Maneja cualquier otro error fatal
        print(f"[!] Error fatal en el consumidor de 'auth': {e}")
        # En un entorno de producción, aquí se podría agregar logging
        # y lógica de reintento o notificación de fallo crítico.
        # Para depuración, puedes añadir:
        # import traceback
        # traceback.print_exc()
