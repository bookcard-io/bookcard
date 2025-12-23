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

"""Tests for authentication utility functions."""

import base64

import pytest

from bookcard.pvr.utils.auth import build_basic_auth_header


class TestBuildBasicAuthHeader:
    """Test build_basic_auth_header function."""

    def test_build_basic_auth_header_with_credentials(self) -> None:
        """Test build_basic_auth_header with username and password."""
        result = build_basic_auth_header("user", "pass")
        assert result is not None
        assert result.startswith("Basic ")
        # Decode and verify
        encoded = result.split(" ")[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert decoded == "user:pass"

    @pytest.mark.parametrize(
        ("username", "password", "expected"),
        [
            ("user", "pass", "Basic dXNlcjpwYXNz"),
            ("admin", "secret123", "Basic YWRtaW46c2VjcmV0MTIz"),
            (
                "test@example.com",
                "p@ssw0rd!",
                "Basic dGVzdEBleGFtcGxlLmNvbTpwQHNzdzByZCE=",
            ),
            ("", "", None),  # Empty strings are falsy
        ],
    )
    def test_build_basic_auth_header_various_credentials(
        self, username: str, password: str, expected: str | None
    ) -> None:
        """Test build_basic_auth_header with various credentials."""
        result = build_basic_auth_header(username, password)
        if expected is None:
            assert result is None
        else:
            assert result == expected

    def test_build_basic_auth_header_none_username(self) -> None:
        """Test build_basic_auth_header with None username."""
        result = build_basic_auth_header(None, "pass")
        assert result is None

    def test_build_basic_auth_header_none_password(self) -> None:
        """Test build_basic_auth_header with None password."""
        result = build_basic_auth_header("user", None)
        assert result is None

    def test_build_basic_auth_header_both_none(self) -> None:
        """Test build_basic_auth_header with both None."""
        result = build_basic_auth_header(None, None)
        assert result is None

    def test_build_basic_auth_header_empty_strings(self) -> None:
        """Test build_basic_auth_header with empty strings."""
        # Empty strings are falsy, so should return None
        result = build_basic_auth_header("", "")
        assert result is None

    def test_build_basic_auth_header_username_empty(self) -> None:
        """Test build_basic_auth_header with empty username."""
        result = build_basic_auth_header("", "pass")
        assert result is None

    def test_build_basic_auth_header_password_empty(self) -> None:
        """Test build_basic_auth_header with empty password."""
        result = build_basic_auth_header("user", "")
        assert result is None
