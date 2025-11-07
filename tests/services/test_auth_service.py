# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for AuthService business logic."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import pytest

from rainbow.services.auth_service import AuthError, AuthService
from tests.conftest import (
    DummySession,
    FakeHasher,
    FakeJWTManager,
    InMemoryUser,
    InMemoryUserRepository,
)


@dataclass
class DummyUser:
    """Lightweight stand-in for ORM User for unit tests."""

    id: int | None = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_admin: bool = False
    last_login: datetime | None = None


@pytest.fixture
def auth_service(
    session: DummySession,
    user_repo: InMemoryUserRepository,
    fake_hasher: FakeHasher,
    fake_jwt: FakeJWTManager,
) -> AuthService:
    return AuthService(session, user_repo, fake_hasher, fake_jwt)  # type: ignore[arg-type]


def test_register_user_success(
    monkeypatch: pytest.MonkeyPatch, auth_service: AuthService, session: DummySession
) -> None:
    # Ensure service uses our dummy user class instead of ORM
    import rainbow.services.auth_service as auth_mod

    monkeypatch.setattr(auth_mod, "User", DummyUser, raising=False)

    user, token = auth_service.register_user("alice", "a@example.com", "pw")

    assert isinstance(user, DummyUser)
    assert user.username == "alice"
    assert user.email == "a@example.com"
    assert user.password_hash
    assert user.password_hash.startswith("hash(")
    # id auto-assigned by DummySession.flush
    assert user.id is not None
    assert token.startswith("token(")
    # session add + flush were called
    assert session.added
    assert session.flush_count >= 1


@pytest.mark.parametrize(
    ("pre_existing", "expected"),
    [
        ("username", AuthError.USERNAME_EXISTS),
        ("email", AuthError.EMAIL_EXISTS),
    ],
)
def test_register_user_conflicts(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    pre_existing: str,
    expected: str,
) -> None:
    existing = InMemoryUser(id=1, username="bob", email="b@example.com")
    user_repo.seed(existing)

    if pre_existing == "username":
        # Seed a conflicting username
        user_repo.seed(InMemoryUser(id=2, username="alice", email="other@example.com"))
    else:
        # Seed a conflicting email
        user_repo.seed(InMemoryUser(id=3, username="other", email="a@example.com"))

    with pytest.raises(ValueError, match=rf"^{expected}$") as err:
        auth_service.register_user("alice", "a@example.com", "pw")
    assert str(err.value) == expected


@pytest.mark.parametrize("identifier", ["charlie", "c@example.com"])
def test_login_user_success(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: "Callable[..., InMemoryUser]",
    identifier: str,
    session: DummySession,
) -> None:
    # Seed a user with matching credentials
    user = user_factory(
        user_id=7, username="charlie", email="c@example.com", password_hash="hash(pw)"
    )
    user_repo.seed(user)

    authed_user, token = auth_service.login_user(identifier, "pw")

    assert authed_user.id == 7
    assert authed_user.last_login is not None
    assert token.startswith("token(")
    assert session.flush_count >= 1


def _no_user(repo: InMemoryUserRepository) -> None:
    return None


def _seed_wrong_password(repo: InMemoryUserRepository) -> None:
    repo.seed(
        InMemoryUser(
            id=2, username="dora", email="d@example.com", password_hash="hash(pw)"
        )
    )


@pytest.mark.parametrize(
    ("identifier", "password", "setup_repo"),
    [
        ("ghost", "pw", _no_user),  # user missing
        ("dora", "wrong", _seed_wrong_password),  # wrong password
    ],
)
def test_login_user_invalid(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    identifier: str,
    password: str,
    setup_repo: Callable[[InMemoryUserRepository], None],
) -> None:
    setup_repo(user_repo)
    with pytest.raises(ValueError, match=rf"^{AuthError.INVALID_CREDENTIALS}$") as err:
        auth_service.login_user(identifier, password)
    assert str(err.value) == AuthError.INVALID_CREDENTIALS


def test_change_password_success(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    fake_hasher: FakeHasher,
) -> None:
    """Test change_password updates password successfully."""
    user = user_factory(
        user_id=1, username="alice", email="a@example.com", password_hash="hash(oldpw)"
    )
    user_repo.seed(user)

    auth_service.change_password(1, "oldpw", "newpw")

    assert user.password_hash == "hash(newpw)"
    assert session.flush_count >= 1


def test_change_password_user_not_found(
    auth_service: AuthService, user_repo: InMemoryUserRepository
) -> None:
    """Test change_password raises when user not found."""
    with pytest.raises(ValueError, match=r"^user_not_found$"):
        auth_service.change_password(999, "oldpw", "newpw")


def test_change_password_invalid_current_password(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
) -> None:
    """Test change_password raises when current password is incorrect."""
    user = user_factory(
        user_id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash(correct)",
    )
    user_repo.seed(user)

    with pytest.raises(ValueError, match=rf"^{AuthError.INVALID_PASSWORD}$"):
        auth_service.change_password(1, "wrongpw", "newpw")


def test_update_profile_picture_success(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
) -> None:
    """Test update_profile_picture updates profile picture path."""
    user = user_factory(
        user_id=1, username="alice", email="a@example.com", password_hash="hash(pw)"
    )
    user_repo.seed(user)

    result = auth_service.update_profile_picture(1, "/path/to/picture.jpg")

    assert result.profile_picture == "/path/to/picture.jpg"
    assert session.flush_count >= 1


def test_update_profile_picture_user_not_found(
    auth_service: AuthService, user_repo: InMemoryUserRepository
) -> None:
    """Test update_profile_picture raises when user not found."""
    with pytest.raises(ValueError, match=r"^user_not_found$"):
        auth_service.update_profile_picture(999, "/path/to/picture.jpg")


def test_delete_profile_picture_success(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
) -> None:
    """Test delete_profile_picture removes profile picture."""
    user = user_factory(
        user_id=1,
        username="alice",
        email="a@example.com",
        password_hash="hash(pw)",
    )
    user.profile_picture = "/path/to/picture.jpg"
    user_repo.seed(user)

    result = auth_service.delete_profile_picture(1)

    assert result.profile_picture is None
    assert session.flush_count >= 1


def test_delete_profile_picture_user_not_found(
    auth_service: AuthService, user_repo: InMemoryUserRepository
) -> None:
    """Test delete_profile_picture raises when user not found."""
    with pytest.raises(ValueError, match=r"^user_not_found$"):
        auth_service.delete_profile_picture(999)


def test_validate_invite_token_success(
    auth_service: AuthService, session: DummySession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test validate_invite_token returns True for valid token."""
    from datetime import UTC, datetime, timedelta

    from rainbow.models.auth import Invite

    invite = Invite(
        id=1,
        created_by=1,
        token="valid-token-123",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        used_by=None,
    )  # type: ignore[call-arg]

    class MockInviteRepoClass:
        def __init__(self, session: object) -> None:
            pass

        def get_by_token(self, token: str) -> Invite | None:
            if token == "valid-token-123":
                return invite
            return None

    import rainbow.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "InviteRepository", MockInviteRepoClass)

    result = auth_service.validate_invite_token("valid-token-123")
    assert result is True


def test_validate_invite_token_not_found(
    auth_service: AuthService, session: DummySession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test validate_invite_token raises when token not found."""
    from rainbow.models.auth import Invite

    class MockInviteRepoClass:
        def __init__(self, session: object) -> None:
            pass

        def get_by_token(self, token: str) -> Invite | None:
            return None

    import rainbow.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "InviteRepository", MockInviteRepoClass)

    with pytest.raises(ValueError, match=rf"^{AuthError.INVALID_INVITE}$"):
        auth_service.validate_invite_token("missing-token")


def test_validate_invite_token_expired(
    auth_service: AuthService, session: DummySession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test validate_invite_token raises when token is expired."""
    from datetime import UTC, datetime, timedelta

    from rainbow.models.auth import Invite

    expired_invite = Invite(
        id=1,
        created_by=1,
        token="expired-token",
        expires_at=datetime.now(UTC) - timedelta(days=1),
        used_by=None,
    )  # type: ignore[call-arg]

    class MockInviteRepoClass:
        def __init__(self, session: object) -> None:
            pass

        def get_by_token(self, token: str) -> Invite | None:
            if token == "expired-token":
                return expired_invite
            return None

    import rainbow.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "InviteRepository", MockInviteRepoClass)

    with pytest.raises(ValueError, match=rf"^{AuthError.INVITE_EXPIRED}$"):
        auth_service.validate_invite_token("expired-token")


def test_validate_invite_token_already_used(
    auth_service: AuthService, session: DummySession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test validate_invite_token raises when token is already used."""
    from datetime import UTC, datetime, timedelta

    from rainbow.models.auth import Invite

    used_invite = Invite(
        id=1,
        created_by=1,
        token="used-token",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        used_by=2,
    )  # type: ignore[call-arg]

    class MockInviteRepoClass:
        def __init__(self, session: object) -> None:
            pass

        def get_by_token(self, token: str) -> Invite | None:
            if token == "used-token":
                return used_invite
            return None

    import rainbow.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "InviteRepository", MockInviteRepoClass)

    with pytest.raises(ValueError, match=rf"^{AuthError.INVITE_ALREADY_USED}$"):
        auth_service.validate_invite_token("used-token")
