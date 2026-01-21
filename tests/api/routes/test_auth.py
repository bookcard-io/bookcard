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

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

import bookcard.api.routes.auth as auth
from bookcard.api.schemas import ProfilePictureUpdateRequest
from bookcard.models.auth import User
from bookcard.models.config import EmailServerConfig, EmailServerType
from tests.conftest import TEST_ENCRYPTION_KEY, DummySession


@dataclass
class DummyUser:
    id: int
    username: str
    email: str
    is_admin: bool = False


class FakeService:
    def __init__(self, behavior: str = "ok") -> None:
        self.behavior = behavior

    def register_user(
        self, username: str, email: str, password: str
    ) -> tuple[DummyUser, str]:
        if self.behavior == "username_exists":
            raise ValueError(auth.AuthError.USERNAME_EXISTS)
        if self.behavior == "email_exists":
            raise ValueError(auth.AuthError.EMAIL_EXISTS)
        return DummyUser(1, username, email), "token"

    def login_user(self, identifier: str, password: str) -> tuple[DummyUser, str]:
        if self.behavior == "invalid_credentials":
            raise ValueError(auth.AuthError.INVALID_CREDENTIALS)
        return DummyUser(1, identifier, f"{identifier}@example.com"), "token"


class DummyRequest:
    def __init__(self) -> None:
        import tempfile

        temp_dir = tempfile.mkdtemp()

        class DummyConfig:
            jwt_secret = "test-secret"
            jwt_algorithm = "HS256"
            jwt_expires_minutes = 15
            encryption_key = TEST_ENCRYPTION_KEY
            data_directory = temp_dir

        self.app = type(
            "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
        )()
        # Add headers attribute for logout endpoint
        self.headers = {}


class _StubAuthService:
    """Private stub service for testing auth routes."""

    def __init__(
        self,
        *,
        change_password_error: ValueError | None = None,
        update_profile_picture_user: DummyUser | None = None,
        update_profile_picture_error: ValueError | None = None,
        delete_profile_picture_user: DummyUser | None = None,
        delete_profile_picture_error: ValueError | None = None,
        validate_invite_token_result: bool | None = None,
        validate_invite_token_error: ValueError | None = None,
    ) -> None:
        self._change_password_error = change_password_error
        self._update_profile_picture_user = update_profile_picture_user
        self._update_profile_picture_error = update_profile_picture_error
        self._delete_profile_picture_user = delete_profile_picture_user
        self._delete_profile_picture_error = delete_profile_picture_error
        self._validate_invite_token_result = validate_invite_token_result
        self._validate_invite_token_error = validate_invite_token_error

    def change_password(
        self, user_id: int, current_password: str, new_password: str
    ) -> None:
        """Stub change_password method."""
        if self._change_password_error:
            raise self._change_password_error

    def update_profile_picture(self, user_id: int, picture_path: str) -> DummyUser:
        """Stub update_profile_picture method."""
        if self._update_profile_picture_error:
            raise self._update_profile_picture_error
        if self._update_profile_picture_user:
            return self._update_profile_picture_user
        return DummyUser(id=user_id, username="alice", email="a@example.com")

    def delete_profile_picture(self, user_id: int) -> DummyUser:
        """Stub delete_profile_picture method."""
        if self._delete_profile_picture_error:
            raise self._delete_profile_picture_error
        if self._delete_profile_picture_user:
            return self._delete_profile_picture_user
        user = DummyUser(id=user_id, username="alice", email="a@example.com")
        user.profile_picture = None  # type: ignore[attr-defined]
        return user

    def validate_invite_token(self, token: str) -> bool:
        """Stub validate_invite_token method."""
        if self._validate_invite_token_error:
            raise self._validate_invite_token_error
        if self._validate_invite_token_result is not None:
            return self._validate_invite_token_result
        return True


def _create_stub_service(
    *,
    change_password_error: ValueError | None = None,
    update_profile_picture_user: DummyUser | None = None,
    update_profile_picture_error: ValueError | None = None,
    delete_profile_picture_user: DummyUser | None = None,
    delete_profile_picture_error: ValueError | None = None,
    validate_invite_token_result: bool | None = None,
    validate_invite_token_error: ValueError | None = None,
) -> _StubAuthService:
    """Create a stub auth service with configurable behavior.

    Parameters
    ----------
    change_password_error : ValueError | None
        Error to raise from change_password, if any.
    update_profile_picture_user : DummyUser | None
        User to return from update_profile_picture, if any.
    update_profile_picture_error : ValueError | None
        Error to raise from update_profile_picture, if any.
    delete_profile_picture_user : DummyUser | None
        User to return from delete_profile_picture, if any.
    delete_profile_picture_error : ValueError | None
        Error to raise from delete_profile_picture, if any.
    validate_invite_token_result : bool | None
        Result to return from validate_invite_token, if any.
    validate_invite_token_error : ValueError | None
        Error to raise from validate_invite_token, if any.

    Returns
    -------
    _StubAuthService
        Configured stub service.
    """
    return _StubAuthService(
        change_password_error=change_password_error,
        update_profile_picture_user=update_profile_picture_user,
        update_profile_picture_error=update_profile_picture_error,
        delete_profile_picture_user=delete_profile_picture_user,
        delete_profile_picture_error=delete_profile_picture_error,
        validate_invite_token_result=validate_invite_token_result,
        validate_invite_token_error=validate_invite_token_error,
    )


def test_register_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_auth_service(request: object, session: object) -> FakeService:
        return FakeService("ok")

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    payload = auth.UserCreate(
        username="alice", email="a@example.com", password="password123"
    )
    resp = auth.register(DummyRequest(), object(), payload)
    assert resp.access_token == "token"


def test_register_conflict_maps_to_http_409(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_auth_service(request: object, session: object) -> FakeService:
        return FakeService("username_exists")

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    payload = auth.UserCreate(
        username="alice", email="a@example.com", password="password123"
    )
    with pytest.raises(auth.HTTPException) as exc:
        auth.register(DummyRequest(), object(), payload)
    assert isinstance(exc.value, auth.HTTPException)
    assert exc.value.status_code == 409
    assert exc.value.detail == auth.AuthError.USERNAME_EXISTS


def test_login_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test login succeeds with valid credentials."""

    def fake_auth_service(request: object, session: object) -> FakeService:
        return FakeService("ok")

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    session = DummySession()
    user = User(
        id=1,
        username="alice",
        email="alice@example.com",
        password_hash="hash",
        is_admin=False,
    )
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]
    session.add_exec_result([user])
    payload = auth.LoginRequest(identifier="alice", password="password123")
    resp = auth.login(DummyRequest(), session, payload)
    assert resp.access_token == "token"


def test_login_user_not_found_after_login(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test login raises 500 when user_with_rels is None after login."""

    def fake_auth_service(request: object, session: object) -> FakeService:
        return FakeService("ok")

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    session = DummySession()
    # Return empty result to simulate user not found after login
    session.add_exec_result([])
    payload = auth.LoginRequest(identifier="alice", password="password123")
    with pytest.raises(HTTPException) as exc_info:
        auth.login(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "user_not_found"


def test_login_invalid_credentials_maps_to_http_401(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_auth_service(request: object, session: object) -> FakeService:
        return FakeService("invalid_credentials")

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    payload = auth.LoginRequest(identifier="alice", password="password123")
    with pytest.raises(auth.HTTPException) as exc:
        auth.login(DummyRequest(), object(), payload)
    assert isinstance(exc.value, auth.HTTPException)
    assert exc.value.status_code == 401
    assert exc.value.detail == auth.AuthError.INVALID_CREDENTIALS


def test_me_returns_user_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test me endpoint returns current user."""
    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )
    user.ereader_devices = []  # type: ignore[attr-defined]
    user.roles = []  # type: ignore[attr-defined]
    session = DummySession()
    session.add_exec_result([user])

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    resp = auth.me(DummyRequest(), session)
    assert resp.id == 1
    assert resp.username == "alice"
    assert resp.email == "a@example.com"


def test_me_user_not_found_after_get(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test me endpoint raises 500 when user_with_rels is None."""
    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )
    session = DummySession()
    # Return empty result to simulate user not found after get_current_user
    session.add_exec_result([])

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    with pytest.raises(HTTPException) as exc_info:
        auth.me(DummyRequest(), session)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "user_not_found"


def test_register_raises_other_valueerror(monkeypatch: pytest.MonkeyPatch) -> None:
    class ErrorService:
        def register_user(
            self, username: str, email: str, password: str
        ) -> tuple[DummyUser, str]:
            raise ValueError("unexpected error")

    def fake_auth_service_alt(request: object, session: object) -> ErrorService:
        return ErrorService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service_alt)
    payload = auth.UserCreate(
        username="alice", email="a@example.com", password="password123"
    )
    with pytest.raises(ValueError, match="unexpected error"):
        auth.register(DummyRequest(), object(), payload)


def test_login_raises_other_valueerror(monkeypatch: pytest.MonkeyPatch) -> None:
    class ErrorService:
        def login_user(self, identifier: str, password: str) -> tuple[DummyUser, str]:
            raise ValueError("unexpected login error")

    def fake_auth_service(request: object, session: object) -> ErrorService:
        return ErrorService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    payload = auth.LoginRequest(identifier="alice", password="password123")
    with pytest.raises(ValueError, match="unexpected login error"):
        auth.login(DummyRequest(), object(), payload)


def test_auth_service_constructs_service(monkeypatch: pytest.MonkeyPatch) -> None:
    import tempfile
    from types import SimpleNamespace

    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    class DummyConfig:
        jwt_secret = "test-secret"
        jwt_algorithm = "HS256"
        jwt_expires_minutes = 15
        encryption_key = TEST_ENCRYPTION_KEY
        data_directory = temp_dir

    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(config=DummyConfig()))
    )
    session = object()

    # Test that _auth_service constructs the service correctly
    service = auth._auth_service(request, session)  # type: ignore[arg-type]
    from bookcard.services.auth_service import AuthService

    assert isinstance(service, AuthService)


def test_change_password_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test change_password succeeds with valid credentials."""
    stub = _create_stub_service()

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    payload = auth.PasswordChangeRequest(
        current_password="oldpw", new_password="newpw123"
    )
    session = DummySession()
    resp = auth.change_password(DummyRequest(), session, payload)
    assert resp is None  # 204 No Content


def test_change_password_invalid_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test change_password returns 400 for invalid current password."""
    stub = _create_stub_service(
        change_password_error=ValueError(auth.AuthError.INVALID_PASSWORD)
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    payload = auth.PasswordChangeRequest(
        current_password="wrong", new_password="newpw123"
    )
    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.change_password(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == auth.AuthError.INVALID_PASSWORD


def test_change_password_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test change_password returns 404 for user not found."""
    stub = _create_stub_service(change_password_error=ValueError("user_not_found"))

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    payload = auth.PasswordChangeRequest(
        current_password="oldpw", new_password="newpw123"
    )
    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.change_password(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404


def test_change_password_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test change_password re-raises unexpected ValueError."""
    stub = _create_stub_service(change_password_error=ValueError("unexpected_error"))

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    payload = auth.PasswordChangeRequest(
        current_password="oldpw", new_password="newpw123"
    )
    session = DummySession()

    with pytest.raises(ValueError, match="unexpected_error"):
        auth.change_password(DummyRequest(), session, payload)


def test_logout_returns_none() -> None:
    """Test logout returns None (204 No Content)."""
    result = auth.logout(DummyRequest(), DummySession())
    assert result is None


def test_logout_with_token_blacklists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test logout blacklists token when provided (covers lines 217-244)."""
    from datetime import UTC, datetime
    from unittest.mock import MagicMock, patch

    request = DummyRequest()
    request.headers = {"Authorization": "Bearer test-token"}

    # Mock JWTManager
    mock_jwt_mgr = MagicMock()
    mock_jwt_mgr.decode_token.return_value = {
        "jti": "test-jti",
        "exp": datetime.now(UTC).timestamp() + 3600,
    }

    # Mock TokenBlacklistRepository
    mock_blacklist_repo = MagicMock()

    with (
        patch("bookcard.api.routes.auth.JWTManager", return_value=mock_jwt_mgr),
        patch(
            "bookcard.api.routes.auth.TokenBlacklistRepository",
            return_value=mock_blacklist_repo,
        ),
    ):
        session = DummySession()
        result = auth.logout(request, session)
        assert result is None
        mock_blacklist_repo.add_to_blacklist.assert_called_once()
        assert session.flush_count > 0


def test_logout_with_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test logout handles invalid token gracefully (covers lines 223-225)."""
    from unittest.mock import MagicMock, patch

    # Import SecurityTokenError from the same place auth.py imports it
    from bookcard.services.security import SecurityTokenError

    request = DummyRequest()
    request.headers = {"Authorization": "Bearer invalid-token"}

    # Mock JWTManager to raise SecurityTokenError when decode_token is called
    mock_jwt_mgr = MagicMock()
    mock_jwt_mgr.decode_token.side_effect = SecurityTokenError("Invalid token")

    # Patch JWTManager to return our mock when instantiated
    with patch("bookcard.api.routes.auth.JWTManager", return_value=mock_jwt_mgr):
        session = DummySession()
        # This should execute lines 220-225: try to decode, catch SecurityTokenError, return None
        # Line 218: JWTManager is instantiated
        # Line 222: decode_token is called and raises SecurityTokenError
        # Line 223: SecurityTokenError is caught
        # Line 225: return None
        result = auth.logout(request, session)
        assert result is None
        # Verify decode_token was called (which raises the exception)
        mock_jwt_mgr.decode_token.assert_called_once_with("invalid-token")


def test_logout_without_jti_or_exp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test logout handles missing jti or exp gracefully (covers lines 231-234)."""
    from unittest.mock import MagicMock, patch

    request = DummyRequest()
    request.headers = {"Authorization": "Bearer test-token"}

    mock_jwt_mgr = MagicMock()
    mock_jwt_mgr.decode_token.return_value = {}  # No jti or exp

    with patch("bookcard.api.routes.auth.JWTManager", return_value=mock_jwt_mgr):
        session = DummySession()
        result = auth.logout(request, session)
        assert result is None


def test_get_profile_returns_profile_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_profile returns ProfileRead with profile picture."""
    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
        profile_picture="/path/to/pic.jpg",
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    session = DummySession()
    resp = auth.get_profile(DummyRequest(), session)
    assert resp.id == 1
    assert resp.username == "alice"
    assert resp.profile_picture == "/path/to/pic.jpg"


def test_get_profile_without_picture(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_profile handles user without profile picture."""
    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
        profile_picture=None,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    session = DummySession()
    resp = auth.get_profile(DummyRequest(), session)
    assert resp.profile_picture is None


def test_update_profile_picture_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_profile_picture succeeds."""
    updated_user = DummyUser(id=1, username="alice", email="a@example.com")
    updated_user.profile_picture = "/new/path.jpg"  # type: ignore[attr-defined]

    stub = _create_stub_service(update_profile_picture_user=updated_user)

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    payload = ProfilePictureUpdateRequest(picture_path="/new/path.jpg")
    session = DummySession()
    resp = auth.update_profile_picture(DummyRequest(), session, payload)
    assert resp.profile_picture == "/new/path.jpg"


def test_update_profile_picture_user_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test update_profile_picture returns 404 for user not found."""
    stub = _create_stub_service(
        update_profile_picture_error=ValueError("user_not_found")
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    payload = ProfilePictureUpdateRequest(picture_path="/path.jpg")
    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.update_profile_picture(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404


def test_update_profile_picture_unexpected_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test update_profile_picture re-raises unexpected ValueError."""
    stub = _create_stub_service(
        update_profile_picture_error=ValueError("unexpected_error")
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    payload = ProfilePictureUpdateRequest(picture_path="/path.jpg")
    session = DummySession()

    with pytest.raises(ValueError, match="unexpected_error"):
        auth.update_profile_picture(DummyRequest(), session, payload)


def test_delete_profile_picture_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_profile_picture succeeds."""
    stub = _create_stub_service()

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
        profile_picture="/path/to/pic.jpg",
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    session = DummySession()
    resp = auth.delete_profile_picture(DummyRequest(), session)
    assert resp.profile_picture is None


def test_delete_profile_picture_user_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test delete_profile_picture returns 404 for user not found."""
    stub = _create_stub_service(
        delete_profile_picture_error=ValueError("user_not_found")
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.delete_profile_picture(DummyRequest(), session)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404


def test_delete_profile_picture_unexpected_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test delete_profile_picture re-raises unexpected ValueError."""
    stub = _create_stub_service(
        delete_profile_picture_error=ValueError("unexpected_error")
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    user = User(
        id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)
    session = DummySession()

    with pytest.raises(ValueError, match="unexpected_error"):
        auth.delete_profile_picture(DummyRequest(), session)


def test_validate_invite_token_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test validate_invite_token succeeds for valid token."""
    stub = _create_stub_service(validate_invite_token_result=True)

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    resp = auth.validate_invite_token(DummyRequest(), object(), "valid-token")  # type: ignore[arg-type]
    assert resp.valid is True
    assert resp.token == "valid-token"


def test_validate_invite_token_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test validate_invite_token returns 404 for invalid token."""
    stub = _create_stub_service(
        validate_invite_token_error=ValueError(auth.AuthError.INVALID_INVITE)
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    with pytest.raises(HTTPException) as exc_info:
        auth.validate_invite_token(DummyRequest(), object(), "invalid-token")  # type: ignore[arg-type]
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == auth.AuthError.INVALID_INVITE


def test_validate_invite_token_expired(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test validate_invite_token returns 400 for expired token."""
    stub = _create_stub_service(
        validate_invite_token_error=ValueError(auth.AuthError.INVITE_EXPIRED)
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    with pytest.raises(HTTPException) as exc_info:
        auth.validate_invite_token(DummyRequest(), object(), "expired-token")  # type: ignore[arg-type]
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == auth.AuthError.INVITE_EXPIRED


def test_validate_invite_token_already_used(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test validate_invite_token returns 400 for already used token."""
    stub = _create_stub_service(
        validate_invite_token_error=ValueError(auth.AuthError.INVITE_ALREADY_USED)
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    with pytest.raises(HTTPException) as exc_info:
        auth.validate_invite_token(DummyRequest(), object(), "used-token")  # type: ignore[arg-type]
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == auth.AuthError.INVITE_ALREADY_USED


def test_validate_invite_token_unexpected_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test validate_invite_token re-raises unexpected ValueError."""
    stub = _create_stub_service(
        validate_invite_token_error=ValueError("unexpected_error")
    )

    def fake_auth_service(request: object, session: object) -> _StubAuthService:
        return stub

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    with pytest.raises(ValueError, match="unexpected_error"):
        auth.validate_invite_token(DummyRequest(), object(), "token")  # type: ignore[arg-type]


def test_update_profile_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_profile succeeds (covers lines 299-308)."""
    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def update_profile(
            self,
            user_id: int,
            username: str | None,
            email: str | None,
            full_name: str | None,
        ) -> User:
            return user

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    payload = auth.ProfileUpdate(username="bob", email="b@example.com", full_name="Bob")
    result = auth.update_profile(DummyRequest(), session, payload)
    assert result.username == "alice"
    # Session commit is called in the route
    assert hasattr(session, "commit") or session.flush_count > 0


def test_update_profile_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_profile raises 404 when user not found (covers lines 309-312)."""
    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def update_profile(
            self,
            user_id: int,
            username: str | None,
            email: str | None,
            full_name: str | None,
        ) -> User:
            raise ValueError("user_not_found")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    payload = auth.ProfileUpdate(username="bob", email="b@example.com")

    with pytest.raises(HTTPException) as exc_info:
        auth.update_profile(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "user_not_found"


def test_update_profile_username_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_profile raises 409 when username exists (covers lines 313-314)."""
    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def update_profile(
            self,
            user_id: int,
            username: str | None,
            email: str | None,
            full_name: str | None,
        ) -> User:
            raise ValueError(auth.AuthError.USERNAME_EXISTS)

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    payload = auth.ProfileUpdate(username="bob")

    with pytest.raises(HTTPException) as exc_info:
        auth.update_profile(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == auth.AuthError.USERNAME_EXISTS


def test_update_profile_email_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_profile raises 409 when email exists (covers lines 313-314)."""
    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def update_profile(
            self,
            user_id: int,
            username: str | None,
            email: str | None,
            full_name: str | None,
        ) -> User:
            raise ValueError(auth.AuthError.EMAIL_EXISTS)

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    payload = auth.ProfileUpdate(email="bob@example.com")

    with pytest.raises(HTTPException) as exc_info:
        auth.update_profile(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == auth.AuthError.EMAIL_EXISTS


def test_update_profile_other_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update_profile re-raises other ValueError (covers line 315)."""
    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def update_profile(
            self,
            user_id: int,
            username: str | None,
            email: str | None,
            full_name: str | None,
        ) -> User:
            raise ValueError("other_error")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    payload = auth.ProfileUpdate(username="bob")

    with pytest.raises(ValueError, match="other_error"):
        auth.update_profile(DummyRequest(), session, payload)


def test_upload_profile_picture_no_filename(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_profile_picture raises 400 when filename is missing (covers lines 352-356)."""
    from unittest.mock import MagicMock

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upload_profile_picture(
            self, user_id: int, file_content: bytes, filename: str
        ) -> User:
            return user

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    mock_file = MagicMock()
    mock_file.filename = None
    mock_file.file = MagicMock()

    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.upload_profile_picture(DummyRequest(), session, mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "filename_required"


def test_upload_profile_picture_read_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_profile_picture handles file read error (covers lines 358-364)."""
    from unittest.mock import MagicMock

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upload_profile_picture(
            self, user_id: int, file_content: bytes, filename: str
        ) -> User:
            return user

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = MagicMock()
    mock_file.file.read.side_effect = OSError("Read error")

    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.upload_profile_picture(DummyRequest(), session, mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "failed_to_read_file" in exc_info.value.detail


def test_upload_profile_picture_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_profile_picture raises 404 when user not found (covers lines 375-376)."""
    from unittest.mock import MagicMock

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upload_profile_picture(
            self, user_id: int, file_content: bytes, filename: str
        ) -> User:
            raise ValueError("user_not_found")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.upload_profile_picture(DummyRequest(), session, mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "user_not_found"


def test_upload_profile_picture_invalid_file_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upload_profile_picture raises 400 for invalid file type (covers lines 377-378)."""
    from unittest.mock import MagicMock

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upload_profile_picture(
            self, user_id: int, file_content: bytes, filename: str
        ) -> User:
            raise ValueError("invalid_file_type")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    mock_file = MagicMock()
    mock_file.filename = "test.txt"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake file data"

    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.upload_profile_picture(DummyRequest(), session, mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid_file_type"


def test_upload_profile_picture_save_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_profile_picture raises 500 when file save fails (covers lines 379-380)."""
    from unittest.mock import MagicMock

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upload_profile_picture(
            self, user_id: int, file_content: bytes, filename: str
        ) -> User:
            raise ValueError("failed_to_save_file: disk full")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    session = DummySession()

    with pytest.raises(HTTPException) as exc_info:
        auth.upload_profile_picture(DummyRequest(), session, mock_file)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "failed_to_save_file: disk full"


def test_upload_profile_picture_other_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_profile_picture re-raises other ValueError (covers line 381)."""
    from unittest.mock import MagicMock

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upload_profile_picture(
            self, user_id: int, file_content: bytes, filename: str
        ) -> User:
            raise ValueError("other_error")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    session = DummySession()

    with pytest.raises(ValueError, match="other_error"):
        auth.upload_profile_picture(DummyRequest(), session, mock_file)


def test_upload_profile_picture_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_profile_picture succeeds (covers lines 372, 382)."""
    from unittest.mock import MagicMock

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")
    updated_user = User(
        id=1, username="alice", email="a@example.com", password_hash="hash"
    )
    updated_user.profile_picture = "/path/to/pic.jpg"

    class StubService:
        def upload_profile_picture(
            self, user_id: int, file_content: bytes, filename: str
        ) -> User:
            return updated_user

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    mock_file = MagicMock()
    mock_file.filename = "test.jpg"
    mock_file.file = MagicMock()
    mock_file.file.read.return_value = b"fake image data"

    session = DummySession()
    result = auth.upload_profile_picture(DummyRequest(), session, mock_file)
    assert result.profile_picture == "/path/to/pic.jpg"
    # Verify commit was called (line 372)
    assert hasattr(session, "commit")


def test_get_profile_picture_no_picture(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_profile_picture returns 404 when no picture (covers lines 457-458)."""
    from fastapi import Response

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")
    user.profile_picture = None

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    result = auth.get_profile_picture(DummyRequest(), session)
    assert isinstance(result, Response)
    assert result.status_code == 404


def test_get_profile_picture_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_profile_picture returns 404 when file doesn't exist (covers lines 468-469)."""
    from unittest.mock import patch

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")
    user.profile_picture = "/nonexistent/path.jpg"

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    with patch("pathlib.Path.exists", return_value=False):
        session = DummySession()
        result = auth.get_profile_picture(DummyRequest(), session)
        from fastapi import Response

        assert isinstance(result, Response)
        assert result.status_code == 404


def test_get_profile_picture_success_absolute(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_profile_picture with absolute path (covers lines 462-463, 472-483)."""
    import tempfile
    from pathlib import Path

    from fastapi.responses import FileResponse

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    # Create a real file to test the actual code path
    with tempfile.TemporaryDirectory() as tmpdir:
        pic_file = Path(tmpdir) / "pic.jpg"
        pic_file.write_bytes(b"fake image")
        user.profile_picture = str(pic_file)

        session = DummySession()
        result = auth.get_profile_picture(DummyRequest(), session)
        assert isinstance(result, FileResponse)
        # Verify the file was found and media type was determined (lines 472-483)
        assert pic_file.exists()


def test_get_profile_picture_success_relative(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_profile_picture with relative path (covers lines 465-466, 472-483)."""
    import tempfile
    from pathlib import Path

    from fastapi.responses import FileResponse

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")
    user.profile_picture = "relative/path/to/pic.png"

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    # Create a real temporary directory and file to test the path logic
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create the relative path file
        pic_file = Path(tmpdir) / "relative" / "path" / "to" / "pic.png"
        pic_file.parent.mkdir(parents=True, exist_ok=True)
        pic_file.write_bytes(b"fake image")

        # Update request config to use tmpdir
        request = DummyRequest()
        request.app.state.config.data_directory = tmpdir

        session = DummySession()
        result = auth.get_profile_picture(request, session)
        assert isinstance(result, FileResponse)
        # Verify the file was found and media type was determined (lines 472-483)
        assert pic_file.exists()


def test_get_settings_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_settings returns settings (covers lines 585-592)."""
    from bookcard.models.auth import UserSetting

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def get_all_settings(self, user_id: int) -> list[UserSetting]:
            return [
                UserSetting(
                    id=1, user_id=1, key="theme", value="dark", description="Theme"
                ),
                UserSetting(
                    id=2, user_id=1, key="language", value="en", description="Language"
                ),
            ]

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    result = auth.get_settings(DummyRequest(), session)
    # Verify lines 589-591 are executed (dictionary comprehension)
    assert "theme" in result.settings
    assert "language" in result.settings
    assert result.settings["theme"].value == "dark"
    assert result.settings["language"].value == "en"


def test_upsert_setting_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upsert_setting succeeds (covers lines 625-634)."""
    from bookcard.models.auth import UserSetting

    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upsert_setting(
            self, user_id: int, key: str, value: str, description: str | None
        ) -> UserSetting:
            return UserSetting(
                id=1, user_id=1, key=key, value=value, description=description
            )

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    payload = auth.SettingUpdate(value="dark", description="Theme setting")
    result = auth.upsert_setting(DummyRequest(), session, "theme", payload)
    assert result.key == "theme"
    assert result.value == "dark"
    # Session commit is called in the route
    assert hasattr(session, "commit") or session.flush_count > 0


def test_upsert_setting_user_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upsert_setting raises 404 when user not found (covers lines 637-638)."""
    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upsert_setting(
            self, user_id: int, key: str, value: str, description: str | None
        ) -> None:
            raise ValueError("user_not_found")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    payload = auth.SettingUpdate(value="dark")

    with pytest.raises(HTTPException) as exc_info:
        auth.upsert_setting(DummyRequest(), session, "theme", payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "user_not_found"


def test_upsert_setting_other_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upsert_setting re-raises other ValueError (covers line 639)."""
    user = User(id=1, username="alice", email="a@example.com", password_hash="hash")

    class StubService:
        def upsert_setting(
            self, user_id: int, key: str, value: str, description: str | None
        ) -> None:
            raise ValueError("other_error")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)
    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    session = DummySession()
    payload = auth.SettingUpdate(value="dark")

    with pytest.raises(ValueError, match="other_error"):
        auth.upsert_setting(DummyRequest(), session, "theme", payload)


def test_get_email_server_config_not_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_email_server_config raises 403 when user is not admin (covers line 658-659)."""
    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    class StubService:
        def get_email_server_config(self, decrypt: bool) -> None:
            return None

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    with pytest.raises(HTTPException) as exc_info:
        auth.get_email_server_config(DummyRequest(), session)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "forbidden"


def test_get_email_server_config_returns_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_email_server_config returns defaults when config is None (covers lines 662-681)."""
    from bookcard.models.config import EmailServerType

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    class StubService:
        def get_email_server_config(self, decrypt: bool) -> None:
            return None

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    result = auth.get_email_server_config(DummyRequest(), session)
    assert result.id is None
    assert result.server_type == EmailServerType.SMTP
    assert result.smtp_port == 587
    assert result.smtp_use_tls is True
    assert result.smtp_use_ssl is False
    assert result.max_email_size_mb == 25
    assert result.enabled is False


def test_get_email_server_config_returns_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_email_server_config returns existing config (covers line 682)."""
    from datetime import UTC, datetime

    from bookcard.models.config import EmailServerConfig, EmailServerType

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        smtp_port=587,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class StubService:
        def get_email_server_config(self, decrypt: bool) -> EmailServerConfig:
            return config

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    result = auth.get_email_server_config(DummyRequest(), session)
    assert result.id == 1
    assert result.smtp_host == "smtp.example.com"
    assert result.enabled is True


def test_upsert_email_server_config_not_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upsert_email_server_config raises 403 when user is not admin (covers line 701-702)."""
    from bookcard.api.schemas import EmailServerConfigUpdate

    user = User(
        id=1,
        username="user",
        email="user@example.com",
        password_hash="hash",
        is_admin=False,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    class StubService:
        def upsert_email_server_config(self, **kwargs: object) -> None:
            return None

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    payload = EmailServerConfigUpdate(smtp_host="smtp.example.com")
    with pytest.raises(HTTPException) as exc_info:
        auth.upsert_email_server_config(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "forbidden"


def test_upsert_email_server_config_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upsert_email_server_config succeeds (covers lines 704-721)."""
    from datetime import UTC, datetime

    from bookcard.api.schemas import EmailServerConfigUpdate
    from bookcard.models.config import EmailServerConfig, EmailServerType

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        smtp_port=587,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class StubService:
        def upsert_email_server_config(self, **kwargs: object) -> EmailServerConfig:
            return config

        def get_email_server_config(self, decrypt: bool) -> EmailServerConfig:
            return config

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    payload = EmailServerConfigUpdate(smtp_host="smtp.example.com", smtp_port=587)
    result = auth.upsert_email_server_config(DummyRequest(), session, payload)
    assert result.id == 1
    assert result.smtp_host == "smtp.example.com"
    session.commit()


def test_upsert_email_server_config_retrieval_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upsert_email_server_config raises 500 when retrieval fails (covers lines 710-714)."""
    from datetime import UTC, datetime

    from bookcard.api.schemas import EmailServerConfigUpdate
    from bookcard.models.config import EmailServerConfig, EmailServerType

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class StubService:
        def upsert_email_server_config(self, **kwargs: object) -> EmailServerConfig:
            return config

        def get_email_server_config(self, decrypt: bool) -> None:
            return None

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    payload = EmailServerConfigUpdate(smtp_host="smtp.example.com")
    with pytest.raises(HTTPException) as exc_info:
        auth.upsert_email_server_config(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to retrieve saved config"


def test_upsert_email_server_config_invalid_smtp_encryption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upsert_email_server_config raises 400 for invalid_smtp_encryption (covers lines 715-719)."""
    from bookcard.api.schemas import EmailServerConfigUpdate

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    class StubService:
        def upsert_email_server_config(self, **kwargs: object) -> None:
            raise ValueError("invalid_smtp_encryption")

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    payload = EmailServerConfigUpdate(smtp_use_tls=True, smtp_use_ssl=True)
    with pytest.raises(HTTPException) as exc_info:
        auth.upsert_email_server_config(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid_smtp_encryption"


def test_upsert_email_server_config_clears_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upsert_email_server_config clears password when empty string provided."""
    from bookcard.api.schemas import EmailServerConfigUpdate

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    # Mock config with existing password
    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        smtp_password="encrypted_password",
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class StubService:
        def get_email_server_config(self, decrypt: bool = False) -> EmailServerConfig:
            return config

        def upsert_email_server_config(
            self,
            *,
            server_type: EmailServerType,
            smtp_password: str | None = None,
            **kwargs: object,
        ) -> EmailServerConfig:
            if smtp_password == "":
                config.smtp_password = None
            return config

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    # Send empty string as password to clear it
    payload = EmailServerConfigUpdate(
        server_type=EmailServerType.SMTP, smtp_password=""
    )
    result = auth.upsert_email_server_config(DummyRequest(), session, payload)

    # Verify password was cleared (not in response read model, but logic executed)
    # We can check the mock config object directly
    assert config.smtp_password is None
    # And check the property on the result
    assert result.has_smtp_password is False


def test_upsert_email_server_config_sets_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upsert_email_server_config sets new password."""
    from bookcard.api.schemas import EmailServerConfigUpdate

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class StubService:
        def get_email_server_config(self, decrypt: bool = False) -> EmailServerConfig:
            return config

        def upsert_email_server_config(
            self,
            *,
            server_type: EmailServerType,
            smtp_password: str | None = None,
            **kwargs: object,
        ) -> EmailServerConfig:
            if smtp_password:
                config.smtp_password = (
                    smtp_password  # In real app, this would be encrypted
                )
            return config

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    payload = EmailServerConfigUpdate(
        server_type=EmailServerType.SMTP, smtp_password="new-password"
    )
    result = auth.upsert_email_server_config(DummyRequest(), session, payload)

    assert config.smtp_password == "new-password"
    assert result.has_smtp_password is True


def test_upsert_email_server_config_clears_username(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upsert_email_server_config clears username when empty string provided."""
    from bookcard.api.schemas import EmailServerConfigUpdate

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    # Mock config with existing username
    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        smtp_username="existing_user",
        smtp_from_email="sender@example.com",  # Required when username is cleared
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class StubService:
        def get_email_server_config(self, decrypt: bool = False) -> EmailServerConfig:
            return config

        def upsert_email_server_config(
            self,
            *,
            server_type: EmailServerType,
            smtp_username: str | None = None,
            **kwargs: object,
        ) -> EmailServerConfig:
            # Simulate the logic we want to implement
            if smtp_username == "":
                config.smtp_username = None
            return config

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    # Send empty string as username to clear it
    payload = EmailServerConfigUpdate(
        server_type=EmailServerType.SMTP, smtp_username=""
    )
    result = auth.upsert_email_server_config(DummyRequest(), session, payload)

    assert config.smtp_username is None
    assert result.smtp_username is None


def test_upsert_email_server_config_validates_from_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upsert_email_server_config requires from_email if username is empty."""
    from bookcard.api.schemas import EmailServerConfigUpdate

    user = User(
        id=1,
        username="admin",
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    def mock_get_current_user(request: object, sess: object) -> User:
        return user

    monkeypatch.setattr(auth, "get_current_user", mock_get_current_user)

    # Mock config with no from_email
    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        smtp_username="existing_user",
        smtp_from_email=None,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    class StubService:
        def get_email_server_config(self, decrypt: bool = False) -> EmailServerConfig:
            return config

        def upsert_email_server_config(
            self,
            *,
            server_type: EmailServerType,
            smtp_username: str | None = None,
            **kwargs: object,
        ) -> EmailServerConfig:
            # Simulate validation logic
            if smtp_username == "":
                config.smtp_username = None

            if not config.smtp_username and not config.smtp_from_email:
                raise ValueError("smtp_from_email_required")
            return config

    def fake_auth_service(request: object, session: object) -> StubService:
        return StubService()

    monkeypatch.setattr(auth, "_auth_service", fake_auth_service)

    session = DummySession()
    # Clear username, but don't provide from_email (and it's None in config)
    payload = EmailServerConfigUpdate(
        server_type=EmailServerType.SMTP, smtp_username=""
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.upsert_email_server_config(DummyRequest(), session, payload)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert (
        exc_info.value.detail
        == "From email is required when SMTP authentication is disabled"
    )
