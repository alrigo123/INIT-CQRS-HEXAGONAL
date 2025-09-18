# tests/auth/domain/test_models.py
"""
Pruebas unitarias para el modelo de dominio Token.
Estas pruebas validan las reglas de negocio centrales del token.
"""
import pytest
from datetime import datetime, timedelta
import uuid
# Importamos la entidad de dominio y sus excepciones
from app.auth.domain.models import Token

class TestTokenModel:
    """Grupo de pruebas para la clase Token."""

    def test_token_creation_with_valid_data(self):
        """Prueba la creación de un token con datos válidos."""
        token_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        access_token = "un_token_de_acceso_seguro"
        expires_at = datetime.utcnow() + timedelta(hours=1)

        token = Token(
            token_id=token_id,
            user_id=user_id,
            access_token=access_token,
            expires_at=expires_at
        )

        assert token.id == token_id
        assert token.user_id == user_id
        assert token.access_token == access_token
        assert token.expires_at == expires_at

    def test_token_is_expired_returns_true_for_expired_token(self):
        """Prueba que is_expired() devuelva True para un token expirado."""
        token_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        access_token = "un_token_de_acceso_seguro"
        # Fecha en el futuro (para crear el token válido)
        future_expires_at = datetime.utcnow() + timedelta(hours=1)

        # 1. Crear un token válido con fecha futura
        token = Token(
            token_id=token_id,
            user_id=user_id,
            access_token=access_token,
            expires_at=future_expires_at
        )

        # 2. Simular que el token ha expirado modificando su atributo
        # Esto simula un token que existió y ahora está expirado
        past_expires_at = datetime.utcnow() - timedelta(hours=1)
        # Accedemos directamente al atributo protegido para modificarlo en la prueba
        token._expires_at = past_expires_at

        # 3. Verificar que is_expired() devuelva True
        assert token.is_expired() is True

    def test_token_is_expired_returns_false_for_active_token(self):
        """Prueba que is_expired() devuelva False para un token activo."""
        token_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        access_token = "un_token_de_acceso_seguro"
        # Fecha en el futuro
        expires_at = datetime.utcnow() + timedelta(hours=1)

        token = Token(
            token_id=token_id,
            user_id=user_id,
            access_token=access_token,
            expires_at=expires_at
        )

        assert token.is_expired() is False

    def test_token_equality_is_based_on_id(self):
        """Prueba que dos tokens sean iguales si tienen el mismo ID."""
        token_id = str(uuid.uuid4())
        user_id_1 = str(uuid.uuid4())
        user_id_2 = str(uuid.uuid4()) # Diferente user_id
        access_token_1 = "token1"
        access_token_2 = "token2" # Diferente access_token
        expires_at_1 = datetime.utcnow() + timedelta(hours=1)
        expires_at_2 = datetime.utcnow() + timedelta(hours=2) # Diferente expires_at

        token1 = Token(token_id, user_id_1, access_token_1, expires_at_1)
        token2 = Token(token_id, user_id_2, access_token_2, expires_at_2) # Mismo ID
        token3 = Token(str(uuid.uuid4()), user_id_1, access_token_1, expires_at_1) # Diferente ID

        assert token1 == token2  # Mismo ID
        assert token1 != token3  # Diferente ID
        assert token2 != token3  # Diferente ID

    # Puedes agregar más pruebas aquí para otros comportamientos del modelo
    # Por ejemplo, probar la representación (__repr__), etc.
