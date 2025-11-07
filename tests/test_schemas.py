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

"""Tests for API schemas."""

import pytest
from pydantic import ValidationError

from rainbow.api.schemas import (
    InviteValidationResponse,
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    ProfilePictureUpdateRequest,
    ProfileRead,
    TokenResponse,
    UserCreate,
    UserRead,
)


@pytest.mark.parametrize(
    ("username", "email", "password"),
    [
        ("alice", "alice@example.com", "password123"),
        ("bob", "bob@test.com", "securepass"),
        ("charlie", "charlie@domain.org", "p@ssw0rd"),
    ],
)
def test_user_create_valid(username: str, email: str, password: str) -> None:
    """Test UserCreate schema with valid data."""
    user = UserCreate(username=username, email=email, password=password)
    assert user.username == username
    assert user.email == email
    assert user.password == password


@pytest.mark.parametrize(
    ("username", "email", "password", "expected_error"),
    [
        ("ab", "test@example.com", "password123", "username"),  # too short
        ("a" * 51, "test@example.com", "password123", "username"),  # too long
        ("valid", "invalid-email", "password123", "email"),  # invalid email
        ("valid", "test@example.com", "short", "password"),  # password too short
        ("valid", "test@example.com", "a" * 129, "password"),  # password too long
    ],
)
def test_user_create_invalid(
    username: str, email: str, password: str, expected_error: str
) -> None:
    """Test UserCreate schema validation errors."""
    with pytest.raises(ValidationError):
        UserCreate(username=username, email=email, password=password)


@pytest.mark.parametrize(
    ("identifier", "password"),
    [
        ("username", "password123"),
        ("email@example.com", "password123"),
        ("", "password123"),
    ],
)
def test_login_request(identifier: str, password: str) -> None:
    """Test LoginRequest schema."""
    request = LoginRequest(identifier=identifier, password=password)
    assert request.identifier == identifier
    assert request.password == password


@pytest.mark.parametrize(
    ("access_token", "token_type"),
    [
        ("token123", "bearer"),
        ("another_token", "Bearer"),
        ("token", "bearer"),
    ],
)
def test_token_response(access_token: str, token_type: str) -> None:
    """Test TokenResponse schema."""
    response = TokenResponse(access_token=access_token, token_type=token_type)
    assert response.access_token == access_token
    assert response.token_type == token_type


def test_token_response_default_type() -> None:
    """Test TokenResponse default token_type."""
    response = TokenResponse(access_token="token123")
    assert response.token_type == "bearer"


@pytest.mark.parametrize(
    ("user_id", "username", "email", "profile_picture", "is_admin"),
    [
        (1, "alice", "alice@example.com", None, False),
        (2, "bob", "bob@example.com", "/path/to/pic.jpg", True),
        (3, "charlie", "charlie@example.com", "https://example.com/pic.png", False),
    ],
)
def test_user_read(
    user_id: int,
    username: str,
    email: str,
    profile_picture: str | None,
    is_admin: bool,
) -> None:
    """Test UserRead schema."""
    user = UserRead(
        id=user_id,
        username=username,
        email=email,
        profile_picture=profile_picture,
        is_admin=is_admin,
    )
    assert user.id == user_id
    assert user.username == username
    assert user.email == email
    assert user.profile_picture == profile_picture
    assert user.is_admin == is_admin


def test_login_response() -> None:
    """Test LoginResponse schema."""
    user = UserRead(id=1, username="alice", email="alice@example.com", is_admin=False)
    response = LoginResponse(access_token="token123", user=user)
    assert response.access_token == "token123"
    assert response.token_type == "bearer"
    assert response.user == user


@pytest.mark.parametrize(
    ("current_password", "new_password"),
    [
        ("oldpass", "newpass123"),
        ("current", "newpassword"),
    ],
)
def test_password_change_request(current_password: str, new_password: str) -> None:
    """Test PasswordChangeRequest schema."""
    request = PasswordChangeRequest(
        current_password=current_password, new_password=new_password
    )
    assert request.current_password == current_password
    assert request.new_password == new_password


@pytest.mark.parametrize(
    ("current_password", "new_password", "expected_error"),
    [
        ("", "newpass123", "current_password"),  # empty current
        ("oldpass", "short", "new_password"),  # new too short
        ("oldpass", "a" * 129, "new_password"),  # new too long
    ],
)
def test_password_change_request_invalid(
    current_password: str, new_password: str, expected_error: str
) -> None:
    """Test PasswordChangeRequest validation errors."""
    with pytest.raises(ValidationError):
        PasswordChangeRequest(
            current_password=current_password, new_password=new_password
        )


@pytest.mark.parametrize(
    "picture_path",
    [
        "/path/to/picture.jpg",
        "https://example.com/avatar.png",
        "relative/path/image.gif",
    ],
)
def test_profile_picture_update_request(picture_path: str) -> None:
    """Test ProfilePictureUpdateRequest schema."""
    request = ProfilePictureUpdateRequest(picture_path=picture_path)
    assert request.picture_path == picture_path


@pytest.mark.parametrize(
    ("picture_path", "expected_error"),
    [
        ("", "picture_path"),  # empty
        ("a" * 501, "picture_path"),  # too long
    ],
)
def test_profile_picture_update_request_invalid(
    picture_path: str, expected_error: str
) -> None:
    """Test ProfilePictureUpdateRequest validation errors."""
    with pytest.raises(ValidationError):
        ProfilePictureUpdateRequest(picture_path=picture_path)


@pytest.mark.parametrize(
    ("user_id", "username", "email", "profile_picture", "is_admin"),
    [
        (1, "alice", "alice@example.com", None, False),
        (2, "bob", "bob@example.com", "/path/to/pic.jpg", True),
    ],
)
def test_profile_read(
    user_id: int,
    username: str,
    email: str,
    profile_picture: str | None,
    is_admin: bool,
) -> None:
    """Test ProfileRead schema."""
    profile = ProfileRead(
        id=user_id,
        username=username,
        email=email,
        profile_picture=profile_picture,
        is_admin=is_admin,
    )
    assert profile.id == user_id
    assert profile.username == username
    assert profile.email == email
    assert profile.profile_picture == profile_picture
    assert profile.is_admin == is_admin


@pytest.mark.parametrize(
    ("valid", "token"),
    [
        (True, "token123"),
        (False, "invalid-token"),
    ],
)
def test_invite_validation_response(valid: bool, token: str) -> None:
    """Test InviteValidationResponse schema."""
    response = InviteValidationResponse(valid=valid, token=token)
    assert response.valid == valid
    assert response.token == token
