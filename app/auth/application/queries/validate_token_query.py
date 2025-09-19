# QUERY
# Representa una solicitud de lectura de información.
# Es una clase de datos simple, sin lógica de negocio.
# En CQRS, las consultas son mensajes que solicitan datos.

from dataclasses import dataclass # Para crear clases de datos inmutables fácilmente

@dataclass(frozen=True) # frozen=True hace que la instancia sea inmutable después de su creación
class ValidateTokenQuery:
    """ Consulta para validar un token de acceso. """

    access_token: str # Campo requerido: El token que se quiere validar.



# --- Notas sobre la implementación ---
# 1. `@dataclass(frozen=True)`: Hace que el objeto sea inmutable.
#    Esto es bueno para evitar modificaciones accidentales y facilita el uso en estructuras de datos inmutables.
# 2. Atributo simple: Solo contiene el token a validar.
#    Mantiene el comando/consulta enfocado en una sola responsabilidad.
# 3. Independiente: Pertenece a la capa de Aplicación de `auth`.
#    No tiene dependencias de frameworks ni de detalles de infraestructura.
# 4. Lenguaje Ubicuo: Usa términos del dominio de autenticación (ValidateToken, access_token).