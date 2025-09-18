# tests/auth/application/commands/test_handlers.py
"""
Pruebas unitarias para el handler handle_register_user_for_auth_context.
Estas pruebas validan la lógica de aplicación para registrar un usuario en auth.
Se mockean las dependencias (repositorios, funciones).
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
# Importamos lo que vamos a probar
from app.auth.application.commands.handlers import handle_register_user_for_auth_context
# Importamos las interfaces para mockearlas
from app.auth.domain.repositories import TokenRepository
from app.auth.domain.models import Token

# --- Funciones auxiliares para las pruebas ---
def dummy_generate_token():
    return "token_generado_por_funcion_dummy"

def dummy_calculate_expires(hours: int = 1):
    from datetime import datetime, timedelta
    return datetime.utcnow() + timedelta(hours=hours)

class TestHandleRegisterUserForAuthContext:
    """Grupo de pruebas para handle_register_user_for_auth_context."""

    def test_handle_register_user_success(self):
        """Prueba que el handler maneje correctamente un registro exitoso."""
        # 1. Arrange (Preparar)
        user_id = "user-test-id-123"
        mock_token_repository = Mock(spec=TokenRepository)
        mock_token_repository.save.return_value = None # Simula guardado exitoso

        # 2. Act (Ejecutar)
        access_token = handle_register_user_for_auth_context(
            user_id=user_id,
            user_email="test@example.com",
            token_repository=mock_token_repository,
            generate_token_fn=dummy_generate_token,
            calculate_expires_fn=dummy_calculate_expires
        )

        # 3. Assert (Verificar)
        # Verificar que se llamó a save en el repositorio
        mock_token_repository.save.assert_called_once()
        # Verificar que el objeto pasado a save es una instancia de Token
        args, kwargs = mock_token_repository.save.call_args
        saved_token = args[0] # El primer argumento posicional
        assert isinstance(saved_token, Token)
        assert saved_token.user_id == user_id
        assert saved_token.access_token == "token_generado_por_funcion_dummy"
        # Verificar que se devuelve el token de acceso
        assert access_token == "token_generado_por_funcion_dummy"

    def test_handle_register_user_repository_error_is_handled(self):
        """Prueba que un error del repositorio sea manejado correctamente."""
         # 1. Arrange
        user_id = "user-test-id-123"
        mock_token_repository = Mock(spec=TokenRepository)
        # Configuramos el mock para que save lance una excepción
        mock_token_repository.save.side_effect = RuntimeError("Error al guardar en BD")

        # 2. Act & Assert
        with pytest.raises(RuntimeError, match="Error al procesar el registro de usuario en auth"):
            handle_register_user_for_auth_context(
                user_id=user_id,
                user_email="test@example.com",
                token_repository=mock_token_repository,
                generate_token_fn=dummy_generate_token,
                calculate_expires_fn=dummy_calculate_expires
            )
        
        # Verificar que el repositorio fue llamado
        mock_token_repository.save.assert_called_once()

