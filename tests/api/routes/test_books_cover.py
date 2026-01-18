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

"""Tests for book cover upload API endpoint."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Generator

from bookcard.api.deps import get_current_user, get_db_session
from bookcard.api.main import app
from bookcard.api.routes.books import (
    _get_active_library_service,
    _get_cover_service,
    _get_permission_helper,
)
from bookcard.models.auth import User
from bookcard.models.core import Book
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.book_cover_service import BookCoverService
from bookcard.services.book_service import BookService


@pytest.fixture
def mock_cover_service() -> MagicMock:
    """Create mock cover service."""
    return MagicMock(spec=BookCoverService)


@pytest.fixture
def mock_book_service() -> MagicMock:
    """Create mock book service."""
    return MagicMock(spec=BookService)


@pytest.fixture
def override_dependencies(
    mock_book_service: MagicMock,
    mock_cover_service: MagicMock,
    session: object,
) -> Generator[None, None, None]:
    """Override API dependencies."""
    # Ensure clean state
    app.dependency_overrides = {}

    # Mock permission helper
    mock_permission_helper = MagicMock()
    mock_permission_helper.check_write_permission.return_value = None

    def mock_get_active_library_service() -> BookService:
        return mock_book_service

    def mock_get_cover_service() -> BookCoverService:
        return mock_cover_service

    def mock_get_permission_helper() -> MagicMock:
        return mock_permission_helper

    def mock_get_db_session() -> Generator[object, None, None]:
        yield session

    def mock_get_current_user() -> User:
        return User(id=1, username="test", is_admin=True)

    app.dependency_overrides[_get_active_library_service] = (
        mock_get_active_library_service
    )
    app.dependency_overrides[_get_cover_service] = mock_get_cover_service
    app.dependency_overrides[_get_permission_helper] = mock_get_permission_helper
    app.dependency_overrides[get_db_session] = mock_get_db_session
    app.dependency_overrides[get_current_user] = mock_get_current_user

    yield

    app.dependency_overrides = {}


@pytest.fixture
def client(override_dependencies: None) -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_upload_cover_image_success(
    client: TestClient,
    mock_book_service: MagicMock,
    mock_cover_service: MagicMock,
) -> None:
    """Test successful cover upload."""
    book_id = 1
    mock_book = BookWithFullRelations(
        book=Book(id=book_id, title="Test", has_cover=False),
        authors=[],
        tags=[],
        identifiers=[],
        formats=[],
        languages=[],
        language_ids=[],
        series=None,
        series_id=None,
        description=None,
        publisher=None,
        publisher_id=None,
        rating=None,
        rating_id=None,
    )
    mock_book_service.get_book_full.return_value = mock_book
    mock_cover_service.save_cover_image.return_value = f"/api/books/{book_id}/cover"

    # Create valid image bytes for the test
    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()

    files = {"file": ("cover.jpg", image_bytes, "image/jpeg")}

    response = client.post(
        f"/books/{book_id}/cover",
        files=files,
    )

    assert response.status_code == 200
    assert response.json() == {"temp_url": f"/api/books/{book_id}/cover"}


def test_upload_cover_image_book_not_found(
    client: TestClient,
    mock_book_service: MagicMock,
) -> None:
    """Test upload fails when book not found."""
    book_id = 999
    mock_book_service.get_book_full.return_value = None

    files = {"file": ("cover.jpg", b"fake-content", "image/jpeg")}
    response = client.post(
        f"/books/{book_id}/cover",
        files=files,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "book_not_found"


def test_upload_cover_image_invalid_file(
    client: TestClient,
    mock_book_service: MagicMock,
    mock_cover_service: MagicMock,
) -> None:
    """Test upload fails when file is invalid."""
    book_id = 1
    mock_book = BookWithFullRelations(
        book=Book(id=book_id, title="Test", has_cover=False),
        authors=[],
        tags=[],
        identifiers=[],
        formats=[],
        languages=[],
        language_ids=[],
        series=None,
        series_id=None,
        description=None,
        publisher=None,
        publisher_id=None,
        rating=None,
        rating_id=None,
    )
    mock_book_service.get_book_full.return_value = mock_book
    mock_cover_service.save_cover_image.side_effect = ValueError("invalid_image_format")

    files = {"file": ("cover.txt", b"not-an-image", "text/plain")}
    response = client.post(
        f"/books/{book_id}/cover",
        files=files,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_image_format"
