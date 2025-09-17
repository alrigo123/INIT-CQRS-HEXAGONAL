# tests/users/application/test_create_user_handler.py
"""
Pruebas unitarias para el handler handle_create_user.
Estas pruebas validan la lógica de aplicación para crear un usuario,
mockeando las dependencias (repositorio, hasher).
"""

import pytest
from unittest.mock import Mock, MagicMock
# Importamos lo que vamos a probar
from app.users.application.commands.create_user_command import CreateUserCommand
from app.users.application.commands.handlers import handle_create_user
# Importamos las excepciones del dominio que podrían ser lanzadas
from app.users.domain.models import InvalidEmailError
# Importamos las interfaces para mockearlas
from app.users.domain.repositories import UserRepository


# Una funcion de hash dummy para las pruebas
def dummy_hasher(password: str) -> str:
    return f"hashed_{password}"

class TestHandleCreateUser:
    """Grupo de pruebas para la función handle_create_user."""

    def test_handle_create_user_success(self):
        """Prueba que el handler maneje correctamente un comando válido."""
        # 1. Arrange (Preparar)
        command = CreateUserCommand(
            name="Juan Pérez",
            email="juan.perez@example.com",
            password="UnaContraseñaSegura123!"
        )
        
        # Mock del repositorio
        mock_repository = Mock(spec=UserRepository)
        # Configuramos el mock para que save no lance excepciones
        mock_repository.save.return_value = None 

        # 2. Act (Ejecutar)
        user_id = handle_create_user(command, mock_repository, dummy_hasher)

        # 3. Assert (Verificar)
        # Verificar que se llamó a save en el repositorio
        mock_repository.save.assert_called_once()
        # Verificar que el objeto pasado a save es una instancia de User
        args, kwargs = mock_repository.save.call_args
        saved_user = args[0] # El primer argumento posicional
        assert saved_user.name == command.name
        assert saved_user.email == command.email.lower()
        assert saved_user.hashed_password == "hashed_UnaContraseñaSegura123!"
        # Verificar que se devuelve un ID (no necesitamos verificar el valor exacto del UUID)
        assert isinstance(user_id, str)
        # Un UUID típico tiene varios guiones
        assert len(user_id) > 10 
        assert "-" in user_id

    def test_handle_create_user_invalid_email_raises_error(self):
        """Prueba que el handler maneje un email inválido lanzando una excepción."""
        # 1. Arrange
        command = CreateUserCommand(
            name="Juan Pérez",
            email="email_invalido", # Email inválido
            password="UnaContraseñaSegura123!"
        )
        mock_repository = Mock(spec=UserRepository)

        # 2. Act & Assert
        # Esperamos que se lance una excepción (podría ser ValueError del handler o InvalidEmailError del dominio)
        with pytest.raises((ValueError, InvalidEmailError)):
            handle_create_user(command, mock_repository, dummy_hasher)
        
        # Verificar que el repositorio NO fue llamado
        mock_repository.save.assert_not_called()

    def test_handle_create_user_repository_error_is_handled(self):
        """Prueba que un error del repositorio sea manejado correctamente."""
         # 1. Arrange
        command = CreateUserCommand(
            name="Juan Pérez",
            email="juan.perez@example.com",
            password="UnaContraseñaSegura123!"
        )
        mock_repository = Mock(spec=UserRepository)
        # Configuramos el mock para que save lance una excepción
        mock_repository.save.side_effect = RuntimeError("Error al guardar en BD")

        # 2. Act & Assert
        with pytest.raises(RuntimeError, match="Error al guardar el usuario en el repositorio"):
            handle_create_user(command, mock_repository, dummy_hasher)
