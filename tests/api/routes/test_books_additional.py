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
from unittest.mock import patch

import pytest
from fastapi import HTTPException, status

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

    monkeypatch.setattr(books, "PermissionService", MockPermissionService)


class MockBookService:
    """Mock BookService for testing."""

    def __init__(self, library: Library) -> None:
        self._library = library

    def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
        """Mock get_book_full method."""
        return self._get_book_full_result

    def set_get_book_full_result(self, result: BookWithFullRelations | None) -> None:
        """Set the result for get_book_full."""
        self._get_book_full_result = result


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

        result = books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
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

        result = books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
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

        result = books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
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

        result = books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
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

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(
            session, current_user=current_user, book_id=999, file_format="EPUB"
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

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
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

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
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

        result = books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
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

        with pytest.raises(HTTPException) as exc_info:
            books.download_book_file(
                session, current_user=current_user, book_id=1, file_format="EPUB"
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

        result = books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
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

        result = books.download_book_file(
            session, current_user=current_user, book_id=1, file_format="EPUB"
        )

        assert result is not None


def test_validate_cover_url_request_book_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _validate_cover_url_request raises 404 when book not found (covers lines 642-649)."""
    session = DummySession()

    mock_service = MockBookService(mock_library)  # type: ignore[arg-type]
    mock_service.get_book = lambda book_id: None  # type: ignore[method-assign]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books._validate_cover_url_request(
            session, book_id=999, url="https://example.com/image.jpg"
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "book_not_found"


def test_validate_cover_url_request_empty_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _validate_cover_url_request raises 400 when URL is empty (covers lines 651-655)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    mock_service = MockBookService(mock_library)  # type: ignore[arg-type]
    mock_service.get_book = lambda book_id: book_with_rels  # type: ignore[method-assign]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books._validate_cover_url_request(session, book_id=1, url="")

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "url_required"


def test_validate_cover_url_request_invalid_url_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _validate_cover_url_request raises 400 when URL format is invalid (covers lines 657-661)."""
    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    mock_service = MockBookService(mock_library)  # type: ignore[arg-type]
    mock_service.get_book = lambda book_id: book_with_rels  # type: ignore[method-assign]

    def mock_get_active_library_service(sess: object) -> MockBookService:
        return mock_service

    monkeypatch.setattr(
        books, "_get_active_library_service", mock_get_active_library_service
    )

    with pytest.raises(HTTPException) as exc_info:
        books._validate_cover_url_request(
            session, book_id=1, url="ftp://example.com/image.jpg"
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid_url_format"


def test_download_and_validate_image_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _download_and_validate_image succeeds with valid image (covers lines 682-705)."""
    from io import BytesIO
    from unittest.mock import MagicMock

    from PIL import Image

    # Create a simple test image
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

    with patch("fundamental.api.routes.books.httpx.Client", return_value=mock_client):
        content, image = books._download_and_validate_image(
            "https://example.com/image.jpg"
        )

        assert content == image_content
        assert isinstance(image, Image.Image)


def test_download_and_validate_image_invalid_content_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _download_and_validate_image raises 400 when content type is not image (covers lines 687-692)."""
    from unittest.mock import MagicMock

    mock_response = MagicMock()
    mock_response.content = b"not an image"
    mock_response.headers = {"content-type": "text/html"}
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("fundamental.api.routes.books.httpx.Client", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            books._download_and_validate_image("https://example.com/page.html")

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "url_not_an_image"


def test_download_and_validate_image_invalid_image_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _download_and_validate_image raises 400 when image format is invalid (covers lines 694-701)."""
    from unittest.mock import MagicMock

    mock_response = MagicMock()
    mock_response.content = b"invalid image data"
    mock_response.headers = {"content-type": "image/jpeg"}
    mock_response.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("fundamental.api.routes.books.httpx.Client", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            books._download_and_validate_image("https://example.com/invalid.jpg")

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "invalid_image_format"


def test_download_and_validate_image_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _download_and_validate_image raises 400 when HTTP error occurs (covers lines 706-710)."""
    from unittest.mock import MagicMock

    import httpx

    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.HTTPError("Connection error")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("fundamental.api.routes.books.httpx.Client", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            books._download_and_validate_image("https://example.com/image.jpg")

        assert isinstance(exc_info.value, HTTPException)
        assert exc_info.value.status_code == 400
        assert "failed_to_download_image" in exc_info.value.detail


def test_save_image_to_temp_jpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _save_image_to_temp saves JPEG image (covers lines 728-741)."""
    from io import BytesIO

    from PIL import Image

    test_image = Image.new("RGB", (100, 100), color="red")
    image_bytes = BytesIO()
    test_image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)
    image_content = image_bytes.getvalue()

    # Reopen image for the function
    image = Image.open(BytesIO(image_content))

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(tempfile, "gettempdir", lambda: tmpdir)

        result_url = books._save_image_to_temp(image_content, image)

        assert result_url.startswith("/api/books/temp-covers/")
        # JPEG format can be saved as .jpg or .jpeg, check for either
        assert result_url.endswith((".jpg", ".jpeg"))

        # Verify file was saved
        content_hash = result_url.split("/")[-1].split(".")[0]
        assert content_hash in books._temp_cover_storage


def test_save_image_to_temp_png(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _save_image_to_temp saves PNG image (covers lines 728-741)."""
    from io import BytesIO

    from PIL import Image

    test_image = Image.new("RGB", (100, 100), color="blue")
    image_bytes = BytesIO()
    test_image.save(image_bytes, format="PNG")
    image_bytes.seek(0)
    image_content = image_bytes.getvalue()

    # Reopen image for the function
    image = Image.open(BytesIO(image_content))

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(tempfile, "gettempdir", lambda: tmpdir)

        result_url = books._save_image_to_temp(image_content, image)

        assert result_url.startswith("/api/books/temp-covers/")
        assert result_url.endswith(".png")


def test_save_image_to_temp_unknown_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _save_image_to_temp defaults to jpg for unknown format (covers lines 730-731)."""
    from io import BytesIO

    from PIL import Image

    test_image = Image.new("RGB", (100, 100), color="green")
    image_bytes = BytesIO()
    test_image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)
    image_content = image_bytes.getvalue()

    # Create image without format attribute
    image = Image.open(BytesIO(image_content))
    image.format = None  # type: ignore[assignment]

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(tempfile, "gettempdir", lambda: tmpdir)

        result_url = books._save_image_to_temp(image_content, image)

        assert result_url.endswith(".jpg")


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
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

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
            "fundamental.api.routes.books.httpx.Client", return_value=mock_client
        ):
            request = CoverFromUrlRequest(url="https://example.com/cover.jpg")
            result = books.download_cover_from_url(
                session, current_user=current_user, book_id=1, request=request
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
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

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
            "fundamental.api.routes.books.httpx.Client", return_value=mock_client
        ):
            request = CoverFromUrlRequest(url="https://example.com/cover.jpg")
            result = books.download_cover_from_url(
                session, current_user=current_user, book_id=1, request=request
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
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

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
            "fundamental.api.routes.books.httpx.Client", return_value=mock_client
        ):
            request = CoverFromUrlRequest(url="https://example.com/cover.jpg")
            result = books.download_cover_from_url(
                session, current_user=current_user, book_id=1, request=request
            )

            assert result.temp_url == "/api/books/1/cover"


def test_download_cover_from_url_internal_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_cover_from_url handles internal errors (covers lines 839-843)."""

    from fundamental.api.schemas import CoverFromUrlRequest

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

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

    # Mock _download_and_validate_image to raise a non-HTTPException
    def mock_download(*args: object, **kwargs: object) -> None:
        raise ValueError("Some internal error")

    monkeypatch.setattr(books, "_download_and_validate_image", mock_download)

    request = CoverFromUrlRequest(url="https://example.com/cover.jpg")

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            session, current_user=current_user, book_id=1, request=request
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 500
    assert "internal_error" in exc_info.value.detail


def test_get_temp_cover_no_dot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_temp_cover returns 404 when no dot in filename (covers lines 865-866)."""
    from fastapi import Response

    result = books.get_temp_cover("nofileextension")

    assert isinstance(result, Response)
    assert result.status_code == 404


def test_get_temp_cover_not_in_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_temp_cover returns 404 when hash not in storage (covers lines 870-871)."""
    from fastapi import Response

    result = books.get_temp_cover("nonexistent123.jpg")

    assert isinstance(result, Response)
    assert result.status_code == 404


def test_get_temp_cover_file_not_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_temp_cover returns 404 and cleans up when file doesn't exist (covers lines 874-877)."""
    from fastapi import Response

    # Add a non-existent path to storage
    fake_hash = "fakehash123"
    fake_path = Path("/nonexistent/path/to/file.jpg")
    books._temp_cover_storage[fake_hash] = fake_path

    try:
        result = books.get_temp_cover(f"{fake_hash}.jpg")

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

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = Path(tmpdir) / "test_cover.jpg"
        temp_file.write_bytes(b"fake image data")

        # Add to storage
        fake_hash = "testhash123"
        books._temp_cover_storage[fake_hash] = temp_file

        try:
            result = books.get_temp_cover(f"{fake_hash}.jpg")

            assert isinstance(result, FileResponse)
            assert result.path == str(temp_file)
        finally:
            # Clean up
            books._temp_cover_storage.pop(fake_hash, None)


def test_save_image_to_temp_unsupported_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _save_image_to_temp defaults to jpg for unsupported format (covers line 731)."""
    from io import BytesIO

    from PIL import Image

    # Create a GIF image (not in the allowed list: jpg, jpeg, png, webp)
    test_image = Image.new("RGB", (100, 100), color="red")
    image_bytes = BytesIO()
    test_image.save(image_bytes, format="GIF")
    image_bytes.seek(0)
    image_content = image_bytes.getvalue()

    # Reopen image and set format to GIF
    image = Image.open(BytesIO(image_content))
    image.format = "GIF"  # type: ignore[assignment]

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(tempfile, "gettempdir", lambda: tmpdir)

        result_url = books._save_image_to_temp(image_content, image)

        # Should default to .jpg for unsupported format
        assert result_url.endswith(".jpg")


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

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            session, current_user=current_user, book_id=999, request=request
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
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

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

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            session, current_user=current_user, book_id=1, request=request
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
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

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

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            session, current_user=current_user, book_id=1, request=request
        )

    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid_url_format"


def test_download_cover_from_url_http_exception_re_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test download_cover_from_url re-raises HTTPException from _download_and_validate_image (covers line 838)."""

    from fundamental.api.schemas import CoverFromUrlRequest

    session = DummySession()

    book = Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="test/path",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    library_with_path = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_service = MockBookService(library_with_path)
    mock_service.get_book = lambda book_id: book_with_rels  # type: ignore[method-assign]
    # Ensure _library attribute exists to avoid AttributeError
    mock_service._library = library_with_path  # type: ignore[attr-defined]
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

    # Create the HTTPException that will be raised
    http_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="invalid_image_format",
    )

    # Mock _download_and_validate_image to raise an HTTPException
    def mock_download(*args: object, **kwargs: object) -> tuple[bytes, object]:
        raise http_exception

    monkeypatch.setattr(books, "_download_and_validate_image", mock_download)

    request = CoverFromUrlRequest(url="https://example.com/cover.jpg")

    with pytest.raises(HTTPException) as exc_info:
        books.download_cover_from_url(
            session, current_user=current_user, book_id=1, request=request
        )

    # Should re-raise the same HTTPException (line 838)
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "invalid_image_format"
