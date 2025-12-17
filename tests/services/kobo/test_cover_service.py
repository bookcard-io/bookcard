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

"""Tests for KoboCoverService to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse

from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.kobo.cover_service import KoboCoverService
from bookcard.services.kobo.store_proxy_service import KoboStoreProxyService

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_book_service() -> MagicMock:
    """Create a mock BookService.

    Returns
    -------
    MagicMock
        Mock book service instance.
    """
    service = MagicMock()
    service.get_book = MagicMock(return_value=None)
    service.get_thumbnail_path = MagicMock(return_value=None)
    return service


@pytest.fixture
def mock_book_lookup_service() -> MagicMock:
    """Create a mock KoboBookLookupService.

    Returns
    -------
    MagicMock
        Mock book lookup service instance.
    """
    service = MagicMock()
    service.find_book_by_uuid = MagicMock(return_value=None)
    return service


@pytest.fixture
def mock_proxy_service() -> MagicMock:
    """Create a mock KoboStoreProxyService.

    Returns
    -------
    MagicMock
        Mock proxy service instance.
    """
    service = MagicMock(spec=KoboStoreProxyService)
    service.should_proxy = MagicMock(return_value=False)
    return service


@pytest.fixture
def cover_service(
    mock_book_service: MagicMock,
    mock_book_lookup_service: MagicMock,
    mock_proxy_service: MagicMock,
) -> KoboCoverService:
    """Create KoboCoverService instance for testing.

    Parameters
    ----------
    mock_book_service : MagicMock
        Mock book service.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_proxy_service : MagicMock
        Mock proxy service.

    Returns
    -------
    KoboCoverService
        Service instance.
    """
    return KoboCoverService(
        mock_book_service,  # type: ignore[arg-type]
        mock_book_lookup_service,
        mock_proxy_service,
    )


@pytest.fixture
def book() -> Book:
    """Create a test book.

    Returns
    -------
    Book
        Book instance.
    """
    return Book(id=1, title="Test Book", uuid="test-uuid-123")


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
        authors=["Author One"],
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
        formats=[],
    )


@pytest.fixture
def cover_file() -> Path:
    """Create a temporary cover file.

    Returns
    -------
    Path
        Path to temporary cover file.
    """
    with NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"fake image data")
        return Path(f.name)


# ============================================================================
# Tests for KoboCoverService.__init__
# ============================================================================


def test_init(
    mock_book_service: MagicMock,
    mock_book_lookup_service: MagicMock,
    mock_proxy_service: MagicMock,
) -> None:
    """Test KoboCoverService initialization.

    Parameters
    ----------
    mock_book_service : MagicMock
        Mock book service.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    service = KoboCoverService(
        mock_book_service,  # type: ignore[arg-type]
        mock_book_lookup_service,
        mock_proxy_service,
    )
    assert service._book_service == mock_book_service
    assert service._book_lookup_service == mock_book_lookup_service
    assert service._proxy_service == mock_proxy_service


# ============================================================================
# Tests for KoboCoverService.get_cover_image
# ============================================================================


def test_get_cover_image_success(
    cover_service: KoboCoverService,
    mock_book_lookup_service: MagicMock,
    mock_book_service: MagicMock,
    book: Book,
    book_with_rels: BookWithFullRelations,
    cover_file: Path,
) -> None:
    """Test getting cover image when book and cover exist.

    Parameters
    ----------
    cover_service : KoboCoverService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_book_service : MagicMock
        Mock book service.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    cover_file : Path
        Temporary cover file.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)
    mock_book_service.get_book.return_value = book_with_rels
    mock_book_service.get_thumbnail_path.return_value = cover_file

    result = cover_service.get_cover_image(
        book_uuid="test-uuid-123", width="300", height="400"
    )

    assert isinstance(result, FileResponse)
    assert result.path == str(cover_file)
    assert result.media_type == "image/jpeg"
    mock_book_lookup_service.find_book_by_uuid.assert_called_once_with("test-uuid-123")
    mock_book_service.get_book.assert_called_once_with(1)
    mock_book_service.get_thumbnail_path.assert_called_once_with(book_with_rels)

    # Cleanup
    cover_file.unlink()


def test_get_cover_image_book_not_found_redirect(
    cover_service: KoboCoverService,
    mock_book_lookup_service: MagicMock,
    mock_proxy_service: MagicMock,
) -> None:
    """Test redirecting when book not found and proxy enabled.

    Parameters
    ----------
    cover_service : KoboCoverService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = None
    mock_proxy_service.should_proxy.return_value = True

    result = cover_service.get_cover_image(
        book_uuid="non-existent", width="300", height="400"
    )

    assert isinstance(result, RedirectResponse)
    assert result.status_code == 307
    assert "cdn.kobo.com" in result.headers["location"]


def test_get_cover_image_book_not_found_no_proxy(
    cover_service: KoboCoverService,
    mock_book_lookup_service: MagicMock,
    mock_proxy_service: MagicMock,
) -> None:
    """Test raising exception when book not found and proxy disabled.

    Parameters
    ----------
    cover_service : KoboCoverService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = None
    mock_proxy_service.should_proxy.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        cover_service.get_cover_image(
            book_uuid="non-existent", width="300", height="400"
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "cover_not_found"


def test_get_cover_image_book_not_found_after_lookup(
    cover_service: KoboCoverService,
    mock_book_lookup_service: MagicMock,
    mock_book_service: MagicMock,
    book: Book,
    mock_proxy_service: MagicMock,
) -> None:
    """Test when book lookup succeeds but get_book returns None.

    Parameters
    ----------
    cover_service : KoboCoverService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_book_service : MagicMock
        Mock book service.
    book : Book
        Test book.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)
    mock_book_service.get_book.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        cover_service.get_cover_image(
            book_uuid="test-uuid-123", width="300", height="400"
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "book_not_found"


def test_get_cover_image_cover_not_found_redirect(
    cover_service: KoboCoverService,
    mock_book_lookup_service: MagicMock,
    mock_book_service: MagicMock,
    book: Book,
    book_with_rels: BookWithFullRelations,
    mock_proxy_service: MagicMock,
) -> None:
    """Test redirecting when cover not found and proxy enabled.

    Parameters
    ----------
    cover_service : KoboCoverService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_book_service : MagicMock
        Mock book service.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)
    mock_book_service.get_book.return_value = book_with_rels
    mock_book_service.get_thumbnail_path.return_value = None
    mock_proxy_service.should_proxy.return_value = True

    result = cover_service.get_cover_image(
        book_uuid="test-uuid-123", width="300", height="400"
    )

    assert isinstance(result, RedirectResponse)
    assert result.status_code == 307


def test_get_cover_image_cover_not_found_no_proxy(
    cover_service: KoboCoverService,
    mock_book_lookup_service: MagicMock,
    mock_book_service: MagicMock,
    book: Book,
    book_with_rels: BookWithFullRelations,
    mock_proxy_service: MagicMock,
) -> None:
    """Test raising exception when cover not found and proxy disabled.

    Parameters
    ----------
    cover_service : KoboCoverService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_book_service : MagicMock
        Mock book service.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)
    mock_book_service.get_book.return_value = book_with_rels
    mock_book_service.get_thumbnail_path.return_value = None
    mock_proxy_service.should_proxy.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        cover_service.get_cover_image(
            book_uuid="test-uuid-123", width="300", height="400"
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "cover_not_found"


def test_get_cover_image_cover_path_not_exists_redirect(
    cover_service: KoboCoverService,
    mock_book_lookup_service: MagicMock,
    mock_book_service: MagicMock,
    book: Book,
    book_with_rels: BookWithFullRelations,
    mock_proxy_service: MagicMock,
) -> None:
    """Test redirecting when cover path does not exist and proxy enabled.

    Parameters
    ----------
    cover_service : KoboCoverService
        Service instance.
    mock_book_lookup_service : MagicMock
        Mock book lookup service.
    mock_book_service : MagicMock
        Mock book service.
    book : Book
        Test book.
    book_with_rels : BookWithFullRelations
        Test book with relations.
    mock_proxy_service : MagicMock
        Mock proxy service.
    """
    non_existent_path = Path("/non/existent/cover.jpg")
    mock_book_lookup_service.find_book_by_uuid.return_value = (1, book)
    mock_book_service.get_book.return_value = book_with_rels
    mock_book_service.get_thumbnail_path.return_value = non_existent_path
    mock_proxy_service.should_proxy.return_value = True

    result = cover_service.get_cover_image(
        book_uuid="test-uuid-123", width="300", height="400"
    )

    assert isinstance(result, RedirectResponse)
    assert result.status_code == 307
