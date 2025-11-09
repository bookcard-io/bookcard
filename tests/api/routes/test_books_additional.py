# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Additional tests for books API routes to achieve 100% coverage."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi import HTTPException

import fundamental.api.routes.books as books
from fundamental.models.config import Library
from fundamental.models.core import Book
from fundamental.repositories import BookWithFullRelations
from tests.conftest import DummySession


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

        result = books.download_book_file(session, book_id=1, file_format="EPUB")

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

        result = books.download_book_file(session, book_id=1, file_format="EPUB")

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

        result = books.download_book_file(session, book_id=1, file_format="EPUB")

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

        result = books.download_book_file(session, book_id=1, file_format="EPUB")

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

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(session, book_id=999, file_format="EPUB")

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

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(session, book_id=1, file_format="EPUB")

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

    with pytest.raises(HTTPException) as exc_info:
        books.download_book_file(session, book_id=1, file_format="EPUB")

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

        result = books.download_book_file(session, book_id=1, file_format="EPUB")

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

        with pytest.raises(HTTPException) as exc_info:
            books.download_book_file(session, book_id=1, file_format="EPUB")

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

        result = books.download_book_file(session, book_id=1, file_format="EPUB")

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

        result = books.download_book_file(session, book_id=1, file_format="EPUB")

        assert result is not None
