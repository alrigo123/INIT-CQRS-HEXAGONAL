# tests/users/domain/test_user_model.py
"""
Pruebas unitarias para el modelo de dominio User.
Estas pruebas validan las reglas de negocio centrales del usuario.
"""

import pytest
# Importamos la entidad de dominio y sus excepciones
from app.users.domain.models import User, InvalidEmailError

class TestUserModel:
    """Grupo de pruebas para la clase User."""

    def test_user_creation_with_valid_data(self):
        """Prueba la creación de un usuario con datos válidos."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        name = "Juan Pérez"
        email = "juan.perez@example.com"
        hashed_password = "una_contraseña_hasheada_segura"

        user = User(user_id, name, email, hashed_password)

        assert user.id == user_id
        assert user.name == name
        assert user.email == email.lower()  # Verifica normalización
        assert user.hashed_password == hashed_password

    def test_user_creation_with_invalid_email_raises_exception(self):
        """Prueba que crear un usuario con email inválido lance una excepción."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        name = "Juan Pérez"
        invalid_email = "not-an-email"
        hashed_password = "una_contraseña_hasheada_segura"

        with pytest.raises(InvalidEmailError):
            User(user_id, name, invalid_email, hashed_password)

    def test_user_email_is_normalized_to_lowercase(self):
        """Prueba que el email se normalice a minúsculas."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        name = "Juan Pérez"
        email_mixed_case = "Juan.Perez@Example.com" # Email con mayúsculas
        hashed_password = "una_contraseña_hasheada_segura"

        user = User(user_id, name, email_mixed_case, hashed_password)

        # El email almacenado debe estar en minúsculas
        assert user.email == email_mixed_case.lower()
        assert user.email == "juan.perez@example.com"

    def test_user_name_cannot_be_empty_or_whitespace(self):
        """Prueba que el nombre no pueda ser vacío o solo espacios."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        email = "juan.perez@example.com"
        hashed_password = "una_contraseña_hasheada_segura"

        # Prueba con string vacío
        with pytest.raises(ValueError, match="El nombre no puede estar vacío."):
            user = User(user_id, "", email, hashed_password)
            user.name = "" # También probar el setter

        # Prueba con solo espacios
        with pytest.raises(ValueError, match="El nombre no puede estar vacío."):
            user = User(user_id, "   ", email, hashed_password)
            user.name = "   " # También probar el setter

    # Puedes agregar más pruebas aquí para otros comportamientos del modelo
    # Por ejemplo, probar la igualdad (__eq__) si la implementaste
    def test_user_equality_is_based_on_id(self):
        """Prueba que dos usuarios sean iguales si tienen el mismo ID."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        user1 = User(user_id, "Juan", "juan@example.com", "hash1")
        user2 = User(user_id, "Maria", "maria@example.com", "hash2") # Diferente nombre y email
        user3 = User("otro-id", "Juan", "juan@example.com", "hash1") # Mismo nombre, diferente ID

        assert user1 == user2  # Mismo ID
        assert user1 != user3  # Diferente ID
        assert user2 != user3  # Diferente ID
