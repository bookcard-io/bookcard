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

"""Tests for selenium challenge detector module."""

from unittest.mock import MagicMock, patch

from bookcard.pvr.download_clients.direct_http.bypass.selenium.challenge_detector import (
    ChallengeDetectionService,
    CloudflareDetector,
    DdosGuardDetector,
)


class TestCloudflareDetector:
    """Test CloudflareDetector class."""

    def test_get_name(self) -> None:
        """Test get_name method."""
        detector = CloudflareDetector()
        assert detector.get_name() == "cloudflare"

    def test_detect_cloudflare_indicator_in_title(self, mock_driver: MagicMock) -> None:
        """Test detection with Cloudflare indicator in title."""
        mock_driver.get_title.return_value = "Just a moment..."
        mock_driver.get_text.return_value = "Page content"
        mock_driver.get_current_url.return_value = "https://example.com"

        detector = CloudflareDetector()
        result = detector.detect(mock_driver)
        assert result is True

    def test_detect_cloudflare_indicator_in_body(self, mock_driver: MagicMock) -> None:
        """Test detection with Cloudflare indicator in body."""
        mock_driver.get_title.return_value = "Page Title"
        mock_driver.get_text.return_value = "Verify you are human"
        mock_driver.get_current_url.return_value = "https://example.com"

        detector = CloudflareDetector()
        result = detector.detect(mock_driver)
        assert result is True

    def test_detect_cloudflare_url_pattern(self, mock_driver: MagicMock) -> None:
        """Test detection with Cloudflare URL pattern."""
        mock_driver.get_title.return_value = "Page Title"
        mock_driver.get_text.return_value = "Content"
        mock_driver.get_current_url.return_value = (
            "https://example.com/cdn-cgi/challenge"
        )

        detector = CloudflareDetector()
        result = detector.detect(mock_driver)
        assert result is True

    def test_detect_no_cloudflare(self, mock_driver: MagicMock) -> None:
        """Test detection when no Cloudflare challenge."""
        mock_driver.get_title.return_value = "Normal Page"
        mock_driver.get_text.return_value = "Normal content"
        mock_driver.get_current_url.return_value = "https://example.com"

        detector = CloudflareDetector()
        result = detector.detect(mock_driver)
        assert result is False

    def test_detect_exception(self, mock_driver: MagicMock) -> None:
        """Test detection with exception."""
        mock_driver.get_title.side_effect = RuntimeError("Error")
        detector = CloudflareDetector()
        result = detector.detect(mock_driver)
        assert result is False


class TestDdosGuardDetector:
    """Test DdosGuardDetector class."""

    def test_get_name(self) -> None:
        """Test get_name method."""
        detector = DdosGuardDetector()
        assert detector.get_name() == "ddos_guard"

    def test_detect_ddos_guard_indicator(self, mock_driver: MagicMock) -> None:
        """Test detection with DDoS-Guard indicator."""
        mock_driver.get_title.return_value = "DDoS-Guard"
        mock_driver.get_text.return_value = "Checking your browser"

        detector = DdosGuardDetector()
        result = detector.detect(mock_driver)
        assert result is True

    def test_detect_no_ddos_guard(self, mock_driver: MagicMock) -> None:
        """Test detection when no DDoS-Guard challenge."""
        mock_driver.get_title.return_value = "Normal Page"
        mock_driver.get_text.return_value = "Normal content"

        detector = DdosGuardDetector()
        result = detector.detect(mock_driver)
        assert result is False

    def test_detect_exception(self, mock_driver: MagicMock) -> None:
        """Test detection with exception."""
        mock_driver.get_title.side_effect = RuntimeError("Error")
        detector = DdosGuardDetector()
        result = detector.detect(mock_driver)
        assert result is False


class TestChallengeDetectionService:
    """Test ChallengeDetectionService class."""

    def test_init_default_detectors(self) -> None:
        """Test initialization with default detectors."""
        service = ChallengeDetectionService()
        assert len(service._detectors) == 2
        assert isinstance(service._detectors[0], DdosGuardDetector)
        assert isinstance(service._detectors[1], CloudflareDetector)

    def test_init_custom_detectors(self) -> None:
        """Test initialization with custom detectors."""
        detector1 = CloudflareDetector()
        detector2 = DdosGuardDetector()
        service = ChallengeDetectionService([detector1, detector2])
        assert service._detectors == [detector1, detector2]

    def test_detect_cloudflare(
        self, mock_driver: MagicMock, mock_challenge_detector: MagicMock
    ) -> None:
        """Test detect with Cloudflare challenge."""
        cloudflare_detector = CloudflareDetector()
        # Use patch to avoid implicit shadowing warning
        with patch.object(cloudflare_detector, "detect", return_value=True):
            service = ChallengeDetectionService([cloudflare_detector])
            result = service.detect(mock_driver)
            assert result == "cloudflare"

    def test_detect_ddos_guard(self, mock_driver: MagicMock) -> None:
        """Test detect with DDoS-Guard challenge."""
        ddos_detector = DdosGuardDetector()
        # Use patch to avoid implicit shadowing warning
        with patch.object(ddos_detector, "detect", return_value=True):
            service = ChallengeDetectionService([ddos_detector])
            result = service.detect(mock_driver)
            assert result == "ddos_guard"

    def test_detect_none(self, mock_driver: MagicMock) -> None:
        """Test detect with no challenge."""
        detector = CloudflareDetector()
        # Use patch to avoid implicit shadowing warning
        with patch.object(detector, "detect", return_value=False):
            service = ChallengeDetectionService([detector])
            result = service.detect(mock_driver)
            assert result == "none"
