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

"""Preferences for download decision evaluation.

Defines user preferences and criteria for evaluating releases.
Can be built from database models (DownloadDecisionDefaults, TrackedBook)
or created directly for runtime use.
"""

from dataclasses import dataclass, field

from bookcard.models.pvr import (
    DownloadDecisionDefaults,
    TrackedBook,
)


@dataclass
class DownloadDecisionPreferences:
    """Preferences for evaluating download decisions.

    Attributes
    ----------
    preferred_formats : list[str] | None
        Preferred file formats (e.g., ['epub', 'pdf', 'mobi']).
        None means all formats are acceptable.
    min_size_bytes : int | None
        Minimum file size in bytes. None = no minimum.
    max_size_bytes : int | None
        Maximum file size in bytes. None = no maximum.
    min_seeders : int | None
        Minimum number of seeders for torrents. None = no minimum.
    min_leechers : int | None
        Minimum number of leechers for torrents. None = no minimum.
    max_age_days : int | None
        Maximum age in days. None = no maximum age.
    min_age_days : int | None
        Minimum age in days (delay). None = no delay.
    exclude_keywords : list[str]
        Keywords that must not appear in release title/description.
    require_keywords : list[str]
        Keywords that must appear in release title/description.
    allowed_indexer_ids : list[int] | None
        Allowed indexer IDs. None = all indexers allowed.
    blocklisted_urls : set[str]
        Blocklisted download URLs (already downloaded, etc.).
    require_title_match : bool
        Whether title must match search criteria (default: True).
    require_author_match : bool
        Whether author must match search criteria (default: True).
    require_isbn_match : bool
        Whether ISBN must match if provided (default: False).
    """

    preferred_formats: list[str] | None = None
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    min_seeders: int | None = None
    min_leechers: int | None = None
    max_age_days: int | None = None
    min_age_days: int | None = None
    exclude_keywords: list[str] = field(default_factory=list)
    require_keywords: list[str] = field(default_factory=list)
    allowed_indexer_ids: list[int] | None = None
    blocklisted_urls: set[str] = field(default_factory=set)
    require_title_match: bool = True
    require_author_match: bool = True
    require_isbn_match: bool = False

    @classmethod
    def from_defaults(
        cls, defaults: DownloadDecisionDefaults | None
    ) -> "DownloadDecisionPreferences":
        """Create preferences from system defaults.

        Parameters
        ----------
        defaults : DownloadDecisionDefaults | None
            System-wide defaults. If None, returns empty preferences.

        Returns
        -------
        DownloadDecisionPreferences
            Preferences initialized from defaults.
        """
        if not defaults:
            return cls()

        return cls(
            preferred_formats=defaults.preferred_formats,
            min_size_bytes=defaults.min_size_bytes,
            max_size_bytes=defaults.max_size_bytes,
            min_seeders=defaults.min_seeders,
            min_leechers=defaults.min_leechers,
            max_age_days=defaults.max_age_days,
            min_age_days=defaults.min_age_days,
            exclude_keywords=defaults.exclude_keywords or [],
            require_keywords=defaults.require_keywords or [],
            require_title_match=defaults.require_title_match,
            require_author_match=defaults.require_author_match,
            require_isbn_match=defaults.require_isbn_match,
        )

    def apply_tracked_book_preferences(
        self, tracked_book: TrackedBook
    ) -> "DownloadDecisionPreferences":
        """Apply per-book preferences, overriding defaults.

        Only book-specific preferences are applied (formats, keywords, matching rules).
        System-wide preferences (size, seeders, age) remain from defaults.

        Parameters
        ----------
        tracked_book : TrackedBook
            Per-book preferences.

        Returns
        -------
        DownloadDecisionPreferences
            Self with per-book preferences applied.
        """
        if tracked_book.preferred_formats is not None:
            self.preferred_formats = tracked_book.preferred_formats
        if tracked_book.exclude_keywords is not None:
            self.exclude_keywords = tracked_book.exclude_keywords
        if tracked_book.require_keywords is not None:
            self.require_keywords = tracked_book.require_keywords
        self.require_title_match = tracked_book.require_title_match
        self.require_author_match = tracked_book.require_author_match
        self.require_isbn_match = tracked_book.require_isbn_match
        return self

    @classmethod
    def from_models(
        cls,
        defaults: DownloadDecisionDefaults | None = None,
        tracked_book: TrackedBook | None = None,
        blocklisted_urls: set[str] | None = None,
        allowed_indexer_ids: list[int] | None = None,
    ) -> "DownloadDecisionPreferences":
        """Build preferences from database models.

        Merges system defaults with per-book preferences, with per-book
        preferences taking precedence.

        Parameters
        ----------
        defaults : DownloadDecisionDefaults | None
            System-wide defaults. If None, uses empty defaults.
        tracked_book : TrackedBook | None
            Per-book preferences. If None, only defaults are used.
        blocklisted_urls : set[str] | None
            Blocklisted URLs from DownloadBlocklist. If None, empty set.
        allowed_indexer_ids : list[int] | None
            Allowed indexer IDs. If None, all indexers allowed.

        Returns
        -------
        DownloadDecisionPreferences
            Merged preferences with per-book values overriding defaults.
        """
        prefs = cls.from_defaults(defaults)

        if tracked_book:
            prefs.apply_tracked_book_preferences(tracked_book)

        prefs.blocklisted_urls = blocklisted_urls or set()
        prefs.allowed_indexer_ids = allowed_indexer_ids

        return prefs
