# tests/auth/application/test_handlers.py
"""
Pruebas unitarias para los handlers de aplicación del contexto 'auth'.
Estas pruebas validan la lógica de los casos de uso, aislando las dependencias
(mockeando repositorios, usuarios y funciones auxiliares).
"""
import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta, timezone

# Importamos los comandos y queries
from app.auth.application.commands.login_command import LoginCommand
from app.auth.application.queries.validate_token_query import ValidateTokenQuery

# Importamos los handlers a probar
# Importamos las funciones auxiliares seguras desde donde las definiste
from app.auth.application.commands.handlers import (
    handle_login_user,
    secure_verify_password,
    generate_access_token,
    calculate_expires_at
)
# Importamos el handler de validación (consulta) desde queries.handlers
from app.auth.application.queries.handlers import handle_validate_token

# Importamos modelos de dominio y repositorios (para tipos y mocks)
from app.users.domain.models import User
from app.users.domain.repositories import UserRepository
from app.auth.domain.models import Token
from app.auth.domain.repositories import TokenRepository

# --- Mocks para funciones auxiliares (simulando implementaciones reales) ---
def mock_verify_password(plain: str, hashed: str) -> bool:
    return hashed == "correct_hashed_password"

def mock_generate_token() -> str:
    return "generated_test_token_abc123"

def mock_calculate_expires(hours: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)

# --- Función auxiliar para crear mocks compatibles ---
def create_user_repo_mock_with_get_by_email():
    """Crea un mock de UserRepository y le añade el método get_by_email."""
    mock_repo = Mock(spec=UserRepository) # Crea el mock con la spec
    # Añade explícitamente el método get_by_email que necesitamos simular
    mock_repo.get_by_email = Mock()
    return mock_repo

# --- Pruebas para handle_login_user ---

def test_handle_login_user_success():
    """Prueba el login exitoso de un usuario."""
    # 1. Arrange
    command = LoginCommand(email="user@example.com", password="secret")

    mock_user = User("user-123", "Test User", "user@example.com", "correct_hashed_password")
    
    mock_user_repo = create_user_repo_mock_with_get_by_email()
    mock_user_repo.get_by_email.return_value = mock_user
    
    mock_token_repo = Mock(spec=TokenRepository)
    mock_token_repo.save.return_value = None

    # 2. Act
    access_token_result = handle_login_user(
        command,
        mock_user_repo,
        mock_token_repo,
        mock_verify_password,
        mock_generate_token,
        mock_calculate_expires
    )

    # 3. Assert
    mock_user_repo.get_by_email.assert_called_once_with(command.email)
    mock_token_repo.save.assert_called_once()
    
    saved_token_arg = mock_token_repo.save.call_args[0][0] # Primer argumento posicional
    assert isinstance(saved_token_arg, Token)
    assert saved_token_arg.user_id == mock_user.id
    assert saved_token_arg.access_token == mock_generate_token()
    expected_expires = mock_calculate_expires(1)
    assert abs((saved_token_arg.expires_at - expected_expires).total_seconds()) < 2
    
    assert access_token_result == mock_generate_token()

def test_handle_login_user_invalid_credentials_user_not_found():
    """Prueba login con credenciales inválidas (usuario no encontrado)."""
    command = LoginCommand(email="nonexistent@example.com", password="any_password")
    
    mock_user_repo = create_user_repo_mock_with_get_by_email()
    mock_user_repo.get_by_email.return_value = None
    
    mock_token_repo = Mock(spec=TokenRepository)

    with pytest.raises(ValueError, match="Credenciales inválidas."):
        handle_login_user(
            command,
            mock_user_repo,
            mock_token_repo,
            mock_verify_password,
            mock_generate_token,
            mock_calculate_expires
        )
    
    mock_user_repo.get_by_email.assert_called_once_with(command.email)
    mock_token_repo.save.assert_not_called()

def test_handle_login_user_invalid_credentials_wrong_password():
    """Prueba login con credenciales inválidas (contraseña incorrecta)."""
    command = LoginCommand(email="user@example.com", password="wrong_password")

    # Creamos el usuario mock con la contraseña hasheada correcta
    mock_user = User("user-123", "Test User", "user@example.com", "correct_hashed_password")
    mock_user_repo = create_user_repo_mock_with_get_by_email()
    mock_user_repo.get_by_email.return_value = mock_user

    mock_token_repo = Mock(spec=TokenRepository)

    # Llamamos al handler
    # NO esperamos que lance una excepcion aqui, solo queremos verificar la llamada a verify_password_fn
    # Para eso, mockeamos verify_password_fn directamente en la llamada al handler
    from unittest.mock import MagicMock
    mock_verify_password_fn = MagicMock()
    # Configuramos el mock para que devuelva False, simulando una contraseña incorrecta
    mock_verify_password_fn.return_value = False

    # Ahora llamamos al handler con nuestro mock
    with pytest.raises(ValueError, match="Credenciales inválidas."):
        handle_login_user(
            command,
            mock_user_repo,
            mock_token_repo,
            mock_verify_password_fn, # <-- Usamos nuestro mock controlado
            mock_generate_token,
            mock_calculate_expires
        )

    # Aserciones adicionales para verificar que se llamó correctamente
    mock_user_repo.get_by_email.assert_called_once_with(command.email)
    # Verificamos que nuestra funcion mock haya sido llamada con los argumentos correctos
    mock_verify_password_fn.assert_called_once_with(command.password, mock_user.hashed_password)
    mock_token_repo.save.assert_not_called()

# --- Pruebas para handle_validate_token ---

def test_handle_validate_token_success_valid():
    """Prueba la validación exitosa de un token válido."""
    # 1. Arrange
    query = ValidateTokenQuery(access_token="valid_test_token")
    
    mock_token = Token(
        token_id="token-789",
        user_id="user-123",
        access_token=query.access_token,
        expires_at= datetime.now(timezone.utc) + timedelta(hours=1) # No expirado
    )
    
    mock_token_repo = Mock(spec=TokenRepository)
    mock_token_repo.find_by_access_token.return_value = mock_token

    # 2. Act
    result = handle_validate_token(query, mock_token_repo)

    # 3. Assert
    mock_token_repo.find_by_access_token.assert_called_once_with(query.access_token)
    
    assert result is not None
    assert result["is_valid"] is True
    assert result["user_id"] == mock_token.user_id
    assert result["expires_at"] == mock_token.expires_at.isoformat()

def test_handle_validate_token_not_found():
    """Prueba la validación de un token que no existe."""
    query = ValidateTokenQuery(access_token="nonexistent_token")
    
    mock_token_repo = Mock(spec=TokenRepository)
    mock_token_repo.find_by_access_token.return_value = None

    result = handle_validate_token(query, mock_token_repo)

    mock_token_repo.find_by_access_token.assert_called_once_with(query.access_token)
    assert result is None

# Nota: Probar un token expirado directamente es complejo con el constructor actual de Token.
# La lógica de Token.is_expired() se prueba en tests/auth/domain/test_models.py.
# Esta prueba se omite para evitar fragilidad.
