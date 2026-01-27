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

"""Tests for FastAPI dependency providers."""

from contextlib import suppress
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from sqlmodel import Session

from bookcard.api.deps import (
    get_current_user,
    get_db_session,
    get_kobo_auth_token,
    get_kobo_user,
    get_opds_user,
    get_optional_user,
    require_permission,
)
from bookcard.config import AppConfig
from bookcard.database import create_db_engine
from bookcard.models.auth import User
from bookcard.services.security import SecurityTokenError
from tests.conftest import TEST_ENCRYPTION_KEY, DummySession


def test_get_db_session() -> None:
    """Test database session dependency."""
    config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        database_url="sqlite:///:memory:",
        echo_sql=False,
    )
    engine = create_db_engine(config)
    request = MagicMock(spec=Request)
    request.app.state.engine = engine
    session_gen = get_db_session(request)
    session = next(session_gen)
    assert isinstance(session, Session)
    # Cleanup
    with suppress(StopIteration):
        next(session_gen)


@pytest.mark.parametrize(
    ("auth_header", "expected_error"),
    [
        ("", "missing_token"),
        ("Invalid", "missing_token"),
        ("Basic token123", "missing_token"),
    ],
)
def test_get_current_user_missing_token(auth_header: str, expected_error: str) -> None:
    """Test get_current_user with missing or invalid authorization header."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": auth_header}
    session = DummySession()
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request, session)  # type: ignore[arg-type]
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.detail == expected_error


def test_get_current_user_invalid_token() -> None:
    """Test get_current_user with invalid JWT token."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer invalid_token"}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    session = DummySession()
    with patch("bookcard.api.deps.JWTManager") as mock_jwt_class:
        mock_jwt = MagicMock()
        mock_jwt.decode_token.side_effect = SecurityTokenError()
        mock_jwt_class.return_value = mock_jwt
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(request, session)  # type: ignore[arg-type]
        exc = exc_info.value
        assert isinstance(exc, HTTPException)
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.detail == "invalid_token"


def test_get_current_user_user_not_found() -> None:
    """Test get_current_user when user doesn't exist."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer valid_token"}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    session = DummySession()
    with patch("bookcard.api.deps.JWTManager") as mock_jwt_class:
        mock_jwt = MagicMock()
        mock_jwt.decode_token.return_value = {"sub": "999"}
        mock_jwt_class.return_value = mock_jwt
        with patch("bookcard.api.deps.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = None
            mock_repo_class.return_value = mock_repo
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(request, session)  # type: ignore[arg-type]
            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc.detail == "user_not_found"


def test_get_current_user_success() -> None:
    """Test successful get_current_user."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer valid_token"}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    with patch("bookcard.api.deps.JWTManager") as mock_jwt_class:
        mock_jwt = MagicMock()
        mock_jwt.decode_token.return_value = {"sub": "1"}
        mock_jwt_class.return_value = mock_jwt
        with patch("bookcard.api.deps.UserRepository") as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = user
            mock_repo_class.return_value = mock_repo
            result = get_current_user(request, session)  # type: ignore[arg-type]
            assert result == user
            assert result.id == 1
            assert result.username == "testuser"


def test_get_optional_user_bootstrap_allows_anonymous_when_no_active_library() -> None:
    """Allow anonymous access during bootstrap when no active library exists."""
    request = MagicMock(spec=Request)
    request.headers = {}
    session = DummySession()

    with (
        patch("bookcard.api.deps.LibraryRepository") as mock_library_repo_class,
        patch("bookcard.api.deps.LibraryService") as mock_library_service_class,
    ):
        mock_library_repo_class.return_value = MagicMock()
        mock_library_service = MagicMock()
        mock_library_service.get_active_library.return_value = None
        mock_library_service_class.return_value = mock_library_service

        result = get_optional_user(request, session)  # type: ignore[arg-type]
        assert result is None


def test_get_optional_user_missing_token_denied_when_library_exists_and_anonymous_disabled() -> (
    None
):
    """Raise 401 when no token is provided and anonymous browsing is disabled."""
    request = MagicMock(spec=Request)
    request.headers = {}
    session = DummySession()

    with (
        patch("bookcard.api.deps.LibraryRepository") as mock_library_repo_class,
        patch("bookcard.api.deps.LibraryService") as mock_library_service_class,
        patch("bookcard.api.deps.BasicConfigService") as mock_basic_cfg_service_class,
    ):
        mock_library_repo_class.return_value = MagicMock()
        mock_library_service = MagicMock()
        mock_library_service.get_active_library.return_value = MagicMock()
        mock_library_service_class.return_value = mock_library_service

        mock_basic_cfg_service = MagicMock()
        mock_basic_cfg = MagicMock()
        mock_basic_cfg.allow_anonymous_browsing = False
        mock_basic_cfg_service.get_basic_config.return_value = mock_basic_cfg
        mock_basic_cfg_service_class.return_value = mock_basic_cfg_service

        with pytest.raises(HTTPException) as exc:
            get_optional_user(request, session)  # type: ignore[arg-type]
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.value.detail == "missing_token"


def test_get_optional_user_missing_token_allowed_when_library_exists_and_anonymous_enabled() -> (
    None
):
    """Allow anonymous access when anonymous browsing is enabled."""
    request = MagicMock(spec=Request)
    request.headers = {}
    session = DummySession()

    with (
        patch("bookcard.api.deps.LibraryRepository") as mock_library_repo_class,
        patch("bookcard.api.deps.LibraryService") as mock_library_service_class,
        patch("bookcard.api.deps.BasicConfigService") as mock_basic_cfg_service_class,
    ):
        mock_library_repo_class.return_value = MagicMock()
        mock_library_service = MagicMock()
        mock_library_service.get_active_library.return_value = MagicMock()
        mock_library_service_class.return_value = mock_library_service

        mock_basic_cfg_service = MagicMock()
        mock_basic_cfg = MagicMock()
        mock_basic_cfg.allow_anonymous_browsing = True
        mock_basic_cfg_service.get_basic_config.return_value = mock_basic_cfg
        mock_basic_cfg_service_class.return_value = mock_basic_cfg_service

        result = get_optional_user(request, session)  # type: ignore[arg-type]
        assert result is None


def test_get_current_user_oidc_fallback_by_sub() -> None:
    """When local JWT fails and OIDC is enabled, use OIDC token validation."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer any_token"}
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
        oidc_enabled=True,
    )
    session = DummySession()

    user = User(
        id=1,
        username="oidc-user",
        email="oidc@example.com",
        password_hash="hash",
        oidc_sub="oidc-sub",
    )

    with (
        patch("bookcard.api.deps.JWTManager") as mock_jwt_class,
        patch("bookcard.api.deps.OIDCAuthService") as mock_oidc_class,
        patch("bookcard.api.deps.UserRepository") as mock_repo_class,
    ):
        mock_jwt = MagicMock()
        mock_jwt.decode_token.side_effect = SecurityTokenError()
        mock_jwt_class.return_value = mock_jwt

        mock_oidc = MagicMock()
        mock_oidc.validate_access_token.return_value = {"sub": "oidc-sub"}
        mock_oidc_class.return_value = mock_oidc

        mock_repo = MagicMock()
        mock_repo.find_by_oidc_sub.return_value = user
        mock_repo.find_by_email.return_value = None
        mock_repo.find_by_username.return_value = None
        mock_repo_class.return_value = mock_repo

        result = get_current_user(request, session)  # type: ignore[arg-type]
        assert result == user


def test_get_admin_user_success() -> None:
    """Test successful get_admin_user with admin user."""
    from bookcard.api.deps import get_admin_user

    admin_user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )
    result = get_admin_user(admin_user)
    assert result == admin_user
    assert result.is_admin is True


def test_get_admin_user_not_admin() -> None:
    """Test get_admin_user raises 403 when user is not admin."""
    from bookcard.api.deps import get_admin_user

    regular_user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
        is_admin=False,
    )
    with pytest.raises(HTTPException) as exc_info:
        get_admin_user(regular_user)
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_403_FORBIDDEN
    assert exc.detail == "admin_required"


def test_require_permission_no_context() -> None:
    """Test require_permission with no context."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    permission_checker = require_permission("books", "read")

    with patch("bookcard.api.deps.PermissionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.check_permission.return_value = None  # Permission granted
        mock_service_class.return_value = mock_service

        # Should not raise
        permission_checker(user, session)  # type: ignore[arg-type]

        mock_service.check_permission.assert_called_once_with(
            user, "books", "read", None
        )


def test_require_permission_with_dict_context() -> None:
    """Test require_permission with dict context."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    context = {"book_id": 123}
    permission_checker = require_permission("books", "read", context=context)

    with patch("bookcard.api.deps.PermissionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.check_permission.return_value = None  # Permission granted
        mock_service_class.return_value = mock_service

        # Should not raise
        permission_checker(user, session)  # type: ignore[arg-type]

        mock_service.check_permission.assert_called_once_with(
            user, "books", "read", context
        )


def test_require_permission_with_callable_context() -> None:
    """Test require_permission with callable context (resolves to None)."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    # Test the callable context path by using a callable and type: ignore
    # The implementation checks isinstance(context, dict) first, then callable
    def context_provider() -> dict[str, object]:
        return {"book_id": 123}

    # Use type: ignore to bypass type checker since we're testing the callable path
    permission_checker = require_permission(
        "books",
        "read",
        context=context_provider,  # type: ignore[arg-type]
    )

    with patch("bookcard.api.deps.PermissionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.check_permission.return_value = None  # Permission granted
        mock_service_class.return_value = mock_service

        # Should not raise, but callable context resolves to None
        permission_checker(user, session)  # type: ignore[arg-type]

        # Callable context is not supported, so resolved_context should be None
        mock_service.check_permission.assert_called_once_with(
            user, "books", "read", None
        )


def test_require_permission_denied() -> None:
    """Test require_permission raises HTTPException when permission denied."""
    session = DummySession()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )

    permission_checker = require_permission("books", "write")

    with patch("bookcard.api.deps.PermissionService") as mock_service_class:
        mock_service = MagicMock()
        mock_service.check_permission.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission_denied: books:write",
        )
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            permission_checker(user, session)  # type: ignore[arg-type]
        exc = exc_info.value
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert "permission_denied" in exc.detail


# ============================================================================
# Tests for get_opds_user
# ============================================================================


@pytest.fixture
def mock_request_with_config() -> MagicMock:
    """Create a mock request with app state config.

    Returns
    -------
    MagicMock
        Mock request object with app.state.config set.
    """
    request = MagicMock(spec=Request)
    request.app.state.config = AppConfig(
        jwt_secret="test-secret",
        jwt_algorithm="HS256",
        jwt_expires_minutes=15,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    return request


@pytest.fixture
def test_user() -> User:
    """Create a test user.

    Returns
    -------
    User
        Test user instance.
    """
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


@pytest.mark.parametrize(
    ("auth_result", "expected_result"),
    [
        (None, None),
        (
            User(id=1, username="user", email="user@example.com", password_hash="hash"),
            User(id=1, username="user", email="user@example.com", password_hash="hash"),
        ),
    ],
)
def test_get_opds_user(
    mock_request_with_config: MagicMock,
    auth_result: User | None,
    expected_result: User | None,
) -> None:
    """Test get_opds_user with different authentication results.

    Parameters
    ----------
    mock_request_with_config : MagicMock
        Mock request with config.
    auth_result : User | None
        Result from auth service.
    expected_result : User | None
        Expected return value.
    """
    session = DummySession()
    with (
        patch("bookcard.api.deps.UserRepository") as mock_repo_class,
        patch("bookcard.api.deps.PasswordHasher") as mock_hasher_class,
        patch("bookcard.api.deps.JWTManager") as mock_jwt_class,
        patch("bookcard.api.deps.OpdsAuthService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_hasher = MagicMock()
        mock_hasher_class.return_value = mock_hasher
        mock_jwt = MagicMock()
        mock_jwt_class.return_value = mock_jwt
        mock_service = MagicMock()
        mock_service.authenticate_request.return_value = auth_result
        mock_service_class.return_value = mock_service

        result = get_opds_user(
            mock_request_with_config,
            session,  # type: ignore[arg-type]
        )

        if expected_result is None:
            assert result is None
        else:
            assert result is not None
            assert result.id == expected_result.id
            assert result.username == expected_result.username
            assert result.email == expected_result.email
        mock_service_class.assert_called_once_with(
            session=session,
            user_repo=mock_repo,
            hasher=mock_hasher,
            jwt_manager=mock_jwt,
        )
        mock_service.authenticate_request.assert_called_once_with(
            mock_request_with_config
        )


# ============================================================================
# Tests for get_kobo_auth_token
# ============================================================================


@pytest.fixture
def mock_request_with_url() -> MagicMock:
    """Create a mock request with URL path.

    Returns
    -------
    MagicMock
        Mock request object with url.path attribute.
    """
    return MagicMock(spec=Request)


@pytest.mark.parametrize(
    ("path", "expected_token"),
    [
        ("/kobo/token123/v1/books", "token123"),
        ("/kobo/abc123def456/v1/library", "abc123def456"),
        ("/kobo/test-token/v1/", "test-token"),
    ],
)
def test_get_kobo_auth_token_success(
    mock_request_with_url: MagicMock, path: str, expected_token: str
) -> None:
    """Test successful get_kobo_auth_token extraction.

    Parameters
    ----------
    mock_request_with_url : MagicMock
        Mock request object.
    path : str
        URL path to test.
    expected_token : str
        Expected token to be extracted.
    """
    mock_request_with_url.url.path = path
    result = get_kobo_auth_token(mock_request_with_url)
    assert result == expected_token


@pytest.mark.parametrize(
    ("path", "expected_detail"),
    [
        ("/invalid/path", "kobo_path_invalid"),
        ("/notkobo/token/v1", "kobo_path_invalid"),
        ("/kobo", "kobo_path_invalid"),
        ("/", "kobo_path_invalid"),
    ],
)
def test_get_kobo_auth_token_invalid_path(
    mock_request_with_url: MagicMock, path: str, expected_detail: str
) -> None:
    """Test get_kobo_auth_token with invalid path.

    Parameters
    ----------
    mock_request_with_url : MagicMock
        Mock request object.
    path : str
        Invalid URL path.
    expected_detail : str
        Expected error detail.
    """
    mock_request_with_url.url.path = path
    with pytest.raises(HTTPException) as exc_info:
        get_kobo_auth_token(mock_request_with_url)
    exc = exc_info.value
    assert isinstance(exc, HTTPException)
    assert exc.status_code == status.HTTP_404_NOT_FOUND
    assert exc.detail == expected_detail


# ============================================================================
# Tests for get_kobo_user
# ============================================================================


@pytest.mark.parametrize(
    ("auth_token", "validate_result", "expected_user", "should_raise"),
    [
        (
            "valid_token",
            User(id=1, username="user", email="user@example.com", password_hash="hash"),
            User(id=1, username="user", email="user@example.com", password_hash="hash"),
            False,
        ),
        ("invalid_token", None, None, True),
    ],
)
def test_get_kobo_user(
    auth_token: str,
    validate_result: User | None,
    expected_user: User | None,
    should_raise: bool,
) -> None:
    """Test get_kobo_user with different validation results.

    Parameters
    ----------
    auth_token : str
        Auth token to validate.
    validate_result : User | None
        Result from auth service validation.
    expected_user : User | None
        Expected user if successful.
    should_raise : bool
        Whether an exception should be raised.
    """
    session = DummySession()
    with (
        patch("bookcard.api.deps.KoboAuthTokenRepository") as mock_token_repo_class,
        patch("bookcard.api.deps.UserRepository") as mock_user_repo_class,
        patch("bookcard.api.deps.KoboAuthService") as mock_service_class,
    ):
        mock_token_repo = MagicMock()
        mock_token_repo_class.return_value = mock_token_repo
        mock_user_repo = MagicMock()
        mock_user_repo_class.return_value = mock_user_repo
        mock_service = MagicMock()
        mock_service.validate_auth_token.return_value = validate_result
        mock_service_class.return_value = mock_service

        if should_raise:
            with pytest.raises(HTTPException) as exc_info:
                get_kobo_user(auth_token, session)  # type: ignore[arg-type]
            exc = exc_info.value
            assert isinstance(exc, HTTPException)
            assert exc.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc.detail == "kobo_auth_invalid"
        else:
            result = get_kobo_user(auth_token, session)  # type: ignore[arg-type]
            assert result is not None
            assert expected_user is not None
            assert result.id == expected_user.id
            assert result.username == expected_user.username
            assert result.email == expected_user.email

        mock_service_class.assert_called_once_with(
            session=session,
            auth_token_repo=mock_token_repo,
            user_repo=mock_user_repo,
        )
        mock_service.validate_auth_token.assert_called_once_with(auth_token)
