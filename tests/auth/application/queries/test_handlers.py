# tests/auth/application/queries/test_handlers.py
"""
Pruebas unitarias para el handler handle_validate_token.
Estas pruebas validan la lógica de aplicación para validar un token.
Se mockean las dependencias (repositorios).
"""
import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
# Importamos lo que vamos a probar
from app.auth.application.queries.handlers import handle_validate_token
from app.auth.application.queries.validate_token_query import ValidateTokenQuery
# Importamos las interfaces y modelos para mockearlos
from app.auth.domain.repositories import TokenRepository
from app.auth.domain.models import Token

class TestHandleValidateToken:
    """Grupo de pruebas para handle_validate_token."""

    def test_handle_validate_token_valid_token_returns_user_info(self):
        """Prueba que se devuelva información correcta para un token válido."""
        # 1. Arrange
        access_token = "token_valido_123"
        user_id = "user-test-id-456"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        query = ValidateTokenQuery(access_token=access_token)
        mock_token_repository = Mock(spec=TokenRepository)
        
        # Mock del token encontrado
        mock_token = Mock(spec=Token)
        mock_token.user_id = user_id
        mock_token.expires_at = expires_at
        mock_token.is_expired.return_value = False # Token no expirado
        
        mock_token_repository.find_by_access_token.return_value = mock_token

        # 2. Act
        result = handle_validate_token(query, mock_token_repository)

        # 3. Assert
        assert result is not None
        assert result["is_valid"] is True
        assert result["user_id"] == user_id
        assert result["expires_at"] == expires_at.isoformat()
        mock_token_repository.find_by_access_token.assert_called_once_with(access_token)

    def test_handle_validate_token_not_found_returns_none(self):
        """Prueba que se devuelva None si el token no se encuentra."""
        # 1. Arrange
        access_token = "token_inexistente_789"
        query = ValidateTokenQuery(access_token=access_token)
        mock_token_repository = Mock(spec=TokenRepository)
        mock_token_repository.find_by_access_token.return_value = None # Token no encontrado

        # 2. Act
        result = handle_validate_token(query, mock_token_repository)

        # 3. Assert
        assert result is None
        mock_token_repository.find_by_access_token.assert_called_once_with(access_token)

    def test_handle_validate_token_expired_returns_none(self):
        """Prueba que se devuelva None si el token ha expirado."""
        # 1. Arrange
        access_token = "token_expirado_000"
        user_id = "user-test-id-000"
        expires_at = datetime.utcnow() - timedelta(hours=1) # Fecha pasada
        
        query = ValidateTokenQuery(access_token=access_token)
        mock_token_repository = Mock(spec=TokenRepository)
        
        # Mock del token expirado
        mock_token = Mock(spec=Token)
        mock_token.user_id = user_id
        mock_token.expires_at = expires_at
        mock_token.is_expired.return_value = True # Token expirado
        
        mock_token_repository.find_by_access_token.return_value = mock_token

        # 2. Act
        result = handle_validate_token(query, mock_token_repository)

        # 3. Assert
        assert result is None
        mock_token_repository.find_by_access_token.assert_called_once_with(access_token)
        mock_token.is_expired.assert_called_once() # Verificar que se llamó a is_expired

    def test_handle_validate_token_repository_error_is_handled(self):
        """Prueba que un error del repositorio sea manejado."""
         # 1. Arrange
        access_token = "token_error_repo_abc"
        query = ValidateTokenQuery(access_token=access_token)
        mock_token_repository = Mock(spec=TokenRepository)
        # Simular error en el repositorio
        mock_token_repository.find_by_access_token.side_effect = RuntimeError("Error de BD")

        # 2. Act & Assert
        with pytest.raises(RuntimeError, match="Error al validar el token"):
            handle_validate_token(query, mock_token_repository)
