# tests/auth/domain/test_repositories.py
import pytest
from abc import ABC, abstractmethod
from typing import Optional
# Importamos timezone para ser consistentes con la app
from datetime import datetime, timedelta, timezone

from app.auth.domain.models import Token
# Importamos la interfaz a probar
from app.auth.domain.repositories import TokenRepository

# --- Mock simple que implementa TokenRepository ---
class MockTokenRepository(TokenRepository):
    def __init__(self):
        self._tokens = {}

    def save(self, token: Token) -> None:
        self._tokens[token.id] = token

    def find_by_access_token(self, access_token: str) -> Optional[Token]:
        # Buscar por access_token en el diccionario
        for t in self._tokens.values():
            if t.access_token == access_token:
                return t
        return None

    def delete(self, token_id: str) -> bool:
        if token_id in self._tokens:
            del self._tokens[token_id]
            return True
        return False

# --- Pruebas para el contrato TokenRepository ---
def test_token_repository_save_and_find_by_access_token():
    """Prueba save y find_by_access_token."""
    repo = MockTokenRepository()
    # Usamos datetime.now(timezone.utc) para ser consistentes con la app
    token = Token("123", "user1", "access123", datetime.now(timezone.utc) + timedelta(hours=1))

    repo.save(token)
    found_token = repo.find_by_access_token("access123")

    assert found_token is not None
    assert found_token == token
    assert found_token.id == "123"
    assert found_token.user_id == "user1"
    assert found_token.access_token == "access123"

def test_token_repository_find_by_access_token_not_found():
    """Prueba find_by_access_token devuelve None si no se encuentra."""
    repo = MockTokenRepository()
    found_token = repo.find_by_access_token("non-existent-token")
    assert found_token is None

def test_token_repository_delete_success():
    """Prueba delete devuelve True si se elimina."""
    repo = MockTokenRepository()
    # Usamos datetime.now(timezone.utc) para ser consistentes con la app
    token = Token("123", "user1", "access123", datetime.now(timezone.utc) + timedelta(hours=1))
    repo.save(token)

    result = repo.delete("123")
    assert result is True
    assert repo.find_by_access_token("access123") is None

def test_token_repository_delete_not_found():
    """Prueba delete devuelve False si no se encuentra."""
    repo = MockTokenRepository()
    result = repo.delete("non-existent-id")
    assert result is False

# --- Prueba para verificar que TokenRepository es una interfaz abstracta ---
# Corregida para usar TokenRepository
def test_token_repository_is_abstract():
    """Prueba que TokenRepository sea una clase abstracta."""
    with pytest.raises(TypeError):
        TokenRepository() # type: ignore

    # Verificar que los métodos sean abstractos
    assert hasattr(TokenRepository, 'save')
    assert hasattr(TokenRepository.save, '__isabstractmethod__')
    assert TokenRepository.save.__isabstractmethod__ is True # type: ignore
    
    assert hasattr(TokenRepository, 'find_by_access_token')
    assert hasattr(TokenRepository.find_by_access_token, '__isabstractmethod__')
    assert TokenRepository.find_by_access_token.__isabstractmethod__ is True # type: ignore

    assert hasattr(TokenRepository, 'delete')
    assert hasattr(TokenRepository.delete, '__isabstractmethod__')
    assert TokenRepository.delete.__isabstractmethod__ is True # type: ignore
