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

"""Tests for Anna's Archive countdown module."""

from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from bookcard.pvr.download_clients.direct_http.anna.countdown import CountdownHandler


class TestCountdownHandler:
    """Test CountdownHandler class."""

    def test_init(self, mock_time_provider: MagicMock) -> None:
        """Test initialization."""
        handler = CountdownHandler(mock_time_provider, 300)
        assert handler._time == mock_time_provider
        assert handler._max_seconds == 300

    def test_handle_countdown_no_countdown(self, mock_time_provider: MagicMock) -> None:
        """Test handle_countdown with no countdown."""
        handler = CountdownHandler(mock_time_provider, 300)
        soup = BeautifulSoup("<html><body>No countdown</body></html>", "html.parser")
        result = handler.handle_countdown(
            soup, "<html><body>No countdown</body></html>"
        )
        assert result == 0

    def test_handle_countdown_js_partner_countdown(
        self, mock_time_provider: MagicMock
    ) -> None:
        """Test handle_countdown with js-partner-countdown span."""
        handler = CountdownHandler(mock_time_provider, 300)
        html = '<html><body><span class="js-partner-countdown">5</span></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        with patch.object(mock_time_provider, "sleep"):
            result = handler.handle_countdown(soup, html)
            assert result == 5

    def test_handle_countdown_timer_class(self, mock_time_provider: MagicMock) -> None:
        """Test handle_countdown with timer class."""
        handler = CountdownHandler(mock_time_provider, 300)
        html = '<html><body><div class="timer">10</div></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        with patch.object(mock_time_provider, "sleep"):
            result = handler.handle_countdown(soup, html)
            assert result == 10

    def test_handle_countdown_data_attribute(
        self, mock_time_provider: MagicMock
    ) -> None:
        """Test handle_countdown with data-countdown attribute."""
        handler = CountdownHandler(mock_time_provider, 300)
        html = '<html><body><div data-countdown="15"></div></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        with patch.object(mock_time_provider, "sleep"):
            result = handler.handle_countdown(soup, html)
            assert result == 15

    def test_handle_countdown_regex_pattern(
        self, mock_time_provider: MagicMock
    ) -> None:
        """Test handle_countdown with regex pattern."""
        handler = CountdownHandler(mock_time_provider, 300)
        html = "<html><body><script>var countdown = 20;</script></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        with patch.object(mock_time_provider, "sleep"):
            result = handler.handle_countdown(soup, html)
            assert result == 20

    def test_handle_countdown_too_long(self, mock_time_provider: MagicMock) -> None:
        """Test handle_countdown with countdown exceeding max."""
        handler = CountdownHandler(mock_time_provider, 300)
        html = '<html><body><span class="js-partner-countdown">600</span></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        with pytest.raises(TimeoutError, match="Countdown too long"):
            handler.handle_countdown(soup, html)

    def test_handle_countdown_valid_seconds(
        self, mock_time_provider: MagicMock
    ) -> None:
        """Test handle_countdown with valid seconds."""
        handler = CountdownHandler(mock_time_provider, 300)
        html = '<html><body><span class="js-partner-countdown">30</span></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        with patch.object(mock_time_provider, "sleep"):
            result = handler.handle_countdown(soup, html)
            assert result == 30
            mock_time_provider.sleep.assert_called_once_with(31)  # seconds + 1
