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

"""Shared fixtures for download decision tests."""

from datetime import UTC, datetime

import pytest

from bookcard.models.pvr import (
    DownloadDecisionDefaults,
    DownloadRejectionReason,
    RejectionType,
    TrackedBook,
    TrackedBookStatus,
)
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.decision.models import (
    DownloadDecision,
    DownloadRejection,
)
from bookcard.services.pvr.decision.preferences import DownloadDecisionPreferences


@pytest.fixture
def sample_release() -> ReleaseInfo:
    """Create a sample release for testing.

    Returns
    -------
    ReleaseInfo
        Sample release instance.
    """
    return ReleaseInfo(
        indexer_id=1,
        title="Test Book Title",
        download_url="https://example.com/torrent.torrent",
        size_bytes=1024000,
        publish_date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        seeders=100,
        leechers=10,
        quality="epub",
        author="Test Author",
        isbn="9781234567890",
        description="A test book description",
        category="Books",
    )


@pytest.fixture
def sample_release_minimal() -> ReleaseInfo:
    """Create a minimal release for testing.

    Returns
    -------
    ReleaseInfo
        Minimal release instance.
    """
    return ReleaseInfo(
        title="Minimal Book",
        download_url="https://example.com/book.torrent",
    )


@pytest.fixture
def sample_release_pdf() -> ReleaseInfo:
    """Create a PDF release for testing.

    Returns
    -------
    ReleaseInfo
        PDF release instance.
    """
    return ReleaseInfo(
        title="PDF Book",
        download_url="https://example.com/book.pdf.torrent",
        quality="pdf",
        size_bytes=2048000,
        seeders=50,
    )


@pytest.fixture
def sample_release_old() -> ReleaseInfo:
    """Create an old release for testing.

    Returns
    -------
    ReleaseInfo
        Old release instance.
    """
    return ReleaseInfo(
        title="Old Book",
        download_url="https://example.com/old.torrent",
        publish_date=datetime(2020, 1, 1, tzinfo=UTC),
        quality="epub",
        seeders=5,
    )


@pytest.fixture
def sample_release_low_seeders() -> ReleaseInfo:
    """Create a release with low seeders for testing.

    Returns
    -------
    ReleaseInfo
        Low seeder release instance.
    """
    return ReleaseInfo(
        title="Low Seeders Book",
        download_url="https://example.com/low.torrent",
        quality="epub",
        seeders=2,
        leechers=1,
    )


@pytest.fixture
def default_preferences() -> DownloadDecisionPreferences:
    """Create default preferences for testing.

    Returns
    -------
    DownloadDecisionPreferences
        Default preferences instance.
    """
    return DownloadDecisionPreferences()


@pytest.fixture
def strict_preferences() -> DownloadDecisionPreferences:
    """Create strict preferences for testing.

    Returns
    -------
    DownloadDecisionPreferences
        Strict preferences instance.
    """
    return DownloadDecisionPreferences(
        preferred_formats=["epub", "pdf"],
        min_size_bytes=100000,
        max_size_bytes=10000000,
        min_seeders=10,
        max_age_days=365,
        exclude_keywords=["sample", "test"],
        require_keywords=["complete"],
    )


@pytest.fixture
def lenient_preferences() -> DownloadDecisionPreferences:
    """Create lenient preferences for testing.

    Returns
    -------
    DownloadDecisionPreferences
        Lenient preferences instance.
    """
    return DownloadDecisionPreferences(
        preferred_formats=None,  # Accept all formats
        min_size_bytes=None,
        max_size_bytes=None,
        min_seeders=None,
        max_age_days=None,
    )


@pytest.fixture
def download_decision_defaults() -> DownloadDecisionDefaults:
    """Create download decision defaults for testing.

    Returns
    -------
    DownloadDecisionDefaults
        Defaults instance.
    """
    return DownloadDecisionDefaults(
        id=1,
        preferred_formats=["epub", "pdf", "mobi"],
        min_size_bytes=50000,
        max_size_bytes=50000000,
        min_seeders=5,
        max_age_days=730,
        exclude_keywords=["sample"],
        require_title_match=True,
        require_author_match=True,
        require_isbn_match=False,
    )


@pytest.fixture
def tracked_book() -> TrackedBook:
    """Create a tracked book for testing.

    Returns
    -------
    TrackedBook
        Tracked book instance.
    """
    return TrackedBook(
        id=1,
        title="Test Book",
        author="Test Author",
        status=TrackedBookStatus.WANTED,
        preferred_formats=["epub"],
        exclude_keywords=["sample"],
        require_title_match=True,
        require_author_match=True,
        require_isbn_match=False,
    )


@pytest.fixture
def tracked_book_custom_prefs() -> TrackedBook:
    """Create a tracked book with custom preferences for testing.

    Returns
    -------
    TrackedBook
        Tracked book with custom preferences.
    """
    return TrackedBook(
        id=2,
        title="Custom Book",
        author="Custom Author",
        status=TrackedBookStatus.WANTED,
        preferred_formats=["pdf"],  # Override default
        exclude_keywords=["test", "draft"],  # Override default
        require_keywords=["final"],  # Book-specific
        require_title_match=False,  # Override default
    )


@pytest.fixture
def sample_rejection() -> DownloadRejection:
    """Create a sample rejection for testing.

    Returns
    -------
    DownloadRejection
        Sample rejection instance.
    """
    return DownloadRejection(
        reason=DownloadRejectionReason.WRONG_FORMAT,
        message="Format not in preferred formats",
        type=RejectionType.PERMANENT,
    )


@pytest.fixture
def sample_temporary_rejection() -> DownloadRejection:
    """Create a temporary rejection for testing.

    Returns
    -------
    DownloadRejection
        Temporary rejection instance.
    """
    return DownloadRejection(
        reason=DownloadRejectionReason.INSUFFICIENT_SEEDERS,
        message="Only 2 seeders, minimum 10 required",
        type=RejectionType.TEMPORARY,
    )


@pytest.fixture
def approved_decision(sample_release: ReleaseInfo) -> DownloadDecision:
    """Create an approved decision for testing.

    Parameters
    ----------
    sample_release : ReleaseInfo
        Sample release.

    Returns
    -------
    DownloadDecision
        Approved decision instance.
    """
    return DownloadDecision(
        release=sample_release,
        approved=True,
        score=0.85,
    )


@pytest.fixture
def rejected_decision(
    sample_release: ReleaseInfo, sample_rejection: DownloadRejection
) -> DownloadDecision:
    """Create a rejected decision for testing.

    Parameters
    ----------
    sample_release : ReleaseInfo
        Sample release.
    sample_rejection : DownloadRejection
        Sample rejection.

    Returns
    -------
    DownloadDecision
        Rejected decision instance.
    """
    decision = DownloadDecision(release=sample_release, approved=True, score=0.5)
    decision.add_rejection(
        reason=sample_rejection.reason,
        message=sample_rejection.message,
        rejection_type=sample_rejection.type,
    )
    return decision
