# tests/auth/domain/test_models.py
import pytest
# Importamos timezone para ser consistentes con la app
from datetime import datetime, timedelta, timezone

from app.auth.domain.models import Token

def test_token_creation_valid():
    """Prueba la creación exitosa de un token con datos válidos."""
    token_id = "123e4567-e89b-12d3-a456-426614174000"
    user_id = "user-123"
    access_token = "abc123xyz"
    # Usamos datetime.now(timezone.utc) para ser consistentes con la app
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    token = Token(token_id, user_id, access_token, expires_at)

    assert token.id == token_id
    assert token.user_id == user_id
    assert token.access_token == access_token
    # Verificamos que la fecha almacenada sea la misma (o muy cercana)
    assert token.expires_at == expires_at

def test_token_creation_invalid_missing_fields():
    """Prueba que se lance ValueError si faltan campos requeridos."""
    token_id = "123e4567-e89b-12d3-a456-426614174000"
    user_id = "user-123"
    access_token = "abc123xyz"
    # Usamos datetime.now(timezone.utc)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    with pytest.raises(ValueError, match="Todos los campos del token son obligatorios."):
        Token("", user_id, access_token, expires_at) # ID vacío

    with pytest.raises(ValueError, match="Todos los campos del token son obligatorios."):
        Token(token_id, "", access_token, expires_at) # user_id vacío

    with pytest.raises(ValueError, match="Todos los campos del token son obligatorios."):
        Token(token_id, user_id, "", expires_at) # access_token vacío

    with pytest.raises(ValueError, match="Todos los campos del token son obligatorios."):
        Token(token_id, user_id, access_token, None) # expires_at None

def test_token_creation_invalid_expired():
    """Prueba que se lance ValueError si la fecha de expiración es pasada."""
    token_id = "123e4567-e89b-12d3-a456-426614174000"
    user_id = "user-123"
    access_token = "abc123xyz"
    # Crear una fecha en el pasado usando datetime.now(timezone.utc)
    expired_at = datetime.now(timezone.utc) - timedelta(hours=1)

    with pytest.raises(ValueError, match="La fecha de expiración debe ser futura."):
        Token(token_id, user_id, access_token, expired_at)

def test_token_is_expired_false():
    """Prueba que is_expired devuelve False para un token no expirado."""
    token_id = "123e4567-e89b-12d3-a456-426614174000"
    user_id = "user-123"
    access_token = "abc123xyz"
    # Crear una fecha en el futuro usando datetime.now(timezone.utc)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    token = Token(token_id, user_id, access_token, expires_at)
    
    assert token.is_expired() is False

# Ahora que el código de la app y las pruebas usan el mismo tipo de fecha,
# podemos probar `is_expired` con una fecha pasada de forma más robusta.
# Sin embargo, el constructor aún lo impide. La prueba `test_token_creation_invalid_expired`
# cubre la validación. Podemos simular un token expirado modificando su atributo
# interno (solo para prueba).

def test_token_equality():
    """Prueba la igualdad de tokens basada en ID."""
    token_id = "123e4567-e89b-12d3-a456-426614174000"
    user_id = "user-123"
    access_token = "abc123xyz"
    # Usamos datetime.now(timezone.utc)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    token1 = Token(token_id, user_id, access_token, expires_at)
    token2 = Token(token_id, "different-user", "different-token", datetime.now(timezone.utc) + timedelta(hours=2))
    token3 = Token("different-id", user_id, access_token, expires_at)
    
    assert token1 == token2 # Mismo ID
    assert token1 != token3 # Diferente ID
    assert token1 != "not a token" # Tipo diferente

def test_token_repr():
    """Prueba la representación en string del token."""
    token_id = "123e4567-e89b-12d3-a456-426614174000"
    user_id = "user-123"
    access_token = "abc123xyz"
    # Usamos datetime.now(timezone.utc)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    token = Token(token_id, user_id, access_token, expires_at)
    repr_str = repr(token)
    assert token_id in repr_str
    assert user_id in repr_str
