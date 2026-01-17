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

"""Tests for Direct HTTP settings module."""

import tempfile
from pathlib import Path

import pytest

from bookcard.pvr.download_clients.direct_http.settings import (
    DirectHttpSettings,
    DownloadConstants,
)


class TestDirectHttpSettings:
    """Test DirectHttpSettings class."""

    def test_init_defaults(self) -> None:
        """Test initialization with default values."""
        settings = DirectHttpSettings(
            host="localhost",
            port=8080,
        )
        assert settings.host == "localhost"
        assert settings.port == 8080
        assert settings.aa_donator_key is None
        assert settings.flaresolverr_url == "http://flaresolverr:8191"
        assert settings.flaresolverr_path == "/v1"
        assert settings.flaresolverr_timeout == 60000
        assert settings.use_seleniumbase is True

    def test_init_with_all_params(self) -> None:
        """Test initialization with all parameters."""
        settings = DirectHttpSettings(
            host="localhost",
            port=8080,
            aa_donator_key="test-key",
            flaresolverr_url="http://custom:8191",
            flaresolverr_path="/v2",
            flaresolverr_timeout=120000,
            use_seleniumbase=False,
        )
        assert settings.aa_donator_key == "test-key"
        assert settings.flaresolverr_url == "http://custom:8191"
        assert settings.flaresolverr_path == "/v2"
        assert settings.flaresolverr_timeout == 120000
        assert settings.use_seleniumbase is False

    @pytest.mark.parametrize(
        "timeout",
        [1000, 150000, 300000],
    )
    def test_flaresolverr_timeout_valid(self, timeout: int) -> None:
        """Test valid flaresolverr timeout values."""
        settings = DirectHttpSettings(
            host="localhost",
            port=8080,
            flaresolverr_timeout=timeout,
        )
        assert settings.flaresolverr_timeout == timeout

    @pytest.mark.parametrize(
        "timeout",
        [999, 300001],
    )
    def test_flaresolverr_timeout_invalid(self, timeout: int) -> None:
        """Test invalid flaresolverr timeout values."""
        with pytest.raises(Exception):  # noqa: B017, PT011
            DirectHttpSettings(
                host="localhost",
                port=8080,
                flaresolverr_timeout=timeout,
            )


class TestDownloadConstants:
    """Test DownloadConstants class."""

    def test_retention_seconds(self) -> None:
        """Test RETENTION_SECONDS constant."""
        assert DownloadConstants.RETENTION_SECONDS == 86400

    def test_download_chunk_size(self) -> None:
        """Test DOWNLOAD_CHUNK_SIZE constant."""
        assert DownloadConstants.DOWNLOAD_CHUNK_SIZE == 8192

    def test_max_countdown_seconds(self) -> None:
        """Test MAX_COUNTDOWN_SECONDS constant."""
        assert DownloadConstants.MAX_COUNTDOWN_SECONDS == 600

    def test_default_temp_dir(self) -> None:
        """Test DEFAULT_TEMP_DIR constant."""
        assert (
            str(Path(tempfile.gettempdir()) / "bookcard_downloads")
            == DownloadConstants.DEFAULT_TEMP_DIR
        )

    def test_update_interval(self) -> None:
        """Test UPDATE_INTERVAL constant."""
        assert DownloadConstants.UPDATE_INTERVAL == 0.5
