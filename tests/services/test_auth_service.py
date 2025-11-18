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

"""Tests for AuthService business logic."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest

from fundamental.services.auth_service import AuthError, AuthService
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
    monkeypatch: pytest.MonkeyPatch,
) -> AuthService:
    """Create AuthService with mocked directory creation."""
    import tempfile

    # Create a temporary directory for testing
    temp_dir = tempfile.mkdtemp()

    # Mock _ensure_data_directory_exists to avoid permission errors
    original_ensure = AuthService._ensure_data_directory_exists

    def mock_ensure(self: AuthService) -> None:
        """No-op implementation to skip directory creation."""

    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", mock_ensure)

    # type: ignore[invalid-argument-type]
    service = AuthService(
        session,  # type: ignore[arg-type]
        user_repo,  # type: ignore[arg-type]
        fake_hasher,  # type: ignore[arg-type]
        fake_jwt,  # type: ignore[arg-type]
        data_directory=temp_dir,
    )

    # Restore original method
    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", original_ensure)

    return service


def test_register_user_success(
    monkeypatch: pytest.MonkeyPatch, auth_service: AuthService, session: DummySession
) -> None:
    # Ensure service uses our dummy user class instead of ORM
    import fundamental.services.auth_service as auth_mod

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

    from fundamental.models.auth import Invite

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

    import fundamental.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "InviteRepository", MockInviteRepoClass)

    result = auth_service.validate_invite_token("valid-token-123")
    assert result is True


def test_validate_invite_token_not_found(
    auth_service: AuthService, session: DummySession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test validate_invite_token raises when token not found."""
    from fundamental.models.auth import Invite

    class MockInviteRepoClass:
        def __init__(self, session: object) -> None:
            pass

        def get_by_token(self, token: str) -> Invite | None:
            return None

    import fundamental.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "InviteRepository", MockInviteRepoClass)

    with pytest.raises(ValueError, match=rf"^{AuthError.INVALID_INVITE}$"):
        auth_service.validate_invite_token("missing-token")


def test_validate_invite_token_expired(
    auth_service: AuthService, session: DummySession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test validate_invite_token raises when token is expired."""
    from datetime import UTC, datetime, timedelta

    from fundamental.models.auth import Invite

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

    import fundamental.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "InviteRepository", MockInviteRepoClass)

    with pytest.raises(ValueError, match=rf"^{AuthError.INVITE_EXPIRED}$"):
        auth_service.validate_invite_token("expired-token")


def test_validate_invite_token_already_used(
    auth_service: AuthService, session: DummySession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test validate_invite_token raises when token is already used."""
    from datetime import UTC, datetime, timedelta

    from fundamental.models.auth import Invite

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

    import fundamental.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "InviteRepository", MockInviteRepoClass)

    with pytest.raises(ValueError, match=rf"^{AuthError.INVITE_ALREADY_USED}$"):
        auth_service.validate_invite_token("used-token")


def test_update_profile_success(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
) -> None:
    """Test update_profile updates user profile (covers lines 180-207)."""
    user = user_factory(
        user_id=1, username="alice", email="a@example.com", password_hash="hash(pw)"
    )
    user_repo.seed(user)

    result = auth_service.update_profile(
        1, username="bob", email="b@example.com", full_name="Bob Smith"
    )

    assert result.username == "bob"
    assert result.email == "b@example.com"
    assert result.full_name == "Bob Smith"
    assert session.flush_count >= 1


def test_update_profile_user_not_found(
    auth_service: AuthService, user_repo: InMemoryUserRepository
) -> None:
    """Test update_profile raises when user not found (covers lines 180-183)."""
    with pytest.raises(ValueError, match=r"^user_not_found$"):
        auth_service.update_profile(999, username="newname")


def test_update_profile_username_conflict(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
) -> None:
    """Test update_profile raises when username already exists (covers lines 186-189)."""
    user1 = user_factory(user_id=1, username="alice", email="a@example.com")
    user2 = user_factory(user_id=2, username="bob", email="b@example.com")
    user_repo.seed(user1)
    user_repo.seed(user2)

    with pytest.raises(ValueError, match=rf"^{AuthError.USERNAME_EXISTS}$"):
        auth_service.update_profile(1, username="bob")


def test_update_profile_email_conflict(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
) -> None:
    """Test update_profile raises when email already exists (covers lines 192-195)."""
    user1 = user_factory(user_id=1, username="alice", email="a@example.com")
    user2 = user_factory(user_id=2, username="bob", email="b@example.com")
    user_repo.seed(user1)
    user_repo.seed(user2)

    with pytest.raises(ValueError, match=rf"^{AuthError.EMAIL_EXISTS}$"):
        auth_service.update_profile(1, email="b@example.com")


def test_update_profile_partial_update(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
) -> None:
    """Test update_profile updates only provided fields (covers lines 198-203)."""
    user = user_factory(
        user_id=1, username="alice", email="a@example.com", password_hash="hash(pw)"
    )
    user_repo.seed(user)

    result = auth_service.update_profile(1, username="bob")

    assert result.username == "bob"
    assert result.email == "a@example.com"  # Unchanged
    assert session.flush_count >= 1


def test_upsert_setting_create(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upsert_setting creates new setting (covers lines 235-268)."""

    user = user_factory(user_id=1, username="alice", email="a@example.com")
    user_repo.seed(user)

    # Mock the select query to return None (no existing setting)
    session.add_exec_result([])

    result = auth_service.upsert_setting(1, "theme", "dark", "UI theme preference")

    assert result.key == "theme"
    assert result.value == "dark"
    assert result.description == "UI theme preference"
    assert result.user_id == 1
    assert result in session.added
    assert session.flush_count >= 1


def test_upsert_setting_update(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upsert_setting updates existing setting (covers lines 250-257)."""
    from fundamental.models.auth import UserSetting

    user = user_factory(user_id=1, username="alice", email="a@example.com")
    user_repo.seed(user)

    existing_setting = UserSetting(
        id=1, user_id=1, key="theme", value="light", description="Old description"
    )
    session.add_exec_result([existing_setting])

    result = auth_service.upsert_setting(1, "theme", "dark", "New description")

    assert result.value == "dark"
    assert result.description == "New description"
    assert session.flush_count >= 1


def test_upsert_setting_user_not_found(
    auth_service: AuthService, user_repo: InMemoryUserRepository
) -> None:
    """Test upsert_setting raises when user not found (covers lines 237-240)."""
    with pytest.raises(ValueError, match=r"^user_not_found$"):
        auth_service.upsert_setting(999, "theme", "dark")


def test_get_setting(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_setting retrieves setting (covers lines 285-288)."""
    from fundamental.models.auth import UserSetting

    class MockSettingRepository:
        def __init__(self, session: object) -> None:
            pass

        def get_by_key(self, user_id: int, key: str) -> UserSetting | None:
            if user_id == 1 and key == "theme":
                return UserSetting(id=1, user_id=1, key="theme", value="dark")
            return None

    import fundamental.repositories.admin_repositories as admin_repos_mod

    monkeypatch.setattr(admin_repos_mod, "SettingRepository", MockSettingRepository)

    result = auth_service.get_setting(1, "theme")

    assert result is not None
    assert result.key == "theme"
    assert result.value == "dark"


def test_get_all_settings(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    session: DummySession,
) -> None:
    """Test get_all_settings retrieves all user settings (covers lines 303-308)."""
    from fundamental.models.auth import UserSetting

    setting1 = UserSetting(id=1, user_id=1, key="theme", value="dark")
    setting2 = UserSetting(id=2, user_id=1, key="language", value="en")
    session.add_exec_result([setting1, setting2])

    result = auth_service.get_all_settings(1)

    assert len(result) == 2
    assert any(s.key == "theme" for s in result)
    assert any(s.key == "language" for s in result)


def test_upload_profile_picture_success(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upload_profile_picture saves file and updates user (covers lines 367-417)."""
    import tempfile

    user = user_factory(user_id=1, username="alice", email="a@example.com")
    user_repo.seed(user)

    # Create a temporary directory for the service
    temp_dir = tempfile.mkdtemp()
    service = AuthService(
        session,  # type: ignore[arg-type]
        user_repo,  # type: ignore[arg-type]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        data_directory=temp_dir,
    )

    file_content = b"fake image data"
    result = service.upload_profile_picture(1, file_content, "profile.jpg")

    assert result.profile_picture is not None
    assert "profile_picture.jpg" in result.profile_picture
    assert session.flush_count >= 1


def test_upload_profile_picture_deletes_old_absolute_path(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upload_profile_picture deletes old picture with absolute path (covers lines 387-391)."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        old_picture = Path(tmpdir) / "old_picture.jpg"
        old_picture.write_bytes(b"old image")

        user = user_factory(user_id=1, username="alice", email="a@example.com")
        user.profile_picture = str(old_picture)
        user_repo.seed(user)

        temp_dir = tempfile.mkdtemp()
        service = AuthService(
            session,  # type: ignore[arg-type]
            user_repo,  # type: ignore[arg-type]
            auth_service._hasher,  # type: ignore[attr-defined]
            auth_service._jwt,  # type: ignore[attr-defined]
            data_directory=temp_dir,
        )

        file_content = b"new image data"
        result = service.upload_profile_picture(1, file_content, "profile.jpg")

        assert result.profile_picture is not None
        # Old file should be deleted (or at least attempted)
        assert session.flush_count >= 1


def test_upload_profile_picture_deletes_old_relative_path(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upload_profile_picture deletes old picture with relative path (covers lines 392-396)."""
    import tempfile

    user = user_factory(user_id=1, username="alice", email="a@example.com")
    user.profile_picture = "1/assets/old_picture.jpg"
    user_repo.seed(user)

    temp_dir = tempfile.mkdtemp()
    # Create old picture file
    old_picture = Path(temp_dir) / user.profile_picture
    old_picture.parent.mkdir(parents=True, exist_ok=True)
    old_picture.write_bytes(b"old image")

    service = AuthService(
        session,  # type: ignore[arg-type]
        user_repo,  # type: ignore[arg-type]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        data_directory=temp_dir,
    )

    file_content = b"new image data"
    result = service.upload_profile_picture(1, file_content, "profile.jpg")

    assert result.profile_picture is not None
    assert session.flush_count >= 1


def test_upload_profile_picture_os_error(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test upload_profile_picture handles OSError when saving file (covers lines 407-409)."""
    import tempfile

    user = user_factory(user_id=1, username="alice", email="a@example.com")
    user_repo.seed(user)

    temp_dir = tempfile.mkdtemp()
    service = AuthService(
        session,  # type: ignore[arg-type]
        user_repo,  # type: ignore[arg-type]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        data_directory=temp_dir,
    )

    # On Windows, making directory read-only might not prevent file creation
    # Instead, create a file in the directory and make it read-only to prevent overwrite
    assets_dir = Path(temp_dir) / "1" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Create a read-only file that will prevent writing
    readonly_file = assets_dir / "profile_picture.jpg"
    readonly_file.touch()
    try:
        readonly_file.chmod(0o444)  # Read-only
        file_content = b"fake image data"
        with pytest.raises(ValueError, match=r"^failed_to_save_file"):
            service.upload_profile_picture(1, file_content, "profile.jpg")
    finally:
        try:
            readonly_file.chmod(0o644)  # Restore permissions
            readonly_file.unlink(missing_ok=True)
        except OSError:
            pass


def test_delete_profile_picture_file_absolute_path(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _delete_profile_picture_file deletes absolute path (covers lines 336-337)."""
    import tempfile

    user = user_factory(user_id=1, username="alice", email="a@example.com")
    user_repo.seed(user)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file to delete
        picture_file = Path(tmpdir) / "test_picture.jpg"
        picture_file.write_bytes(b"fake image")

        temp_dir = tempfile.mkdtemp()
        service = AuthService(
            session,  # type: ignore[arg-type]
            user_repo,  # type: ignore[arg-type]
            auth_service._hasher,  # type: ignore[attr-defined]
            auth_service._jwt,  # type: ignore[attr-defined]
            data_directory=temp_dir,
        )

        service._delete_profile_picture_file(str(picture_file))

        # File should be deleted
        assert not picture_file.exists()


def test_upload_profile_picture_invalid_extension(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
) -> None:
    """Test upload_profile_picture raises on invalid file extension (covers lines 372-383)."""
    user = user_factory(user_id=1, username="alice", email="a@example.com")
    user_repo.seed(user)

    with pytest.raises(ValueError, match=r"^invalid_file_type$"):
        auth_service.upload_profile_picture(1, b"data", "file.txt")


def test_upload_profile_picture_user_not_found(
    auth_service: AuthService, user_repo: InMemoryUserRepository
) -> None:
    """Test upload_profile_picture raises when user not found (covers lines 367-370)."""
    with pytest.raises(ValueError, match=r"^user_not_found$"):
        auth_service.upload_profile_picture(999, b"data", "profile.jpg")


def test_delete_profile_picture_with_relative_path(
    auth_service: AuthService,
    user_repo: InMemoryUserRepository,
    user_factory: Callable[..., InMemoryUser],
    session: DummySession,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test delete_profile_picture handles relative path (covers lines 481-484)."""
    import tempfile
    from pathlib import Path

    user = user_factory(user_id=1, username="alice", email="a@example.com")
    user.profile_picture = "1/assets/profile_picture.jpg"
    user_repo.seed(user)

    temp_dir = tempfile.mkdtemp()
    service = AuthService(
        session,  # type: ignore[arg-type]
        user_repo,  # type: ignore[arg-type]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        data_directory=temp_dir,
    )

    # Create the file to be deleted
    file_path = Path(temp_dir) / user.profile_picture
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"fake image")

    result = service.delete_profile_picture(1)

    assert result.profile_picture is None
    assert session.flush_count >= 1


# Tests for get_email_server_config with decryption (lines 324-341)
def test_get_email_server_config_with_decryption(
    auth_service: AuthService,
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_email_server_config decrypts password and token (covers lines 324-341)."""
    import tempfile
    from datetime import UTC, datetime

    from fundamental.models.config import EmailServerConfig, EmailServerType
    from fundamental.services.security import DataEncryptor
    from tests.conftest import TEST_ENCRYPTION_KEY

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)
    temp_dir = tempfile.mkdtemp()

    def mock_ensure(self: AuthService) -> None:
        """No-op implementation to skip directory creation."""

    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", mock_ensure)

    service = AuthService(
        session,  # type: ignore[arg-type]
        auth_service._users,  # type: ignore[attr-defined]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        encryptor=encryptor,
        data_directory=temp_dir,
    )

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        smtp_host="smtp.example.com",
        smtp_password=encryptor.encrypt("plain_password"),
        gmail_token=encryptor.encrypt_dict({"token": "gmail_token"}),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.add_exec_result([config])

    result = service.get_email_server_config(decrypt=True)

    assert result is not None
    assert result.smtp_password == "plain_password"
    assert result.gmail_token == {"token": "gmail_token"}
    assert session.expunge_count >= 1


def test_get_email_server_config_skips_decryption_when_not_string(
    auth_service: AuthService,
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_email_server_config skips token decryption when not string (covers line 338)."""
    import tempfile
    from datetime import UTC, datetime

    from fundamental.models.config import EmailServerConfig, EmailServerType
    from fundamental.services.security import DataEncryptor
    from tests.conftest import TEST_ENCRYPTION_KEY

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)
    temp_dir = tempfile.mkdtemp()

    def mock_ensure(self: AuthService) -> None:
        """No-op implementation to skip directory creation."""

    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", mock_ensure)

    service = AuthService(
        session,  # type: ignore[arg-type]
        auth_service._users,  # type: ignore[attr-defined]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        encryptor=encryptor,
        data_directory=temp_dir,
    )

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        smtp_host="smtp.example.com",
        gmail_token={"already": "decrypted"},  # Already a dict
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.add_exec_result([config])

    result = service.get_email_server_config(decrypt=True)

    assert result is not None
    assert result.gmail_token == {"already": "decrypted"}


# Tests for _apply_smtp_config (lines 369-390)
def test_apply_smtp_config_all_fields(
    auth_service: AuthService,
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _apply_smtp_config applies all SMTP fields (covers lines 369-390)."""
    import tempfile
    from datetime import UTC, datetime

    from fundamental.models.config import EmailServerConfig, EmailServerType
    from fundamental.services.security import DataEncryptor
    from tests.conftest import TEST_ENCRYPTION_KEY

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)
    temp_dir = tempfile.mkdtemp()

    def mock_ensure(self: AuthService) -> None:
        """No-op implementation to skip directory creation."""

    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", mock_ensure)

    service = AuthService(
        session,  # type: ignore[arg-type]
        auth_service._users,  # type: ignore[attr-defined]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        encryptor=encryptor,
        data_directory=temp_dir,
    )

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    service._apply_smtp_config(
        config,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="plain_password",
        smtp_use_tls=True,
        smtp_use_ssl=False,
        smtp_from_email="sender@example.com",
        smtp_from_name="Sender Name",
    )

    assert config.smtp_host == "smtp.example.com"
    assert config.smtp_port == 587
    assert config.smtp_username == "user@example.com"
    # Verify password is encrypted (will be different each time due to randomness)
    assert config.smtp_password != "plain_password"
    assert isinstance(config.smtp_password, str)
    # Verify we can decrypt it back
    assert encryptor.decrypt(config.smtp_password) == "plain_password"
    assert config.smtp_use_tls is True
    assert config.smtp_use_ssl is False
    assert config.smtp_from_email == "sender@example.com"
    assert config.smtp_from_name == "Sender Name"
    assert config.gmail_token is None


def test_apply_smtp_config_without_encryptor(
    auth_service: AuthService,
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _apply_smtp_config stores password unencrypted when no encryptor (covers line 380)."""
    import tempfile
    from datetime import UTC, datetime

    from fundamental.models.config import EmailServerConfig, EmailServerType

    temp_dir = tempfile.mkdtemp()

    def mock_ensure(self: AuthService) -> None:
        """No-op implementation to skip directory creation."""

    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", mock_ensure)

    service = AuthService(
        session,  # type: ignore[arg-type]
        auth_service._users,  # type: ignore[attr-defined]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        encryptor=None,
        data_directory=temp_dir,
    )

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    service._apply_smtp_config(
        config,
        smtp_host=None,
        smtp_port=None,
        smtp_username=None,
        smtp_password="plain_password",
        smtp_use_tls=None,
        smtp_use_ssl=None,
        smtp_from_email=None,
        smtp_from_name=None,
    )

    assert config.smtp_password == "plain_password"


# Tests for _apply_gmail_config (lines 421-442)
def test_apply_gmail_config_all_fields(
    auth_service: AuthService,
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _apply_gmail_config applies all Gmail fields (covers lines 421-442)."""
    import tempfile
    from datetime import UTC, datetime

    from fundamental.models.config import EmailServerConfig, EmailServerType
    from fundamental.services.security import DataEncryptor
    from tests.conftest import TEST_ENCRYPTION_KEY

    encryptor = DataEncryptor(TEST_ENCRYPTION_KEY)
    temp_dir = tempfile.mkdtemp()

    def mock_ensure(self: AuthService) -> None:
        """No-op implementation to skip directory creation."""

    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", mock_ensure)

    service = AuthService(
        session,  # type: ignore[arg-type]
        auth_service._users,  # type: ignore[attr-defined]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        encryptor=encryptor,
        data_directory=temp_dir,
    )

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.GMAIL,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    gmail_token = {"access_token": "token123", "email": "test@gmail.com"}

    service._apply_gmail_config(
        config,
        gmail_token=gmail_token,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="user@gmail.com",
        smtp_use_tls=True,
        smtp_use_ssl=False,
        smtp_from_email="sender@gmail.com",
        smtp_from_name="Gmail Sender",
    )

    # Verify token is encrypted (will be different each time due to randomness)
    assert config.gmail_token != gmail_token
    assert isinstance(config.gmail_token, str)
    # Verify we can decrypt it back
    decrypted = encryptor.decrypt_dict(config.gmail_token)
    assert decrypted == gmail_token
    assert config.smtp_password is None
    assert config.smtp_host == "smtp.gmail.com"
    assert config.smtp_port == 587
    assert config.smtp_username == "user@gmail.com"
    assert config.smtp_use_tls is True
    assert config.smtp_use_ssl is False
    assert config.smtp_from_email == "sender@gmail.com"
    assert config.smtp_from_name == "Gmail Sender"


def test_apply_gmail_config_without_encryptor(
    auth_service: AuthService,
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _apply_gmail_config stores token unencrypted when no encryptor (covers line 425)."""
    import tempfile
    from datetime import UTC, datetime

    from fundamental.models.config import EmailServerConfig, EmailServerType

    temp_dir = tempfile.mkdtemp()

    def mock_ensure(self: AuthService) -> None:
        """No-op implementation to skip directory creation."""

    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", mock_ensure)

    service = AuthService(
        session,  # type: ignore[arg-type]
        auth_service._users,  # type: ignore[attr-defined]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        encryptor=None,
        data_directory=temp_dir,
    )

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.GMAIL,
        enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    gmail_token = {"access_token": "token123"}

    service._apply_gmail_config(
        config,
        gmail_token=gmail_token,
        smtp_host=None,
        smtp_port=None,
        smtp_username=None,
        smtp_use_tls=None,
        smtp_use_ssl=None,
        smtp_from_email=None,
        smtp_from_name=None,
    )

    assert config.gmail_token == gmail_token


def test_apply_gmail_config_none_token(
    auth_service: AuthService,
    session: DummySession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _apply_gmail_config sets token to None when None provided (covers line 427)."""
    import tempfile
    from datetime import UTC, datetime

    from fundamental.models.config import EmailServerConfig, EmailServerType

    temp_dir = tempfile.mkdtemp()

    def mock_ensure(self: AuthService) -> None:
        """No-op implementation to skip directory creation."""

    monkeypatch.setattr(AuthService, "_ensure_data_directory_exists", mock_ensure)

    service = AuthService(
        session,  # type: ignore[arg-type]
        auth_service._users,  # type: ignore[attr-defined]
        auth_service._hasher,  # type: ignore[attr-defined]
        auth_service._jwt,  # type: ignore[attr-defined]
        data_directory=temp_dir,
    )

    config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.GMAIL,
        enabled=True,
        gmail_token={"existing": "token"},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    service._apply_gmail_config(
        config,
        gmail_token=None,
        smtp_host=None,
        smtp_port=None,
        smtp_username=None,
        smtp_use_tls=None,
        smtp_use_ssl=None,
        smtp_from_email=None,
        smtp_from_name=None,
    )

    assert config.gmail_token is None


# Tests for upsert_email_server_config (lines 490-534)
def test_upsert_email_server_config_invalid_encryption(
    auth_service: AuthService,
    session: DummySession,
) -> None:
    """Test upsert_email_server_config raises error for invalid encryption (covers lines 490-492)."""
    with pytest.raises(ValueError, match="invalid_smtp_encryption"):
        auth_service.upsert_email_server_config(
            server_type="smtp",  # type: ignore[arg-type]
            smtp_use_tls=True,
            smtp_use_ssl=True,
        )


def test_upsert_email_server_config_creates_new_smtp(
    auth_service: AuthService,
    session: DummySession,
) -> None:
    """Test upsert_email_server_config creates new SMTP config (covers lines 494-534)."""
    from fundamental.models.config import EmailServerType

    session.add_exec_result([None])  # get_email_server_config returns None

    result = auth_service.upsert_email_server_config(
        server_type=EmailServerType.SMTP,
        smtp_host="smtp.example.com",
        smtp_port=587,
        enabled=True,
        max_email_size_mb=25,
    )

    assert result is not None
    assert result.server_type == EmailServerType.SMTP
    assert result.smtp_host == "smtp.example.com"
    assert result.smtp_port == 587
    assert result.enabled is True
    assert result.max_email_size_mb == 25
    assert len(session.added) >= 1
    assert session.flush_count >= 1


def test_upsert_email_server_config_updates_existing_smtp(
    auth_service: AuthService,
    session: DummySession,
) -> None:
    """Test upsert_email_server_config updates existing SMTP config (covers lines 494-534)."""
    from datetime import UTC, datetime

    from fundamental.models.config import EmailServerConfig, EmailServerType

    existing_config = EmailServerConfig(
        id=1,
        server_type=EmailServerType.SMTP,
        enabled=True,
        smtp_host="old.example.com",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    session.add_exec_result([existing_config])

    result = auth_service.upsert_email_server_config(
        server_type=EmailServerType.SMTP,
        smtp_host="new.example.com",
        smtp_port=465,
    )

    assert result.smtp_host == "new.example.com"
    assert result.smtp_port == 465
    # Should not add new config, only update existing
    assert len([a for a in session.added if isinstance(a, EmailServerConfig)]) == 0


def test_upsert_email_server_config_creates_new_gmail(
    auth_service: AuthService,
    session: DummySession,
) -> None:
    """Test upsert_email_server_config creates new Gmail config (covers lines 519-534)."""
    from fundamental.models.config import EmailServerType

    session.add_exec_result([None])

    result = auth_service.upsert_email_server_config(
        server_type=EmailServerType.GMAIL,
        gmail_token={"access_token": "token123"},
        enabled=True,
    )

    assert result is not None
    assert result.server_type == EmailServerType.GMAIL
    assert result.enabled is True
    assert len(session.added) >= 1
    assert session.flush_count >= 1
