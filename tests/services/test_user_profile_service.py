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

"""Tests for user profile service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.models.auth import User
from bookcard.services.user_profile_service import ProfileError, UserProfileService
from tests.conftest import DummySession

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def session() -> DummySession:
    """Return a fresh DummySession."""
    return DummySession()


@pytest.fixture
def user_repo() -> MagicMock:
    """Return a mock UserRepository."""
    return MagicMock(spec=["get", "find_by_username", "find_by_email"])


@pytest.fixture
def hasher() -> MagicMock:
    """Return a mock PasswordHasher."""
    mock = MagicMock(spec=["hash", "verify"])
    mock.hash.return_value = "new_hashed_password"
    mock.verify.return_value = True
    return mock


@pytest.fixture
def file_storage() -> MagicMock:
    """Return a mock FileStorageService."""
    mock = MagicMock(spec=["save_profile_picture", "delete_profile_picture"])
    mock.save_profile_picture.return_value = "1/assets/profile_picture.jpg"
    return mock


@pytest.fixture
def service(
    session: DummySession,
    user_repo: MagicMock,
    hasher: MagicMock,
    file_storage: MagicMock,
) -> UserProfileService:
    """Return a UserProfileService with mocked dependencies."""
    return UserProfileService(
        session=session,  # type: ignore[arg-type]
        user_repo=user_repo,
        hasher=hasher,
        file_storage=file_storage,
    )


@pytest.fixture
def sample_user() -> User:
    """Return a sample user for tests."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="old_hashed_password",
        full_name="Test User",
        profile_picture=None,
    )


# ---------------------------------------------------------------------------
# change_password tests
# ---------------------------------------------------------------------------


class TestChangePassword:
    """Tests for UserProfileService.change_password."""

    def test_change_password_success(
        self,
        service: UserProfileService,
        session: DummySession,
        user_repo: MagicMock,
        hasher: MagicMock,
        sample_user: User,
    ) -> None:
        """Password change succeeds with valid current password."""
        user_repo.get.return_value = sample_user
        hasher.verify.return_value = True

        service.change_password(1, "current_pw", "new_pw")

        assert sample_user.password_hash == "new_hashed_password"
        assert session.flush_count == 1
        hasher.verify.assert_called_once_with("current_pw", "old_hashed_password")
        hasher.hash.assert_called_once_with("new_pw")

    def test_change_password_user_not_found(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
    ) -> None:
        """Password change fails when user not found."""
        user_repo.get.return_value = None

        with pytest.raises(ValueError, match=ProfileError.USER_NOT_FOUND):
            service.change_password(999, "current_pw", "new_pw")

    def test_change_password_invalid_current(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        hasher: MagicMock,
        sample_user: User,
    ) -> None:
        """Password change fails when current password is wrong."""
        user_repo.get.return_value = sample_user
        hasher.verify.return_value = False

        with pytest.raises(ValueError, match=ProfileError.INVALID_PASSWORD):
            service.change_password(1, "wrong_current_pw", "new_pw")


# ---------------------------------------------------------------------------
# update_profile tests
# ---------------------------------------------------------------------------


class TestUpdateProfile:
    """Tests for UserProfileService.update_profile."""

    def test_update_profile_all_fields(
        self,
        service: UserProfileService,
        session: DummySession,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Profile update succeeds with all fields provided."""
        user_repo.get.return_value = sample_user
        user_repo.find_by_username.return_value = None
        user_repo.find_by_email.return_value = None

        result = service.update_profile(
            1,
            username="newusername",
            email="new@example.com",
            full_name="New Name",
        )

        assert result.username == "newusername"
        assert result.email == "new@example.com"
        assert result.full_name == "New Name"
        assert session.flush_count == 1

    def test_update_profile_no_changes(
        self,
        service: UserProfileService,
        session: DummySession,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Profile update succeeds with no fields provided."""
        user_repo.get.return_value = sample_user

        result = service.update_profile(1)

        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert session.flush_count == 1

    def test_update_profile_same_username(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Profile update succeeds when setting same username (no uniqueness check)."""
        user_repo.get.return_value = sample_user

        result = service.update_profile(1, username="testuser")

        assert result.username == "testuser"
        # find_by_username should NOT be called when username is unchanged
        user_repo.find_by_username.assert_not_called()

    def test_update_profile_same_email(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Profile update succeeds when setting same email (no uniqueness check)."""
        user_repo.get.return_value = sample_user

        result = service.update_profile(1, email="test@example.com")

        assert result.email == "test@example.com"
        user_repo.find_by_email.assert_not_called()

    def test_update_profile_user_not_found(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
    ) -> None:
        """Profile update fails when user not found."""
        user_repo.get.return_value = None

        with pytest.raises(ValueError, match=ProfileError.USER_NOT_FOUND):
            service.update_profile(999, username="newname")

    def test_update_profile_username_conflict(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Profile update fails when username already taken by another user."""
        user_repo.get.return_value = sample_user
        other_user = User(
            id=2, username="taken", email="other@example.com", password_hash="h"
        )
        user_repo.find_by_username.return_value = other_user

        with pytest.raises(ValueError, match=ProfileError.USERNAME_EXISTS):
            service.update_profile(1, username="taken")

    def test_update_profile_email_conflict(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Profile update fails when email already taken by another user."""
        user_repo.get.return_value = sample_user
        user_repo.find_by_username.return_value = None
        other_user = User(
            id=2, username="other", email="taken@example.com", password_hash="h"
        )
        user_repo.find_by_email.return_value = other_user

        with pytest.raises(ValueError, match=ProfileError.EMAIL_EXISTS):
            service.update_profile(1, email="taken@example.com")

    def test_update_profile_username_same_user(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Profile update succeeds if username lookup returns same user."""
        user_repo.get.return_value = sample_user
        user_repo.find_by_username.return_value = sample_user  # Same user

        result = service.update_profile(1, username="newusername")

        assert result.username == "newusername"

    def test_update_profile_email_same_user(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Profile update succeeds if email lookup returns same user."""
        user_repo.get.return_value = sample_user
        user_repo.find_by_email.return_value = sample_user  # Same user

        result = service.update_profile(1, email="new@example.com")

        assert result.email == "new@example.com"


# ---------------------------------------------------------------------------
# upload_profile_picture tests
# ---------------------------------------------------------------------------


class TestUploadProfilePicture:
    """Tests for UserProfileService.upload_profile_picture."""

    @pytest.mark.parametrize(
        "filename",
        [
            "photo.jpg",
            "photo.jpeg",
            "photo.png",
            "photo.gif",
            "photo.webp",
            "photo.svg",
            "PHOTO.JPG",  # Uppercase
        ],
    )
    def test_upload_profile_picture_valid_extensions(
        self,
        service: UserProfileService,
        session: DummySession,
        user_repo: MagicMock,
        file_storage: MagicMock,
        sample_user: User,
        filename: str,
    ) -> None:
        """Upload succeeds for all valid image extensions."""
        user_repo.get.return_value = sample_user

        result = service.upload_profile_picture(1, b"image_data", filename)

        assert result.profile_picture == "1/assets/profile_picture.jpg"
        file_storage.save_profile_picture.assert_called_once_with(
            1, b"image_data", filename
        )
        assert session.flush_count == 1

    @pytest.mark.parametrize(
        "filename",
        [
            "file.txt",
            "file.pdf",
            "file.exe",
            "file",  # No extension
            "file.",  # Empty extension
        ],
    )
    def test_upload_profile_picture_invalid_extensions(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        sample_user: User,
        filename: str,
    ) -> None:
        """Upload fails for invalid file extensions."""
        user_repo.get.return_value = sample_user

        with pytest.raises(ValueError, match=ProfileError.INVALID_FILE_TYPE):
            service.upload_profile_picture(1, b"image_data", filename)

    def test_upload_profile_picture_deletes_old(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        file_storage: MagicMock,
        sample_user: User,
    ) -> None:
        """Upload deletes old picture before saving new one."""
        sample_user.profile_picture = "1/assets/old_picture.png"
        user_repo.get.return_value = sample_user

        service.upload_profile_picture(1, b"image_data", "new.jpg")

        file_storage.delete_profile_picture.assert_called_once_with(
            "1/assets/old_picture.png"
        )
        file_storage.save_profile_picture.assert_called_once()

    def test_upload_profile_picture_no_old_picture(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
        file_storage: MagicMock,
        sample_user: User,
    ) -> None:
        """Upload does not call delete when no old picture exists."""
        sample_user.profile_picture = None
        user_repo.get.return_value = sample_user

        service.upload_profile_picture(1, b"image_data", "new.jpg")

        file_storage.delete_profile_picture.assert_not_called()

    def test_upload_profile_picture_user_not_found(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
    ) -> None:
        """Upload fails when user not found."""
        user_repo.get.return_value = None

        with pytest.raises(ValueError, match=ProfileError.USER_NOT_FOUND):
            service.upload_profile_picture(999, b"image_data", "photo.jpg")


# ---------------------------------------------------------------------------
# delete_profile_picture tests
# ---------------------------------------------------------------------------


class TestDeleteProfilePicture:
    """Tests for UserProfileService.delete_profile_picture."""

    def test_delete_profile_picture_success(
        self,
        service: UserProfileService,
        session: DummySession,
        user_repo: MagicMock,
        file_storage: MagicMock,
        sample_user: User,
    ) -> None:
        """Delete succeeds and removes file when picture exists."""
        sample_user.profile_picture = "1/assets/profile_picture.jpg"
        user_repo.get.return_value = sample_user

        result = service.delete_profile_picture(1)

        assert result.profile_picture is None
        file_storage.delete_profile_picture.assert_called_once_with(
            "1/assets/profile_picture.jpg"
        )
        assert session.flush_count == 1

    def test_delete_profile_picture_no_picture(
        self,
        service: UserProfileService,
        session: DummySession,
        user_repo: MagicMock,
        file_storage: MagicMock,
        sample_user: User,
    ) -> None:
        """Delete succeeds even when no picture exists (no file deleted)."""
        sample_user.profile_picture = None
        user_repo.get.return_value = sample_user

        result = service.delete_profile_picture(1)

        assert result.profile_picture is None
        file_storage.delete_profile_picture.assert_not_called()
        assert session.flush_count == 1

    def test_delete_profile_picture_user_not_found(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
    ) -> None:
        """Delete fails when user not found."""
        user_repo.get.return_value = None

        with pytest.raises(ValueError, match=ProfileError.USER_NOT_FOUND):
            service.delete_profile_picture(999)


# ---------------------------------------------------------------------------
# update_profile_picture_path tests
# ---------------------------------------------------------------------------


class TestUpdateProfilePicturePath:
    """Tests for UserProfileService.update_profile_picture_path."""

    def test_update_profile_picture_path_success(
        self,
        service: UserProfileService,
        session: DummySession,
        user_repo: MagicMock,
        sample_user: User,
    ) -> None:
        """Path update succeeds."""
        user_repo.get.return_value = sample_user

        result = service.update_profile_picture_path(1, "new/path/pic.jpg")

        assert result.profile_picture == "new/path/pic.jpg"
        assert session.flush_count == 1

    def test_update_profile_picture_path_user_not_found(
        self,
        service: UserProfileService,
        user_repo: MagicMock,
    ) -> None:
        """Path update fails when user not found."""
        user_repo.get.return_value = None

        with pytest.raises(ValueError, match=ProfileError.USER_NOT_FOUND):
            service.update_profile_picture_path(999, "path/pic.jpg")
