from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import HTTPException

import fundamental.api.routes.auth as auth
from fundamental.models.auth import User
from tests.conftest import DummySession


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
        self.app = type(
            "App", (), {"state": type("State", (), {"config": object()})()}
        )()


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
    from types import SimpleNamespace

    class DummyConfig:
        jwt_secret = "test-secret"
        jwt_algorithm = "HS256"
        jwt_expires_minutes = 15

    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(config=DummyConfig()))
    )
    session = object()

    # Test that _auth_service constructs the service correctly
    service = auth._auth_service(request, session)  # type: ignore[arg-type]
    from fundamental.services.auth_service import AuthService

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
    result = auth.logout()
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
    payload = auth.ProfilePictureUpdateRequest(picture_path="/new/path.jpg")
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
    payload = auth.ProfilePictureUpdateRequest(picture_path="/path.jpg")
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
    payload = auth.ProfilePictureUpdateRequest(picture_path="/path.jpg")
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
