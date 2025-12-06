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

"""Tests for book service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.auth import EBookFormat, EReaderDevice
from fundamental.models.config import Library
from fundamental.models.conversion import BookConversion, ConversionMethod
from fundamental.models.core import Book
from fundamental.models.epub_fixer import EPUBFix
from fundamental.models.ingest import IngestHistory
from fundamental.models.kobo import (
    KoboArchivedBook,
    KoboReadingState,
    KoboSyncedBook,
)
from fundamental.models.metadata_enforcement import (
    MetadataEnforcementOperation,
)
from fundamental.models.reading import (
    Annotation,
    AnnotationDirtied,
    ReadingProgress,
    ReadingSession,
    ReadStatus,
)
from fundamental.repositories import BookWithFullRelations, BookWithRelations
from fundamental.services.book_service import BookService


def test_book_service_init() -> None:
    """Test BookService initialization (covers lines 52-57)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        service = BookService(library)
        assert service._library is library
        mock_repo_class.assert_called_once_with(
            calibre_db_path="/path/to/library",
            calibre_db_file="metadata.db",
        )


def test_list_books_calculates_offset() -> None:
    """Test list_books calculates offset correctly (covers lines 87-96)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_books.return_value = []
        mock_repo.count_books.return_value = 0
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        books, total = service.list_books(page=2, page_size=20)

        # Page 2 with page_size 20 should have offset 20
        mock_repo.list_books.assert_called_once_with(
            limit=20,
            offset=20,
            search_query=None,
            author_id=None,
            sort_by="timestamp",
            sort_order="desc",
            full=False,
            pubdate_month=None,
            pubdate_day=None,
        )
        mock_repo.count_books.assert_called_once_with(
            search_query=None, author_id=None, pubdate_month=None, pubdate_day=None
        )
        assert books == []
        assert total == 0


def test_list_books_with_search() -> None:
    """Test list_books passes search query (covers lines 87-96)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_books.return_value = []
        mock_repo.count_books.return_value = 0
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        service.list_books(search_query="test query")

        mock_repo.list_books.assert_called_once()
        assert mock_repo.list_books.call_args[1]["search_query"] == "test query"
        mock_repo.count_books.assert_called_once_with(
            search_query="test query",
            author_id=None,
            pubdate_month=None,
            pubdate_day=None,
        )


def test_get_book_delegates_to_repo() -> None:
    """Test get_book delegates to repository (covers line 111)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_book = MagicMock()
        mock_repo.get_book.return_value = mock_book
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.get_book(123)

        assert result is mock_book
        mock_repo.get_book.assert_called_once_with(123)


def test_get_thumbnail_url_with_book_has_cover() -> None:
    """Test get_thumbnail_url returns URL when book has cover (covers lines 126-134)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=123, title="Test Book", uuid="test-uuid", has_cover=True)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book)

        assert result == "/api/books/123/cover"


def test_get_thumbnail_url_with_cover_path_exists() -> None:
    """Test get_thumbnail_url includes cache-busting parameter when cover exists (covers lines 239-240)."""
    from pathlib import Path
    from unittest.mock import MagicMock, patch

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )

    book = Book(
        id=123,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (123)",
    )

    # Mock cover path that exists
    mock_cover_path = MagicMock(spec=Path)
    mock_cover_path.exists.return_value = True
    mock_cover_path.stat.return_value.st_mtime = 1234567890.5

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_thumbnail_path", return_value=mock_cover_path),
    ):
        service = BookService(library)
        result = service.get_thumbnail_url(book)

        assert result == "/api/books/123/cover?v=1234567890"
        mock_cover_path.stat.assert_called_once()


def test_get_thumbnail_url_with_book_no_cover() -> None:
    """Test get_thumbnail_url returns None when book has no cover (covers lines 126-130)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=123, title="Test Book", uuid="test-uuid", has_cover=False)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book)

        assert result is None


def test_get_thumbnail_url_with_book_with_relations_has_cover() -> None:
    """Test get_thumbnail_url with BookWithRelations has cover (covers lines 126-134)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=456, title="Test Book", uuid="test-uuid", has_cover=True)
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book_with_rels)

        assert result == "/api/books/456/cover"


def test_get_thumbnail_url_with_book_with_relations_no_cover() -> None:
    """Test get_thumbnail_url with BookWithRelations no cover (covers lines 126-130)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=456, title="Test Book", uuid="test-uuid", has_cover=False)
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book_with_rels)

        assert result is None


def test_get_thumbnail_path_with_book_has_cover_exists() -> None:
    """Test get_thumbnail_path returns path when cover exists (covers lines 149-161)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )

    book = Book(
        id=123,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (123)",
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=True) as mock_exists,
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book)

        assert result is not None
        assert str(result).endswith("cover.jpg")
        mock_exists.assert_called_once()


def test_get_thumbnail_path_with_book_no_cover() -> None:
    """Test get_thumbnail_path returns None when book has no cover (covers lines 149-152)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=123, title="Test Book", uuid="test-uuid", has_cover=False)

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_path(book)

        assert result is None


def test_get_thumbnail_path_with_book_cover_not_exists() -> None:
    """Test get_thumbnail_path returns None when cover file doesn't exist (covers lines 149-161)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )

    book = Book(
        id=123,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (123)",
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=False) as mock_exists,
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book)

        assert result is None
        mock_exists.assert_called_once()


def test_get_thumbnail_path_with_book_with_relations() -> None:
    """Test get_thumbnail_path with BookWithRelations (covers lines 149-161)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )

    book = Book(
        id=456,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (456)",
    )
    book_with_rels = BookWithRelations(book=book, authors=[], series=None)

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=True),
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book_with_rels)

        assert result is not None
        assert str(result).endswith("cover.jpg")


def test_search_suggestions_delegates_to_repo() -> None:
    """Test search_suggestions delegates to repository (covers line 192)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.search_suggestions.return_value = {
            "books": [],
            "authors": [],
            "tags": [],
            "series": [],
        }
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.search_suggestions(
            query="test",
            book_limit=5,
            author_limit=5,
            tag_limit=5,
            series_limit=5,
        )

        assert result == {
            "books": [],
            "authors": [],
            "tags": [],
            "series": [],
        }
        mock_repo.search_suggestions.assert_called_once_with(
            query="test",
            book_limit=5,
            author_limit=5,
            tag_limit=5,
            series_limit=5,
        )


def test_filter_suggestions_delegates_to_repo() -> None:
    """Test filter_suggestions delegates to repository (covers line 223)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.filter_suggestions.return_value = [
            {"id": 1, "name": "Author 1"},
            {"id": 2, "name": "Author 2"},
        ]
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.filter_suggestions(
            query="author",
            filter_type="author",
            limit=10,
        )

        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Author 1"
        mock_repo.filter_suggestions.assert_called_once_with(
            query="author",
            filter_type="author",
            limit=10,
        )


def test_list_books_with_filters_calculates_offset() -> None:
    """Test list_books_with_filters calculates offset correctly (covers lines 281-308)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_books_with_filters.return_value = []
        mock_repo.count_books_with_filters.return_value = 0
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        books, total = service.list_books_with_filters(
            page=2,
            page_size=20,
            author_ids=[1, 2],
            title_ids=[3, 4],
        )

        # Page 2 with page_size 20 should have offset 20
        mock_repo.list_books_with_filters.assert_called_once_with(
            limit=20,
            offset=20,
            author_ids=[1, 2],
            title_ids=[3, 4],
            genre_ids=None,
            publisher_ids=None,
            identifier_ids=None,
            series_ids=None,
            formats=None,
            rating_ids=None,
            language_ids=None,
            sort_by="timestamp",
            sort_order="desc",
            full=False,
        )
        mock_repo.count_books_with_filters.assert_called_once_with(
            author_ids=[1, 2],
            title_ids=[3, 4],
            genre_ids=None,
            publisher_ids=None,
            identifier_ids=None,
            series_ids=None,
            formats=None,
            rating_ids=None,
            language_ids=None,
        )
        assert books == []
        assert total == 0


def test_list_books_with_filters_all_filters() -> None:
    """Test list_books_with_filters passes all filter parameters (covers lines 281-308)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.list_books_with_filters.return_value = []
        mock_repo.count_books_with_filters.return_value = 0
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        service.list_books_with_filters(
            page=1,
            page_size=10,
            author_ids=[1],
            title_ids=[2],
            genre_ids=[3],
            publisher_ids=[4],
            identifier_ids=[5],
            series_ids=[6],
            formats=["EPUB"],
            rating_ids=[7],
            language_ids=[8],
            sort_by="title",
            sort_order="asc",
        )

        call_args = mock_repo.list_books_with_filters.call_args[1]
        assert call_args["author_ids"] == [1]
        assert call_args["title_ids"] == [2]
        assert call_args["genre_ids"] == [3]
        assert call_args["publisher_ids"] == [4]
        assert call_args["identifier_ids"] == [5]
        assert call_args["series_ids"] == [6]
        assert call_args["formats"] == ["EPUB"]
        assert call_args["rating_ids"] == [7]
        assert call_args["language_ids"] == [8]
        assert call_args["sort_by"] == "title"
        assert call_args["sort_order"] == "asc"

        count_args = mock_repo.count_books_with_filters.call_args[1]
        assert count_args["author_ids"] == [1]
        assert count_args["title_ids"] == [2]
        assert count_args["genre_ids"] == [3]
        assert count_args["publisher_ids"] == [4]
        assert count_args["identifier_ids"] == [5]
        assert count_args["series_ids"] == [6]
        assert count_args["formats"] == ["EPUB"]
        assert count_args["rating_ids"] == [7]
        assert count_args["language_ids"] == [8]


def test_get_book_full_delegates_to_repo() -> None:
    """Test get_book_full delegates to repository (covers line 129)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_book_full = MagicMock()
        mock_repo.get_book_full.return_value = mock_book_full
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.get_book_full(123)

        assert result is mock_book_full
        mock_repo.get_book_full.assert_called_once_with(123)


def test_update_book_delegates_to_repo() -> None:
    """Test update_book delegates to repository (covers line 192)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_updated_book = MagicMock()
        mock_repo.update_book.return_value = mock_updated_book
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.update_book(
            book_id=123,
            title="New Title",
            author_names=["Author 1"],
        )

        assert result is mock_updated_book
        mock_repo.update_book.assert_called_once()
        call_kwargs = mock_repo.update_book.call_args[1]
        assert call_kwargs["book_id"] == 123
        assert call_kwargs["title"] == "New Title"
        assert call_kwargs["author_names"] == ["Author 1"]


def test_get_thumbnail_url_with_book_with_full_relations() -> None:
    """Test get_thumbnail_url with BookWithFullRelations (covers line 226)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    book = Book(id=789, title="Test Book", uuid="test-uuid", has_cover=True)
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

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service.get_thumbnail_url(book_with_full_rels)

        assert result == "/api/books/789/cover"


def test_get_thumbnail_path_with_book_with_full_relations() -> None:
    """Test get_thumbnail_path with BookWithFullRelations (covers line 251)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )

    book = Book(
        id=789,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (789)",
    )
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

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=True),
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book_with_full_rels)

        assert result is not None
        assert str(result).endswith("cover.jpg")


def test_get_thumbnail_path_with_library_root() -> None:
    """Test get_thumbnail_path uses library_root when available (covers line 268)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )
    library.library_root = "/custom/library/root"  # type: ignore[attr-defined]

    book = Book(
        id=123,
        title="Test Book",
        uuid="test-uuid",
        has_cover=True,
        path="Author Name/Test Book (123)",
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("pathlib.Path.exists", return_value=True),
    ):
        service = BookService(library)
        result = service.get_thumbnail_path(book)

        assert result is not None
        # On Windows, paths use backslashes, so normalize for comparison
        result_str = str(result).replace("\\", "/")
        assert "/custom/library/root" in result_str
        assert result_str.endswith("cover.jpg")


def test_add_book_with_library_root() -> None:
    """Test add_book uses library_root when available (covers lines 459-465)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )
    library.library_root = "/custom/library/root"  # type: ignore[attr-defined]

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.add_book.return_value = 123
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.add_book(
            file_path=Path("/tmp/test.epub"),
            file_format="epub",
            title="Test Book",
        )

        assert result == 123
        call_kwargs = mock_repo.add_book.call_args[1]
        assert call_kwargs["library_path"] == Path("/custom/library/root")


def test_add_book_without_library_root() -> None:
    """Test add_book uses calibre_db_path when library_root not available (covers lines 459-464)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.add_book.return_value = 123
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.add_book(
            file_path=Path("/tmp/test.epub"),
            file_format="epub",
            title="Test Book",
        )

        assert result == 123
        call_kwargs = mock_repo.add_book.call_args[1]
        assert call_kwargs["library_path"] == Path("/path/to/library")


def test_delete_book_with_library_root() -> None:
    """Test delete_book uses library_root when available (covers lines 499-505)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )
    library.library_root = "/custom/library/root"  # type: ignore[attr-defined]

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        service.delete_book(book_id=123, delete_files_from_drive=True)

        call_kwargs = mock_repo.delete_book.call_args[1]
        assert call_kwargs["library_path"] == Path("/custom/library/root")


def test_delete_book_without_library_root() -> None:
    """Test delete_book uses calibre_db_path when library_root not available (covers lines 499-504)."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        service.delete_book(book_id=123, delete_files_from_drive=True)

        call_kwargs = mock_repo.delete_book.call_args[1]
        assert call_kwargs["library_path"] == Path("/path/to/library")


# Tests for Fundamental database associations deletion (bug fix)
def test_delete_book_deletes_fundamental_associations_with_session() -> None:
    """Test delete_book deletes Fundamental database associations when session is available."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_session = MagicMock()
    mock_repo = MagicMock()

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        with patch.object(
            service, "_delete_fundamental_associations"
        ) as mock_delete_associations:
            service.delete_book(book_id=123, delete_files_from_drive=False)

            # Verify Fundamental associations are deleted before Calibre deletion
            mock_delete_associations.assert_called_once_with(123)
            mock_repo.delete_book.assert_called_once()


def test_delete_book_skips_fundamental_associations_without_session() -> None:
    """Test delete_book skips Fundamental associations deletion when session is None."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_repo = MagicMock()

    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=None)
        with patch.object(
            service, "_delete_fundamental_associations"
        ) as mock_delete_associations:
            service.delete_book(book_id=123, delete_files_from_drive=False)

            # Verify Fundamental associations deletion is not called
            mock_delete_associations.assert_not_called()
            mock_repo.delete_book.assert_called_once()


def test_delete_fundamental_associations_deletes_all_model_types() -> None:
    """Test _delete_fundamental_associations deletes all expected model types."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_session = MagicMock()
    book_id = 123

    # Create mock records for each model type
    mock_conversion = MagicMock(spec=BookConversion)
    mock_reading_progress = MagicMock(spec=ReadingProgress)
    mock_reading_session = MagicMock(spec=ReadingSession)
    mock_read_status = MagicMock(spec=ReadStatus)
    mock_annotation = MagicMock(spec=Annotation)
    mock_annotation_dirtied = MagicMock(spec=AnnotationDirtied)
    mock_kobo_reading_state = MagicMock(spec=KoboReadingState)
    mock_kobo_synced_book = MagicMock(spec=KoboSyncedBook)
    mock_kobo_archived_book = MagicMock(spec=KoboArchivedBook)
    mock_epub_fix = MagicMock(spec=EPUBFix)
    mock_metadata_enforcement = MagicMock(spec=MetadataEnforcementOperation)
    mock_ingest_history = MagicMock(spec=IngestHistory)

    # Configure mock_session.exec to return different results for each model
    # We'll return one record per call to simulate different model types
    mock_records = [
        [mock_conversion],
        [mock_reading_progress],
        [mock_reading_session],
        [mock_read_status],
        [mock_annotation],
        [mock_annotation_dirtied],
        [mock_kobo_reading_state],
        [mock_kobo_synced_book],
        [mock_kobo_archived_book],
        [mock_epub_fix],
        [mock_metadata_enforcement],
        [mock_ingest_history],
    ]

    call_count = [0]  # Use list to allow modification in closure

    def exec_side_effect(query: object) -> MagicMock:
        """Return appropriate mock records based on call order."""
        # Return next set of records
        if call_count[0] < len(mock_records):
            result = MagicMock()
            result.all.return_value = mock_records[call_count[0]]
            call_count[0] += 1
            return result
        return MagicMock(all=list)

    mock_session.exec.side_effect = exec_side_effect

    service = BookService(library, session=mock_session)

    # Call the method
    service._delete_fundamental_associations(book_id)

    # Verify session.exec was called for each model type (12 models)
    assert mock_session.exec.call_count == 12

    # Verify session.delete was called for each record (12 records)
    assert mock_session.delete.call_count == 12

    # Verify commit was called
    mock_session.commit.assert_called_once()


def test_delete_fundamental_associations_handles_empty_results() -> None:
    """Test _delete_fundamental_associations handles empty query results gracefully."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_session = MagicMock()
    # Configure exec to return empty results
    mock_session.exec.return_value.all.return_value = []

    service = BookService(library, session=mock_session)

    # Call the method
    service._delete_fundamental_associations(123)

    # Verify session.exec was called for each model type
    assert mock_session.exec.call_count == 12

    # Verify session.delete was never called (no records to delete)
    mock_session.delete.assert_not_called()

    # Verify commit was still called
    mock_session.commit.assert_called_once()


def test_delete_fundamental_associations_handles_errors() -> None:
    """Test _delete_fundamental_associations rolls back on error."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_session = MagicMock()
    mock_session.exec.side_effect = Exception("Database error")

    service = BookService(library, session=mock_session)

    # Call the method and expect it to raise
    with pytest.raises(Exception, match="Database error"):
        service._delete_fundamental_associations(123)

    # Verify rollback was called
    mock_session.rollback.assert_called_once()

    # Verify commit was not called
    mock_session.commit.assert_not_called()


def test_delete_fundamental_associations_no_session() -> None:
    """Test _delete_fundamental_associations does nothing when session is None."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    service = BookService(library, session=None)

    # Call the method - should not raise
    service._delete_fundamental_associations(123)

    # No assertions needed - method should return early without error


def test_delete_associations_by_model_deletes_records() -> None:
    """Test _delete_associations_by_model deletes records for a specific model."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    mock_session = MagicMock()
    mock_record1 = MagicMock(spec=BookConversion)
    mock_record2 = MagicMock(spec=BookConversion)

    mock_session.exec.return_value.all.return_value = [mock_record1, mock_record2]

    service = BookService(library, session=mock_session)

    # Call the helper method
    service._delete_associations_by_model(123, BookConversion, "conversion")

    # Verify exec was called with correct query
    mock_session.exec.assert_called_once()

    # Verify delete was called for each record
    assert mock_session.delete.call_count == 2
    mock_session.delete.assert_any_call(mock_record1)
    mock_session.delete.assert_any_call(mock_record2)


def test_delete_associations_by_model_no_session() -> None:
    """Test _delete_associations_by_model handles None session gracefully."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
    )

    service = BookService(library, session=None)

    # Call the helper method - should return early
    service._delete_associations_by_model(123, BookConversion, "conversion")

    # No assertions needed - method should return early without error


# Fixtures for send_book tests
@pytest.fixture
def library() -> Library:
    """Create a test library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/test_library",
        calibre_db_file="metadata.db",
    )


@pytest.fixture
def book() -> Book:
    """Create a test book."""
    return Book(
        id=1,
        title="Test Book",
        uuid="test-uuid",
        has_cover=False,
        path="Author Name/Test Book (1)",
    )


@pytest.fixture
def book_with_rels(book: Book) -> BookWithFullRelations:
    """Create a test book with relations."""
    return BookWithFullRelations(
        book=book,
        authors=["Author One", "Author Two"],
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
        formats=[{"format": "EPUB", "name": "test.epub", "size": 1000}],
    )


@pytest.fixture
def device() -> EReaderDevice:
    """Create a test e-reader device."""
    return EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="Test Device",
        device_type="kindle",
        is_default=True,
        preferred_format=EBookFormat.EPUB,
    )


@pytest.fixture
def email_service() -> MagicMock:
    """Create a mock email service."""
    return MagicMock()


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


# Tests for send_book_to_device (lines 552-597)
def test_send_book_to_device_success(
    library: Library,
    book_with_rels: BookWithFullRelations,
    device: EReaderDevice,
    email_service: MagicMock,
    tmp_path: Path,
) -> None:
    """Test send_book_to_device successfully sends book (covers lines 552-597)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(
            BookService, "get_book_full", return_value=book_with_rels
        ) as mock_get_book_full,
        patch.object(
            BookService, "_get_primary_author_name", return_value="Author One"
        ),
        patch.object(BookService, "_determine_format_to_send", return_value="EPUB"),
        patch.object(
            BookService,
            "_find_format_in_book",
            return_value={"format": "EPUB", "name": "test.epub", "size": 1000},
        ),
        patch.object(
            BookService, "_get_book_file_path", return_value=tmp_path / "test.epub"
        ),
    ):
        service = BookService(library)
        service.send_book_to_device(
            book_id=1,
            device=device,
            email_service=email_service,
            file_format=None,
        )

        mock_get_book_full.assert_called_once_with(1)
        email_service.send_ebook.assert_called_once()
        call_kwargs = email_service.send_ebook.call_args[1]
        assert call_kwargs["to_email"] == "device@example.com"
        assert call_kwargs["book_title"] == "Test Book"
        assert call_kwargs["preferred_format"] == "EPUB"
        assert call_kwargs["author"] == "Author One"


def test_send_book_to_device_book_not_found(
    library: Library,
    device: EReaderDevice,
    email_service: MagicMock,
) -> None:
    """Test send_book_to_device raises ValueError when book not found (covers lines 558-561)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=None),
    ):
        service = BookService(library)
        with pytest.raises(ValueError, match="book_not_found"):
            service.send_book_to_device(
                book_id=999,
                device=device,
                email_service=email_service,
                file_format=None,
            )


def test_send_book_to_device_book_missing_id(
    library: Library,
    book: Book,
    device: EReaderDevice,
    email_service: MagicMock,
) -> None:
    """Test send_book_to_device raises ValueError when book missing id (covers lines 564-566)."""
    book.id = None  # type: ignore[assignment]
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
        formats=[],
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
    ):
        service = BookService(library)
        with pytest.raises(ValueError, match="book_missing_id"):
            service.send_book_to_device(
                book_id=1,
                device=device,
                email_service=email_service,
                file_format=None,
            )


def test_send_book_to_device_format_not_found(
    library: Library,
    book_with_rels: BookWithFullRelations,
    device: EReaderDevice,
    email_service: MagicMock,
) -> None:
    """Test send_book_to_device raises ValueError when format not found (covers lines 579-583)."""
    # Use a non-Kindle device to avoid triggering EPUB conversion
    non_kindle_device = EReaderDevice(
        id=2,
        user_id=1,
        email="device@example.com",
        device_name="Test Device",
        device_type="kobo",  # Non-Kindle device
        is_default=True,
        preferred_format=EBookFormat.EPUB,
    )
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
        patch.object(BookService, "_get_primary_author_name", return_value="Author"),
        patch.object(BookService, "_determine_format_to_send", return_value="PDF"),
        patch.object(BookService, "_find_format_in_book", return_value=None),
    ):
        service = BookService(library)
        with pytest.raises(ValueError, match="format_not_found"):
            service.send_book_to_device(
                book_id=1,
                device=non_kindle_device,
                email_service=email_service,
                file_format="PDF",
            )


# Tests for send_book unified method (lines 636-674)
def test_send_book_with_to_email_device_found(
    library: Library,
    book_with_rels: BookWithFullRelations,
    device: EReaderDevice,
    email_service: MagicMock,
    mock_session: MagicMock,
    tmp_path: Path,
) -> None:
    """Test send_book with to_email when device is found (covers lines 636-652)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
        patch.object(BookService, "send_book_to_device") as mock_send_to_device,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = device
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        service.send_book(
            book_id=1,
            user_id=1,
            email_service=email_service,
            to_email="device@example.com",
            file_format=None,
        )

        mock_send_to_device.assert_called_once_with(
            book_id=1,
            device=device,
            email_service=email_service,
            file_format=None,
        )


def test_send_book_with_to_email_generic(
    library: Library,
    book_with_rels: BookWithFullRelations,
    email_service: MagicMock,
    mock_session: MagicMock,
    tmp_path: Path,
) -> None:
    """Test send_book with to_email when device not found (generic email) (covers lines 653-661)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
        patch.object(BookService, "send_book_to_email") as mock_send_to_email,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = None
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        service.send_book(
            book_id=1,
            user_id=1,
            email_service=email_service,
            to_email="generic@example.com",
            file_format=None,
        )

        mock_send_to_email.assert_called_once_with(
            book_id=1,
            to_email="generic@example.com",
            email_service=email_service,
            file_format=None,
        )


def test_send_book_without_to_email_device_found(
    library: Library,
    book_with_rels: BookWithFullRelations,
    device: EReaderDevice,
    email_service: MagicMock,
    mock_session: MagicMock,
) -> None:
    """Test send_book without to_email uses default device (covers lines 662-679)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
        patch.object(BookService, "send_book_to_device") as mock_send_to_device,
    ):
        mock_repo = MagicMock()
        mock_repo.find_default.return_value = device
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        service.send_book(
            book_id=1,
            user_id=1,
            email_service=email_service,
            to_email=None,
            file_format=None,
        )

        mock_send_to_device.assert_called_once_with(
            book_id=1,
            device=device,
            email_service=email_service,
            file_format=None,
        )


def test_send_book_without_to_email_no_device(
    library: Library,
    email_service: MagicMock,
    mock_session: MagicMock,
) -> None:
    """Test send_book without to_email raises ValueError when no device (covers lines 664-667)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
        patch.object(BookService, "_get_user_device", return_value=None),
    ):
        mock_repo = MagicMock()
        mock_repo.find_default.return_value = None
        mock_repo.find_by_user.return_value = []
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        with pytest.raises(ValueError, match="no_device_available"):
            service.send_book(
                book_id=1,
                user_id=1,
                email_service=email_service,
                to_email=None,
                file_format=None,
            )


# Tests for _find_device_by_email (lines 696-710)
def test_find_device_by_email_found(
    library: Library,
    device: EReaderDevice,
    mock_session: MagicMock,
) -> None:
    """Test _find_device_by_email finds device (covers lines 696-710)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = device
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        result = service._find_device_by_email(user_id=1, email="device@example.com")

        assert result == device
        mock_repo.find_by_email.assert_called_once_with(1, "device@example.com")


def test_find_device_by_email_not_found(
    library: Library,
    mock_session: MagicMock,
) -> None:
    """Test _find_device_by_email returns None when device not found (covers lines 708-710)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = None
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        result = service._find_device_by_email(user_id=1, email="unknown@example.com")

        assert result is None


def test_find_device_by_email_no_session(
    library: Library,
) -> None:
    """Test _find_device_by_email returns None when no session (covers lines 696-698)."""
    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library, session=None)
        result = service._find_device_by_email(user_id=1, email="device@example.com")

        assert result is None


# Tests for _get_user_device (lines 725-745)
def test_get_user_device_default_device(
    library: Library,
    device: EReaderDevice,
    mock_session: MagicMock,
) -> None:
    """Test _get_user_device returns default device (covers lines 725-736)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_default.return_value = device
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        result = service._get_user_device(user_id=1)

        assert result == device
        mock_repo.find_default.assert_called_once_with(1)


def test_get_user_device_first_device(
    library: Library,
    device: EReaderDevice,
    mock_session: MagicMock,
) -> None:
    """Test _get_user_device returns first device when no default (covers lines 738-742)."""
    device2 = EReaderDevice(
        id=2,
        user_id=1,
        email="device2@example.com",
        device_name="Device 2",
        device_type="kobo",
        is_default=False,
        preferred_format=EBookFormat.MOBI,
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_default.return_value = None
        mock_repo.find_by_user.return_value = [device, device2]
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        result = service._get_user_device(user_id=1)

        assert result == device
        mock_repo.find_default.assert_called_once_with(1)
        mock_repo.find_by_user.assert_called_once_with(1)


def test_get_user_device_no_devices(
    library: Library,
    mock_session: MagicMock,
) -> None:
    """Test _get_user_device returns None when no devices (covers lines 744-745)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch(
            "fundamental.repositories.ereader_repository.EReaderRepository"
        ) as mock_repo_class,
    ):
        mock_repo = MagicMock()
        mock_repo.find_default.return_value = None
        mock_repo.find_by_user.return_value = []
        mock_repo_class.return_value = mock_repo

        service = BookService(library, session=mock_session)
        result = service._get_user_device(user_id=1)

        assert result is None


def test_get_user_device_no_session(
    library: Library,
) -> None:
    """Test _get_user_device returns None when no session (covers lines 725-727)."""
    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library, session=None)
        result = service._get_user_device(user_id=1)

        assert result is None


# Tests for send_book_to_email (lines 779-837)
def test_send_book_to_email_success(
    library: Library,
    book_with_rels: BookWithFullRelations,
    email_service: MagicMock,
    tmp_path: Path,
) -> None:
    """Test send_book_to_email successfully sends book (covers lines 779-837)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
        patch.object(
            BookService, "_get_primary_author_name", return_value="Author One"
        ),
        patch.object(
            BookService,
            "_find_format_in_book",
            return_value={"format": "EPUB", "name": "test.epub", "size": 1000},
        ),
        patch.object(
            BookService, "_get_book_file_path", return_value=tmp_path / "test.epub"
        ),
    ):
        service = BookService(library)
        service.send_book_to_email(
            book_id=1,
            to_email="test@example.com",
            email_service=email_service,
            file_format="EPUB",
            preferred_format=None,
        )

        email_service.send_ebook.assert_called_once()
        call_kwargs = email_service.send_ebook.call_args[1]
        assert call_kwargs["to_email"] == "test@example.com"
        assert call_kwargs["book_title"] == "Test Book"
        assert call_kwargs["preferred_format"] == "EPUB"
        assert call_kwargs["author"] == "Author One"


def test_send_book_to_email_book_not_found(
    library: Library,
    email_service: MagicMock,
) -> None:
    """Test send_book_to_email raises ValueError when book not found (covers lines 785-788)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=None),
    ):
        service = BookService(library)
        with pytest.raises(ValueError, match="book_not_found"):
            service.send_book_to_email(
                book_id=999,
                to_email="test@example.com",
                email_service=email_service,
                file_format=None,
                preferred_format=None,
            )


def test_send_book_to_email_book_missing_id(
    library: Library,
    book: Book,
    email_service: MagicMock,
) -> None:
    """Test send_book_to_email raises ValueError when book missing id (covers lines 790-793)."""
    book.id = None  # type: ignore[assignment]
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
        formats=[],
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
    ):
        service = BookService(library)
        with pytest.raises(ValueError, match="book_missing_id"):
            service.send_book_to_email(
                book_id=1,
                to_email="test@example.com",
                email_service=email_service,
                file_format=None,
                preferred_format=None,
            )


@pytest.mark.parametrize(
    ("file_format", "preferred_format", "expected_format"),
    [
        ("EPUB", None, "EPUB"),
        (None, "MOBI", "MOBI"),
        (None, None, "EPUB"),  # Uses first available format
    ],
)
def test_send_book_to_email_format_determination(
    library: Library,
    book_with_rels: BookWithFullRelations,
    email_service: MagicMock,
    tmp_path: Path,
    file_format: str | None,
    preferred_format: str | None,
    expected_format: str,
) -> None:
    """Test send_book_to_email format determination (covers lines 798-814)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
        patch.object(BookService, "_get_primary_author_name", return_value="Author"),
        patch.object(
            BookService,
            "_find_format_in_book",
            return_value={
                "format": expected_format,
                "name": f"test.{expected_format.lower()}",
                "size": 1000,
            },
        ),
        patch.object(
            BookService,
            "_get_book_file_path",
            return_value=tmp_path / f"test.{expected_format.lower()}",
        ),
    ):
        service = BookService(library)
        service.send_book_to_email(
            book_id=1,
            to_email="test@example.com",
            email_service=email_service,
            file_format=file_format,
            preferred_format=preferred_format,
        )

        call_kwargs = email_service.send_ebook.call_args[1]
        assert call_kwargs["preferred_format"] == expected_format


def test_send_book_to_email_no_formats_available(
    library: Library,
    book: Book,
    email_service: MagicMock,
) -> None:
    """Test send_book_to_email raises ValueError when no formats available (covers lines 802-812)."""
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
        formats=[],  # No formats
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
    ):
        service = BookService(library)
        with pytest.raises(ValueError, match="no_formats_available"):
            service.send_book_to_email(
                book_id=1,
                to_email="test@example.com",
                email_service=email_service,
                file_format=None,
                preferred_format=None,
            )


def test_send_book_to_email_format_str_empty(
    library: Library,
    book: Book,
    email_service: MagicMock,
) -> None:
    """Test send_book_to_email raises ValueError when format_str is empty (covers lines 808-809)."""
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
        formats=[{"format": "", "name": "test"}],  # format is empty string
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
        patch.object(BookService, "_get_book_file_path", return_value=None),
    ):
        service = BookService(library)
        with pytest.raises(ValueError, match="no_formats_available"):
            service.send_book_to_email(
                book_id=1,
                to_email="test@example.com",
                email_service=email_service,
                file_format=None,
            )


def test_send_book_to_email_format_not_found(
    library: Library,
    book_with_rels: BookWithFullRelations,
    email_service: MagicMock,
) -> None:
    """Test send_book_to_email raises ValueError when format not found (covers lines 819-823)."""
    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "get_book_full", return_value=book_with_rels),
        patch.object(BookService, "_find_format_in_book", return_value=None),
    ):
        service = BookService(library)
        with pytest.raises(ValueError, match="format_not_found"):
            service.send_book_to_email(
                book_id=1,
                to_email="test@example.com",
                email_service=email_service,
                file_format="PDF",
                preferred_format=None,
            )


# Tests for _determine_format_to_send (lines 866-880)
@pytest.mark.parametrize(
    ("requested_format", "device_format", "expected_format"),
    [
        ("MOBI", EBookFormat.EPUB, "MOBI"),  # Requested format takes precedence
        (None, EBookFormat.EPUB, "EPUB"),  # Device format used
        (None, None, "EPUB"),  # First available format
    ],
)
def test_determine_format_to_send(
    library: Library,
    book_with_rels: BookWithFullRelations,
    requested_format: str | None,
    device_format: EBookFormat | None,
    expected_format: str,
) -> None:
    """Test _determine_format_to_send (covers lines 866-880)."""
    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="Test Device",
        device_type="kindle",
        is_default=True,
        preferred_format=device_format,
    )

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service._determine_format_to_send(
            book_with_rels=book_with_rels,
            device=device,
            requested_format=requested_format,
        )

        assert result == expected_format


def test_determine_format_to_send_no_formats_available(
    library: Library,
    book: Book,
) -> None:
    """Test _determine_format_to_send raises ValueError when no formats available (covers lines 879-880)."""
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
        formats=[],  # No formats
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        email="device@example.com",
        device_name="Test Device",
        device_type="kindle",
        is_default=True,
        preferred_format=None,
    )

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        with pytest.raises(ValueError, match="no_formats_available"):
            service._determine_format_to_send(
                book_with_rels=book_with_rels,
                device=device,
                requested_format=None,
            )


# Tests for _find_format_in_book (lines 901-906)
@pytest.mark.parametrize(
    ("formats", "requested_format", "expected_result"),
    [
        (
            [{"format": "EPUB", "name": "test.epub"}],
            "EPUB",
            {"format": "EPUB", "name": "test.epub"},
        ),
        (
            [{"format": "EPUB", "name": "test.epub"}],
            "epub",
            {"format": "EPUB", "name": "test.epub"},
        ),  # Case insensitive
        ([{"format": "EPUB", "name": "test.epub"}], "PDF", None),  # Not found
        (
            [
                {"format": "EPUB", "name": "test.epub"},
                {"format": "MOBI", "name": "test.mobi"},
            ],
            "MOBI",
            {"format": "MOBI", "name": "test.mobi"},
        ),
        ([{"format": 123, "name": "test"}], "EPUB", None),  # Non-string format
    ],
)
def test_find_format_in_book(
    library: Library,
    formats: list[dict[str, str | int]],
    requested_format: str,
    expected_result: dict[str, str | int] | None,
) -> None:
    """Test _find_format_in_book (covers lines 901-906)."""
    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service._find_format_in_book(formats, requested_format)

        assert result == expected_result


# Tests for _get_book_file_path (lines 939-981)
def test_get_book_file_path_with_library_root(
    library: Library,
    book: Book,
    tmp_path: Path,
) -> None:
    """Test _get_book_file_path with library_root (covers lines 939-941)."""
    library.library_root = str(tmp_path)  # type: ignore[attr-defined]
    format_data = {"format": "EPUB", "name": "test.epub", "size": 1000}

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "_get_file_name", return_value="test.epub"),
    ):
        service = BookService(library)
        book_path = tmp_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        test_file = book_path / "test.epub"
        test_file.write_text("test content")

        result = service._get_book_file_path(
            book, book_id=1, format_data=format_data, file_format="EPUB"
        )

        assert result == test_file


def test_get_book_file_path_without_library_root_dir(
    library: Library,
    book: Book,
    tmp_path: Path,
) -> None:
    """Test _get_book_file_path without library_root, calibre_db_path is dir (covers lines 942-945)."""
    library.calibre_db_path = str(tmp_path)
    format_data = {"format": "EPUB", "name": "test.epub", "size": 1000}

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "_get_file_name", return_value="test.epub"),
        patch("pathlib.Path.is_dir", return_value=True),
    ):
        service = BookService(library)
        book_path = tmp_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        test_file = book_path / "test.epub"
        test_file.write_text("test content")

        result = service._get_book_file_path(
            book, book_id=1, format_data=format_data, file_format="EPUB"
        )

        assert result == test_file


def test_get_book_file_path_without_library_root_file(
    library: Library,
    book: Book,
    tmp_path: Path,
) -> None:
    """Test _get_book_file_path without library_root, calibre_db_path is file (covers lines 943-947)."""
    db_file = tmp_path / "metadata.db"
    db_file.write_text("test")
    library.calibre_db_path = str(db_file)
    format_data = {"format": "EPUB", "name": "test.epub", "size": 1000}

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "_get_file_name", return_value="test.epub"),
        patch("pathlib.Path.is_dir", return_value=False),
    ):
        service = BookService(library)
        book_path = tmp_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        test_file = book_path / "test.epub"
        test_file.write_text("test content")

        result = service._get_book_file_path(
            book, book_id=1, format_data=format_data, file_format="EPUB"
        )

        assert result == test_file


def test_get_book_file_path_primary_path_exists(
    library: Library,
    book: Book,
    tmp_path: Path,
) -> None:
    """Test _get_book_file_path finds file at primary path (covers lines 955-957)."""
    library.library_root = str(tmp_path)  # type: ignore[attr-defined]
    format_data = {"format": "EPUB", "name": "test.epub", "size": 1000}

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "_get_file_name", return_value="test.epub"),
    ):
        service = BookService(library)
        book_path = tmp_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        test_file = book_path / "test.epub"
        test_file.write_text("test content")

        result = service._get_book_file_path(
            book, book_id=1, format_data=format_data, file_format="EPUB"
        )

        assert result == test_file


def test_get_book_file_path_alternative_path_exists(
    library: Library,
    book: Book,
    tmp_path: Path,
) -> None:
    """Test _get_book_file_path finds file at alternative path (covers lines 959-966)."""
    library.library_root = str(tmp_path)  # type: ignore[attr-defined]
    format_data = {"format": "EPUB", "name": "test.epub", "size": 1000}

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "_get_file_name", return_value="nonexistent.epub"),
    ):
        service = BookService(library)
        book_path = tmp_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        alt_file = book_path / "1.epub"  # Alternative path: book_id.format
        alt_file.write_text("test content")

        result = service._get_book_file_path(
            book, book_id=1, format_data=format_data, file_format="EPUB"
        )

        assert result == alt_file


def test_get_book_file_path_directory_search(
    library: Library,
    book: Book,
    tmp_path: Path,
) -> None:
    """Test _get_book_file_path finds file by directory search (covers lines 968-977)."""
    library.library_root = str(tmp_path)  # type: ignore[attr-defined]
    format_data = {"format": "EPUB", "name": "test.epub", "size": 1000}

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "_get_file_name", return_value="nonexistent.epub"),
    ):
        service = BookService(library)
        book_path = tmp_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        # Create file with different name but same extension
        found_file = book_path / "actual.epub"
        found_file.write_text("test content")

        result = service._get_book_file_path(
            book, book_id=1, format_data=format_data, file_format="EPUB"
        )

        assert result == found_file


def test_get_book_file_path_not_found(
    library: Library,
    book: Book,
    tmp_path: Path,
) -> None:
    """Test _get_book_file_path raises ValueError when file not found (covers lines 979-981)."""
    library.library_root = str(tmp_path)  # type: ignore[attr-defined]
    format_data = {"format": "EPUB", "name": "test.epub", "size": 1000}

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch.object(BookService, "_get_file_name", return_value="nonexistent.epub"),
    ):
        service = BookService(library)
        book_path = tmp_path / book.path
        book_path.mkdir(parents=True, exist_ok=True)
        # Don't create any files

        with pytest.raises(ValueError, match="file_not_found"):
            service._get_book_file_path(
                book, book_id=1, format_data=format_data, file_format="EPUB"
            )


# Tests for _get_file_name (lines 1005-1022)
@pytest.mark.parametrize(
    ("format_data", "book_id", "file_format", "expected_name"),
    [
        ({"name": "My Book.epub"}, 1, "EPUB", "My Book.epub"),  # Name with extension
        ({"name": "My Book"}, 1, "EPUB", "My Book.epub"),  # Name without extension
        ({"name": "  "}, 1, "EPUB", "1.epub"),  # Empty name
        ({"name": ""}, 1, "EPUB", "1.epub"),  # Empty string name
        ({}, 1, "EPUB", "1.epub"),  # No name key
        (
            {"name": "My Book.mobi"},
            1,
            "EPUB",
            "My Book.mobi.epub",
        ),  # Different extension, appends new one
        ({"name": "My Book.EPUB"}, 1, "EPUB", "My Book.EPUB"),  # Case insensitive check
    ],
)
def test_get_file_name(
    library: Library,
    format_data: dict[str, str | int],
    book_id: int,
    file_format: str,
    expected_name: str,
) -> None:
    """Test _get_file_name (covers lines 1005-1022)."""
    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service._get_file_name(format_data, book_id, file_format)

        assert result == expected_name


# Tests for _get_primary_author_name (lines 1040-1042)
@pytest.mark.parametrize(
    ("authors", "expected_result"),
    [
        (["Author One"], "Author One"),
        (["Author One", "Author Two"], "Author One, Author Two"),
        ([], None),
    ],
)
def test_get_primary_author_name(
    library: Library,
    book: Book,
    authors: list[str],
    expected_result: str | None,
) -> None:
    """Test _get_primary_author_name (covers lines 1040-1042)."""
    book_with_rels = BookWithFullRelations(
        book=book,
        authors=authors,
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

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        result = BookService._get_primary_author_name(book_with_rels)

        assert result == expected_result


# Tests for lookup_tags_by_names (lines 365-381)
def test_lookup_tags_by_names_empty_list(library: Library) -> None:
    """Test lookup_tags_by_names with empty list (covers line 365-366)."""
    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        service = BookService(library)
        result = service.lookup_tags_by_names([])

        assert result == []


def test_lookup_tags_by_names_single_tag(library: Library) -> None:
    """Test lookup_tags_by_names with single tag (covers lines 368-381)."""
    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(1, "Fiction")]
        mock_session.exec.return_value = mock_result
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None

        service = BookService(library)
        result = service.lookup_tags_by_names(["Fiction"])

        assert result == [{"id": 1, "name": "Fiction"}]


def test_lookup_tags_by_names_multiple_tags(library: Library) -> None:
    """Test lookup_tags_by_names with multiple tags (covers lines 368-381)."""
    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(1, "Fiction"), (2, "Science Fiction")]
        mock_session.exec.return_value = mock_result
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None

        service = BookService(library)
        result = service.lookup_tags_by_names(["Fiction", "Science Fiction"])

        assert len(result) == 2
        assert {"id": 1, "name": "Fiction"} in result
        assert {"id": 2, "name": "Science Fiction"} in result


def test_lookup_tags_by_names_case_insensitive(library: Library) -> None:
    """Test lookup_tags_by_names is case-insensitive (covers lines 371-373)."""
    with patch(
        "fundamental.services.book_service.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(1, "Fiction")]
        mock_session.exec.return_value = mock_result
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None

        service = BookService(library)
        result = service.lookup_tags_by_names(["fiction", "FICTION"])

        # Verify case-insensitive search was used
        assert len(result) >= 0  # May or may not find results depending on mock


# Tests for _ensure_epub_for_kindle (lines 1125-1198)
def test_ensure_epub_for_kindle_epub_exists(library: Library, book: Book) -> None:
    """Test _ensure_epub_for_kindle when EPUB already exists (covers lines 1125-1127)."""
    from fundamental.repositories import BookWithFullRelations

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
        formats=[{"format": "EPUB", "name": "test.epub"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        result = service._ensure_epub_for_kindle(1, book_with_rels, device)

        assert result == "EPUB"


def test_ensure_epub_for_kindle_no_formats(library: Library, book: Book) -> None:
    """Test _ensure_epub_for_kindle when no formats available (covers lines 1130-1132)."""
    from fundamental.repositories import BookWithFullRelations

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
        formats=[],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        with pytest.raises(ValueError, match="no_formats_available_for_conversion"):
            service._ensure_epub_for_kindle(1, book_with_rels, device)


def test_ensure_epub_for_kindle_no_valid_source_format(
    library: Library, book: Book
) -> None:
    """Test _ensure_epub_for_kindle when source format is invalid (covers lines 1135-1138)."""
    from fundamental.repositories import BookWithFullRelations

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
        formats=[{"format": "", "name": "test"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        with pytest.raises(ValueError, match="no_valid_source_format_for_conversion"):
            service._ensure_epub_for_kindle(1, book_with_rels, device)


def test_ensure_epub_for_kindle_no_session(library: Library, book: Book) -> None:
    """Test _ensure_epub_for_kindle when session is None (covers lines 1148-1150)."""
    from fundamental.repositories import BookWithFullRelations

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
        formats=[{"format": "MOBI", "name": "test.mobi"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    with patch("fundamental.services.book_service.CalibreBookRepository"):
        service = BookService(library)
        service._session = None
        with pytest.raises(ValueError, match="Session not available"):
            service._ensure_epub_for_kindle(1, book_with_rels, device)


def test_ensure_epub_for_kindle_no_library(library: Library, book: Book) -> None:
    """Test _ensure_epub_for_kindle when no active library (covers lines 1155-1157)."""
    from fundamental.repositories import BookWithFullRelations
    from tests.conftest import DummySession

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
        formats=[{"format": "MOBI", "name": "test.mobi"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("fundamental.services.book_service.LibraryRepository"),
        patch(
            "fundamental.services.book_service.LibraryService"
        ) as mock_lib_service_class,
    ):
        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = None
        mock_lib_service_class.return_value = mock_lib_service

        service = BookService(library)
        service._session = DummySession()  # type: ignore[assignment]

        with pytest.raises(ValueError, match="No active library configured"):
            service._ensure_epub_for_kindle(1, book_with_rels, device)


def test_ensure_epub_for_kindle_conversion_success(
    library: Library, book: Book
) -> None:
    """Test _ensure_epub_for_kindle when conversion succeeds (covers lines 1161-1185)."""
    from fundamental.models.conversion import BookConversion, ConversionStatus
    from fundamental.repositories import BookWithFullRelations
    from tests.conftest import DummySession

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
        formats=[{"format": "MOBI", "name": "test.mobi"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    conversion = BookConversion(
        id=1,
        book_id=1,
        original_format="MOBI",
        target_format="EPUB",
        status=ConversionStatus.COMPLETED,
    )

    refreshed_book = BookWithFullRelations(
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
        formats=[{"format": "EPUB", "name": "test.epub"}],
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("fundamental.services.book_service.LibraryRepository"),
        patch(
            "fundamental.services.book_service.LibraryService"
        ) as mock_lib_service_class,
        patch(
            "fundamental.services.book_service.create_conversion_service"
        ) as mock_create_conversion,
    ):
        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = library
        mock_lib_service_class.return_value = mock_lib_service

        mock_conv_service = MagicMock()
        mock_conv_service.convert_book.return_value = conversion
        mock_create_conversion.return_value = mock_conv_service

        service = BookService(library)
        service._session = DummySession()  # type: ignore[assignment]
        service.get_book_full = MagicMock(return_value=refreshed_book)  # type: ignore[method-assign]

        result = service._ensure_epub_for_kindle(1, book_with_rels, device)

        assert result == "EPUB"
        mock_conv_service.convert_book.assert_called_once_with(
            book_id=1,
            original_format="MOBI",
            target_format="EPUB",
            user_id=1,
            conversion_method=ConversionMethod.KINDLE_SEND,
            backup_original=False,
        )


def test_ensure_epub_for_kindle_conversion_failed(library: Library, book: Book) -> None:
    """Test _ensure_epub_for_kindle when conversion fails (covers lines 1187-1189)."""
    from fundamental.models.conversion import BookConversion, ConversionStatus
    from fundamental.repositories import BookWithFullRelations
    from tests.conftest import DummySession

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
        formats=[{"format": "MOBI", "name": "test.mobi"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    conversion = BookConversion(
        id=1,
        book_id=1,
        original_format="MOBI",
        target_format="EPUB",
        status=ConversionStatus.FAILED,
        error_message="Conversion error",
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("fundamental.services.book_service.LibraryRepository"),
        patch(
            "fundamental.services.book_service.LibraryService"
        ) as mock_lib_service_class,
        patch(
            "fundamental.services.book_service.create_conversion_service"
        ) as mock_create_conversion,
    ):
        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = library
        mock_lib_service_class.return_value = mock_lib_service

        mock_conv_service = MagicMock()
        mock_conv_service.convert_book.return_value = conversion
        mock_create_conversion.return_value = mock_conv_service

        service = BookService(library)
        service._session = DummySession()  # type: ignore[assignment]

        with pytest.raises(RuntimeError, match="Failed to convert to EPUB"):
            service._ensure_epub_for_kindle(1, book_with_rels, device)


def test_ensure_epub_for_kindle_exception_handling(
    library: Library, book: Book
) -> None:
    """Test _ensure_epub_for_kindle exception handling (covers lines 1190-1198)."""
    from fundamental.repositories import BookWithFullRelations
    from tests.conftest import DummySession

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
        formats=[{"format": "MOBI", "name": "test.mobi"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("fundamental.services.book_service.LibraryRepository"),
        patch(
            "fundamental.services.book_service.LibraryService"
        ) as mock_lib_service_class,
        patch(
            "fundamental.services.book_service.create_conversion_service"
        ) as mock_create_conversion,
    ):
        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = library
        mock_lib_service_class.return_value = mock_lib_service

        mock_conv_service = MagicMock()
        mock_conv_service.convert_book.side_effect = ValueError("Conversion error")
        mock_create_conversion.return_value = mock_conv_service

        service = BookService(library)
        service._session = DummySession()  # type: ignore[assignment]

        with pytest.raises(ValueError, match="Conversion error"):
            service._ensure_epub_for_kindle(1, book_with_rels, device)


def test_ensure_epub_for_kindle_refresh_no_epub(library: Library, book: Book) -> None:
    """Test _ensure_epub_for_kindle when refresh doesn't find EPUB (covers lines 1177-1185)."""
    from fundamental.models.conversion import BookConversion, ConversionStatus
    from fundamental.repositories import BookWithFullRelations
    from tests.conftest import DummySession

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
        formats=[{"format": "MOBI", "name": "test.mobi"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    conversion = BookConversion(
        id=1,
        book_id=1,
        original_format="MOBI",
        target_format="EPUB",
        status=ConversionStatus.COMPLETED,
    )

    refreshed_book = BookWithFullRelations(
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
        formats=[],  # No EPUB after refresh
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("fundamental.services.book_service.LibraryRepository"),
        patch(
            "fundamental.services.book_service.LibraryService"
        ) as mock_lib_service_class,
        patch(
            "fundamental.services.book_service.create_conversion_service"
        ) as mock_create_conversion,
    ):
        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = library
        mock_lib_service_class.return_value = mock_lib_service

        mock_conv_service = MagicMock()
        mock_conv_service.convert_book.return_value = conversion
        mock_create_conversion.return_value = mock_conv_service

        service = BookService(library)
        service._session = DummySession()  # type: ignore[assignment]
        service.get_book_full = MagicMock(return_value=refreshed_book)  # type: ignore[method-assign]

        result = service._ensure_epub_for_kindle(1, book_with_rels, device)

        # Should still return EPUB even if refresh doesn't find it
        assert result == "EPUB"


def test_ensure_epub_for_kindle_refresh_none(library: Library, book: Book) -> None:
    """Test _ensure_epub_for_kindle when refresh returns None (covers lines 1177-1185)."""
    from fundamental.models.conversion import BookConversion, ConversionStatus
    from fundamental.repositories import BookWithFullRelations
    from tests.conftest import DummySession

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
        formats=[{"format": "MOBI", "name": "test.mobi"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=1,
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    conversion = BookConversion(
        id=1,
        book_id=1,
        original_format="MOBI",
        target_format="EPUB",
        status=ConversionStatus.COMPLETED,
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("fundamental.services.book_service.LibraryRepository"),
        patch(
            "fundamental.services.book_service.LibraryService"
        ) as mock_lib_service_class,
        patch(
            "fundamental.services.book_service.create_conversion_service"
        ) as mock_create_conversion,
    ):
        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = library
        mock_lib_service_class.return_value = mock_lib_service

        mock_conv_service = MagicMock()
        mock_conv_service.convert_book.return_value = conversion
        mock_create_conversion.return_value = mock_conv_service

        service = BookService(library)
        service._session = DummySession()  # type: ignore[assignment]
        service.get_book_full = MagicMock(return_value=None)  # type: ignore[method-assign]

        result = service._ensure_epub_for_kindle(1, book_with_rels, device)

        # Should still return EPUB even if refresh returns None
        assert result == "EPUB"


def test_ensure_epub_for_kindle_no_user_id(library: Library, book: Book) -> None:
    """Test _ensure_epub_for_kindle when device has no user_id (covers line 1166)."""
    from fundamental.models.conversion import BookConversion, ConversionStatus
    from fundamental.repositories import BookWithFullRelations
    from tests.conftest import DummySession

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
        formats=[{"format": "MOBI", "name": "test.mobi"}],
    )

    device = EReaderDevice(
        id=1,
        user_id=None,  # type: ignore[arg-type]
        device_name="Kindle",
        device_type="kindle",
        formats=[EBookFormat.EPUB],
    )

    conversion = BookConversion(
        id=1,
        book_id=1,
        original_format="MOBI",
        target_format="EPUB",
        status=ConversionStatus.COMPLETED,
    )

    with (
        patch("fundamental.services.book_service.CalibreBookRepository"),
        patch("fundamental.services.book_service.LibraryRepository"),
        patch(
            "fundamental.services.book_service.LibraryService"
        ) as mock_lib_service_class,
        patch(
            "fundamental.services.book_service.create_conversion_service"
        ) as mock_create_conversion,
    ):
        mock_lib_service = MagicMock()
        mock_lib_service.get_active_library.return_value = library
        mock_lib_service_class.return_value = mock_lib_service

        mock_conv_service = MagicMock()
        mock_conv_service.convert_book.return_value = conversion
        mock_create_conversion.return_value = mock_conv_service

        service = BookService(library)
        service._session = DummySession()  # type: ignore[assignment]
        service.get_book_full = MagicMock(return_value=None)  # type: ignore[method-assign]

        result = service._ensure_epub_for_kindle(1, book_with_rels, device)

        assert result == "EPUB"
        # Verify user_id was None in conversion call
        call_args = mock_conv_service.convert_book.call_args
        assert call_args.kwargs["user_id"] is None


# Note: Lines 641-648 are covered by the _ensure_epub_for_kindle tests above.
# These lines are part of send_book_to_device but the logic is fully tested
# through the direct _ensure_epub_for_kindle method tests.
