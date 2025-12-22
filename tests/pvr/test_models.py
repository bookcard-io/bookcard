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

"""Tests for PVR models (ReleaseInfo)."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from bookcard.pvr.models import ReleaseInfo


class TestReleaseInfo:
    """Test ReleaseInfo Pydantic model."""

    def test_release_info_minimal(self) -> None:
        """Test ReleaseInfo with minimal required fields."""
        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/torrent.torrent",
        )

        assert release.title == "Test Book"
        assert release.download_url == "https://example.com/torrent.torrent"
        assert release.indexer_id is None
        assert release.size_bytes is None
        assert release.publish_date is None
        assert release.seeders is None
        assert release.leechers is None
        assert release.quality is None
        assert release.author is None
        assert release.isbn is None
        assert release.description is None
        assert release.category is None
        assert release.additional_info is None

    def test_release_info_complete(self) -> None:
        """Test ReleaseInfo with all fields."""
        publish_date = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        release = ReleaseInfo(
            indexer_id=1,
            title="Test Book Title",
            download_url="magnet:?xt=urn:btih:test",
            size_bytes=1024000,
            publish_date=publish_date,
            seeders=100,
            leechers=10,
            quality="epub",
            author="Test Author",
            isbn="9781234567890",
            description="A test book description",
            category="Books",
            additional_info={"source": "test", "rating": 4.5},
        )

        assert release.indexer_id == 1
        assert release.title == "Test Book Title"
        assert release.download_url == "magnet:?xt=urn:btih:test"
        assert release.size_bytes == 1024000
        assert release.publish_date == publish_date
        assert release.seeders == 100
        assert release.leechers == 10
        assert release.quality == "epub"
        assert release.author == "Test Author"
        assert release.isbn == "9781234567890"
        assert release.description == "A test book description"
        assert release.category == "Books"
        assert release.additional_info == {"source": "test", "rating": 4.5}

    @pytest.mark.parametrize(
        ("seeders", "leechers"),
        [
            (0, 0),
            (100, 50),
            (1000, 200),
            (None, None),
            (0, None),
            (None, 0),
        ],
    )
    def test_release_info_seeders_leechers(
        self, seeders: int | None, leechers: int | None
    ) -> None:
        """Test ReleaseInfo with various seeders/leechers values."""
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/torrent.torrent",
            seeders=seeders,
            leechers=leechers,
        )

        assert release.seeders == seeders
        assert release.leechers == leechers

    @pytest.mark.parametrize(
        ("seeders", "should_raise"),
        [
            (-1, True),
            (-100, True),
            (0, False),
            (100, False),
        ],
    )
    def test_release_info_seeders_validation(
        self, seeders: int, should_raise: bool
    ) -> None:
        """Test ReleaseInfo seeders validation (must be >= 0)."""
        if should_raise:
            with pytest.raises(ValidationError) as exc_info:
                ReleaseInfo(
                    title="Test",
                    download_url="https://example.com/torrent.torrent",
                    seeders=seeders,
                )
            assert "seeders" in str(exc_info.value).lower()
        else:
            release = ReleaseInfo(
                title="Test",
                download_url="https://example.com/torrent.torrent",
                seeders=seeders,
            )
            assert release.seeders == seeders

    @pytest.mark.parametrize(
        ("leechers", "should_raise"),
        [
            (-1, True),
            (-100, True),
            (0, False),
            (100, False),
        ],
    )
    def test_release_info_leechers_validation(
        self, leechers: int, should_raise: bool
    ) -> None:
        """Test ReleaseInfo leechers validation (must be >= 0)."""
        if should_raise:
            with pytest.raises(ValidationError) as exc_info:
                ReleaseInfo(
                    title="Test",
                    download_url="https://example.com/torrent.torrent",
                    leechers=leechers,
                )
            assert "leechers" in str(exc_info.value).lower()
        else:
            release = ReleaseInfo(
                title="Test",
                download_url="https://example.com/torrent.torrent",
                leechers=leechers,
            )
            assert release.leechers == leechers

    def test_release_info_missing_required_fields(self) -> None:
        """Test ReleaseInfo validation with missing required fields."""
        # Missing title
        with pytest.raises(ValidationError) as exc_info:
            ReleaseInfo(download_url="https://example.com/torrent.torrent")
        assert "title" in str(exc_info.value).lower()

        # Missing download_url
        with pytest.raises(ValidationError) as exc_info:
            ReleaseInfo(title="Test Book")
        assert "download_url" in str(exc_info.value).lower()

    def test_release_info_additional_info_types(self) -> None:
        """Test ReleaseInfo additional_info with various value types."""
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/torrent.torrent",
            additional_info={
                "string": "value",
                "int": 42,
                "float": 3.14,
                "none": None,
            },
        )

        assert release.additional_info == {
            "string": "value",
            "int": 42,
            "float": 3.14,
            "none": None,
        }
