# Eventos de Dominio (Domain Events)
# Son objetos que representan cosas que sucedieron en el pasado dentro del dominio.
# Se utilizan para desacoplar componentes y comunicar cambios importantes.

# Este archivo está vacío, pero es un excelente lugar para definir eventos del dominio 'auth'.

# ¿Se puede agregar algo en el futuro? ¡Sí, absolutamente!

# Ejemplo de eventos que podrían definirse aquí:

# from dataclasses import dataclass
# from datetime import datetime
# from typing import Any
#
# @dataclass(frozen=True) # frozen=True para hacerlo inmutable
# class UserLoggedIn:
#     """Evento lanzado cuando un usuario se autentica exitosamente."""
#     user_id: str
#     timestamp: datetime = datetime.utcnow()
#     ip_address: str = ""
#
# @dataclass(frozen=True)
# class TokenGenerated:
#     """Evento lanzado cuando se genera un nuevo token."""
#     token_id: str
#     user_id: str
#     access_token: str
#     expires_at: datetime
#     timestamp: datetime = datetime.utcnow()
#
# @dataclass(frozen=True)
# class TokenRevoked:
#     """Evento lanzado cuando un token es revocado/eliminado."""
#     token_id: str
#     user_id: str
#     reason: str = ""
#     timestamp: datetime = datetime.utcnow()

# Rol en la Arquitectura:
# Eventos de Dominio: Representan hechos importantes ocurridos en el dominio.
# Desacoplamiento: Permiten que otras partes del sistema reaccionen a estos hechos sin acoplamiento directo.
# Comunicación Asincrónica: Son ideales para ser publicados en colas de mensajes (como RabbitMQ).
# Extensibilidad: Facilitan agregar nueva lógica sin modificar el código existente (Principio Abierto/Cerrado).
# Lenguaje Ubicuo: Los nombres de los eventos deben reflejar el lenguaje del dominio.

# Aunque está vacío ahora, es una parte crucial para sistemas evolutivos y bien desacoplados.