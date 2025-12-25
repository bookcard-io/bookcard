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

"""Filtering components for indexer search results.

Implements composite pattern for extensible filtering.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta

from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.utils import (
    check_threshold,
    ensure_utc,
    normalize_text,
)


class FilterCriterion(ABC):
    """Abstract base class for filter criteria.

    Follows composite pattern to allow flexible filter combinations.
    """

    @abstractmethod
    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release matches filter criterion.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if release matches, False otherwise.
        """
        raise NotImplementedError


class FormatFilter(FilterCriterion):
    """Filter by file format/quality.

    Attributes
    ----------
    formats : list[str]
        Allowed formats (e.g., ['epub', 'pdf']).
    """

    def __init__(self, formats: list[str]) -> None:
        """Initialize format filter.

        Parameters
        ----------
        formats : list[str]
            Allowed formats.
        """
        self.formats = [fmt.lower() for fmt in formats]

    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release format matches.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if format matches or quality is None, False otherwise.
        """
        if release.quality is None:
            return False
        release_format = release.quality.lower()
        return any(fmt in release_format for fmt in self.formats)


class SizeRangeFilter(FilterCriterion):
    """Filter by file size range.

    Attributes
    ----------
    min_size : int | None
        Minimum file size in bytes.
    max_size : int | None
        Maximum file size in bytes.
    """

    def __init__(
        self, min_size: int | None = None, max_size: int | None = None
    ) -> None:
        """Initialize size range filter.

        Parameters
        ----------
        min_size : int | None
            Minimum file size in bytes.
        max_size : int | None
            Maximum file size in bytes.
        """
        self.min_size = min_size
        self.max_size = max_size

    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release size is within range.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if size is within range or size_bytes is None, False otherwise.
        """
        if release.size_bytes is None:
            return True
        return not (
            (self.min_size is not None and release.size_bytes < self.min_size)
            or (self.max_size is not None and release.size_bytes > self.max_size)
        )


class SeederLeecherFilter(FilterCriterion):
    """Filter by seeder/leecher count for torrents.

    Attributes
    ----------
    min_seeders : int | None
        Minimum number of seeders.
    min_leechers : int | None
        Minimum number of leechers.
    """

    def __init__(
        self, min_seeders: int | None = None, min_leechers: int | None = None
    ) -> None:
        """Initialize seeder/leecher filter.

        Parameters
        ----------
        min_seeders : int | None
            Minimum seeders.
        min_leechers : int | None
            Minimum leechers.
        """
        self.min_seeders = min_seeders
        self.min_leechers = min_leechers

    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release meets seeder/leecher requirements.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if requirements are met, False otherwise.
        """
        return check_threshold(
            release.seeders, self.min_seeders, lambda v, t: v >= t
        ) and check_threshold(release.leechers, self.min_leechers, lambda v, t: v >= t)


class IndexerFilter(FilterCriterion):
    """Filter by indexer ID.

    Attributes
    ----------
    indexer_ids : list[int]
        Allowed indexer IDs.
    """

    def __init__(self, indexer_ids: list[int]) -> None:
        """Initialize indexer filter.

        Parameters
        ----------
        indexer_ids : list[int]
            Allowed indexer IDs.
        """
        self.indexer_ids = set(indexer_ids)

    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release is from allowed indexer.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if indexer ID matches, False otherwise.
        """
        return release.indexer_id is not None and release.indexer_id in self.indexer_ids


class AgeFilter(FilterCriterion):
    """Filter by release age.

    Attributes
    ----------
    max_age_days : int
        Maximum age in days.
    """

    def __init__(self, max_age_days: int) -> None:
        """Initialize age filter.

        Parameters
        ----------
        max_age_days : int
            Maximum age in days.
        """
        self.max_age_days = max_age_days

    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release is within age limit.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if within age limit or publish_date is None, False otherwise.
        """
        if release.publish_date is None:
            return True
        publish_date = ensure_utc(release.publish_date)
        if publish_date is None:
            return True
        from datetime import UTC, datetime

        age = datetime.now(UTC) - publish_date
        # Use total_seconds() for precise comparison to handle microsecond precision
        max_age_seconds = timedelta(days=self.max_age_days).total_seconds()
        return age.total_seconds() <= max_age_seconds


class KeywordFilter(FilterCriterion):
    """Filter by keywords (exclude/require).

    Attributes
    ----------
    exclude_keywords : list[str]
        Keywords to exclude.
    require_keywords : list[str]
        Keywords that must be present.
    """

    def __init__(
        self,
        exclude_keywords: list[str] | None = None,
        require_keywords: list[str] | None = None,
    ) -> None:
        """Initialize keyword filter.

        Parameters
        ----------
        exclude_keywords : list[str] | None
            Keywords to exclude.
        require_keywords : list[str] | None
            Keywords that must be present.
        """
        self.exclude_keywords = [normalize_text(kw) for kw in (exclude_keywords or [])]
        self.require_keywords = [normalize_text(kw) for kw in (require_keywords or [])]

    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release matches keyword criteria.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if matches keyword criteria, False otherwise.
        """
        title_norm = normalize_text(release.title)
        author_norm = normalize_text(release.author)
        description_norm = normalize_text(release.description)
        search_text = f"{title_norm} {author_norm} {description_norm}"

        # Exclude keywords
        if any(kw in search_text for kw in self.exclude_keywords):
            return False

        # Require keywords
        return not any(kw not in search_text for kw in self.require_keywords)


class CompositeFilter(FilterCriterion):
    """Composite filter that combines multiple criteria.

    Attributes
    ----------
    filters : list[FilterCriterion]
        List of filter criteria.
    operator : str
        Logical operator: "AND" or "OR" (default: "AND").
    """

    def __init__(self, filters: list[FilterCriterion], operator: str = "AND") -> None:
        """Initialize composite filter.

        Parameters
        ----------
        filters : list[FilterCriterion]
            List of filter criteria.
        operator : str
            Logical operator: "AND" or "OR".
        """
        self.filters = filters
        self.operator = operator.upper()

    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release matches all/any criteria.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if matches criteria based on operator, False otherwise.
        """
        if not self.filters:
            return True

        if self.operator == "AND":
            return all(f.matches(release) for f in self.filters)
        return any(f.matches(release) for f in self.filters)


@dataclass
class IndexerSearchFilter:
    """Convenience filter class that builds composite filter from parameters.

    This is a compatibility class that maintains the original API while
    using the new composite filter pattern internally.

    Attributes
    ----------
    formats : list[str] | None
        Allowed formats. None = no format filter.
    min_size_bytes : int | None
        Minimum file size in bytes.
    max_size_bytes : int | None
        Maximum file size in bytes.
    min_seeders : int | None
        Minimum number of seeders.
    min_leechers : int | None
        Minimum number of leechers.
    indexer_ids : list[int] | None
        Allowed indexer IDs. None = all indexers.
    max_age_days : int | None
        Maximum age in days. None = no age limit.
    exclude_keywords : list[str]
        Keywords to exclude.
    require_keywords : list[str]
        Keywords that must be present.
    """

    formats: list[str] | None = None
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    min_seeders: int | None = None
    min_leechers: int | None = None
    indexer_ids: list[int] | None = None
    max_age_days: int | None = None
    exclude_keywords: list[str] = field(default_factory=list)
    require_keywords: list[str] = field(default_factory=list)

    def matches(self, release: ReleaseInfo) -> bool:
        """Check if release matches filter criteria.

        Builds a composite filter from the configured criteria.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.

        Returns
        -------
        bool
            True if release matches all criteria, False otherwise.
        """
        criteria: list[FilterCriterion] = []

        if self.formats is not None:
            criteria.append(FormatFilter(self.formats))

        if self.min_size_bytes is not None or self.max_size_bytes is not None:
            criteria.append(SizeRangeFilter(self.min_size_bytes, self.max_size_bytes))

        if self.min_seeders is not None or self.min_leechers is not None:
            criteria.append(SeederLeecherFilter(self.min_seeders, self.min_leechers))

        if self.indexer_ids is not None:
            criteria.append(IndexerFilter(self.indexer_ids))

        if self.max_age_days is not None:
            criteria.append(AgeFilter(self.max_age_days))

        if self.exclude_keywords or self.require_keywords:
            criteria.append(KeywordFilter(self.exclude_keywords, self.require_keywords))

        if not criteria:
            return True

        composite = CompositeFilter(criteria, operator="AND")
        return composite.matches(release)
