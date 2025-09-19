# tests/users/domain/test_models.py
import pytest
from app.users.domain.models import User, InvalidEmailError #, WeakPasswordError (si la usas)

def test_user_creation_valid():
    """Prueba la creación exitosa de un usuario con datos válidos."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    name = "Alice"
    email = "alice@example.com"
    hashed_password = "hashed_password_123"

    user = User(user_id, name, email, hashed_password)

    assert user.id == user_id
    assert user.name == name
    assert user.email == email.lower() # Verifica normalización
    assert user.hashed_password == hashed_password

def test_user_creation_invalid_email():
    """Prueba que se lance InvalidEmailError con un email inválido."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    name = "Bob"
    invalid_email = "not-an-email"
    hashed_password = "hashed_password_123"

    with pytest.raises(InvalidEmailError):
        User(user_id, name, invalid_email, hashed_password)

def test_user_name_setter_valid():
    """Prueba el setter de name con un valor válido."""
    user = User("123e4567-e89b-12d3-a456-426614174000", "Alice", "alice@example.com", "hashed_password_123")
    new_name = "Alice Cooper"
    
    user.name = new_name
    
    assert user.name == new_name

def test_user_name_setter_invalid_empty():
    """Prueba que el setter de name lance ValueError con un nombre vacío."""
    user = User("123e4567-e89b-12d3-a456-426614174000", "Alice", "alice@example.com", "hashed_password_123")
    
    with pytest.raises(ValueError, match="El nombre no puede estar vacío."):
        user.name = ""

def test_user_name_setter_invalid_whitespace():
    """Prueba que el setter de name limpie espacios y lance ValueError si queda vacío."""
    user = User("123e4567-e89b-12d3-a456-426614174000", "Alice", "alice@example.com", "hashed_password_123")
    
    with pytest.raises(ValueError, match="El nombre no puede estar vacío."):
        user.name = "   "

def test_user_equality():
    """Prueba la igualdad de usuarios basada en ID."""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    user1 = User(user_id, "Alice", "alice@example.com", "hashed_password_123")
    user2 = User(user_id, "Bob", "bob@example.com", "different_hashed_password")
    user3 = User("different-id", "Alice", "alice@example.com", "hashed_password_123")
    
    assert user1 == user2 # Mismo ID
    assert user1 != user3 # Diferente ID
    assert user1 != "not a user" # Tipo diferente

# Puedes añadir más pruebas para otros aspectos como __repr__, email en mayúsculas que se normalice, etc.