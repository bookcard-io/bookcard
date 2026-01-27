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

"""Tests for KoboMetadataService to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from bookcard.models.core import Book
from bookcard.models.kobo import KoboBookmark, KoboReadingState, KoboStatistics
from bookcard.models.reading import ReadStatus, ReadStatusEnum
from bookcard.repositories.models import BookWithFullRelations, BookWithRelations
from bookcard.services.kobo.metadata_service import (
    KoboMetadataService,
    convert_to_kobo_timestamp_string,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def metadata_service() -> KoboMetadataService:
    """Create KoboMetadataService instance for testing.

    Returns
    -------
    KoboMetadataService
        Service instance.
    """
    return KoboMetadataService(base_url="https://example.com", auth_token="test_token")


@pytest.fixture
def book() -> Book:
    """Create a test book.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(
        id=1,
        title="Test Book",
        uuid="test-uuid-123",
        timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
        last_modified=datetime(2025, 1, 2, 12, 0, 0, tzinfo=UTC),
        pubdate=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def book_with_rels(book: Book) -> BookWithFullRelations:
    """Create a test book with relations.

    Parameters
    ----------
    book : Book
        Test book.

    Returns
    -------
    BookWithFullRelations
        Book with relations instance.
    """
    return BookWithFullRelations(
        book=book,
        authors=["Author One", "Author Two"],
        series="Test Series",
        series_id=1,
        tags=[],
        identifiers=[],
        description="Test description",
        publisher="Test Publisher",
        publisher_id=1,
        languages=["eng"],
        language_ids=[1],
        rating=None,
        rating_id=None,
        formats=[{"format": "EPUB", "name": "test.epub", "size": 1000}],
    )


@pytest.fixture
def book_with_rels_minimal(book: Book) -> BookWithRelations:
    """Create a minimal test book with relations.

    Parameters
    ----------
    book : Book
        Test book.

    Returns
    -------
    BookWithRelations
        Book with relations instance.
    """
    return BookWithRelations(
        book=book,
        authors=["Author One"],
        series=None,
        formats=[],
    )


# ============================================================================
# Tests for convert_to_kobo_timestamp_string
# ============================================================================


def test_convert_to_kobo_timestamp_string_with_datetime() -> None:
    """Test converting datetime to Kobo timestamp string."""
    dt = datetime(2025, 1, 15, 12, 30, 45, tzinfo=UTC)
    result = convert_to_kobo_timestamp_string(dt)
    assert result == "2025-01-15T12:30:45Z"


def test_convert_to_kobo_timestamp_string_none() -> None:
    """Test converting None to Kobo timestamp string."""
    result = convert_to_kobo_timestamp_string(None)
    assert isinstance(result, str)
    assert "T" in result
    assert "Z" in result


def test_convert_to_kobo_timestamp_string_no_tzinfo() -> None:
    """Test converting datetime without tzinfo to Kobo timestamp string."""
    dt = datetime(2025, 1, 15, 12, 30, 45)  # noqa: DTZ001
    result = convert_to_kobo_timestamp_string(dt)
    assert result.endswith("Z")


# ============================================================================
# Tests for KoboMetadataService.__init__
# ============================================================================


def test_init() -> None:
    """Test KoboMetadataService initialization."""
    service = KoboMetadataService(
        base_url="https://example.com/", auth_token="test_token"
    )
    assert service._base_url == "https://example.com"
    assert service._auth_token == "test_token"


# ============================================================================
# Tests for KoboMetadataService.get_download_url
# ============================================================================


def test_get_download_url(metadata_service: KoboMetadataService) -> None:
    """Test getting download URL.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    """
    result = metadata_service.get_download_url(book_id=1, book_format="EPUB")
    assert result == "https://example.com/kobo/test_token/download/1/epub"


# ============================================================================
# Tests for KoboMetadataService.create_book_entitlement
# ============================================================================


def test_create_book_entitlement(
    metadata_service: KoboMetadataService, book: Book
) -> None:
    """Test creating book entitlement.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    result = metadata_service.create_book_entitlement(book, archived=False)
    assert result["Id"] == str(book.uuid)
    assert result["IsRemoved"] is False
    assert result["Status"] == "Active"


def test_create_book_entitlement_archived(
    metadata_service: KoboMetadataService, book: Book
) -> None:
    """Test creating archived book entitlement.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    result = metadata_service.create_book_entitlement(book, archived=True)
    assert result["IsRemoved"] is True


def test_create_book_entitlement_no_uuid(metadata_service: KoboMetadataService) -> None:
    """Test creating book entitlement when book has no UUID.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    """
    book = Book(id=1, title="Test Book", uuid=None)
    result = metadata_service.create_book_entitlement(book)
    assert result["Id"] is not None
    assert isinstance(result["Id"], str)


# ============================================================================
# Tests for KoboMetadataService.get_book_metadata
# ============================================================================


def test_get_book_metadata_full(
    metadata_service: KoboMetadataService, book_with_rels: BookWithFullRelations
) -> None:
    """Test getting book metadata with full relations.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    """
    result = metadata_service.get_book_metadata(book_with_rels)
    assert result["Title"] == "Test Book"
    assert result["Description"] == "Test description"
    publisher = result["Publisher"]
    assert isinstance(publisher, dict)
    assert publisher["Name"] == "Test Publisher"  # type: ignore[index]
    assert result["Language"] == "en"
    assert "Series" in result
    download_urls = result["DownloadUrls"]
    assert isinstance(download_urls, list)
    assert len(download_urls) > 0


def test_get_book_metadata_with_kepub(
    metadata_service: KoboMetadataService, book: Book
) -> None:
    """Test getting book metadata with KEPUB format.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[{"format": "KEPUB", "name": "test.kepub", "size": 1000}],
    )
    result = metadata_service.get_book_metadata(book_with_rels)
    download_urls = result["DownloadUrls"]
    assert isinstance(download_urls, list)
    assert len(download_urls) > 0
    assert any(
        isinstance(url, dict) and url.get("Format") == "KEPUB"  # type: ignore[index]
        for url in download_urls
    )


def test_get_book_metadata_minimal(
    metadata_service: KoboMetadataService, book_with_rels_minimal: BookWithRelations
) -> None:
    """Test getting book metadata with minimal relations.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book_with_rels_minimal : BookWithRelations
        Minimal book with relations.
    """
    result = metadata_service.get_book_metadata(book_with_rels_minimal)
    assert result["Title"] == "Test Book"
    assert result["Description"] is None
    publisher = result["Publisher"]
    assert isinstance(publisher, dict)
    assert publisher["Name"] is None  # type: ignore[index]
    assert result["Language"] == "en"


def test_get_book_metadata_language_mapping(
    metadata_service: KoboMetadataService, book: Book
) -> None:
    """Test getting book metadata with language mapping.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=["fra"],
        language_ids=[1],
        rating=None,
        rating_id=None,
        formats=[],
    )
    result = metadata_service.get_book_metadata(book_with_rels)
    assert result["Language"] == "fr"


def test_get_book_metadata_language_short_code(
    metadata_service: KoboMetadataService, book: Book
) -> None:
    """Test getting book metadata with short language code.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=["xx"],
        language_ids=[1],
        rating=None,
        rating_id=None,
        formats=[],
    )
    result = metadata_service.get_book_metadata(book_with_rels)
    assert result["Language"] == "xx"


def test_get_book_metadata_series(
    metadata_service: KoboMetadataService, book_with_rels: BookWithFullRelations
) -> None:
    """Test getting book metadata with series.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    """
    book_with_rels.book.series_index = 2.5
    result = metadata_service.get_book_metadata(book_with_rels)
    assert "Series" in result
    series = result["Series"]
    assert isinstance(series, dict)
    assert series["Name"] == "Test Series"  # type: ignore[index]
    assert series["Number"] == 2  # type: ignore[index]
    assert series["NumberFloat"] == 2.5  # type: ignore[index]


def test_get_book_metadata_series_no_index(
    metadata_service: KoboMetadataService, book: Book
) -> None:
    """Test getting book metadata with series but no index.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    book_with_rels = BookWithRelations(
        book=book,
        authors=[],
        series="Test Series",
        formats=[],
    )
    result = metadata_service.get_book_metadata(book_with_rels)
    assert "Series" in result
    series = result["Series"]
    assert isinstance(series, dict)
    assert series["Number"] == 1  # type: ignore[index]


# ============================================================================
# Tests for KoboMetadataService.get_reading_state_response
# ============================================================================


def test_get_reading_state_response_with_read_status(
    metadata_service: KoboMetadataService,
    book: Book,
) -> None:
    """Test getting reading state response with read status.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    reading_state = KoboReadingState(
        id=1, user_id=1, book_id=1, last_modified=datetime.now(UTC)
    )
    read_status = ReadStatus(
        id=1,
        user_id=1,
        library_id=1,
        book_id=1,
        status=ReadStatusEnum.READING,
        updated_at=datetime.now(UTC),
        first_opened_at=datetime.now(UTC),
    )

    result = metadata_service.get_reading_state_response(
        book, reading_state, read_status
    )
    assert result["EntitlementId"] == str(book.uuid)
    assert "StatusInfo" in result
    status_info = result["StatusInfo"]
    assert isinstance(status_info, dict)
    assert status_info["Status"] == "Reading"  # type: ignore[index]
    assert "LastTimeStartedReading" in status_info


def test_get_reading_state_response_without_read_status(
    metadata_service: KoboMetadataService,
    book: Book,
) -> None:
    """Test getting reading state response without read status.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    reading_state = KoboReadingState(
        id=1, user_id=1, book_id=1, last_modified=datetime.now(UTC)
    )

    result = metadata_service.get_reading_state_response(book, reading_state, None)
    assert result["EntitlementId"] == str(book.uuid)
    status_info = result["StatusInfo"]
    assert isinstance(status_info, dict)
    assert status_info["Status"] == "ReadyToRead"  # type: ignore[index]
    assert status_info["TimesStartedReading"] == 0  # type: ignore[index]


def test_get_reading_state_response_with_statistics(
    metadata_service: KoboMetadataService,
    book: Book,
) -> None:
    """Test getting reading state response with statistics.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    reading_state = KoboReadingState(
        id=1, user_id=1, book_id=1, last_modified=datetime.now(UTC)
    )
    statistics = KoboStatistics(
        id=1,
        reading_state_id=1,
        spent_reading_minutes=120,
        remaining_time_minutes=60,
    )
    reading_state.statistics = statistics

    result = metadata_service.get_reading_state_response(book, reading_state, None)
    assert "Statistics" in result
    statistics = result["Statistics"]
    assert isinstance(statistics, dict)
    assert statistics["SpentReadingMinutes"] == 120  # type: ignore[index]
    assert statistics["RemainingTimeMinutes"] == 60  # type: ignore[index]


def test_get_reading_state_response_with_bookmark(
    metadata_service: KoboMetadataService,
    book: Book,
) -> None:
    """Test getting reading state response with bookmark.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    reading_state = KoboReadingState(
        id=1, user_id=1, book_id=1, last_modified=datetime.now(UTC)
    )
    bookmark = KoboBookmark(
        id=1,
        reading_state_id=1,
        progress_percent=50.0,
        content_source_progress_percent=45.0,
        location_value="epubcfi(/6/4[chap01ref]!/4/2/2)",
        location_type="CFI",
        location_source="kobo",
    )
    reading_state.current_bookmark = bookmark

    result = metadata_service.get_reading_state_response(book, reading_state, None)
    assert "CurrentBookmark" in result
    bookmark = result["CurrentBookmark"]
    assert isinstance(bookmark, dict)
    assert bookmark["ProgressPercent"] == 50.0  # type: ignore[index]
    assert bookmark["ContentSourceProgressPercent"] == 45.0  # type: ignore[index]
    assert "Location" in bookmark


def test_get_reading_state_response_without_statistics(
    metadata_service: KoboMetadataService,
    book: Book,
) -> None:
    """Test getting reading state response without statistics.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    reading_state = KoboReadingState(
        id=1, user_id=1, book_id=1, last_modified=datetime.now(UTC)
    )
    reading_state.statistics = None

    result = metadata_service.get_reading_state_response(book, reading_state, None)
    assert "Statistics" in result
    statistics = result["Statistics"]
    assert isinstance(statistics, dict)
    assert "SpentReadingMinutes" not in statistics


def test_get_reading_state_response_without_bookmark(
    metadata_service: KoboMetadataService,
    book: Book,
) -> None:
    """Test getting reading state response without bookmark.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    reading_state = KoboReadingState(
        id=1, user_id=1, book_id=1, last_modified=datetime.now(UTC)
    )
    reading_state.current_bookmark = None

    result = metadata_service.get_reading_state_response(book, reading_state, None)
    assert "CurrentBookmark" in result
    bookmark = result["CurrentBookmark"]
    assert isinstance(bookmark, dict)
    assert "ProgressPercent" not in bookmark


# ============================================================================
# Tests for KoboMetadataService._get_read_status_for_kobo
# ============================================================================


@pytest.mark.parametrize(
    ("status_enum", "expected"),
    [
        (None, "ReadyToRead"),
        (ReadStatusEnum.NOT_READ, "ReadyToRead"),
        (ReadStatusEnum.READ, "Finished"),
        (ReadStatusEnum.READING, "Reading"),
    ],
)
def test_get_read_status_for_kobo(
    metadata_service: KoboMetadataService,
    status_enum: ReadStatusEnum | None,
    expected: str,
) -> None:
    """Test converting read status to Kobo format.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    status_enum : ReadStatusEnum | None
        Read status enum.
    expected : str
        Expected Kobo status string.
    """
    result = metadata_service._get_read_status_for_kobo(status_enum)
    assert result == expected


# ============================================================================
# Tests for KoboMetadataService.get_kepub_format
# ============================================================================


def test_get_kepub_format_found(
    metadata_service: KoboMetadataService, book: Book
) -> None:
    """Test getting KEPUB format when available.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[{"format": "KEPUB", "name": "test.kepub", "size": 1000}],
    )
    result = metadata_service.get_kepub_format(book_with_rels)
    assert result == "KEPUB"


def test_get_kepub_format_not_found(
    metadata_service: KoboMetadataService, book_with_rels: BookWithFullRelations
) -> None:
    """Test getting KEPUB format when not available.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    """
    result = metadata_service.get_kepub_format(book_with_rels)
    assert result is None


def test_get_kepub_format_case_insensitive(
    metadata_service: KoboMetadataService, book: Book
) -> None:
    """Test getting KEPUB format with case insensitive matching.

    Parameters
    ----------
    metadata_service : KoboMetadataService
        Service instance.
    book : Book
        Test book.
    """
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=[],
        series=None,
        series_id=None,
        tags=[],
        identifiers=[],
        description=None,
        publisher=None,
        publisher_id=None,
        languages=[],
        language_ids=[],
        rating=None,
        rating_id=None,
        formats=[{"format": "kepub", "name": "test.kepub", "size": 1000}],
    )
    result = metadata_service.get_kepub_format(book_with_rels)
    assert result == "KEPUB"
