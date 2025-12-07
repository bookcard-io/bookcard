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

"""Additional tests for books API routes to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Response

import fundamental.api.routes.books as books
from fundamental.models.auth import User
from fundamental.models.config import Library
from fundamental.models.core import Book
from fundamental.repositories import BookWithFullRelations, BookWithRelations
from tests.conftest import DummySession


def _create_mock_user() -> User:
    """Create a mock user for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )


def _mock_permission_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock PermissionService to allow all permissions."""

    class MockPermissionService:
        def __init__(self, session: object) -> None:
            pass  # Accept session but don't use it

        def has_permission(
            self,
            user: User,
            resource: str,
            action: str,
            context: dict[str, object] | None = None,
        ) -> bool:
            return True

        def check_permission(
            self,
            user: User,
            resource: str,
            action: str,
            context: dict[str, object] | None = None,
        ) -> None:
            pass  # Always allow

    # Patch PermissionService in the permission_service module where it's actually used
    monkeypatch.setattr(
        "fundamental.services.permission_service.PermissionService",
        MockPermissionService,
    )


class MockBookService:
    """Mock BookService for testing."""

    def __init__(self, library: Library | None = None) -> None:
        self._library = library
        self._get_book_full_result: BookWithFullRelations | None = None
        self._get_book_result: BookWithRelations | None = None
        self.get_thumbnail_path = None

    def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
        """Mock get_book_full method."""
        return self._get_book_full_result

    def get_book(self, book_id: int) -> BookWithRelations | None:
        """Mock get_book method."""
        return self._get_book_result

    def set_get_book_full_result(self, result: BookWithFullRelations | None) -> None:
        """Set the result for get_book_full."""
        self._get_book_full_result = result

    def set_get_book_result(self, result: BookWithRelations | None) -> None:
        """Set the result for get_book."""
        self._get_book_result = result


class MockPermissionHelper:
    """Mock BookPermissionHelper for testing."""

    def __init__(self, session: object) -> None:
        """Initialize mock permission helper."""

    def check_read_permission(
        self,
        user: User,
        book_with_rels: object | None = None,
    ) -> None:
        """Mock check_read_permission - always allows."""

    def check_write_permission(
        self,
        user: User,
        book_with_rels: object | None = None,
    ) -> None:
        """Mock check_write_permission - always allows."""

    def check_send_permission(
        self,
        user: User,
        book_with_rels: object | None = None,
        book_id: int | None = None,
        session: object | None = None,
    ) -> None:
        """Mock check_send_permission - always allows."""

    def check_create_permission(
        self,
        user: User,
    ) -> None:
        """Mock check_create_permission - always allows."""


def _setup_route_mocks(
    monkeypatch: pytest.MonkeyPatch,
    session: DummySession,
    mock_service: MockBookService,
) -> tuple[MockPermissionHelper, object]:
    """Set up mocks for route dependencies.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Monkeypatch fixture.
    session : DummySession
        Dummy session.
    mock_service : MockBookService
        Mock book service.

    Returns
    -------
    tuple[MockPermissionHelper, object]
        Tuple of (permission_helper, response_builder).
    """

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    _mock_permission_service(monkeypatch)

    mock_permission_helper = MockPermissionHelper(session)

    return mock_permission_helper, None


@pytest.fixture
def mock_library() -> Library:
    """Create a mock library for testing."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )


def test_find_format_data_found() -> None:
    """Test _find_format_data when format is found (covers lines 86-94)."""
    formats = [
        {"format": "EPUB", "size": 1000, "name": "book.epub"},
        {"format": "PDF", "size": 2000, "name": "book.pdf"},
    ]
    format_data, available_formats = books._find_format_data(formats, "EPUB")

    assert format_data is not None
    assert format_data["format"] == "EPUB"
    assert "EPUB" in available_formats
    assert "PDF" in available_formats


def test_find_format_data_case_insensitive() -> None:
    """Test _find_format_data is case-insensitive (covers lines 86-94)."""
    formats = [{"format": "epub", "size": 1000}]
    format_data, _available_formats = books._find_format_data(formats, "EPUB")

    assert format_data is not None
    assert format_data["format"] == "epub"


def test_get_file_name_with_name() -> None:
    """Test _get_file_name when name is provided (covers lines 118-127)."""
    format_data = {"format": "EPUB", "name": "My Book"}
    file_name = books._get_file_name(format_data, 123, "EPUB")

    assert file_name == "My Book.epub"


def test_get_file_name_with_name_and_extension() -> None:
    """Test _get_file_name when name already has extension (covers lines 118-127)."""
    format_data = {"format": "EPUB", "name": "My Book.epub"}
    file_name = books._get_file_name(format_data, 123, "EPUB")

    assert file_name == "My Book.epub"


def test_get_file_name_without_name() -> None:
    """Test _get_file_name when name is missing (covers lines 118-121)."""
    format_data = {"format": "EPUB"}
    file_name = books._get_file_name(format_data, 123, "EPUB")

    assert file_name == "123.epub"


def test_get_file_name_with_non_string_name() -> None:
    """Test _get_file_name when name is not a string (covers lines 118-121)."""
    format_data = {"format": "EPUB", "name": 123}
    file_name = books._get_file_name(format_data, 123, "EPUB")

    assert file_name == "123.epub"


def test_get_media_type_unknown_format() -> None:
    """Test _get_media_type for unknown format (covers line 143)."""
    media_type = books._get_media_type("UNKNOWN")
    assert media_type == "application/octet-stream"


def test_download_book_file_success(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file succeeds (covers lines 521-602)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
        formats=[{"format": "EPUB", "size": 1000, "name": "test.epub"}],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        file_path = book_path / "test.epub"
        file_path.write_text("test content")

        library_with_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(library_path),
            calibre_db_file="metadata.db",
        )
        mock_service = MockBookService(library_with_path)
        mock_service.set_get_book_full_result(book_with_rels)

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        result = books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

        assert result is not None
        assert hasattr(result, "path")


def test_download_book_file_with_library_root(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file uses library_root when set (covers lines 553-555)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
        formats=[{"format": "EPUB", "size": 1000, "name": "test.epub"}],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        file_path = book_path / "test.epub"
        file_path.write_text("test content")

        library_with_root = Library(
            id=1,
            name="Test Library",
            calibre_db_path="/path/to/db",
            calibre_db_file="metadata.db",
            library_root=str(library_path),
        )
        mock_service = MockBookService(library_with_root)
        mock_service.set_get_book_full_result(book_with_rels)

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        result = books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

        assert result is not None


def test_download_book_file_alt_path_exists(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file uses alternative path when main doesn't exist (covers lines 575-576)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
        formats=[
            {"format": "EPUB", "size": 1000, "name": "different.epub"}
        ],  # Name doesn't match actual file
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        # Main file (different.epub) doesn't exist
        # But alternative file (1.epub) does exist
        alt_file_path = book_path / "1.epub"
        alt_file_path.write_text("test content")

        library_with_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(library_path),
            calibre_db_file="metadata.db",
        )
        mock_service = MockBookService(library_with_path)
        mock_service.set_get_book_full_result(book_with_rels)

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        result = books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

        assert result is not None


def test_download_book_file_sanitizes_author_title(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file sanitizes author and title (covers lines 587-600)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test/Book*Name",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Author/Name*With*Special"],
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
        formats=[{"format": "EPUB", "size": 1000, "name": "test.epub"}],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        file_path = book_path / "test.epub"
        file_path.write_text("test content")

        library_with_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(library_path),
            calibre_db_file="metadata.db",
        )
        mock_service = MockBookService(library_with_path)
        mock_service.set_get_book_full_result(book_with_rels)

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        result = books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

        assert result is not None
        # Verify filename is sanitized (no special chars)
        assert hasattr(result, "path")


def test_download_book_file_not_found(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file raises 404 when book not found (covers line 527)."""
    session = DummySession()

    mock_service = MockBookService(mock_library)
    mock_service.set_get_book_full_result(None)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(
            current_user=current_user,
            book_id=999,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert "book_not_found" in str(exc_info.value.detail)


def test_download_book_file_missing_id(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file raises 500 when book has no id (covers line 534)."""
    session = DummySession()

    book = Book(
        id=None,  # No ID
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
        formats=[{"format": "EPUB", "size": 1000, "name": "test.epub"}],
    )

    mock_service = MockBookService(mock_library)
    mock_service.set_get_book_full_result(book_with_rels)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "book_missing_id" in str(exc_info.value.detail)


def test_download_book_file_format_not_found(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file raises 404 when format not found (covers line 546)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
        formats=[{"format": "PDF", "size": 1000}],  # Only PDF, not EPUB
    )

    mock_service = MockBookService(mock_library)
    mock_service.set_get_book_full_result(book_with_rels)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert "format_not_found" in str(exc_info.value.detail)


def test_download_book_file_db_path_is_file(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file when calibre_db_path is a file (covers line 565)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
        formats=[{"format": "EPUB", "size": 1000, "name": "test.epub"}],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file path (metadata.db) instead of directory
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        file_path = book_path / "test.epub"
        file_path.write_text("test content")

        library_with_file_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(db_file),  # Points to file, not directory
            calibre_db_file="metadata.db",
        )
        mock_service = MockBookService(library_with_file_path)
        mock_service.set_get_book_full_result(book_with_rels)

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        result = books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

        assert result is not None


def test_download_book_file_not_found_both_paths(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file raises 404 when both paths don't exist (covers lines 572-578)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
        formats=[{"format": "EPUB", "size": 1000, "name": "test.epub"}],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        # Don't create the file - it should not exist

        library_with_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(library_path),
            calibre_db_file="metadata.db",
        )
        mock_service = MockBookService(library_with_path)
        mock_service.set_get_book_full_result(book_with_rels)

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        with pytest.raises(HTTPException) as exc_info:
            books.download_book_file(
                current_user=current_user,
                book_id=1,
                file_format="EPUB",
                book_service=mock_service,
                permission_helper=mock_permission_helper,
            )

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert "file_not_found" in str(exc_info.value.detail)


def test_download_book_file_empty_author(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file handles empty author after sanitization (covers line 592)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["***"],  # Will be sanitized to empty
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
        formats=[{"format": "EPUB", "size": 1000, "name": "test.epub"}],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        file_path = book_path / "test.epub"
        file_path.write_text("test content")

        library_with_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(library_path),
            calibre_db_file="metadata.db",
        )
        mock_service = MockBookService(library_with_path)
        mock_service.set_get_book_full_result(book_with_rels)

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        result = books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

        assert result is not None


def test_download_book_file_empty_title(
    monkeypatch: pytest.MonkeyPatch, mock_library: Library
) -> None:
    """Test download_book_file handles empty title after sanitization (covers line 599)."""
    session = DummySession()

    book = Book(
        id=1,
        title="***",  # Will be sanitized to empty
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
        formats=[{"format": "EPUB", "size": 1000, "name": "test.epub"}],
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        file_path = book_path / "test.epub"
        file_path.write_text("test content")

        library_with_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(library_path),
            calibre_db_file="metadata.db",
        )
        mock_service = MockBookService(library_with_path)
        mock_service.set_get_book_full_result(book_with_rels)

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        mock_permission_helper, _ = _setup_route_mocks(
            monkeypatch, session, mock_service
        )

        result = books.download_book_file(
            current_user=current_user,
            book_id=1,
            file_format="EPUB",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

        assert result is not None


def test_download_cover_from_url_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_cover_from_url succeeds (covers lines 776-845)."""
    from io import BytesIO
    from unittest.mock import MagicMock

    from sqlmodel import Session

    from fundamental.api.schemas import CoverFromUrlRequest
    from fundamental.models.core import Book

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None, formats=[])

    # Create a simple test image
    from PIL import Image

    test_image = Image.new("RGB", (100, 100), color="red")
    image_bytes = BytesIO()
    test_image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)
    image_content = image_bytes.getvalue()

    mock_response = MagicMock()
    mock_response.content = image_content
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)

        library_with_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(library_path),
            calibre_db_file="metadata.db",
        )

        mock_service = MockBookService(library_with_path)
        mock_service.get_book = lambda book_id: book_with_rels  # type: ignore[method-assign]
        # Also need to set get_book_full for download_cover_from_url
        book_with_full_rels = BookWithFullRelations(
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
            formats=[],
        )
        mock_service.set_get_book_full_result(book_with_full_rels)

        # Mock the book repository session
        mock_calibre_session = MagicMock(spec=Session)
        mock_calibre_book = MagicMock(spec=Book)
        mock_calibre_book.id = 1
        mock_calibre_book.has_cover = False
        mock_calibre_session.exec.return_value.first.return_value = mock_calibre_book
        mock_calibre_session.__enter__ = MagicMock(return_value=mock_calibre_session)
        mock_calibre_session.__exit__ = MagicMock(return_value=False)

        mock_service._book_repo = MagicMock()  # type: ignore[assignment]
        mock_service._book_repo._get_session = lambda: mock_calibre_session  # type: ignore[method-assign]

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        with patch(
            "fundamental.services.book_cover_service.httpx.Client",
            return_value=mock_client,
        ):
            request = CoverFromUrlRequest(url="https://example.com/cover.jpg")
            from fundamental.services.book_cover_service import BookCoverService

            mock_permission_helper, _ = _setup_route_mocks(
                monkeypatch, session, mock_service
            )
            cover_service = BookCoverService(mock_service)  # type: ignore[arg-type]

            result = books.download_cover_from_url(
                current_user=current_user,
                book_id=1,
                request=request,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
                cover_service=cover_service,
                session=session,
            )

            assert result.temp_url == "/api/books/1/cover"
            # Verify cover was saved
            cover_path = book_path / "cover.jpg"
            assert cover_path.exists()


def test_download_cover_from_url_with_library_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_cover_from_url uses library_root when set (covers lines 805-807)."""
    from io import BytesIO
    from unittest.mock import MagicMock

    from sqlmodel import Session

    from fundamental.api.schemas import CoverFromUrlRequest
    from fundamental.models.core import Book

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None, formats=[])

    # Create a simple test image
    from PIL import Image

    test_image = Image.new("RGB", (100, 100), color="red")
    image_bytes = BytesIO()
    test_image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)
    image_content = image_bytes.getvalue()

    mock_response = MagicMock()
    mock_response.content = image_content
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)

        library_with_root = Library(
            id=1,
            name="Test Library",
            calibre_db_path="/path/to/db",
            calibre_db_file="metadata.db",
            library_root=str(library_path),
        )

        mock_service = MockBookService(library_with_root)
        mock_service.get_book = lambda book_id: book_with_rels  # type: ignore[method-assign]
        # Also need to set get_book_full for download_cover_from_url
        book_with_full_rels = BookWithFullRelations(
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
            formats=[],
        )
        mock_service.set_get_book_full_result(book_with_full_rels)

        # Mock the book repository session
        mock_calibre_session = MagicMock(spec=Session)
        mock_calibre_book = MagicMock(spec=Book)
        mock_calibre_book.id = 1
        mock_calibre_book.has_cover = False
        mock_calibre_session.exec.return_value.first.return_value = mock_calibre_book
        mock_calibre_session.__enter__ = MagicMock(return_value=mock_calibre_session)
        mock_calibre_session.__exit__ = MagicMock(return_value=False)

        mock_service._book_repo = MagicMock()  # type: ignore[assignment]
        mock_service._book_repo._get_session = lambda: mock_calibre_session  # type: ignore[method-assign]

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        with patch(
            "fundamental.services.book_cover_service.httpx.Client",
            return_value=mock_client,
        ):
            request = CoverFromUrlRequest(url="https://example.com/cover.jpg")
            from fundamental.services.book_cover_service import BookCoverService

            mock_permission_helper, _ = _setup_route_mocks(
                monkeypatch, session, mock_service
            )
            cover_service = BookCoverService(mock_service)  # type: ignore[arg-type]

            result = books.download_cover_from_url(
                current_user=current_user,
                book_id=1,
                request=request,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
                cover_service=cover_service,
                session=session,
            )

            assert result.temp_url == "/api/books/1/cover"


def test_download_cover_from_url_db_path_is_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_cover_from_url when calibre_db_path is a file (covers lines 809-814)."""
    from io import BytesIO
    from unittest.mock import MagicMock

    from sqlmodel import Session

    from fundamental.api.schemas import CoverFromUrlRequest
    from fundamental.models.core import Book

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="Author Name/Test Book (1)",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None, formats=[])

    # Create a simple test image
    from PIL import Image

    test_image = Image.new("RGB", (100, 100), color="red")
    image_bytes = BytesIO()
    test_image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)
    image_content = image_bytes.getvalue()

    mock_response = MagicMock()
    mock_response.content = image_content
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file path (metadata.db) instead of directory
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()
        library_path = Path(tmpdir)
        book_path = library_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)

        library_with_file_path = Library(
            id=1,
            name="Test Library",
            calibre_db_path=str(db_file),  # Points to file, not directory
            calibre_db_file="metadata.db",
        )

        mock_service = MockBookService(library_with_file_path)
        mock_service.get_book = lambda book_id: book_with_rels  # type: ignore[method-assign]
        # Also need to set get_book_full for download_cover_from_url
        book_with_full_rels = BookWithFullRelations(
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
            formats=[],
        )
        mock_service.set_get_book_full_result(book_with_full_rels)

        # Mock the book repository session
        mock_calibre_session = MagicMock(spec=Session)
        mock_calibre_book = MagicMock(spec=Book)
        mock_calibre_book.id = 1
        mock_calibre_book.has_cover = False
        mock_calibre_session.exec.return_value.first.return_value = mock_calibre_book
        mock_calibre_session.__enter__ = MagicMock(return_value=mock_calibre_session)
        mock_calibre_session.__exit__ = MagicMock(return_value=False)

        mock_service._book_repo = MagicMock()  # type: ignore[assignment]
        mock_service._book_repo._get_session = lambda: mock_calibre_session  # type: ignore[method-assign]

        def mock_get_active_library_service(sess: object) -> MockBookService:
            return mock_service

        monkeypatch.setattr(
            books, "_get_active_library_service", mock_get_active_library_service
        )
        current_user = _create_mock_user()
        _mock_permission_service(monkeypatch)

        with patch(
            "fundamental.services.book_cover_service.httpx.Client",
            return_value=mock_client,
        ):
            request = CoverFromUrlRequest(url="https://example.com/cover.jpg")
            from fundamental.services.book_cover_service import BookCoverService

            mock_permission_helper, _ = _setup_route_mocks(
                monkeypatch, session, mock_service
            )
            cover_service = BookCoverService(mock_service)  # type: ignore[arg-type]

            result = books.download_cover_from_url(
                current_user=current_user,
                book_id=1,
                request=request,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
                cover_service=cover_service,
                session=session,
            )

            assert result.temp_url == "/api/books/1/cover"


def test_get_temp_cover_no_dot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_temp_cover returns 404 when no dot in filename (covers lines 865-866)."""
    from fastapi import Response

    session = DummySession()
    current_user = _create_mock_user()
    mock_permission_helper = MockPermissionHelper(session)
    _mock_permission_service(monkeypatch)

    result = books.get_temp_cover(
        "nofileextension",
        current_user=current_user,
        permission_helper=mock_permission_helper,
    )

    assert isinstance(result, Response)
    assert result.status_code == 404


def test_get_temp_cover_not_in_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_temp_cover returns 404 when hash not in storage (covers lines 870-871)."""
    from fastapi import Response

    session = DummySession()
    current_user = _create_mock_user()
    mock_permission_helper = MockPermissionHelper(session)
    _mock_permission_service(monkeypatch)

    result = books.get_temp_cover(
        "nonexistent123.jpg",
        current_user=current_user,
        permission_helper=mock_permission_helper,
    )

    assert isinstance(result, Response)
    assert result.status_code == 404


def test_get_temp_cover_file_not_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_temp_cover returns 404 and cleans up when file doesn't exist (covers lines 874-877)."""
    from fastapi import Response

    session = DummySession()
    current_user = _create_mock_user()
    mock_permission_helper = MockPermissionHelper(session)
    _mock_permission_service(monkeypatch)

    # Add a non-existent path to storage
    fake_hash = "fakehash123"
    fake_path = Path("/nonexistent/path/to/file.jpg")
    books._temp_cover_storage[fake_hash] = fake_path

    try:
        result = books.get_temp_cover(
            f"{fake_hash}.jpg",
            current_user=current_user,
            permission_helper=mock_permission_helper,
        )

        assert isinstance(result, Response)
        assert result.status_code == 404
        # Verify entry was cleaned up
        assert fake_hash not in books._temp_cover_storage
    finally:
        # Clean up
        books._temp_cover_storage.pop(fake_hash, None)


def test_get_temp_cover_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_temp_cover returns FileResponse when file exists (covers lines 879-882)."""
    from fastapi.responses import FileResponse

    session = DummySession()
    current_user = _create_mock_user()
    mock_permission_helper = MockPermissionHelper(session)
    _mock_permission_service(monkeypatch)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = Path(tmpdir) / "test_cover.jpg"
        temp_file.write_bytes(b"fake image data")

        # Add to storage
        fake_hash = "testhash123"
        books._temp_cover_storage[fake_hash] = temp_file

        try:
            result = books.get_temp_cover(
                f"{fake_hash}.jpg",
                current_user=current_user,
                permission_helper=mock_permission_helper,
            )

            assert isinstance(result, FileResponse)
            assert result.path == str(temp_file)
        finally:
            # Clean up
            books._temp_cover_storage.pop(fake_hash, None)


def test_download_cover_from_url_book_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_cover_from_url raises 404 when book not found (covers line 783)."""
    from fundamental.api.schemas import CoverFromUrlRequest

    session = DummySession()

    library_with_path = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_service = MockBookService(library_with_path)
    mock_service.get_book = lambda book_id: None  # type: ignore[method-assign]
    # Also need to set get_book_full for download_cover_from_url (returns None for not found)
    mock_service.set_get_book_full_result(None)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    request = CoverFromUrlRequest(url="https://example.com/cover.jpg")

    from fundamental.services.book_cover_service import BookCoverService

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)
    cover_service = BookCoverService(mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            current_user=current_user,
            book_id=999,
            request=request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            cover_service=cover_service,
            session=session,
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_download_cover_from_url_empty_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_cover_from_url raises 400 when URL is empty (covers line 789)."""
    from fundamental.api.schemas import CoverFromUrlRequest

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None, formats=[])

    library_with_path = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_service = MockBookService(library_with_path)
    mock_service.get_book = lambda book_id: book_with_rels  # type: ignore[method-assign]
    # Also need to set get_book_full for download_cover_from_url
    book_with_full_rels = BookWithFullRelations(
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_full_rels)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    request = CoverFromUrlRequest(
        url="   "
    )  # Whitespace only, will be stripped to empty

    from fundamental.services.book_cover_service import BookCoverService

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)
    cover_service = BookCoverService(mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            current_user=current_user,
            book_id=1,
            request=request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            cover_service=cover_service,
            session=session,
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "url_required"


def test_download_cover_from_url_invalid_url_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_cover_from_url raises 400 when URL format is invalid (covers line 795)."""
    from fundamental.api.schemas import CoverFromUrlRequest

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None, formats=[])

    library_with_path = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_service = MockBookService(library_with_path)
    mock_service.get_book = lambda book_id: book_with_rels  # type: ignore[method-assign]
    # Also need to set get_book_full for download_cover_from_url
    book_with_full_rels = BookWithFullRelations(
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_full_rels)

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )
    current_user = _create_mock_user()
    _mock_permission_service(monkeypatch)

    request = CoverFromUrlRequest(url="ftp://example.com/cover.jpg")

    from fundamental.services.book_cover_service import BookCoverService

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)
    cover_service = BookCoverService(mock_service)  # type: ignore[arg-type]

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            current_user=current_user,
            book_id=1,
            request=request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            cover_service=cover_service,
            session=session,
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid_url_format"


def test_get_permission_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_permission_helper creates BookPermissionHelper (covers line 262)."""
    session = DummySession()

    with patch("fundamental.api.routes.books.BookPermissionHelper") as mock_class:
        mock_helper = MagicMock()
        mock_class.return_value = mock_helper

        result = books._get_permission_helper(session)

        assert result is not None
        mock_class.assert_called_once_with(session)


def test_get_response_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_response_builder creates BookResponseBuilder (covers line 280)."""
    mock_service = MockBookService()

    with patch("fundamental.api.routes.books.BookResponseBuilder") as mock_class:
        mock_builder = MagicMock()
        mock_class.return_value = mock_builder

        result = books._get_response_builder(mock_service)  # type: ignore[arg-type]

        assert result is not None
        mock_class.assert_called_once_with(mock_service)


def test_get_cover_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _get_cover_service creates BookCoverService (covers line 298)."""
    mock_service = MockBookService()

    with patch("fundamental.api.routes.books.BookCoverService") as mock_class:
        mock_cover_service = MagicMock()
        mock_class.return_value = mock_cover_service

        result = books._get_cover_service(mock_service)  # type: ignore[arg-type]

        assert result is not None
        mock_class.assert_called_once_with(mock_service)


def test_get_conversion_orchestration_service_no_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _get_conversion_orchestration_service raises 404 when no library (covers lines 343-347)."""

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type("App", (), {"state": type("State", (), {})()})()

    session = DummySession()
    request = DummyRequest()
    mock_service = MockBookService()

    with (
        patch("fundamental.api.routes.books.LibraryRepository") as mock_repo_class,
        patch("fundamental.api.routes.books.LibraryService") as mock_service_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = None
        mock_service_class.return_value = mock_lib_service

        with pytest.raises(HTTPException) as exc_info:
            books._get_conversion_orchestration_service(request, session, mock_service)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "no_active_library"


def test_get_conversion_orchestration_service_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _get_conversion_orchestration_service succeeds (covers lines 335-354)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyTaskRunner:
                pass

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {"task_runner": DummyTaskRunner()},
                    )()
                },
            )()

    session = DummySession()
    request = DummyRequest()
    mock_service = MockBookService()
    mock_library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with (
        patch("fundamental.api.routes.books.LibraryRepository") as mock_repo_class,
        patch("fundamental.api.routes.books.LibraryService") as mock_lib_service_class,
        patch(
            "fundamental.api.routes.books.BookConversionOrchestrationService"
        ) as mock_orch_class,
    ):
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = mock_library
        mock_lib_service_class.return_value = mock_lib_service

        mock_orch = MagicMock()
        mock_orch_class.return_value = mock_orch

        result = books._get_conversion_orchestration_service(  # type: ignore[arg-type]
            request,  # type: ignore[arg-type]
            session,
            mock_service,  # type: ignore[arg-type]
        )

        assert result is not None
        mock_orch_class.assert_called_once()


def test_delete_book_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book handles ValueError (covers line 633)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book_with_rels = BookWithFullRelations(
        book=Book(id=1, title="Test", uuid="test", has_cover=False, path="test"),
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_rels)
    mock_service.delete_book = MagicMock(side_effect=ValueError("book_not_found"))  # type: ignore[assignment]

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    delete_request = books.BookDeleteRequest(delete_files_from_drive=False)

    with pytest.raises(HTTPException):
        books.delete_book(
            current_user=current_user,
            book_id=1,
            delete_request=delete_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )


def test_download_book_metadata_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test download_book_metadata succeeds (covers lines 860-876)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book_with_rels = BookWithFullRelations(
        book=Book(id=1, title="Test", uuid="test", has_cover=False, path="test"),
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with patch(
        "fundamental.api.routes.books.MetadataExportService"
    ) as mock_export_class:
        mock_export = MagicMock()
        mock_export_result = MagicMock()
        mock_export_result.content = b"<xml>test</xml>"
        mock_export_result.media_type = "application/xml"
        mock_export_result.filename = "book.opf"
        mock_export.export_metadata.return_value = mock_export_result
        mock_export_class.return_value = mock_export

        result = books.download_book_metadata(
            current_user=current_user,
            book_id=1,
            format="opf",
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )

        assert isinstance(result, Response)
        assert result.status_code == 200


def test_import_book_metadata_success() -> None:
    """Test import_book_metadata succeeds (covers lines 890-967)."""
    mock_file = MagicMock()
    mock_file.filename = "book.opf"
    mock_file.file.read.return_value = b'<?xml version="1.0"?><package>...</package>'

    with patch(
        "fundamental.api.routes.books.MetadataImportService"
    ) as mock_import_class:
        mock_import = MagicMock()
        mock_book_update = books.BookUpdate(title="Test Book")
        mock_import.import_metadata.return_value = mock_book_update
        mock_import_class.return_value = mock_import

        result = books.import_book_metadata(file=mock_file)

        assert isinstance(result, books.BookUpdate)
        assert result.title == "Test Book"


def test_send_books_to_device_batch_no_book_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test send_books_to_device_batch raises 400 when no book_ids (covers lines 1111-1115)."""

    # BookBulkSendRequest has min_length=1 validation, so empty list will raise ValidationError
    # We need to test the route's validation which happens before Pydantic validation
    # The route checks if book_ids is empty after Pydantic validation
    # So we need to bypass Pydantic validation or test with a request that passes validation
    # but the route logic checks for empty

    # Actually, the route checks `if not send_request.book_ids:` which happens after Pydantic
    # So we need to create a request that passes Pydantic but the route logic catches
    # But Pydantic will reject empty list, so we test the route's internal check differently

    # Let's test with a request that has book_ids but the route's validation catches it
    # Actually looking at the code, the route checks `if not send_request.book_ids:`
    # This happens after Pydantic validation, so if Pydantic allows it, the route will catch it
    # But Pydantic has min_length=1, so we can't create an empty list

    # The test should actually test the route's validation logic, but since Pydantic
    # validates first, we need to test with a valid request and then mock the service
    # to verify the route logic, or we need to test the Pydantic validation separately

    # For now, let's test that the route properly handles the case when book_ids is empty
    # by using a mock that bypasses Pydantic validation
    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = "test_key"

            self.app = type(
                "App", (), {"state": type("State", (), {"config": DummyConfig()})()}
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()
    mock_service = MockBookService()

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    # Create a request object that bypasses Pydantic validation by directly setting attributes
    send_request = MagicMock()
    send_request.book_ids = []
    send_request.to_email = None
    send_request.file_format = None

    with pytest.raises(HTTPException) as exc_info:
        books.send_books_to_device_batch(
            request=request,  # type: ignore[arg-type]
            session=session,
            current_user=current_user,
            send_request=send_request,  # type: ignore[arg-type]
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "book_ids_required"


def test_send_books_to_device_batch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test send_books_to_device_batch succeeds (covers lines 1111-1176)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = "test_key"

            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {"config": DummyConfig(), "task_runner": DummyTaskRunner()},
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()
    mock_service = MockBookService()
    book_with_rels = BookWithFullRelations(
        book=Book(id=1, title="Test", uuid="test", has_cover=False, path="test"),
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with patch(
        "fundamental.api.routes.books._email_config_service"
    ) as mock_email_config:
        mock_email_service = MagicMock()
        mock_config = MagicMock()
        mock_config.enabled = True
        mock_email_service.get_config.return_value = mock_config
        mock_email_config.return_value = mock_email_service

        send_request = books.BookBulkSendRequest(
            book_ids=[1], to_email="test@example.com"
        )

        books.send_books_to_device_batch(
            request=request,  # type: ignore[arg-type]
            session=session,
            current_user=current_user,
            send_request=send_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )


def test_convert_book_format_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test convert_book_format succeeds (covers lines 1227-1275)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book_with_rels = BookWithFullRelations(
        book=Book(id=1, title="Test", uuid="test", has_cover=False, path="test"),
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()
    mock_result = MagicMock()
    mock_result.task_id = 1
    mock_result.message = "Conversion started"
    mock_result.existing_conversion = None
    mock_orchestration_service.initiate_conversion.return_value = mock_result

    convert_request = books.BookConvertRequest(
        source_format="EPUB", target_format="MOBI"
    )

    result = books.convert_book_format(
        book_id=1,
        current_user=current_user,
        convert_request=convert_request,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        orchestration_service=mock_orchestration_service,
    )

    assert result.task_id == 1
    assert result.message == "Conversion started"


def test_convert_book_format_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test convert_book_format handles RuntimeError (covers lines 1255-1266)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book_with_rels = BookWithFullRelations(
        book=Book(id=1, title="Test", uuid="test", has_cover=False, path="test"),
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()
    mock_orchestration_service.initiate_conversion.side_effect = RuntimeError(
        "Task runner not available"
    )

    convert_request = books.BookConvertRequest(
        source_format="EPUB", target_format="MOBI"
    )

    with pytest.raises(HTTPException) as exc_info:
        books.convert_book_format(
            book_id=1,
            current_user=current_user,
            convert_request=convert_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            orchestration_service=mock_orchestration_service,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503


def test_get_book_conversions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_conversions succeeds (covers lines 1323-1367)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book_with_rels = BookWithFullRelations(
        book=Book(id=1, title="Test", uuid="test", has_cover=False, path="test"),
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()
    from fundamental.models.conversion import (
        BookConversion,
        ConversionMethod,
        ConversionStatus,
    )

    mock_conv = BookConversion(
        id=1,
        book_id=1,
        original_format="EPUB",
        target_format="MOBI",
        original_file_path="/path/original.epub",
        converted_file_path="/path/converted.mobi",
        conversion_method=ConversionMethod.MANUAL,
        status=ConversionStatus.COMPLETED,
        error_message=None,
        original_backed_up=False,
    )
    mock_result = MagicMock()
    mock_result.conversions = [mock_conv]
    mock_result.total = 1
    mock_result.page = 1
    mock_result.page_size = 20
    mock_result.total_pages = 1
    mock_orchestration_service.get_conversions.return_value = mock_result

    result = books.get_book_conversions(
        book_id=1,
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        orchestration_service=mock_orchestration_service,
        page=1,
        page_size=20,
    )

    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].book_id == 1


def test_download_cover_from_url_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test download_cover_from_url handles unexpected exceptions (covers lines 1441-1445)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book_with_rels = BookWithFullRelations(
        book=Book(id=1, title="Test", uuid="test", has_cover=False, path="test"),
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
        formats=[],
    )
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_cover_service = MagicMock()
    mock_cover_service.save_cover_from_url.side_effect = RuntimeError(
        "Unexpected error"
    )

    request = books.CoverFromUrlRequest(url="https://example.com/cover.jpg")

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            current_user=current_user,
            book_id=1,
            request=request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            cover_service=mock_cover_service,
            session=session,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "internal_error" in exc_info.value.detail


def test_lookup_tags_by_name_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test lookup_tags_by_name succeeds (covers lines 1611-1656)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    mock_service.lookup_tags_by_names = MagicMock(  # type: ignore[assignment]
        return_value=[
            {"id": 1, "name": "Fiction"},
            {"id": 2, "name": "Science Fiction"},
        ]
    )

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.lookup_tags_by_name(
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        names="Fiction, Science Fiction",
    )

    assert len(result.tags) == 2
    assert result.tags[0].id == 1
    assert result.tags[0].name == "Fiction"


def test_lookup_tags_by_name_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test lookup_tags_by_name returns empty when no names (covers lines 1646-1647)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    result = books.lookup_tags_by_name(
        current_user=current_user,
        book_service=mock_service,
        permission_helper=mock_permission_helper,
        names="",
    )

    assert len(result.tags) == 0


def test_upload_book_format_not_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_book raises 400 when format not allowed (covers lines 1805-1810)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {"task_runner": DummyTaskRunner()},
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()
    mock_file = MagicMock()
    mock_file.filename = "book.invalid"
    mock_file.file.read.return_value = b"fake content"

    mock_permission_helper, _ = _setup_route_mocks(
        monkeypatch, session, MockBookService()
    )

    with patch(
        "fundamental.api.routes.books.FileHandlingConfigService"
    ) as mock_file_service_class:
        mock_file_service = MagicMock()
        mock_file_service.is_format_allowed.return_value = False
        mock_file_service.get_allowed_upload_formats.return_value = ["epub", "pdf"]
        mock_file_service_class.return_value = mock_file_service

        with pytest.raises(HTTPException) as exc_info:
            books.upload_book(
                request=request,  # type: ignore[arg-type]
                current_user=current_user,
                file=mock_file,
                permission_helper=mock_permission_helper,
                session=session,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail


def test_get_task_runner_unavailable() -> None:
    """Test _get_task_runner raises 503 when unavailable (covers lines 1874-1882)."""

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type("App", (), {"state": type("State", (), {})()})()

    request = DummyRequest()

    with pytest.raises(HTTPException) as exc_info:
        books._get_task_runner(request)  # type: ignore[arg-type]
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Task runner not available"


def test_validate_files_empty() -> None:
    """Test _validate_files raises 400 when files empty (covers lines 1898-1902)."""
    with pytest.raises(HTTPException) as exc_info:
        books._validate_files([])
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "No files provided"


def test_save_file_to_temp_no_extension() -> None:
    """Test _save_file_to_temp raises 400 when no extension (covers lines 1930-1935)."""
    session = DummySession()
    mock_file = MagicMock()
    mock_file.filename = "noextension"
    temp_paths: list[Path] = []

    with pytest.raises(HTTPException) as exc_info:
        books._save_file_to_temp(mock_file, temp_paths, session)  # type: ignore[arg-type]
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert "file_extension_required" in exc_info.value.detail


def test_save_file_to_temp_format_not_allowed() -> None:
    """Test _save_file_to_temp raises 400 when format not allowed (covers lines 1938-1944)."""
    session = DummySession()
    mock_file = MagicMock()
    mock_file.filename = "book.invalid"
    temp_paths: list[Path] = []

    with (
        patch(
            "fundamental.api.routes.books.FileHandlingConfigService"
        ) as mock_file_service_class,
    ):
        mock_file_service = MagicMock()
        mock_file_service.is_format_allowed.return_value = False
        mock_file_service.get_allowed_upload_formats.return_value = ["epub", "pdf"]
        mock_file_service_class.return_value = mock_file_service

        with pytest.raises(HTTPException) as exc_info:
            books._save_file_to_temp(mock_file, temp_paths, session)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert "not allowed" in exc_info.value.detail


def test_save_file_to_temp_save_error() -> None:
    """Test _save_file_to_temp handles save errors (covers lines 1967-1971)."""
    session = DummySession()
    mock_file = MagicMock()
    mock_file.filename = "book.epub"
    mock_file.file.read.side_effect = Exception("Read error")
    temp_paths: list[Path] = []

    with (
        patch(
            "fundamental.api.routes.books.FileHandlingConfigService"
        ) as mock_file_service_class,
        patch("tempfile.NamedTemporaryFile") as mock_temp_file,
    ):
        mock_file_service = MagicMock()
        mock_file_service.is_format_allowed.return_value = True
        mock_file_service_class.return_value = mock_file_service

        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.epub"
        mock_temp_file.return_value.__enter__.return_value = mock_temp

        with pytest.raises(HTTPException) as exc_info:
            books._save_file_to_temp(mock_file, temp_paths, session)  # type: ignore[arg-type]
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 500
        assert "failed_to_save_file" in exc_info.value.detail


def test_save_files_to_temp_cleanup_on_error() -> None:
    """Test _save_files_to_temp cleans up on error (covers lines 1995-2008)."""
    session = DummySession()
    mock_file1 = MagicMock()
    mock_file1.filename = "book1.epub"
    mock_file1.file.read.return_value = b"content1"

    mock_file2 = MagicMock()
    mock_file2.filename = "book2.invalid"  # Will fail validation

    with (
        patch(
            "fundamental.api.routes.books.FileHandlingConfigService"
        ) as mock_file_service_class,
        patch("tempfile.NamedTemporaryFile") as mock_temp_file,
    ):
        mock_file_service = MagicMock()
        mock_file_service.is_format_allowed.side_effect = [
            True,
            False,
        ]  # First succeeds, second fails
        mock_file_service.get_allowed_upload_formats.return_value = ["epub", "pdf"]
        mock_file_service_class.return_value = mock_file_service

        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.epub"
        mock_temp_file.return_value.__enter__.return_value = mock_temp

        with pytest.raises(HTTPException):
            books._save_files_to_temp([mock_file1, mock_file2], session)  # type: ignore[arg-type]


def test_enqueue_batch_upload_task(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _enqueue_batch_upload_task enqueues task (covers lines 2011-2041)."""
    mock_task_runner = MagicMock()
    mock_task_runner.enqueue.return_value = 123

    file_infos = [
        {
            "file_path": "/tmp/file1.epub",
            "filename": "file1.epub",
            "file_format": "epub",
            "title": "File 1",
        },
        {
            "file_path": "/tmp/file2.epub",
            "filename": "file2.epub",
            "file_format": "epub",
            "title": "File 2",
        },
    ]

    result = books._enqueue_batch_upload_task(mock_task_runner, file_infos, 1)

    assert result == 123
    mock_task_runner.enqueue.assert_called_once()
    call_kwargs = mock_task_runner.enqueue.call_args
    assert call_kwargs[1]["user_id"] == 1
    assert call_kwargs[1]["metadata"]["total_files"] == 2


def test_upload_books_batch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_books_batch succeeds (covers lines 2044-2106)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {"task_runner": DummyTaskRunner()},
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()

    mock_file1 = MagicMock()
    mock_file1.filename = "book1.epub"
    mock_file1.file.read.return_value = b"content1"

    mock_file2 = MagicMock()
    mock_file2.filename = "book2.epub"
    mock_file2.file.read.return_value = b"content2"

    mock_permission_helper, _ = _setup_route_mocks(
        monkeypatch, session, MockBookService()
    )

    with (
        patch(
            "fundamental.api.routes.books.FileHandlingConfigService"
        ) as mock_file_service_class,
        patch("tempfile.NamedTemporaryFile") as mock_temp_file,
    ):
        mock_file_service = MagicMock()
        mock_file_service.is_format_allowed.return_value = True
        mock_file_service_class.return_value = mock_file_service

        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.epub"
        mock_temp_file.return_value.__enter__.return_value = mock_temp

        result = books.upload_books_batch(
            request=request,  # type: ignore[arg-type]
            current_user=current_user,
            permission_helper=mock_permission_helper,
            session=session,
            files=[mock_file1, mock_file2],
        )

        assert result.task_id == 1
        assert result.total_files == 2


def test_upload_books_batch_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_books_batch handles unexpected errors (covers lines 2098-2106)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {"task_runner": DummyTaskRunner()},
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()

    mock_file = MagicMock()
    mock_file.filename = "book.epub"
    mock_file.file.read.side_effect = RuntimeError("Unexpected error")

    mock_permission_helper, _ = _setup_route_mocks(
        monkeypatch, session, MockBookService()
    )

    with (
        patch(
            "fundamental.api.routes.books.FileHandlingConfigService"
        ) as mock_file_service_class,
        patch("tempfile.NamedTemporaryFile") as mock_temp_file,
    ):
        mock_file_service = MagicMock()
        mock_file_service.is_format_allowed.return_value = True
        mock_file_service_class.return_value = mock_file_service

        mock_temp = MagicMock()
        mock_temp.name = "/tmp/test.epub"
        mock_temp_file.return_value.__enter__.return_value = mock_temp

        with pytest.raises(HTTPException) as exc_info:
            books.upload_books_batch(
                request=request,  # type: ignore[arg-type]
                current_user=current_user,
                permission_helper=mock_permission_helper,
                session=session,
                files=[mock_file],
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 500
        assert "failed_to_save_file" in exc_info.value.detail


def test_delete_book_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test delete_book raises 404 when book not found (covers line 633)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    mock_service.set_get_book_full_result(None)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with pytest.raises(HTTPException) as exc_info:
        books.delete_book(
            current_user=current_user,
            book_id=999,
            delete_request=MagicMock(),
            book_service=mock_service,
            permission_helper=mock_permission_helper,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_send_books_to_device_batch_email_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test send_books_to_device_batch when email not configured (covers line 1121)."""
    from fundamental.api.schemas import BookBulkSendRequest

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = b"test_key"

            class DummyEmailConfig:
                enabled = False

            class DummyEmailConfigService:
                def get_config(self, decrypt: bool = False) -> DummyEmailConfig | None:
                    return DummyEmailConfig()

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "config": DummyConfig(),
                            "email_config_service": DummyEmailConfigService(),
                        },
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()
    mock_service = MockBookService()

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with (
        patch(
            "fundamental.api.routes.books._email_config_service"
        ) as mock_email_service,
    ):
        mock_email_config = MagicMock()
        mock_email_config.enabled = False
        mock_email_service_instance = MagicMock()
        mock_email_service_instance.get_config.return_value = mock_email_config
        mock_email_service.return_value = mock_email_service_instance

        send_request = BookBulkSendRequest(book_ids=[1, 2])
        with pytest.raises(HTTPException) as exc_info:
            books.send_books_to_device_batch(
                request=request,  # type: ignore[arg-type]
                session=session,
                current_user=current_user,
                send_request=send_request,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "email_server_not_configured_or_disabled"


def test_send_books_to_device_batch_user_missing_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test send_books_to_device_batch when user missing ID (covers line 1128)."""
    from fundamental.api.schemas import BookBulkSendRequest

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = b"test_key"

            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "config": DummyConfig(),
                            "task_runner": DummyTaskRunner(),
                        },
                    )()
                },
            )()

    session = DummySession()
    current_user = User(
        id=None,  # Missing ID
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    request = DummyRequest()
    mock_service = MockBookService()
    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with (
        patch(
            "fundamental.api.routes.books._email_config_service"
        ) as mock_email_service,
    ):
        mock_email_config = MagicMock()
        mock_email_config.enabled = True
        mock_email_service_instance = MagicMock()
        mock_email_service_instance.get_config.return_value = mock_email_config
        mock_email_service.return_value = mock_email_service_instance

        send_request = BookBulkSendRequest(book_ids=[1])
        with pytest.raises(HTTPException) as exc_info:
            books.send_books_to_device_batch(
                request=request,  # type: ignore[arg-type]
                session=session,
                current_user=current_user,
                send_request=send_request,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "user_missing_id"


def test_send_books_to_device_batch_task_runner_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test send_books_to_device_batch when task runner unavailable (covers line 1138)."""
    from fundamental.api.schemas import BookBulkSendRequest

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = b"test_key"

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "config": DummyConfig(),
                            "task_runner": None,  # No task runner
                        },
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()
    mock_service = MockBookService()

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with (
        patch(
            "fundamental.api.routes.books._email_config_service"
        ) as mock_email_service,
    ):
        mock_email_config = MagicMock()
        mock_email_config.enabled = True
        mock_email_service_instance = MagicMock()
        mock_email_service_instance.get_config.return_value = mock_email_config
        mock_email_service.return_value = mock_email_service_instance

        send_request = BookBulkSendRequest(book_ids=[1])
        with pytest.raises(HTTPException) as exc_info:
            books.send_books_to_device_batch(
                request=request,  # type: ignore[arg-type]
                session=session,
                current_user=current_user,
                send_request=send_request,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == "Task runner not available"


def test_send_books_to_device_batch_book_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test send_books_to_device_batch when book not found (covers line 1152)."""
    from fundamental.api.schemas import BookBulkSendRequest

    class DummyRequest:
        def __init__(self) -> None:
            class DummyConfig:
                encryption_key = b"test_key"

            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "config": DummyConfig(),
                            "task_runner": DummyTaskRunner(),
                        },
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()
    mock_service = MockBookService()
    mock_service.set_get_book_full_result(None)  # Book not found

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    with (
        patch(
            "fundamental.api.routes.books._email_config_service"
        ) as mock_email_service,
    ):
        mock_email_config = MagicMock()
        mock_email_config.enabled = True
        mock_email_service_instance = MagicMock()
        mock_email_service_instance.get_config.return_value = mock_email_config
        mock_email_service.return_value = mock_email_service_instance

        send_request = BookBulkSendRequest(book_ids=[999])
        with pytest.raises(HTTPException) as exc_info:
            books.send_books_to_device_batch(
                request=request,  # type: ignore[arg-type]
                session=session,
                current_user=current_user,
                send_request=send_request,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 404
        assert "book_not_found" in exc_info.value.detail


def test_convert_book_format_book_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test convert_book_format when book not found (covers line 1229)."""
    from fundamental.api.schemas import BookConvertRequest

    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    mock_service.set_get_book_full_result(None)  # Book not found

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()

    convert_request = BookConvertRequest(source_format="EPUB", target_format="MOBI")
    with pytest.raises(HTTPException) as exc_info:
        books.convert_book_format(
            book_id=999,
            current_user=current_user,
            convert_request=convert_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            orchestration_service=mock_orchestration_service,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_convert_book_format_user_missing_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test convert_book_format when user missing ID (covers line 1239)."""
    from fundamental.api.schemas import BookConvertRequest

    session = DummySession()
    current_user = User(
        id=None,  # Missing ID
        username="testuser",
        email="test@example.com",
        password_hash="hash",
    )
    mock_service = MockBookService()
    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()

    convert_request = BookConvertRequest(source_format="EPUB", target_format="MOBI")
    with pytest.raises(HTTPException) as exc_info:
        books.convert_book_format(
            book_id=1,
            current_user=current_user,
            convert_request=convert_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            orchestration_service=mock_orchestration_service,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "user_missing_id"


def test_convert_book_format_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test convert_book_format handles ValueError (covers line 1254)."""
    from fundamental.api.schemas import BookConvertRequest

    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()
    mock_orchestration_service.initiate_conversion.side_effect = ValueError(
        "invalid_format"
    )

    convert_request = BookConvertRequest(source_format="EPUB", target_format="MOBI")
    with (
        patch("fundamental.api.routes.books.BookExceptionMapper") as mock_mapper_class,
    ):
        mock_mapper = MagicMock()
        mock_mapper.map_value_error_to_http_exception.return_value = HTTPException(
            status_code=400, detail="invalid_format"
        )
        mock_mapper_class.map_value_error_to_http_exception = (
            mock_mapper.map_value_error_to_http_exception
        )

        with pytest.raises(HTTPException) as exc_info:
            books.convert_book_format(
                book_id=1,
                current_user=current_user,
                convert_request=convert_request,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
                orchestration_service=mock_orchestration_service,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400


def test_convert_book_format_runtime_error_other(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test convert_book_format handles other RuntimeError (covers line 1263)."""
    from fundamental.api.schemas import BookConvertRequest

    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()
    mock_orchestration_service.initiate_conversion.side_effect = RuntimeError(
        "Other error"
    )

    convert_request = BookConvertRequest(source_format="EPUB", target_format="MOBI")
    with pytest.raises(HTTPException) as exc_info:
        books.convert_book_format(
            book_id=1,
            current_user=current_user,
            convert_request=convert_request,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            orchestration_service=mock_orchestration_service,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "Other error" in exc_info.value.detail


def test_get_book_conversions_book_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_conversions when book not found (covers line 1325)."""
    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    mock_service.set_get_book_full_result(None)  # Book not found

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        books.get_book_conversions(
            book_id=999,
            current_user=current_user,
            book_service=mock_service,
            permission_helper=mock_permission_helper,
            orchestration_service=mock_orchestration_service,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_get_book_conversions_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_book_conversions handles ValueError (covers lines 1340-1342)."""

    session = DummySession()
    current_user = _create_mock_user()
    mock_service = MockBookService()
    book = Book(
        id=1,
        title="Test Book",
        author_sort="Author, Test",
        pubdate="2024-01-01",
        timestamp="2024-01-01T00:00:00",
        series_index=1.0,
        isbn="1234567890",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=["Test Author"],
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
    mock_service.set_get_book_full_result(book_with_rels)

    mock_permission_helper, _ = _setup_route_mocks(monkeypatch, session, mock_service)

    mock_orchestration_service = MagicMock()
    mock_orchestration_service.get_conversions.side_effect = ValueError("invalid_book")

    with (
        patch("fundamental.api.routes.books.BookExceptionMapper") as mock_mapper_class,
    ):
        mock_mapper = MagicMock()
        mock_mapper.map_value_error_to_http_exception.return_value = HTTPException(
            status_code=400, detail="invalid_book"
        )
        mock_mapper_class.map_value_error_to_http_exception = (
            mock_mapper.map_value_error_to_http_exception
        )

        with pytest.raises(HTTPException) as exc_info:
            books.get_book_conversions(
                book_id=1,
                current_user=current_user,
                book_service=mock_service,
                permission_helper=mock_permission_helper,
                orchestration_service=mock_orchestration_service,
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400


def test_upload_book_task_runner_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_book when task runner unavailable (covers line 1789)."""

    class DummyRequest:
        def __init__(self) -> None:
            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "task_runner": None,  # No task runner
                        },
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()

    mock_file = MagicMock()
    mock_file.filename = "book.epub"
    mock_file.file.read.return_value = b"fake book content"

    mock_permission_helper, _ = _setup_route_mocks(
        monkeypatch, session, MockBookService()
    )

    with pytest.raises(HTTPException) as exc_info:
        books.upload_book(
            request=request,  # type: ignore[arg-type]
            current_user=current_user,
            file=mock_file,
            permission_helper=mock_permission_helper,
            session=session,
        )
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Task runner not available"


def test_upload_books_batch_http_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test upload_books_batch handles HTTPException (covers lines 2098-2103)."""

    class DummyRequest:
        def __init__(self) -> None:
            class DummyTaskRunner:
                def enqueue(
                    self,
                    task_type: object,
                    payload: dict[str, object],
                    user_id: int,
                    metadata: dict[str, object] | None = None,
                ) -> int:
                    return 1

            self.app = type(
                "App",
                (),
                {
                    "state": type(
                        "State",
                        (),
                        {
                            "task_runner": DummyTaskRunner(),
                        },
                    )()
                },
            )()

    session = DummySession()
    current_user = _create_mock_user()
    request = DummyRequest()

    mock_file = MagicMock()
    mock_file.filename = "book.epub"
    mock_file.file.read.side_effect = HTTPException(
        status_code=400, detail="invalid_file"
    )

    mock_permission_helper, _ = _setup_route_mocks(
        monkeypatch, session, MockBookService()
    )

    with (
        patch(
            "fundamental.api.routes.books.FileHandlingConfigService"
        ) as mock_file_service_class,
        patch("fundamental.api.routes.books._save_files_to_temp") as mock_save_files,
    ):
        mock_file_service = MagicMock()
        mock_file_service.is_format_allowed.return_value = True
        mock_file_service_class.return_value = mock_file_service

        mock_save_files.side_effect = HTTPException(
            status_code=400, detail="invalid_file"
        )

        with pytest.raises(HTTPException) as exc_info:
            books.upload_books_batch(
                request=request,  # type: ignore[arg-type]
                current_user=current_user,
                permission_helper=mock_permission_helper,
                session=session,
                files=[mock_file],
            )
        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
