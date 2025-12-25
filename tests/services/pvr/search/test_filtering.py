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

"""Tests for filtering components."""

from datetime import UTC, datetime, timedelta

import pytest

from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.filtering import (
    AgeFilter,
    CompositeFilter,
    FormatFilter,
    IndexerFilter,
    IndexerSearchFilter,
    KeywordFilter,
    SeederLeecherFilter,
    SizeRangeFilter,
)


class TestFormatFilter:
    """Test FormatFilter."""

    @pytest.mark.parametrize(
        ("formats", "quality", "expected"),
        [
            (["epub"], "epub", True),
            (["epub"], "EPUB", True),
            (["epub", "pdf"], "epub", True),
            (["epub", "pdf"], "pdf", True),
            (["epub"], "mobi", False),
            (["epub"], None, False),
            (["epub", "pdf"], "mobi", False),
        ],
    )
    def test_format_filter(
        self, formats: list[str], quality: str | None, expected: bool
    ) -> None:
        """Test format filter matching.

        Parameters
        ----------
        formats : list[str]
            Allowed formats.
        quality : str | None
            Release quality.
        expected : bool
            Expected match result.
        """
        filter_obj = FormatFilter(formats)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            quality=quality,
        )

        assert filter_obj.matches(release) == expected


class TestSizeRangeFilter:
    """Test SizeRangeFilter."""

    @pytest.mark.parametrize(
        ("min_size", "max_size", "size_bytes", "expected"),
        [
            (None, None, None, True),
            (None, None, 1000, True),
            (1000, None, 2000, True),
            (1000, None, 500, False),
            (None, 5000, 3000, True),
            (None, 5000, 6000, False),
            (1000, 5000, 3000, True),
            (1000, 5000, 500, False),
            (1000, 5000, 6000, False),
        ],
    )
    def test_size_range_filter(
        self,
        min_size: int | None,
        max_size: int | None,
        size_bytes: int | None,
        expected: bool,
    ) -> None:
        """Test size range filter.

        Parameters
        ----------
        min_size : int | None
            Minimum size.
        max_size : int | None
            Maximum size.
        size_bytes : int | None
            Release size.
        expected : bool
            Expected match result.
        """
        filter_obj = SizeRangeFilter(min_size, max_size)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            size_bytes=size_bytes,
        )

        assert filter_obj.matches(release) == expected


class TestSeederLeecherFilter:
    """Test SeederLeecherFilter."""

    @pytest.mark.parametrize(
        ("min_seeders", "min_leechers", "seeders", "leechers", "expected"),
        [
            (None, None, None, None, True),
            (None, None, 10, 5, True),
            (5, None, 10, 5, True),
            (5, None, 3, 5, False),
            (None, 3, 10, 5, True),
            (None, 3, 10, 1, False),
            (5, 3, 10, 5, True),
            (5, 3, 3, 5, False),
            (5, 3, 10, 1, False),
        ],
    )
    def test_seeder_leecher_filter(
        self,
        min_seeders: int | None,
        min_leechers: int | None,
        seeders: int | None,
        leechers: int | None,
        expected: bool,
    ) -> None:
        """Test seeder/leecher filter.

        Parameters
        ----------
        min_seeders : int | None
            Minimum seeders.
        min_leechers : int | None
            Minimum leechers.
        seeders : int | None
            Release seeders.
        leechers : int | None
            Release leechers.
        expected : bool
            Expected match result.
        """
        filter_obj = SeederLeecherFilter(min_seeders, min_leechers)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            seeders=seeders,
            leechers=leechers,
        )

        assert filter_obj.matches(release) == expected


class TestIndexerFilter:
    """Test IndexerFilter."""

    @pytest.mark.parametrize(
        ("indexer_ids", "release_indexer_id", "expected"),
        [
            ([1, 2, 3], 1, True),
            ([1, 2, 3], 2, True),
            ([1, 2, 3], 4, False),
            ([1, 2, 3], None, False),
        ],
    )
    def test_indexer_filter(
        self, indexer_ids: list[int], release_indexer_id: int | None, expected: bool
    ) -> None:
        """Test indexer filter.

        Parameters
        ----------
        indexer_ids : list[int]
            Allowed indexer IDs.
        release_indexer_id : int | None
            Release indexer ID.
        expected : bool
            Expected match result.
        """
        filter_obj = IndexerFilter(indexer_ids)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            indexer_id=release_indexer_id,
        )

        assert filter_obj.matches(release) == expected


class TestAgeFilter:
    """Test AgeFilter."""

    @pytest.mark.parametrize(
        ("max_age_days", "age_days", "expected"),
        [
            (30, 0, True),
            (30, 15, True),
            (30, 30, True),
            (30, 31, False),
            (30, 365, False),
            (7, 7, True),
            (7, 8, False),
        ],
    )
    def test_age_filter(self, max_age_days: int, age_days: int, expected: bool) -> None:
        """Test age filter.

        Parameters
        ----------
        max_age_days : int
            Maximum age in days.
        age_days : int
            Release age in days.
        expected : bool
            Expected match result.
        """
        filter_obj = AgeFilter(max_age_days)
        # For boundary tests, create publish_date slightly before the exact boundary
        # to account for time passing between creation and check
        if age_days == max_age_days:
            # For exact boundary, use slightly less than max_age_days to ensure it passes
            publish_date = datetime.now(UTC) - timedelta(
                days=age_days, hours=-1
            )  # 1 hour before boundary
        else:
            publish_date = datetime.now(UTC) - timedelta(days=age_days)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            publish_date=publish_date,
        )

        assert filter_obj.matches(release) == expected

    def test_age_filter_no_date(self) -> None:
        """Test age filter with no publish date."""
        filter_obj = AgeFilter(30)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            publish_date=None,
        )

        assert filter_obj.matches(release) is True


class TestKeywordFilter:
    """Test KeywordFilter."""

    @pytest.mark.parametrize(
        ("exclude_keywords", "require_keywords", "title", "author", "expected"),
        [
            ([], [], "Test Book", "Author", True),
            (["spam"], [], "Test Book", "Author", True),
            (["spam"], [], "Spam Book", "Author", False),
            ([], ["test"], "Test Book", "Author", True),
            ([], ["test"], "Other Book", "Author", False),
            (["spam"], ["test"], "Test Book", "Author", True),
            (["spam"], ["test"], "Spam Book", "Author", False),
            (["spam"], ["test"], "Other Book", "Author", False),
        ],
    )
    def test_keyword_filter(
        self,
        exclude_keywords: list[str],
        require_keywords: list[str],
        title: str,
        author: str | None,
        expected: bool,
    ) -> None:
        """Test keyword filter.

        Parameters
        ----------
        exclude_keywords : list[str]
            Keywords to exclude.
        require_keywords : list[str]
            Keywords to require.
        title : str
            Release title.
        author : str | None
            Release author.
        expected : bool
            Expected match result.
        """
        filter_obj = KeywordFilter(exclude_keywords, require_keywords)
        release = ReleaseInfo(
            title=title,
            download_url="https://example.com/book.torrent",
            author=author,
        )

        assert filter_obj.matches(release) == expected


class TestCompositeFilter:
    """Test CompositeFilter."""

    def test_composite_filter_and(self, sample_release: ReleaseInfo) -> None:
        """Test composite filter with AND operator.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release.
        """
        format_filter = FormatFilter(["epub"])
        size_filter = SizeRangeFilter(min_size=1000, max_size=5000)

        composite = CompositeFilter([format_filter, size_filter], operator="AND")

        # Release must match both
        sample_release.quality = "epub"
        sample_release.size_bytes = 3000
        assert composite.matches(sample_release) is True

        # Fails if one doesn't match
        sample_release.quality = "pdf"
        assert composite.matches(sample_release) is False

    def test_composite_filter_or(self, sample_release: ReleaseInfo) -> None:
        """Test composite filter with OR operator.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release.
        """
        format_filter = FormatFilter(["epub"])
        size_filter = SizeRangeFilter(min_size=10000)

        composite = CompositeFilter([format_filter, size_filter], operator="OR")

        # Matches if either matches
        sample_release.quality = "epub"
        sample_release.size_bytes = 1000
        assert composite.matches(sample_release) is True

        sample_release.quality = "pdf"
        sample_release.size_bytes = 20000
        assert composite.matches(sample_release) is True

        # Fails if neither matches
        sample_release.quality = "pdf"
        sample_release.size_bytes = 1000
        assert composite.matches(sample_release) is False

    def test_composite_filter_empty(self, sample_release: ReleaseInfo) -> None:
        """Test composite filter with no filters.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release.
        """
        composite = CompositeFilter([], operator="AND")
        assert composite.matches(sample_release) is True


class TestIndexerSearchFilter:
    """Test IndexerSearchFilter convenience class."""

    def test_no_filters(self, sample_release: ReleaseInfo) -> None:
        """Test filter with no criteria.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release.
        """
        filter_obj = IndexerSearchFilter()
        assert filter_obj.matches(sample_release) is True

    def test_format_filter(self, sample_release: ReleaseInfo) -> None:
        """Test format filtering.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release.
        """
        filter_obj = IndexerSearchFilter(formats=["epub"])
        sample_release.quality = "epub"
        assert filter_obj.matches(sample_release) is True

        sample_release.quality = "pdf"
        assert filter_obj.matches(sample_release) is False

    def test_size_filter(self, sample_release: ReleaseInfo) -> None:
        """Test size filtering.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release.
        """
        filter_obj = IndexerSearchFilter(min_size_bytes=1000, max_size_bytes=5000)
        sample_release.size_bytes = 3000
        assert filter_obj.matches(sample_release) is True

        sample_release.size_bytes = 6000
        assert filter_obj.matches(sample_release) is False

    def test_combined_filters(self, sample_release: ReleaseInfo) -> None:
        """Test multiple filters combined.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release.
        """
        filter_obj = IndexerSearchFilter(
            formats=["epub"],
            min_size_bytes=1000,
            min_seeders=10,
            indexer_ids=[1, 2],
            max_age_days=30,
            exclude_keywords=["spam"],
            require_keywords=["test"],
        )

        # Set up release to match all criteria
        sample_release.quality = "epub"
        sample_release.size_bytes = 3000
        sample_release.seeders = 20
        sample_release.indexer_id = 1
        sample_release.publish_date = datetime.now(UTC) - timedelta(days=15)
        sample_release.title = "Test Book"
        sample_release.author = "Author"

        assert filter_obj.matches(sample_release) is True

        # Fail on format
        sample_release.quality = "pdf"
        assert filter_obj.matches(sample_release) is False
