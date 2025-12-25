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

"""Specification classes for download decision evaluation.

Implements specification pattern for checking various criteria.
Each specification checks a specific aspect of a release.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.decision.models import (
    DownloadRejection,
    DownloadRejectionReason,
    RejectionType,
)
from bookcard.services.pvr.decision.preferences import DownloadDecisionPreferences
from bookcard.services.pvr.search.utils import ensure_utc, normalize_text


class IDownloadDecisionSpecification(ABC):
    """Abstract base class for download decision specifications.

    Follows specification pattern to allow composable decision logic.
    """

    @abstractmethod
    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check if release satisfies this specification.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection) - True if satisfied, False with rejection if not.
        """
        raise NotImplementedError


class FormatSpecification(IDownloadDecisionSpecification):
    """Checks if release format matches preferred formats."""

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check format preference.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if preferences.preferred_formats is None:
            return True, None

        if not release.quality:
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.WRONG_FORMAT,
                    message="Release format is unknown",
                    type=RejectionType.PERMANENT,
                ),
            )

        release_format = release.quality.lower()
        preferred_lower = [fmt.lower() for fmt in preferences.preferred_formats]

        if any(fmt in release_format for fmt in preferred_lower):
            return True, None

        return (
            False,
            DownloadRejection(
                reason=DownloadRejectionReason.WRONG_FORMAT,
                message=f"Format '{release.quality}' not in preferred formats: {preferences.preferred_formats}",
                type=RejectionType.PERMANENT,
            ),
        )


class SizeSpecification(IDownloadDecisionSpecification):
    """Checks if release size is within acceptable range."""

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check size constraints.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if release.size_bytes is None:
            # Allow releases without size info
            return True, None

        if (
            preferences.min_size_bytes is not None
            and release.size_bytes < preferences.min_size_bytes
        ):
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.BELOW_MINIMUM_SIZE,
                    message=f"Size {release.size_bytes} bytes is below minimum {preferences.min_size_bytes} bytes",
                    type=RejectionType.PERMANENT,
                ),
            )

        if (
            preferences.max_size_bytes is not None
            and release.size_bytes > preferences.max_size_bytes
        ):
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.ABOVE_MAXIMUM_SIZE,
                    message=f"Size {release.size_bytes} bytes exceeds maximum {preferences.max_size_bytes} bytes",
                    type=RejectionType.PERMANENT,
                ),
            )

        return True, None


class SeederSpecification(IDownloadDecisionSpecification):
    """Checks if torrent has sufficient seeders."""

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check seeder requirements.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if preferences.min_seeders is None:
            return True, None

        if release.seeders is None:
            # Usenet releases don't have seeders
            return True, None

        if release.seeders < preferences.min_seeders:
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.INSUFFICIENT_SEEDERS,
                    message=f"Only {release.seeders} seeders, minimum {preferences.min_seeders} required",
                    type=RejectionType.TEMPORARY,  # May improve over time
                ),
            )

        return True, None


class AgeSpecification(IDownloadDecisionSpecification):
    """Checks if release age is within acceptable range."""

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check age constraints.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if release.publish_date is None:
            # Allow releases without publish date
            return True, None

        publish_date = ensure_utc(release.publish_date)
        if publish_date is None:
            return True, None

        now = datetime.now(UTC)
        age = now - publish_date
        age_days = age.days

        # Check maximum age
        if preferences.max_age_days is not None and age_days > preferences.max_age_days:
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.TOO_OLD,
                    message=f"Release is {age_days} days old, maximum {preferences.max_age_days} days allowed",
                    type=RejectionType.PERMANENT,
                ),
            )

        # Check minimum age (delay)
        if preferences.min_age_days is not None and age_days < preferences.min_age_days:
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.TOO_NEW,
                    message=f"Release is {age_days} days old, minimum {preferences.min_age_days} days delay required",
                    type=RejectionType.TEMPORARY,  # Will be acceptable later
                ),
            )

        return True, None


class KeywordSpecification(IDownloadDecisionSpecification):
    """Checks if release matches keyword requirements."""

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check keyword requirements.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        # Build searchable text
        title_norm = normalize_text(release.title)
        author_norm = normalize_text(release.author or "")
        description_norm = normalize_text(release.description or "")
        search_text = f"{title_norm} {author_norm} {description_norm}"

        # Check excluded keywords
        exclude_keywords_norm = [
            normalize_text(kw) for kw in preferences.exclude_keywords
        ]
        for keyword in exclude_keywords_norm:
            if keyword in search_text:
                return (
                    False,
                    DownloadRejection(
                        reason=DownloadRejectionReason.EXCLUDED_KEYWORD,
                        message=f"Release contains excluded keyword: '{keyword}'",
                        type=RejectionType.PERMANENT,
                    ),
                )

        # Check required keywords
        require_keywords_norm = [
            normalize_text(kw) for kw in preferences.require_keywords
        ]
        for keyword in require_keywords_norm:
            if keyword not in search_text:
                return (
                    False,
                    DownloadRejection(
                        reason=DownloadRejectionReason.MISSING_REQUIRED_KEYWORD,
                        message=f"Release missing required keyword: '{keyword}'",
                        type=RejectionType.PERMANENT,
                    ),
                )

        return True, None


class IndexerSpecification(IDownloadDecisionSpecification):
    """Checks if release is from an allowed indexer."""

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check indexer restrictions.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if preferences.allowed_indexer_ids is None:
            return True, None

        if release.indexer_id is None:
            return True, None

        if release.indexer_id not in preferences.allowed_indexer_ids:
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.INDEXER_DISABLED,
                    message=f"Indexer {release.indexer_id} is not in allowed list",
                    type=RejectionType.PERMANENT,
                ),
            )

        return True, None


class BlocklistSpecification(IDownloadDecisionSpecification):
    """Checks if release URL is blocklisted."""

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check blocklist.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if release.download_url in preferences.blocklisted_urls:
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.BLOCKLISTED,
                    message="Release URL is blocklisted (already downloaded or rejected)",
                    type=RejectionType.PERMANENT,
                ),
            )

        return True, None


class MetadataSpecification(IDownloadDecisionSpecification):
    """Checks if release has required metadata."""

    def is_satisfied_by(
        self,
        release: ReleaseInfo,
        preferences: DownloadDecisionPreferences,  # noqa: ARG002
    ) -> tuple[bool, DownloadRejection | None]:
        """Check required metadata.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences (unused in this specification).

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if not release.title or not release.title.strip():
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.MISSING_METADATA,
                    message="Release is missing title",
                    type=RejectionType.PERMANENT,
                ),
            )

        if not release.download_url or not release.download_url.strip():
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.INVALID_URL,
                    message="Release is missing download URL",
                    type=RejectionType.PERMANENT,
                ),
            )

        return True, None


class TitleMatchSpecification(IDownloadDecisionSpecification):
    """Checks if release title matches search criteria."""

    def __init__(self, search_title: str | None = None) -> None:
        """Initialize title match specification.

        Parameters
        ----------
        search_title : str | None
            Expected title to match.
        """
        self.search_title = search_title

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check title match.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if not preferences.require_title_match or not self.search_title:
            return True, None

        title_norm = normalize_text(self.search_title)
        release_title_norm = normalize_text(release.title)

        # Check for match (full or partial)
        if title_norm in release_title_norm or release_title_norm in title_norm:
            return True, None

        # Check for word matches
        search_words = [w for w in title_norm.split() if w]
        if any(word in release_title_norm for word in search_words):
            return True, None

        return (
            False,
            DownloadRejection(
                reason=DownloadRejectionReason.MISSING_METADATA,
                message=f"Title '{release.title}' does not match expected '{self.search_title}'",
                type=RejectionType.PERMANENT,
            ),
        )


class AuthorMatchSpecification(IDownloadDecisionSpecification):
    """Checks if release author matches search criteria."""

    def __init__(self, search_author: str | None = None) -> None:
        """Initialize author match specification.

        Parameters
        ----------
        search_author : str | None
            Expected author to match.
        """
        self.search_author = search_author

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check author match.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if not preferences.require_author_match or not self.search_author:
            return True, None

        if not release.author:
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.MISSING_METADATA,
                    message="Release is missing author information",
                    type=RejectionType.PERMANENT,
                ),
            )

        author_norm = normalize_text(self.search_author)
        release_author_norm = normalize_text(release.author)

        # Check for match (full or partial)
        if author_norm in release_author_norm or release_author_norm in author_norm:
            return True, None

        # Check for word matches
        search_words = [w for w in author_norm.split() if w]
        if any(word in release_author_norm for word in search_words):
            return True, None

        return (
            False,
            DownloadRejection(
                reason=DownloadRejectionReason.MISSING_METADATA,
                message=f"Author '{release.author}' does not match expected '{self.search_author}'",
                type=RejectionType.PERMANENT,
            ),
        )


class ISBNMatchSpecification(IDownloadDecisionSpecification):
    """Checks if release ISBN matches search criteria."""

    def __init__(self, search_isbn: str | None = None) -> None:
        """Initialize ISBN match specification.

        Parameters
        ----------
        search_isbn : str | None
            Expected ISBN to match.
        """
        self.search_isbn = search_isbn

    def is_satisfied_by(
        self, release: ReleaseInfo, preferences: DownloadDecisionPreferences
    ) -> tuple[bool, DownloadRejection | None]:
        """Check ISBN match.

        Parameters
        ----------
        release : ReleaseInfo
            Release to check.
        preferences : DownloadDecisionPreferences
            User preferences.

        Returns
        -------
        tuple[bool, DownloadRejection | None]
            (is_satisfied, rejection)
        """
        if not preferences.require_isbn_match or not self.search_isbn:
            return True, None

        if not release.isbn:
            return (
                False,
                DownloadRejection(
                    reason=DownloadRejectionReason.MISSING_METADATA,
                    message="Release is missing ISBN information",
                    type=RejectionType.PERMANENT,
                ),
            )

        # Normalize ISBNs (remove hyphens and spaces)
        search_isbn_norm = self.search_isbn.replace("-", "").replace(" ", "")
        release_isbn_norm = release.isbn.replace("-", "").replace(" ", "")

        if search_isbn_norm == release_isbn_norm:
            return True, None

        return (
            False,
            DownloadRejection(
                reason=DownloadRejectionReason.MISSING_METADATA,
                message=f"ISBN '{release.isbn}' does not match expected '{self.search_isbn}'",
                type=RejectionType.PERMANENT,
            ),
        )
