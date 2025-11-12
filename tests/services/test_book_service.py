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

"""Tests for book service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from fundamental.models.config import Library
from fundamental.models.core import Book
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
            sort_by="timestamp",
            sort_order="desc",
        )
        mock_repo.count_books.assert_called_once_with(search_query=None)
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
        mock_repo.count_books.assert_called_once_with(search_query="test query")


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
        assert "/custom/library/root" in str(result)
        assert str(result).endswith("cover.jpg")


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
