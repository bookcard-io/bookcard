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

"""Tests for bypass decorators module."""

import pytest

from bookcard.pvr.download_clients.direct_http.bypass.decorators import (
    log_bypass_errors,
)


class TestLogBypassErrors:
    """Test log_bypass_errors decorator."""

    def test_decorator_success(self) -> None:
        """Test decorator with successful function."""

        @log_bypass_errors
        def test_func(url: str) -> str | None:
            return "success"

        result = test_func("https://example.com")
        # After fix, decorator should return the result
        assert result == "success"

    def test_decorator_function_with_url_arg(self) -> None:
        """Test decorator with function taking url as first arg."""

        @log_bypass_errors
        def test_func(url: str) -> str | None:
            return "result"

        result = test_func("https://example.com")
        # After fix, decorator should return the result
        assert result == "result"

    def test_decorator_method_with_url_arg(self) -> None:
        """Test decorator with method taking url as second arg."""

        class TestClass:
            @log_bypass_errors
            def test_method(self, url: str) -> str | None:
                return "result"

        obj = TestClass()
        result = obj.test_method("https://example.com")
        # After fix, decorator should return the result
        assert result == "result"

    def test_decorator_returns_none_on_failure(self) -> None:
        """Test decorator returns None on failure."""

        @log_bypass_errors
        def test_func(url: str) -> str | None:
            return None

        result = test_func("https://example.com")
        assert result is None

    @pytest.mark.parametrize(
        "exception",
        [
            TimeoutError("Timeout"),
            RuntimeError("Runtime error"),
            AttributeError("Attribute error"),
            KeyError("Key error"),
            TypeError("Type error"),
            ValueError("Value error"),
        ],
    )
    def test_decorator_handles_exceptions(self, exception: Exception) -> None:
        """Test decorator handles various exceptions."""

        @log_bypass_errors
        def test_func(url: str) -> str | None:
            raise exception

        result = test_func("https://example.com")
        assert result is None

    def test_decorator_with_kwargs(self) -> None:
        """Test decorator with keyword arguments."""

        @log_bypass_errors
        def test_func(url: str, param: str = "default") -> str | None:
            return f"result-{param}"

        result = test_func(url="https://example.com", param="test")
        # After fix, decorator should return the result
        assert result == "result-test"

    def test_decorator_preserves_function_name(self) -> None:
        """Test that decorator preserves function name."""

        @log_bypass_errors
        def test_func(url: str) -> str | None:
            return "result"

        assert test_func.__name__ == "test_func"
