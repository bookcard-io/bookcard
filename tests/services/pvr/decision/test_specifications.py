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

"""Tests for download decision specifications."""

from datetime import UTC, datetime, timedelta

import pytest

from bookcard.models.pvr import DownloadRejectionReason, RejectionType
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.decision.preferences import DownloadDecisionPreferences
from bookcard.services.pvr.decision.specifications import (
    AgeSpecification,
    AuthorMatchSpecification,
    BlocklistSpecification,
    FormatSpecification,
    IndexerSpecification,
    ISBNMatchSpecification,
    KeywordSpecification,
    MetadataSpecification,
    SeederSpecification,
    SizeSpecification,
    TitleMatchSpecification,
)


class TestFormatSpecification:
    """Test FormatSpecification."""

    @pytest.mark.parametrize(
        ("formats", "quality", "expected_satisfied", "expected_reason"),
        [
            (None, "epub", True, None),
            (None, None, True, None),
            (["epub"], "epub", True, None),
            (["epub"], "EPUB", True, None),  # Case insensitive
            (["epub", "pdf"], "epub", True, None),
            (["epub", "pdf"], "pdf", True, None),
            (["epub"], "mobi", False, DownloadRejectionReason.WRONG_FORMAT),
            (["epub"], None, False, DownloadRejectionReason.WRONG_FORMAT),
            (["epub", "pdf"], "mobi", False, DownloadRejectionReason.WRONG_FORMAT),
        ],
    )
    def test_format_specification(
        self,
        formats: list[str] | None,
        quality: str | None,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test format specification matching.

        Parameters
        ----------
        formats : list[str] | None
            Preferred formats.
        quality : str | None
            Release quality.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = FormatSpecification()
        prefs = DownloadDecisionPreferences(preferred_formats=formats)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            quality=quality,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
            assert rejection.type == RejectionType.PERMANENT
        else:
            assert rejection is None


class TestSizeSpecification:
    """Test SizeSpecification."""

    @pytest.mark.parametrize(
        ("min_size", "max_size", "size_bytes", "expected_satisfied", "expected_reason"),
        [
            (None, None, None, True, None),
            (None, None, 1000, True, None),
            (1000, None, 2000, True, None),
            (1000, None, 500, False, DownloadRejectionReason.BELOW_MINIMUM_SIZE),
            (None, 5000, 3000, True, None),
            (None, 5000, 6000, False, DownloadRejectionReason.ABOVE_MAXIMUM_SIZE),
            (1000, 5000, 3000, True, None),
            (1000, 5000, 500, False, DownloadRejectionReason.BELOW_MINIMUM_SIZE),
            (1000, 5000, 6000, False, DownloadRejectionReason.ABOVE_MAXIMUM_SIZE),
        ],
    )
    def test_size_specification(
        self,
        min_size: int | None,
        max_size: int | None,
        size_bytes: int | None,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test size specification matching.

        Parameters
        ----------
        min_size : int | None
            Minimum size in bytes.
        max_size : int | None
            Maximum size in bytes.
        size_bytes : int | None
            Release size in bytes.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = SizeSpecification()
        prefs = DownloadDecisionPreferences(
            min_size_bytes=min_size, max_size_bytes=max_size
        )
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            size_bytes=size_bytes,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
            assert rejection.type == RejectionType.PERMANENT
        else:
            assert rejection is None


class TestSeederSpecification:
    """Test SeederSpecification."""

    @pytest.mark.parametrize(
        ("min_seeders", "seeders", "expected_satisfied", "expected_reason"),
        [
            (None, None, True, None),
            (None, 5, True, None),
            (10, None, True, None),  # Usenet releases don't have seeders
            (10, 15, True, None),
            (10, 10, True, None),
            (10, 5, False, DownloadRejectionReason.INSUFFICIENT_SEEDERS),
            (10, 0, False, DownloadRejectionReason.INSUFFICIENT_SEEDERS),
        ],
    )
    def test_seeder_specification(
        self,
        min_seeders: int | None,
        seeders: int | None,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test seeder specification matching.

        Parameters
        ----------
        min_seeders : int | None
            Minimum seeders required.
        seeders : int | None
            Release seeders count.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = SeederSpecification()
        prefs = DownloadDecisionPreferences(min_seeders=min_seeders)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            seeders=seeders,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
            assert rejection.type == RejectionType.TEMPORARY  # May improve over time
        else:
            assert rejection is None


class TestAgeSpecification:
    """Test AgeSpecification."""

    @pytest.mark.parametrize(
        (
            "max_age_days",
            "min_age_days",
            "publish_date",
            "expected_satisfied",
            "expected_reason",
        ),
        [
            (None, None, None, True, None),
            (None, None, datetime(2024, 1, 1, tzinfo=UTC), True, None),
            # 180 days ago - within 365 day limit
            (365, None, "180_days_ago", True, None),
            # 400 days ago - exceeds 365 day limit
            (365, None, "400_days_ago", False, DownloadRejectionReason.TOO_OLD),
            # Today - too new for 7 day delay
            (None, 7, "today", False, DownloadRejectionReason.TOO_NEW),
            # 10 days ago - old enough for 7 day delay
            (None, 7, "10_days_ago", True, None),
            # 200 days ago - within 365 limit but old enough for 7 day delay
            (365, 7, "200_days_ago", True, None),
        ],
    )
    def test_age_specification(
        self,
        max_age_days: int | None,
        min_age_days: int | None,
        publish_date: datetime | str | None,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test age specification matching.

        Parameters
        ----------
        max_age_days : int | None
            Maximum age in days.
        min_age_days : int | None
            Minimum age in days (delay).
        publish_date : datetime | None | str
            Release publish date (or string like "180_days_ago").
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        # Convert string dates to actual dates
        now = datetime.now(UTC)
        actual_date: datetime | None
        if isinstance(publish_date, str):
            if publish_date == "today":
                actual_date = now
            elif publish_date == "180_days_ago":
                actual_date = now - timedelta(days=180)
            elif publish_date == "400_days_ago":
                actual_date = now - timedelta(days=400)
            elif publish_date == "10_days_ago":
                actual_date = now - timedelta(days=10)
            elif publish_date == "200_days_ago":
                actual_date = now - timedelta(days=200)
            else:
                # Should not happen, but handle gracefully
                actual_date = None
        else:
            actual_date = publish_date

        spec = AgeSpecification()
        prefs = DownloadDecisionPreferences(
            max_age_days=max_age_days, min_age_days=min_age_days
        )
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            publish_date=actual_date,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
            # Too old is permanent, too new is temporary
            if expected_reason == DownloadRejectionReason.TOO_OLD:
                assert rejection.type == RejectionType.PERMANENT
            elif expected_reason == DownloadRejectionReason.TOO_NEW:
                assert rejection.type == RejectionType.TEMPORARY
        else:
            assert rejection is None


class TestKeywordSpecification:
    """Test KeywordSpecification."""

    @pytest.mark.parametrize(
        (
            "exclude_keywords",
            "require_keywords",
            "title",
            "description",
            "expected_satisfied",
            "expected_reason",
        ),
        [
            ([], [], "Test Book", "Description", True, None),
            (["sample"], [], "Test Book", "Description", True, None),
            (
                ["sample"],
                [],
                "Sample Book",
                "Description",
                False,
                DownloadRejectionReason.EXCLUDED_KEYWORD,
            ),
            (
                ["sample"],
                [],
                "Test Book",
                "Sample description",
                False,
                DownloadRejectionReason.EXCLUDED_KEYWORD,
            ),
            (
                [],
                ["complete"],
                "Test Book",
                "Description",
                False,
                DownloadRejectionReason.MISSING_REQUIRED_KEYWORD,
            ),
            ([], ["complete"], "Complete Book", "Description", True, None),
            (
                ["sample"],
                ["complete"],
                "Complete Book Title",
                "Description",
                True,
                None,
            ),
            (
                ["sample"],
                ["complete"],
                "Sample Book",
                "Description",
                False,
                DownloadRejectionReason.EXCLUDED_KEYWORD,
            ),
        ],
    )
    def test_keyword_specification(
        self,
        exclude_keywords: list[str],
        require_keywords: list[str],
        title: str,
        description: str,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test keyword specification matching.

        Parameters
        ----------
        exclude_keywords : list[str]
            Keywords to exclude.
        require_keywords : list[str]
            Keywords to require.
        title : str
            Release title.
        description : str
            Release description.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = KeywordSpecification()
        prefs = DownloadDecisionPreferences(
            exclude_keywords=exclude_keywords, require_keywords=require_keywords
        )
        release = ReleaseInfo(
            title=title,
            download_url="https://example.com/book.torrent",
            description=description,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
            assert rejection.type == RejectionType.PERMANENT
        else:
            assert rejection is None


class TestIndexerSpecification:
    """Test IndexerSpecification."""

    @pytest.mark.parametrize(
        ("allowed_indexer_ids", "indexer_id", "expected_satisfied", "expected_reason"),
        [
            (None, None, True, None),
            (None, 1, True, None),
            ([1, 2], 1, True, None),
            ([1, 2], 2, True, None),
            ([1, 2], 3, False, DownloadRejectionReason.INDEXER_DISABLED),
            ([1, 2], None, True, None),  # No indexer ID means pass
        ],
    )
    def test_indexer_specification(
        self,
        allowed_indexer_ids: list[int] | None,
        indexer_id: int | None,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test indexer specification matching.

        Parameters
        ----------
        allowed_indexer_ids : list[int] | None
            Allowed indexer IDs.
        indexer_id : int | None
            Release indexer ID.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = IndexerSpecification()
        prefs = DownloadDecisionPreferences(allowed_indexer_ids=allowed_indexer_ids)
        release = ReleaseInfo(
            title="Test",
            download_url="https://example.com/book.torrent",
            indexer_id=indexer_id,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
            assert rejection.type == RejectionType.PERMANENT
        else:
            assert rejection is None


class TestBlocklistSpecification:
    """Test BlocklistSpecification."""

    @pytest.mark.parametrize(
        ("blocklisted_urls", "download_url", "expected_satisfied", "expected_reason"),
        [
            (set(), "https://example.com/book.torrent", True, None),
            (
                {"https://other.com/book.torrent"},
                "https://example.com/book.torrent",
                True,
                None,
            ),
            (
                {"https://example.com/book.torrent"},
                "https://example.com/book.torrent",
                False,
                DownloadRejectionReason.BLOCKLISTED,
            ),
            ({"url1", "url2"}, "url1", False, DownloadRejectionReason.BLOCKLISTED),
        ],
    )
    def test_blocklist_specification(
        self,
        blocklisted_urls: set[str],
        download_url: str,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test blocklist specification matching.

        Parameters
        ----------
        blocklisted_urls : set[str]
            Blocklisted URLs.
        download_url : str
            Release download URL.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = BlocklistSpecification()
        prefs = DownloadDecisionPreferences(blocklisted_urls=blocklisted_urls)
        release = ReleaseInfo(
            title="Test",
            download_url=download_url,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
            assert rejection.type == RejectionType.PERMANENT
        else:
            assert rejection is None


class TestMetadataSpecification:
    """Test MetadataSpecification."""

    @pytest.mark.parametrize(
        ("title", "download_url", "expected_satisfied", "expected_reason"),
        [
            ("Valid Title", "https://example.com/book.torrent", True, None),
            (
                "",
                "https://example.com/book.torrent",
                False,
                DownloadRejectionReason.MISSING_METADATA,
            ),
            (
                "   ",
                "https://example.com/book.torrent",
                False,
                DownloadRejectionReason.MISSING_METADATA,
            ),
            ("Valid Title", "", False, DownloadRejectionReason.INVALID_URL),
            ("Valid Title", "   ", False, DownloadRejectionReason.INVALID_URL),
        ],
    )
    def test_metadata_specification(
        self,
        title: str,
        download_url: str,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test metadata specification matching.

        Parameters
        ----------
        title : str
            Release title.
        download_url : str
            Release download URL.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = MetadataSpecification()
        prefs = DownloadDecisionPreferences()
        release = ReleaseInfo(
            title=title,
            download_url=download_url,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
            assert rejection.type == RejectionType.PERMANENT
        else:
            assert rejection is None


class TestTitleMatchSpecification:
    """Test TitleMatchSpecification."""

    @pytest.mark.parametrize(
        (
            "search_title",
            "release_title",
            "require_match",
            "expected_satisfied",
            "expected_reason",
        ),
        [
            (None, "Test Book", True, True, None),
            (None, "Test Book", False, True, None),
            ("Test Book", "Test Book", True, True, None),
            ("Test Book", "test book", True, True, None),  # Case insensitive
            ("Test", "Test Book", True, True, None),  # Partial match
            ("Test Book", "Test", True, True, None),  # Partial match
            (
                "Test Book",
                "Completely Different Title",
                True,
                False,
                DownloadRejectionReason.MISSING_METADATA,
            ),
            ("Test Book", "Different Book", False, True, None),  # Not required
        ],
    )
    def test_title_match_specification(
        self,
        search_title: str | None,
        release_title: str,
        require_match: bool,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test title match specification.

        Parameters
        ----------
        search_title : str | None
            Expected title from search.
        release_title : str
            Release title.
        require_match : bool
            Whether title match is required.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = TitleMatchSpecification(search_title=search_title)
        prefs = DownloadDecisionPreferences(require_title_match=require_match)
        release = ReleaseInfo(
            title=release_title,
            download_url="https://example.com/book.torrent",
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
        else:
            assert rejection is None


class TestAuthorMatchSpecification:
    """Test AuthorMatchSpecification."""

    @pytest.mark.parametrize(
        (
            "search_author",
            "release_author",
            "require_match",
            "expected_satisfied",
            "expected_reason",
        ),
        [
            (None, "Test Author", True, True, None),
            (None, "Test Author", False, True, None),
            ("Test Author", "Test Author", True, True, None),
            ("Test Author", "test author", True, True, None),  # Case insensitive
            ("Test", "Test Author", True, True, None),  # Partial match
            (
                "Test Author",
                None,
                True,
                False,
                DownloadRejectionReason.MISSING_METADATA,
            ),
            (
                "Test Author",
                "Completely Different Writer",
                True,
                False,
                DownloadRejectionReason.MISSING_METADATA,
            ),
            ("Test Author", "Different Author", False, True, None),  # Not required
        ],
    )
    def test_author_match_specification(
        self,
        search_author: str | None,
        release_author: str | None,
        require_match: bool,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test author match specification.

        Parameters
        ----------
        search_author : str | None
            Expected author from search.
        release_author : str | None
            Release author.
        require_match : bool
            Whether author match is required.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = AuthorMatchSpecification(search_author=search_author)
        prefs = DownloadDecisionPreferences(require_author_match=require_match)
        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/book.torrent",
            author=release_author,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
        else:
            assert rejection is None


class TestISBNMatchSpecification:
    """Test ISBNMatchSpecification."""

    @pytest.mark.parametrize(
        (
            "search_isbn",
            "release_isbn",
            "require_match",
            "expected_satisfied",
            "expected_reason",
        ),
        [
            (None, "9781234567890", True, True, None),
            (None, "9781234567890", False, True, None),
            ("9781234567890", "9781234567890", True, True, None),
            ("978-1234567890", "9781234567890", True, True, None),  # Hyphens normalized
            ("9781234567890", "978-1234567890", True, True, None),  # Hyphens normalized
            (
                "9781234567890",
                None,
                True,
                False,
                DownloadRejectionReason.MISSING_METADATA,
            ),
            (
                "9781234567890",
                "9789876543210",
                True,
                False,
                DownloadRejectionReason.MISSING_METADATA,
            ),
            ("9781234567890", "9789876543210", False, True, None),  # Not required
        ],
    )
    def test_isbn_match_specification(
        self,
        search_isbn: str | None,
        release_isbn: str | None,
        require_match: bool,
        expected_satisfied: bool,
        expected_reason: DownloadRejectionReason | None,
    ) -> None:
        """Test ISBN match specification.

        Parameters
        ----------
        search_isbn : str | None
            Expected ISBN from search.
        release_isbn : str | None
            Release ISBN.
        require_match : bool
            Whether ISBN match is required.
        expected_satisfied : bool
            Whether specification should be satisfied.
        expected_reason : DownloadRejectionReason | None
            Expected rejection reason if not satisfied.
        """
        spec = ISBNMatchSpecification(search_isbn=search_isbn)
        prefs = DownloadDecisionPreferences(require_isbn_match=require_match)
        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/book.torrent",
            isbn=release_isbn,
        )

        satisfied, rejection = spec.is_satisfied_by(release, prefs)

        assert satisfied == expected_satisfied
        if expected_reason:
            assert rejection is not None
            assert rejection.reason == expected_reason
        else:
            assert rejection is None
