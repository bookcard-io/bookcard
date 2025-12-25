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

"""Tests for download decision preferences."""

import pytest

from bookcard.models.pvr import DownloadDecisionDefaults, TrackedBook
from bookcard.services.pvr.decision.preferences import DownloadDecisionPreferences


class TestDownloadDecisionPreferences:
    """Test DownloadDecisionPreferences dataclass."""

    def test_default_preferences(self) -> None:
        """Test default preferences values.

        Verifies that default preferences are set correctly.
        """
        prefs = DownloadDecisionPreferences()

        assert prefs.preferred_formats is None
        assert prefs.min_size_bytes is None
        assert prefs.max_size_bytes is None
        assert prefs.min_seeders is None
        assert prefs.min_leechers is None
        assert prefs.max_age_days is None
        assert prefs.min_age_days is None
        assert prefs.exclude_keywords == []
        assert prefs.require_keywords == []
        assert prefs.allowed_indexer_ids is None
        assert prefs.blocklisted_urls == set()
        assert prefs.require_title_match is True
        assert prefs.require_author_match is True
        assert prefs.require_isbn_match is False

    def test_custom_preferences(self) -> None:
        """Test custom preferences values.

        Verifies that custom preferences are set correctly.
        """
        prefs = DownloadDecisionPreferences(
            preferred_formats=["epub", "pdf"],
            min_size_bytes=100000,
            max_size_bytes=10000000,
            min_seeders=10,
            exclude_keywords=["sample"],
            require_keywords=["complete"],
        )

        assert prefs.preferred_formats == ["epub", "pdf"]
        assert prefs.min_size_bytes == 100000
        assert prefs.max_size_bytes == 10000000
        assert prefs.min_seeders == 10
        assert prefs.exclude_keywords == ["sample"]
        assert prefs.require_keywords == ["complete"]

    @pytest.mark.parametrize(
        ("formats", "expected"),
        [
            (None, None),
            (["epub"], ["epub"]),
            (["epub", "pdf"], ["epub", "pdf"]),
            ([], []),
        ],
    )
    def test_preferred_formats(
        self, formats: list[str] | None, expected: list[str] | None
    ) -> None:
        """Test preferred formats setting.

        Parameters
        ----------
        formats : list[str] | None
            Formats to set.
        expected : list[str] | None
            Expected formats value.
        """
        prefs = DownloadDecisionPreferences(preferred_formats=formats)
        assert prefs.preferred_formats == expected

    def test_from_defaults_none(self) -> None:
        """Test from_defaults with None.

        Verifies that None defaults creates empty preferences.
        """
        prefs = DownloadDecisionPreferences.from_defaults(None)

        assert prefs.preferred_formats is None
        assert prefs.min_size_bytes is None
        assert prefs.exclude_keywords == []

    def test_from_defaults(
        self, download_decision_defaults: DownloadDecisionDefaults
    ) -> None:
        """Test from_defaults with actual defaults.

        Parameters
        ----------
        download_decision_defaults : DownloadDecisionDefaults
            Defaults fixture.
        """
        prefs = DownloadDecisionPreferences.from_defaults(download_decision_defaults)

        assert prefs.preferred_formats == ["epub", "pdf", "mobi"]
        assert prefs.min_size_bytes == 50000
        assert prefs.max_size_bytes == 50000000
        assert prefs.min_seeders == 5
        assert prefs.max_age_days == 730
        assert prefs.exclude_keywords == ["sample"]
        assert prefs.require_title_match is True
        assert prefs.require_author_match is True
        assert prefs.require_isbn_match is False

    def test_apply_tracked_book_preferences(
        self,
        download_decision_defaults: DownloadDecisionDefaults,
        tracked_book: TrackedBook,
    ) -> None:
        """Test applying tracked book preferences.

        Parameters
        ----------
        download_decision_defaults : DownloadDecisionDefaults
            Defaults fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        prefs = DownloadDecisionPreferences.from_defaults(download_decision_defaults)
        prefs.apply_tracked_book_preferences(tracked_book)

        # Book-specific preferences override defaults
        assert prefs.preferred_formats == ["epub"]  # Overridden
        assert prefs.exclude_keywords == ["sample"]  # Overridden
        # System-wide preferences remain from defaults
        assert prefs.min_size_bytes == 50000  # From defaults
        assert prefs.min_seeders == 5  # From defaults

    def test_apply_tracked_book_preferences_partial(
        self,
        download_decision_defaults: DownloadDecisionDefaults,
        tracked_book_custom_prefs: TrackedBook,
    ) -> None:
        """Test applying tracked book preferences with partial overrides.

        Parameters
        ----------
        download_decision_defaults : DownloadDecisionDefaults
            Defaults fixture.
        tracked_book_custom_prefs : TrackedBook
            Tracked book with custom preferences fixture.
        """
        prefs = DownloadDecisionPreferences.from_defaults(download_decision_defaults)
        prefs.apply_tracked_book_preferences(tracked_book_custom_prefs)

        # Overridden values
        assert prefs.preferred_formats == ["pdf"]
        assert prefs.exclude_keywords == ["test", "draft"]
        assert prefs.require_keywords == ["final"]
        assert prefs.require_title_match is False

        # System-wide values remain
        assert prefs.min_size_bytes == 50000
        assert prefs.min_seeders == 5

    def test_from_models_defaults_only(
        self, download_decision_defaults: DownloadDecisionDefaults
    ) -> None:
        """Test from_models with only defaults.

        Parameters
        ----------
        download_decision_defaults : DownloadDecisionDefaults
            Defaults fixture.
        """
        prefs = DownloadDecisionPreferences.from_models(
            defaults=download_decision_defaults
        )

        assert prefs.preferred_formats == ["epub", "pdf", "mobi"]
        assert prefs.blocklisted_urls == set()
        assert prefs.allowed_indexer_ids is None

    def test_from_models_with_tracked_book(
        self,
        download_decision_defaults: DownloadDecisionDefaults,
        tracked_book: TrackedBook,
    ) -> None:
        """Test from_models with defaults and tracked book.

        Parameters
        ----------
        download_decision_defaults : DownloadDecisionDefaults
            Defaults fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        prefs = DownloadDecisionPreferences.from_models(
            defaults=download_decision_defaults,
            tracked_book=tracked_book,
            blocklisted_urls={"https://example.com/blocked.torrent"},
            allowed_indexer_ids=[1, 2],
        )

        # Book preferences override defaults
        assert prefs.preferred_formats == ["epub"]
        # System defaults remain
        assert prefs.min_size_bytes == 50000
        # Runtime values set
        assert "https://example.com/blocked.torrent" in prefs.blocklisted_urls
        assert prefs.allowed_indexer_ids == [1, 2]

    def test_from_models_no_defaults(self, tracked_book: TrackedBook) -> None:
        """Test from_models without defaults.

        Parameters
        ----------
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        prefs = DownloadDecisionPreferences.from_models(tracked_book=tracked_book)

        assert prefs.preferred_formats == ["epub"]
        assert prefs.min_size_bytes is None  # No defaults
        assert prefs.exclude_keywords == ["sample"]

    def test_from_models_empty(self) -> None:
        """Test from_models with no inputs.

        Verifies that empty from_models creates default preferences.
        """
        prefs = DownloadDecisionPreferences.from_models()

        assert prefs.preferred_formats is None
        assert prefs.min_size_bytes is None
        assert prefs.blocklisted_urls == set()

    @pytest.mark.parametrize(
        ("blocklisted_urls", "expected_count"),
        [
            (None, 0),
            (set(), 0),
            ({"url1", "url2"}, 2),
        ],
    )
    def test_blocklisted_urls(
        self,
        blocklisted_urls: set[str] | None,
        expected_count: int,
    ) -> None:
        """Test blocklisted URLs handling.

        Parameters
        ----------
        blocklisted_urls : set[str] | None
            Blocklisted URLs to set.
        expected_count : int
            Expected count of blocklisted URLs.
        """
        prefs = DownloadDecisionPreferences.from_models(
            blocklisted_urls=blocklisted_urls
        )

        assert len(prefs.blocklisted_urls) == expected_count

    def test_keyword_lists_default_empty(self) -> None:
        """Test that keyword lists default to empty lists.

        Verifies that exclude_keywords and require_keywords default correctly.
        """
        prefs = DownloadDecisionPreferences()

        assert prefs.exclude_keywords == []
        assert prefs.require_keywords == []
        assert isinstance(prefs.exclude_keywords, list)
        assert isinstance(prefs.require_keywords, list)
