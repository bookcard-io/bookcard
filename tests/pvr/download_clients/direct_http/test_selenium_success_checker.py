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

"""Tests for selenium success checker module."""

from unittest.mock import MagicMock, patch

from bookcard.pvr.download_clients.direct_http.bypass.selenium.success_checker import (
    SuccessChecker,
)


class TestSuccessChecker:
    """Test SuccessChecker class."""

    def test_init(self) -> None:
        """Test initialization."""
        checker = SuccessChecker()
        assert checker is not None

    def test_is_bypassed_long_content(self, mock_driver: MagicMock) -> None:
        """Test is_bypassed with long content."""
        mock_driver.get_title.return_value = "Page Title"
        mock_driver.get_text.return_value = "x" * 200000  # Long content
        mock_driver.get_current_url.return_value = "https://example.com"

        checker = SuccessChecker()
        result = checker.is_bypassed(mock_driver)
        assert result is True

    def test_is_bypassed_with_emojis(self, mock_driver: MagicMock) -> None:
        """Test is_bypassed with emojis."""
        mock_driver.get_title.return_value = "Page Title"
        mock_driver.get_text.return_value = "😀😃😄😁😆😅😂🤣"  # Multiple emojis
        mock_driver.get_current_url.return_value = "https://example.com"

        checker = SuccessChecker()
        result = checker.is_bypassed(mock_driver, escape_emojis=True)
        assert result is True

    def test_is_bypassed_with_protection_indicators(
        self, mock_driver: MagicMock
    ) -> None:
        """Test is_bypassed with protection indicators."""
        mock_driver.get_title.return_value = "Just a moment"
        mock_driver.get_text.return_value = "Verifying you are human"
        mock_driver.get_current_url.return_value = "https://example.com"

        checker = SuccessChecker()
        result = checker.is_bypassed(mock_driver)
        assert result is False

    def test_is_bypassed_with_cloudflare_patterns(self, mock_driver: MagicMock) -> None:
        """Test is_bypassed with Cloudflare patterns."""
        mock_driver.get_title.return_value = "Page Title"
        mock_driver.get_text.return_value = "Content with cf- pattern"
        mock_driver.get_current_url.return_value = (
            "https://example.com/cdn-cgi/challenge"
        )

        checker = SuccessChecker()
        result = checker.is_bypassed(mock_driver)
        assert result is False

    def test_is_bypassed_short_content(self, mock_driver: MagicMock) -> None:
        """Test is_bypassed with short content."""
        mock_driver.get_title.return_value = "Page Title"
        mock_driver.get_text.return_value = "Short"  # Too short
        mock_driver.get_current_url.return_value = "https://example.com"

        checker = SuccessChecker()
        result = checker.is_bypassed(mock_driver)
        assert result is False

    def test_is_bypassed_success(self, mock_driver: MagicMock) -> None:
        """Test is_bypassed with successful bypass."""
        # Need content long enough (MIN_BODY_LENGTH = 50) and no protection indicators
        # Also need to avoid Cloudflare patterns in body or URL
        mock_driver.get_title.return_value = "Page Title"
        # Use content that's long enough but doesn't trigger any protection checks
        mock_driver.get_text.return_value = (
            "Normal page content " * 10
        )  # ~200 chars, no indicators
        mock_driver.get_current_url.return_value = (
            "https://example.com"  # No cf- or cdn-cgi
        )

        checker = SuccessChecker()
        result = checker.is_bypassed(mock_driver)
        assert result is True

    def test_is_bypassed_exception(self, mock_driver: MagicMock) -> None:
        """Test is_bypassed with exception."""
        mock_driver.get_title.side_effect = RuntimeError("Error")
        checker = SuccessChecker()
        result = checker.is_bypassed(mock_driver)
        assert result is False

    def test_is_bypassed_emoji_check_error(self, mock_driver: MagicMock) -> None:
        """Test is_bypassed when emoji check fails."""
        mock_driver.get_title.return_value = "Page Title"
        mock_driver.get_text.return_value = "Content"
        mock_driver.get_current_url.return_value = "https://example.com"

        checker = SuccessChecker()
        with patch("emoji.emoji_list", side_effect=AttributeError("Error")):
            result = checker.is_bypassed(mock_driver, escape_emojis=True)
            # Should continue and check other conditions
            assert isinstance(result, bool)
