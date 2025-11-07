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

"""User and auth-related API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRead(BaseModel):
    """Public-facing user representation.

    Attributes
    ----------
    id : int
        Primary identifier.
    username : str
        Unique username.
    email : EmailStr
        Email address.
    profile_picture : str | None
        Optional path to user's profile picture.
    is_admin : bool
        Whether the user has admin privileges.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    profile_picture: str | None = None
    is_admin: bool


class UserCreate(BaseModel):
    """Payload to create a new user account."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Login by username or email and password."""

    identifier: str
    password: str


class TokenResponse(BaseModel):
    """Bearer token response."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105 OAuth token type identifier, not a password


class LoginResponse(BaseModel):
    """Login response containing access token and user data."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105 OAuth token type identifier, not a password
    user: UserRead


class PasswordChangeRequest(BaseModel):
    """Request to change user password."""

    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class ProfilePictureUpdateRequest(BaseModel):
    """Request to update profile picture."""

    picture_path: str = Field(min_length=1, max_length=500)


class ProfileRead(BaseModel):
    """Extended user profile with profile picture."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    profile_picture: str | None
    is_admin: bool


class InviteValidationResponse(BaseModel):
    """Response for invite token validation."""

    valid: bool
    token: str
