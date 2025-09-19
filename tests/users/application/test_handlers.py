# tests/users/application/test_handlers.py
"""
Pruebas unitarias para los handlers de aplicación del contexto 'users'.
Estas pruebas validan la lógica de los casos de uso, aislando las dependencias
(mockeando repositorios y funciones auxiliares).
"""
import pytest
from unittest.mock import Mock

# Importamos los comandos y queries
from app.users.application.queries.get_user_query import GetUserQuery

# Importamos los handlers a probar
from app.users.application.queries.handlers import handle_get_user

# Importamos el modelo de dominio y el repositorio (para tipos y mocks)
from app.users.domain.models import User
from app.users.domain.repositories import UserRepository

# --- Pruebas para handle_get_user ---

def test_handle_get_user_success():
    """Prueba la obtención exitosa de un usuario."""
    # 1. Arrange
    query = GetUserQuery(user_id="123e4567-e89b-12d3-a456-426614174000")
    expected_user = User(
        user_id=query.user_id,
        name="Alice",
        email="alice@example.com",
        hashed_password="hashed_secret"
    )
    
    mock_repo = Mock(spec=UserRepository)
    mock_repo.get_by_id.return_value = expected_user

    # 2. Act
    user_result = handle_get_user(query, mock_repo)

    # 3. Assert
    mock_repo.get_by_id.assert_called_once_with(query.user_id)
    assert user_result == expected_user

def test_handle_get_user_not_found():
    """Prueba la obtención de un usuario que no existe."""
    query = GetUserQuery(user_id="non-existent-id")
    
    mock_repo = Mock(spec=UserRepository)
    mock_repo.get_by_id.return_value = None

    user_result = handle_get_user(query, mock_repo)

    mock_repo.get_by_id.assert_called_once_with(query.user_id)
    assert user_result is None

def test_handle_get_user_repository_error():
    """Prueba que los errores del repositorio se propagan."""
    query = GetUserQuery(user_id="123e4567-e89b-12d3-a456-426614174000")
    
    mock_repo = Mock(spec=UserRepository)
    # Simulamos que el repositorio lanza una excepción
    mock_repo.get_by_id.side_effect = Exception("DB Error")

    # Como handle_get_user no captura excepciones, la excepción se propaga
    with pytest.raises(Exception, match="DB Error"):
        handle_get_user(query, mock_repo)

    mock_repo.get_by_id.assert_called_once_with(query.user_id)
