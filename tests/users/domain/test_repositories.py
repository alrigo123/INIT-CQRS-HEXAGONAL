# tests/users/domain/test_repositories.py
# Este archivo prueba el contrato definido por UserRepository.
# Para ello, creamos un mock simple que implemente la interfaz.
# En un entorno real, la implementación real (SQLAlchemyUserRepository) cumpliría este contrato.

import pytest
from abc import ABC, abstractmethod
from typing import Optional
from app.users.domain.models import User
# Importamos la interfaz a probar
from app.users.domain.repositories import UserRepository

# --- Mock simple que implementa UserRepository ---
# Esto simula una implementación concreta para probar el contrato.
class MockUserRepository(UserRepository):
    def __init__(self):
        self._users = {} # Simula un almacenamiento en memoria

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

# --- Pruebas para el contrato UserRepository ---
# Estas pruebas verifican que cualquier implementación de UserRepository
# debe comportarse de cierta manera.

def test_user_repository_save_and_get_by_id():
    """Prueba que save y get_by_id funcionen como se espera del contrato."""
    repo = MockUserRepository() # Usamos nuestro mock
    user = User("123", "Alice", "alice@example.com", "hashed_pass")

    # Guardar el usuario
    repo.save(user)

    # Recuperar el usuario por ID
    retrieved_user = repo.get_by_id("123")

    # Verificar que se recuperó el mismo usuario
    assert retrieved_user is not None
    assert retrieved_user == user
    assert retrieved_user.id == "123"
    assert retrieved_user.name == "Alice"
    assert retrieved_user.email == "alice@example.com"
    assert retrieved_user.hashed_password == "hashed_pass"

def test_user_repository_get_by_id_not_found():
    """Prueba que get_by_id devuelva None si el usuario no existe."""
    repo = MockUserRepository()

    # Intentar recuperar un usuario que no existe
    retrieved_user = repo.get_by_id("non-existent-id")

    # Verificar que se devuelve None
    assert retrieved_user is None

# --- Prueba para verificar que UserRepository es una interfaz abstracta ---
# Esto asegura que no se pueda instanciar directamente y que tenga métodos abstractos.

def test_user_repository_is_abstract():
    """Prueba que UserRepository sea una clase abstracta."""
    # Intentar instanciar directamente debe fallar
    with pytest.raises(TypeError):
        UserRepository() # type: ignore

    # Verificar que los métodos sean abstractos
    # Esta prueba es más técnica y opcional, pero útil para asegurar la definición.
    assert hasattr(UserRepository, 'save')
    assert hasattr(UserRepository.save, '__isabstractmethod__')
    assert UserRepository.save.__isabstractmethod__ is True # type: ignore
    
    assert hasattr(UserRepository, 'get_by_id')
    assert hasattr(UserRepository.get_by_id, '__isabstractmethod__')
    assert UserRepository.get_by_id.__isabstractmethod__ is True # type: ignore
