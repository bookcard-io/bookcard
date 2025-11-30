# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from fastapi import Request
from sqlmodel import Session

from fundamental.models.auth import User
from fundamental.repositories.user_repository import UserRepository
from fundamental.services.opds.auth_service import OpdsAuthService
from fundamental.services.security import JWTManager, PasswordHasher, SecurityTokenError


@pytest.fixture
def mock_session() -> Mock:
    return Mock(spec=Session)


@pytest.fixture
def mock_user_repo() -> Mock:
    return Mock(spec=UserRepository)


@pytest.fixture
def mock_hasher() -> Mock:
    return Mock(spec=PasswordHasher)


@pytest.fixture
def mock_jwt_manager() -> Mock:
    return Mock(spec=JWTManager)


@pytest.fixture
def auth_service(
    mock_session: Mock, mock_user_repo: Mock, mock_hasher: Mock, mock_jwt_manager: Mock
) -> OpdsAuthService:
    return OpdsAuthService(
        session=mock_session,
        user_repo=mock_user_repo,
        hasher=mock_hasher,
        jwt_manager=mock_jwt_manager,
    )


@pytest.fixture
def mock_request() -> Mock:
    request = Mock(spec=Request)
    request.headers = {}
    request.app = Mock()
    request.app.state = Mock()
    # Ensure config is present for JWT part
    request.app.state.config = Mock()
    return request


class TestOpdsAuthService:
    def test_init(self, auth_service: OpdsAuthService) -> None:
        """Test initialization."""
        assert auth_service is not None

    def test_authenticate_request_basic_auth_success(
        self,
        auth_service: OpdsAuthService,
        mock_request: Mock,
        mock_user_repo: Mock,
        mock_hasher: Mock,
    ) -> None:
        """Test successful authentication via Basic Auth."""
        # Arrange
        mock_request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}  # user:pass
        user = User(id=1, username="user", password_hash="hash")
        mock_user_repo.find_by_username.return_value = user
        mock_hasher.verify.return_value = True

        # Act
        result = auth_service.authenticate_request(mock_request)

        # Assert
        assert result == user
        mock_user_repo.find_by_username.assert_called_with("user")
        mock_hasher.verify.assert_called_with("pass", "hash")

    def test_authenticate_request_basic_auth_invalid_header_format(
        self, auth_service: OpdsAuthService, mock_request: Mock
    ) -> None:
        """Test Basic Auth with invalid header format."""
        mock_request.headers = {"Authorization": "BasicInvalid"}

        result = auth_service.authenticate_request(mock_request)

        # Should try JWT next, but since header doesn't start with Bearer, it returns None
        assert result is None

    def test_authenticate_request_basic_auth_decode_error(
        self, auth_service: OpdsAuthService, mock_request: Mock
    ) -> None:
        """Test Basic Auth with invalid base64."""
        mock_request.headers = {"Authorization": "Basic !!!"}

        result = auth_service.authenticate_request(mock_request)

        assert result is None

    def test_authenticate_request_basic_auth_user_not_found(
        self, auth_service: OpdsAuthService, mock_request: Mock, mock_user_repo: Mock
    ) -> None:
        """Test Basic Auth where user is not found."""
        mock_request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        mock_user_repo.find_by_username.return_value = None
        mock_user_repo.find_by_email.return_value = None

        result = auth_service.authenticate_request(mock_request)

        assert result is None

    def test_authenticate_request_basic_auth_wrong_password(
        self,
        auth_service: OpdsAuthService,
        mock_request: Mock,
        mock_user_repo: Mock,
        mock_hasher: Mock,
    ) -> None:
        """Test Basic Auth with wrong password."""
        mock_request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        user = User(id=1, username="user", password_hash="hash")
        mock_user_repo.find_by_username.return_value = user
        mock_hasher.verify.return_value = False

        result = auth_service.authenticate_request(mock_request)

        assert result is None

    def test_authenticate_request_jwt_success(
        self,
        auth_service: OpdsAuthService,
        mock_request: Mock,
        mock_jwt_manager: Mock,
        mock_user_repo: Mock,
    ) -> None:
        """Test successful authentication via JWT."""
        # Arrange
        mock_request.headers = {"Authorization": "Bearer token123"}

        # We need to mock JWTManager instantiation inside the method or patch it
        # The service instantiates a NEW JWTManager(config).
        # We should patch the class `JWTManager` where it is imported in `auth_service.py`.

        with patch(
            "fundamental.services.opds.auth_service.JWTManager"
        ) as mock_jwt_class:
            mock_jwt_instance = mock_jwt_class.return_value
            mock_jwt_instance.decode_token.return_value = {"sub": "1"}

            user = User(id=1, username="user")
            mock_user_repo.get.return_value = user

            # Act
            result = auth_service.authenticate_request(mock_request)

            # Assert
            assert result == user
            mock_user_repo.get.assert_called_with(1)

    def test_authenticate_request_jwt_no_header(
        self, auth_service: OpdsAuthService, mock_request: Mock
    ) -> None:
        """Test JWT auth with no authorization header."""
        mock_request.headers = {}
        result = auth_service.authenticate_request(mock_request)
        assert result is None

    def test_authenticate_request_jwt_no_config(
        self, auth_service: OpdsAuthService, mock_request: Mock
    ) -> None:
        """Test JWT auth when app state has no config."""
        mock_request.headers = {"Authorization": "Bearer token"}
        del mock_request.app.state.config

        result = auth_service.authenticate_request(mock_request)

        assert result is None

    def test_authenticate_request_jwt_invalid_token(
        self, auth_service: OpdsAuthService, mock_request: Mock
    ) -> None:
        """Test JWT auth with invalid token."""
        mock_request.headers = {"Authorization": "Bearer token"}

        with patch(
            "fundamental.services.opds.auth_service.JWTManager"
        ) as mock_jwt_class:
            mock_jwt_instance = mock_jwt_class.return_value
            mock_jwt_instance.decode_token.side_effect = SecurityTokenError("Invalid")

            result = auth_service.authenticate_request(mock_request)

            assert result is None

    def test_authenticate_request_jwt_invalid_user_id(
        self, auth_service: OpdsAuthService, mock_request: Mock
    ) -> None:
        """Test JWT auth with invalid user ID in claim."""
        mock_request.headers = {"Authorization": "Bearer token"}

        with patch(
            "fundamental.services.opds.auth_service.JWTManager"
        ) as mock_jwt_class:
            mock_jwt_instance = mock_jwt_class.return_value
            mock_jwt_instance.decode_token.return_value = {"sub": "0"}

            result = auth_service.authenticate_request(mock_request)

            assert result is None

    @pytest.mark.parametrize("exception", [ValueError, KeyError])
    def test_authenticate_request_jwt_other_exceptions(
        self,
        auth_service: OpdsAuthService,
        mock_request: Mock,
        exception: type[Exception],
    ) -> None:
        """Test JWT auth catching other exceptions."""
        mock_request.headers = {"Authorization": "Bearer token"}

        with patch(
            "fundamental.services.opds.auth_service.JWTManager"
        ) as mock_jwt_class:
            mock_jwt_instance = mock_jwt_class.return_value
            mock_jwt_instance.decode_token.side_effect = exception

            result = auth_service.authenticate_request(mock_request)

            assert result is None

    def test_authenticate_basic_auth_by_email(
        self,
        auth_service: OpdsAuthService,
        mock_request: Mock,
        mock_user_repo: Mock,
        mock_hasher: Mock,
    ) -> None:
        """Test Basic Auth by email fallback."""
        mock_request.headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        mock_user_repo.find_by_username.return_value = None
        user = User(id=1, email="user", password_hash="hash")
        mock_user_repo.find_by_email.return_value = user
        mock_hasher.verify.return_value = True

        result = auth_service.authenticate_request(mock_request)

        assert result == user
