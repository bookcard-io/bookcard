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

"""Tests for Calibre book repository."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import select

from fundamental.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from fundamental.repositories import (
    AuthorFilterStrategy,
    AuthorSuggestionStrategy,
    BookWithFullRelations,
    CalibreBookRepository,
    FilterBuilder,
    FilterContext,
    FilterSuggestionFactory,
    FormatFilterStrategy,
    FormatSuggestionStrategy,
    GenreFilterStrategy,
    GenreSuggestionStrategy,
    IdentifierFilterStrategy,
    IdentifierSuggestionStrategy,
    LanguageFilterStrategy,
    LanguageSuggestionStrategy,
    PublisherFilterStrategy,
    PublisherSuggestionStrategy,
    RatingFilterStrategy,
    RatingSuggestionStrategy,
    SeriesFilterStrategy,
    SeriesSuggestionStrategy,
    TitleFilterStrategy,
    TitleSuggestionStrategy,
)


def test_calibre_book_repository_init() -> None:
    """Test CalibreBookRepository initialization (covers lines 84-87)."""
    repo = CalibreBookRepository("/path/to/library", "metadata.db")

    assert repo._calibre_db_path == Path("/path/to/library")
    assert repo._calibre_db_file == "metadata.db"
    assert repo._db_path == Path("/path/to/library") / "metadata.db"
    assert repo._engine is None


def test_extract_book_from_book_instance() -> None:
    """Test _extract_book_from_book_instance extracts Book instance (covers lines 119-121)."""
    repo = CalibreBookRepository("/path/to/library")

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    result = repo._extract_book_from_book_instance(book)

    assert result is book


def test_extract_book_from_book_instance_not_book() -> None:
    """Test _extract_book_from_book_instance returns None for non-Book (covers lines 119-121)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_book_from_book_instance("not a book")

    assert result is None


def test_extract_book_from_indexable_container() -> None:
    """Test _extract_book_from_indexable_container extracts from tuple (covers lines 125-129)."""
    repo = CalibreBookRepository("/path/to/library")

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    result = repo._extract_book_from_indexable_container((book, "other"))

    assert result is book


def test_extract_book_from_indexable_container_not_book() -> None:
    """Test _extract_book_from_indexable_container returns None when not Book (covers lines 125-129)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_book_from_indexable_container(("not a book",))

    assert result is None


def test_extract_book_from_indexable_container_exception() -> None:
    """Test _extract_book_from_indexable_container handles exceptions (covers lines 125-129)."""
    repo = CalibreBookRepository("/path/to/library")

    # Object without __getitem__
    result = repo._extract_book_from_indexable_container(object())

    assert result is None


def test_extract_book_from_attr() -> None:
    """Test _extract_book_from_attr extracts from object with Book attribute (covers lines 133-137)."""
    repo = CalibreBookRepository("/path/to/library")

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    mock_result = MagicMock()
    mock_result.Book = book

    result = repo._extract_book_from_attr(mock_result)

    assert result is book


def test_extract_book_from_attr_not_book() -> None:
    """Test _extract_book_from_attr returns None when not Book (covers lines 133-137)."""
    repo = CalibreBookRepository("/path/to/library")

    mock_result = MagicMock()
    mock_result.Book = "not a book"

    result = repo._extract_book_from_attr(mock_result)

    assert result is None


def test_extract_book_from_attr_exception() -> None:
    """Test _extract_book_from_attr handles AttributeError (covers lines 133-137)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_book_from_attr(object())

    assert result is None


def test_extract_book_from_getitem() -> None:
    """Test _extract_book_from_getitem extracts from dict-like (covers lines 141-147)."""
    repo = CalibreBookRepository("/path/to/library")

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    mock_result = MagicMock()
    mock_result.__getitem__ = MagicMock(return_value=book)

    result = repo._extract_book_from_getitem(mock_result)

    assert result is book


def test_extract_book_from_getitem_no_getitem() -> None:
    """Test _extract_book_from_getitem returns None when no __getitem__ (covers lines 141-142)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_book_from_getitem(object())

    assert result is None


def test_extract_book_from_getitem_exception() -> None:
    """Test _extract_book_from_getitem handles exceptions (covers lines 143-147)."""
    repo = CalibreBookRepository("/path/to/library")

    mock_result = MagicMock()
    mock_result.__getitem__ = MagicMock(side_effect=KeyError("not found"))

    result = repo._extract_book_from_getitem(mock_result)

    assert result is None


def test_unwrap_book_from_result_book_instance() -> None:
    """Test _unwrap_book_from_result with Book instance (covers lines 104-115)."""
    repo = CalibreBookRepository("/path/to/library")

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    result = repo._unwrap_book_from_result(book)

    assert result is book


def test_unwrap_book_from_result_tuple() -> None:
    """Test _unwrap_book_from_result with tuple (covers lines 104-115)."""
    repo = CalibreBookRepository("/path/to/library")

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    result = repo._unwrap_book_from_result((book, "other"))

    assert result is book


def test_unwrap_book_from_result_attr() -> None:
    """Test _unwrap_book_from_result with object having Book attr (covers lines 104-115)."""
    repo = CalibreBookRepository("/path/to/library")

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    mock_result = MagicMock()
    mock_result.Book = book

    result = repo._unwrap_book_from_result(mock_result)

    assert result is book


def test_unwrap_book_from_result_getitem() -> None:
    """Test _unwrap_book_from_result with dict-like (covers lines 104-115)."""
    repo = CalibreBookRepository("/path/to/library")

    book = Book(id=1, title="Test Book", uuid="test-uuid")
    mock_result = MagicMock()
    mock_result.__getitem__ = MagicMock(return_value=book)

    result = repo._unwrap_book_from_result(mock_result)

    assert result is book


def test_unwrap_book_from_result_none() -> None:
    """Test _unwrap_book_from_result returns None when all strategies fail (covers lines 111-115)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._unwrap_book_from_result("unrecognized format")

    assert result is None


def test_extract_series_name_from_indexable_container() -> None:
    """Test _extract_series_name_from_indexable_container extracts from tuple (covers lines 178-184)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_series_name_from_indexable_container(("book", "Series Name"))

    assert result == "Series Name"


def test_extract_series_name_from_indexable_container_none() -> None:
    """Test _extract_series_name_from_indexable_container handles None (covers lines 178-184)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_series_name_from_indexable_container(("book", None))

    assert result is None


def test_extract_series_name_from_indexable_container_exception() -> None:
    """Test _extract_series_name_from_indexable_container handles exceptions (covers lines 178-184)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_series_name_from_indexable_container(object())

    assert result is None


def test_extract_series_name_from_attr() -> None:
    """Test _extract_series_name_from_attr extracts from object with attribute (covers lines 188-194)."""
    repo = CalibreBookRepository("/path/to/library")

    mock_result = MagicMock()
    mock_result.series_name = "Test Series"

    result = repo._extract_series_name_from_attr(mock_result)

    assert result == "Test Series"


def test_extract_series_name_from_attr_none() -> None:
    """Test _extract_series_name_from_attr handles None (covers lines 188-194)."""
    repo = CalibreBookRepository("/path/to/library")

    mock_result = MagicMock()
    mock_result.series_name = None

    result = repo._extract_series_name_from_attr(mock_result)

    assert result is None


def test_extract_series_name_from_attr_exception() -> None:
    """Test _extract_series_name_from_attr handles AttributeError (covers lines 188-194)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_series_name_from_attr(object())

    assert result is None


def test_extract_series_name_from_getitem() -> None:
    """Test _extract_series_name_from_getitem extracts from dict-like (covers lines 198-206)."""
    repo = CalibreBookRepository("/path/to/library")

    mock_result = MagicMock()
    mock_result.__getitem__ = MagicMock(return_value="Test Series")

    result = repo._extract_series_name_from_getitem(mock_result)

    assert result == "Test Series"


def test_extract_series_name_from_getitem_no_getitem() -> None:
    """Test _extract_series_name_from_getitem returns None when no __getitem__ (covers lines 198-199)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._extract_series_name_from_getitem(object())

    assert result is None


def test_extract_series_name_from_getitem_none() -> None:
    """Test _extract_series_name_from_getitem handles None (covers lines 200-205)."""
    repo = CalibreBookRepository("/path/to/library")

    mock_result = MagicMock()
    mock_result.__getitem__ = MagicMock(return_value=None)

    result = repo._extract_series_name_from_getitem(mock_result)

    assert result is None


def test_unwrap_series_name_from_result_tuple() -> None:
    """Test _unwrap_series_name_from_result with tuple (covers lines 162-172)."""
    repo = CalibreBookRepository("/path/to/library")

    result = repo._unwrap_series_name_from_result(("book", "Series Name"))

    assert result == "Series Name"


def test_unwrap_series_name_from_result_attr() -> None:
    """Test _unwrap_series_name_from_result with object having attribute (covers lines 162-172)."""
    repo = CalibreBookRepository("/path/to/library")

    mock_result = MagicMock()
    mock_result.series_name = "Test Series"

    result = repo._unwrap_series_name_from_result(mock_result)

    assert result == "Test Series"


def test_unwrap_series_name_from_result_getitem() -> None:
    """Test _unwrap_series_name_from_result with dict-like (covers lines 162-172)."""
    repo = CalibreBookRepository("/path/to/library")

    mock_result = MagicMock()
    mock_result.__getitem__ = MagicMock(return_value="Test Series")

    result = repo._unwrap_series_name_from_result(mock_result)

    assert result == "Test Series"


def test_unwrap_series_name_from_result_none() -> None:
    """Test _unwrap_series_name_from_result returns None when all strategies fail (covers lines 168-172)."""
    repo = CalibreBookRepository("/path/to/library")

    # Use an object that doesn't match any strategy (no __getitem__, no attributes)
    result = repo._unwrap_series_name_from_result(42)

    assert result is None


def test_get_engine_creates_engine() -> None:
    """Test _get_engine creates engine when database exists (covers lines 221-227)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        engine = repo._get_engine()

        assert engine is not None
        assert repo._engine is engine


def test_get_engine_file_not_found() -> None:
    """Test _get_engine raises FileNotFoundError when database missing (covers lines 221-223)."""
    repo = CalibreBookRepository("/nonexistent/path")

    with pytest.raises(FileNotFoundError):
        repo._get_engine()


def test_get_engine_reuses_engine() -> None:
    """Test _get_engine reuses existing engine (covers lines 224-227)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        engine1 = repo._get_engine()
        engine2 = repo._get_engine()

        assert engine1 is engine2


def test_get_session_context_manager() -> None:
    """Test _get_session context manager yields session (covers lines 238-243)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with repo._get_session() as session:
            assert session is not None


def test_count_books_no_search() -> None:
    """Test count_books without search query (covers lines 258-272)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value.one.return_value = 10

            result = repo.count_books()

            assert result == 10


def test_count_books_with_search() -> None:
    """Test count_books with search query (covers lines 258-272)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value.one.return_value = 5

            result = repo.count_books(search_query="test")

            assert result == 5


def test_count_books_returns_zero_when_none() -> None:
    """Test count_books returns 0 when result is None (covers lines 258-272)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value.one.return_value = None

            result = repo.count_books()

            assert result == 0


def test_list_books_no_search() -> None:
    """Test list_books without search (covers lines 303-377)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # First call returns books, second call returns authors
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0)

            assert len(result) == 1
            assert result[0].book.id == 1


def test_list_books_with_search() -> None:
    """Test list_books with search query (covers lines 325-335)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # First call returns books, second call returns authors
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0, search_query="test")

            assert len(result) == 1


def test_list_books_skips_result_when_book_unwrap_fails() -> None:
    """Test list_books skips results when _unwrap_book_from_result returns None (covers lines 352-353)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        # Create a mock result that cannot be unwrapped to a Book
        # Use an object that doesn't match any extraction strategy
        mock_result_unwrappable = (
            object()
        )  # This will cause _unwrap_book_from_result to return None

        # Create a valid book result
        valid_book = Book(id=1, title="Valid Book", uuid="valid-uuid")
        mock_result_valid = MagicMock()
        mock_result_valid.Book = valid_book
        mock_result_valid.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # First call returns both results, second call returns authors for valid book
            mock_exec.all.side_effect = [
                [mock_result_unwrappable, mock_result_valid],
                [],  # Authors query for valid book
            ]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0)

            # Should only include the valid book, skipping the unwrappable one
            assert len(result) == 1
            assert result[0].book.id == 1
            assert result[0].book.title == "Valid Book"


def test_list_books_skips_book_without_id() -> None:
    """Test list_books skips books without id (covers lines 358-359)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=None, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # Only one call for books (no authors query since book.id is None)
            mock_exec.all.return_value = [mock_result]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0)

            assert len(result) == 0


def test_list_books_with_series() -> None:
    """Test list_books includes series name (covers lines 355-375)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = "Test Series"

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # First call returns books, second call returns authors
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0)

            assert len(result) == 1
            assert result[0].series == "Test Series"


def test_list_books_with_authors() -> None:
    """Test list_books includes authors (covers lines 361-367)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # First call returns books, second call returns authors
            mock_exec.all.side_effect = [[mock_result], ["Author 1", "Author 2"]]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0)

            assert len(result) == 1
            assert result[0].authors == ["Author 1", "Author 2"]


def test_list_books_invalid_sort_order() -> None:
    """Test list_books defaults to desc for invalid sort_order (covers lines 312-313)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # First call returns books, second call returns authors
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0, sort_order="invalid")

            assert len(result) == 1


def test_list_books_asc_order() -> None:
    """Test list_books with asc sort order (covers lines 340-341)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # First call returns books, second call returns authors
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0, sort_order="asc")

            assert len(result) == 1


def test_list_books_invalid_sort_by() -> None:
    """Test list_books defaults to timestamp for invalid sort_by (covers lines 310-310)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            # First call returns books, second call returns authors
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books(limit=10, offset=0, sort_by="invalid_field")

            assert len(result) == 1


def test_get_book_not_found() -> None:
    """Test get_book returns None when not found (covers lines 402-403)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value.first.return_value = None

            result = repo.get_book(999)

            assert result is None


def test_get_book_book_unwrap_fails() -> None:
    """Test get_book returns None when book unwrap fails (covers lines 405-407)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        mock_result = MagicMock()
        mock_result.Book = None  # Unwrap will fail

        with patch.object(repo, "_get_session") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value.first.return_value = mock_result

            result = repo.get_book(1)

            assert result is None


def test_get_book_success() -> None:
    """Test get_book returns BookWithRelations when found (covers lines 392-424)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = "Test Series"

        with patch.object(repo, "_get_session") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value.first.return_value = mock_result
            mock_session.return_value.__enter__.return_value.exec.return_value.all.return_value = [
                "Author 1"
            ]  # Authors query

            result = repo.get_book(1)

            assert result is not None
            assert result.book.id == 1
            assert result.series == "Test Series"
            assert result.authors == ["Author 1"]


def test_parse_datetime_none() -> None:
    """Test _parse_datetime returns None for None input (covers lines 443-444)."""
    result = CalibreBookRepository._parse_datetime(None)

    assert result is None


def test_parse_datetime_unix_timestamp() -> None:
    """Test _parse_datetime parses Unix timestamp (covers lines 447-448)."""
    timestamp = 1609459200.0  # 2021-01-01 00:00:00 UTC
    result = CalibreBookRepository._parse_datetime(timestamp)

    assert result is not None
    assert result.year == 2021


def test_parse_datetime_iso_string() -> None:
    """Test _parse_datetime parses ISO string (covers lines 450-454)."""
    iso_string = "2021-01-01T00:00:00+00:00"
    result = CalibreBookRepository._parse_datetime(iso_string)

    assert result is not None
    assert result.year == 2021


def test_parse_datetime_iso_string_with_z() -> None:
    """Test _parse_datetime parses ISO string with Z (covers lines 452-454)."""
    iso_string = "2021-01-01T00:00:00Z"
    result = CalibreBookRepository._parse_datetime(iso_string)

    assert result is not None
    assert result.year == 2021


def test_parse_datetime_unix_string() -> None:
    """Test _parse_datetime parses Unix timestamp string (covers lines 456-459)."""
    timestamp_str = "1609459200.0"
    result = CalibreBookRepository._parse_datetime(timestamp_str)

    assert result is not None
    assert result.year == 2021


def test_parse_datetime_invalid_string() -> None:
    """Test _parse_datetime returns None for invalid string (covers lines 455-460)."""
    result = CalibreBookRepository._parse_datetime("invalid date")

    assert result is None


def test_parse_datetime_other_type() -> None:
    """Test _parse_datetime returns None for unsupported type (covers lines 461-462)."""
    result = CalibreBookRepository._parse_datetime([])  # type: ignore[arg-type]

    assert result is None


def test_parse_datetime_os_error() -> None:
    """Test _parse_datetime handles OSError (covers lines 463-464)."""
    # Use a timestamp that would cause OSError (e.g., out of range)
    # This is hard to trigger, but we can test the exception handler
    with patch("fundamental.repositories.calibre_book_repository.datetime") as mock_dt:
        mock_dt.fromtimestamp.side_effect = OSError("Invalid timestamp")
        result = CalibreBookRepository._parse_datetime(999999999999999999)

        assert result is None


# Filter Strategy Tests


def test_filter_strategy_apply_with_none() -> None:
    """Test FilterStrategy.apply returns context unchanged when filter_value is None (covers lines 131-133)."""
    strategy = AuthorFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy.apply(context, None)

    assert result is context
    assert len(result.or_conditions) == 0


def test_filter_strategy_apply_with_empty_list() -> None:
    """Test FilterStrategy.apply returns context unchanged when filter_value is empty (covers lines 131-133)."""
    strategy = AuthorFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy.apply(context, [])

    assert result is context
    assert len(result.or_conditions) == 0


def test_author_filter_strategy_build_filter() -> None:
    """Test AuthorFilterStrategy._build_filter (covers lines 166-171)."""
    strategy = AuthorFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, [1, 2, 3])

    assert len(result.or_conditions) == 1
    assert result.stmt != base_stmt  # Should have joins added


def test_title_filter_strategy_build_filter() -> None:
    """Test TitleFilterStrategy._build_filter (covers lines 183-184)."""
    strategy = TitleFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, [1, 2, 3])

    assert len(result.or_conditions) == 1
    assert result.stmt == base_stmt  # No joins needed


def test_genre_filter_strategy_build_filter() -> None:
    """Test GenreFilterStrategy._build_filter (covers lines 196-201)."""
    strategy = GenreFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, [1, 2, 3])

    assert len(result.or_conditions) == 1
    assert result.stmt != base_stmt  # Should have joins added


def test_publisher_filter_strategy_build_filter() -> None:
    """Test PublisherFilterStrategy._build_filter (covers lines 213-218)."""
    strategy = PublisherFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, [1, 2, 3])

    assert len(result.or_conditions) == 1
    assert result.stmt != base_stmt  # Should have joins added


def test_identifier_filter_strategy_build_filter() -> None:
    """Test IdentifierFilterStrategy._build_filter (covers lines 230-235)."""
    strategy = IdentifierFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, [1, 2, 3])

    assert len(result.or_conditions) == 1
    assert result.stmt != base_stmt  # Should have joins added


def test_series_filter_strategy_build_filter() -> None:
    """Test SeriesFilterStrategy._build_filter (covers lines 249-251)."""
    strategy = SeriesFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, [1, 2, 3])

    assert len(result.or_conditions) == 1


def test_format_filter_strategy_build_filter() -> None:
    """Test FormatFilterStrategy._build_filter (covers lines 263-266)."""
    strategy = FormatFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, ["EPUB", "PDF"])

    assert len(result.and_conditions) == 1
    assert result.stmt != base_stmt  # Should have joins added


def test_rating_filter_strategy_build_filter() -> None:
    """Test RatingFilterStrategy._build_filter (covers lines 278-283)."""
    strategy = RatingFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, [1, 2, 3])

    assert len(result.and_conditions) == 1
    assert result.stmt != base_stmt  # Should have joins added


def test_language_filter_strategy_build_filter() -> None:
    """Test LanguageFilterStrategy._build_filter (covers lines 295-300)."""
    strategy = LanguageFilterStrategy()
    base_stmt = select(Book)
    context = FilterContext(stmt=base_stmt, or_conditions=[], and_conditions=[])

    result = strategy._build_filter(context, [1, 2, 3])

    assert len(result.and_conditions) == 1
    assert result.stmt != base_stmt  # Should have joins added


# FilterBuilder Tests


def test_filter_builder_init() -> None:
    """Test FilterBuilder initialization (covers lines 318-319)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    assert builder._context.stmt == base_stmt
    assert len(builder._context.or_conditions) == 0
    assert len(builder._context.and_conditions) == 0


def test_filter_builder_with_author_ids() -> None:
    """Test FilterBuilder.with_author_ids (covers lines 344-345)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_author_ids([1, 2, 3])

    assert result is builder
    assert len(builder._context.or_conditions) == 1


def test_filter_builder_with_title_ids() -> None:
    """Test FilterBuilder.with_title_ids (covers lines 360-361)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_title_ids([1, 2, 3])

    assert result is builder
    assert len(builder._context.or_conditions) == 1


def test_filter_builder_with_genre_ids() -> None:
    """Test FilterBuilder.with_genre_ids (covers lines 376-377)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_genre_ids([1, 2, 3])

    assert result is builder
    assert len(builder._context.or_conditions) == 1


def test_filter_builder_with_publisher_ids() -> None:
    """Test FilterBuilder.with_publisher_ids (covers lines 392-395)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_publisher_ids([1, 2, 3])

    assert result is builder
    assert len(builder._context.or_conditions) == 1


def test_filter_builder_with_identifier_ids() -> None:
    """Test FilterBuilder.with_identifier_ids (covers lines 410-413)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_identifier_ids([1, 2, 3])

    assert result is builder
    assert len(builder._context.or_conditions) == 1


def test_filter_builder_with_series_ids_with_alias() -> None:
    """Test FilterBuilder.with_series_ids with alias (covers lines 432-437)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)
    mock_alias = MagicMock()
    mock_alias.id.in_ = MagicMock(return_value="condition")

    result = builder.with_series_ids([1, 2, 3], series_alias=mock_alias)

    assert result is builder
    assert len(builder._context.or_conditions) == 1


def test_filter_builder_with_series_ids_without_alias() -> None:
    """Test FilterBuilder.with_series_ids without alias (covers lines 432-437)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_series_ids([1, 2, 3])

    assert result is builder
    assert len(builder._context.or_conditions) == 1


def test_filter_builder_with_formats() -> None:
    """Test FilterBuilder.with_formats (covers lines 452-453)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_formats(["EPUB", "PDF"])

    assert result is builder
    assert len(builder._context.and_conditions) == 1


def test_filter_builder_with_rating_ids() -> None:
    """Test FilterBuilder.with_rating_ids (covers lines 468-469)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_rating_ids([1, 2, 3])

    assert result is builder
    assert len(builder._context.and_conditions) == 1


def test_filter_builder_with_language_ids() -> None:
    """Test FilterBuilder.with_language_ids (covers lines 484-485)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.with_language_ids([1, 2, 3])

    assert result is builder
    assert len(builder._context.and_conditions) == 1


def test_filter_builder_build_no_conditions() -> None:
    """Test FilterBuilder.build with no conditions (covers lines 500-517)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)

    result = builder.build()

    assert result == base_stmt


def test_filter_builder_build_single_or_condition() -> None:
    """Test FilterBuilder.build with single OR condition (covers lines 500-517)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)
    builder._context.or_conditions.append(Book.id.in_([1, 2, 3]))  # type: ignore[attr-defined]

    result = builder.build()

    assert result != base_stmt


def test_filter_builder_build_multiple_or_conditions() -> None:
    """Test FilterBuilder.build with multiple OR conditions (covers lines 500-517)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)
    builder._context.or_conditions.append(Book.id.in_([1, 2]))  # type: ignore[attr-defined]
    builder._context.or_conditions.append(Book.id.in_([3, 4]))  # type: ignore[attr-defined]

    result = builder.build()

    assert result != base_stmt


def test_filter_builder_build_and_conditions() -> None:
    """Test FilterBuilder.build with AND conditions (covers lines 500-517)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)
    builder._context.and_conditions.append(Book.id.in_([1, 2]))  # type: ignore[attr-defined]

    result = builder.build()

    assert result != base_stmt


def test_filter_builder_build_or_and_conditions() -> None:
    """Test FilterBuilder.build with both OR and AND conditions (covers lines 500-517)."""
    base_stmt = select(Book)
    builder = FilterBuilder(base_stmt)
    builder._context.or_conditions.append(Book.id.in_([1, 2]))  # type: ignore[attr-defined]
    builder._context.and_conditions.append(Book.id.in_([3, 4]))  # type: ignore[attr-defined]

    result = builder.build()

    assert result != base_stmt


# FilterSuggestionStrategy Tests


def test_author_suggestion_strategy() -> None:
    """Test AuthorSuggestionStrategy.get_suggestions (covers lines 552-560)."""
    strategy = AuthorSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [(1, "Author 1"), (2, "Author 2")]

    result = strategy.get_suggestions(mock_session, "author", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Author 1"}
    assert result[1] == {"id": 2, "name": "Author 2"}


def test_title_suggestion_strategy() -> None:
    """Test TitleSuggestionStrategy.get_suggestions (covers lines 572-580)."""
    strategy = TitleSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [(1, "Book 1"), (2, "Book 2")]

    result = strategy.get_suggestions(mock_session, "book", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Book 1"}


def test_genre_suggestion_strategy() -> None:
    """Test GenreSuggestionStrategy.get_suggestions (covers lines 590-598)."""
    strategy = GenreSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [(1, "Tag 1"), (2, "Tag 2")]

    result = strategy.get_suggestions(mock_session, "tag", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Tag 1"}


def test_publisher_suggestion_strategy() -> None:
    """Test PublisherSuggestionStrategy.get_suggestions (covers lines 608-616)."""
    strategy = PublisherSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [
        (1, "Publisher 1"),
        (2, "Publisher 2"),
    ]

    result = strategy.get_suggestions(mock_session, "pub", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Publisher 1"}


def test_identifier_suggestion_strategy() -> None:
    """Test IdentifierSuggestionStrategy.get_suggestions (covers lines 629-637)."""
    strategy = IdentifierSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [
        (1, "123456", "ISBN"),
        (2, "789012", "ASIN"),
    ]

    result = strategy.get_suggestions(mock_session, "123", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "ISBN: 123456"}
    assert result[1] == {"id": 2, "name": "ASIN: 789012"}


def test_series_suggestion_strategy() -> None:
    """Test SeriesSuggestionStrategy.get_suggestions (covers lines 653-661)."""
    strategy = SeriesSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [(1, "Series 1"), (2, "Series 2")]

    result = strategy.get_suggestions(mock_session, "series", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Series 1"}


def test_format_suggestion_strategy() -> None:
    """Test FormatSuggestionStrategy.get_suggestions (covers lines 673-682)."""
    strategy = FormatSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = ["EPUB", "PDF"]

    result = strategy.get_suggestions(mock_session, "epub", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "EPUB"}
    assert result[1] == {"id": 2, "name": "PDF"}


def test_rating_suggestion_strategy_numeric() -> None:
    """Test RatingSuggestionStrategy.get_suggestions with numeric query (covers lines 695-709)."""
    strategy = RatingSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [(1, 5), (2, 4)]

    result = strategy.get_suggestions(mock_session, "5", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "5"}


def test_rating_suggestion_strategy_non_numeric() -> None:
    """Test RatingSuggestionStrategy.get_suggestions with non-numeric query (covers lines 695-709)."""
    strategy = RatingSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [(1, 5), (2, 4), (3, None)]

    result = strategy.get_suggestions(mock_session, "all", 10)

    assert len(result) == 2  # None filtered out
    assert result[0] == {"id": 1, "name": "5"}


def test_language_suggestion_strategy() -> None:
    """Test LanguageSuggestionStrategy.get_suggestions (covers lines 723-731)."""
    strategy = LanguageSuggestionStrategy()
    mock_session = MagicMock()
    mock_session.exec.return_value.all.return_value = [(1, "en"), (2, "fr")]

    result = strategy.get_suggestions(mock_session, "en", 10)

    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "en"}


def test_filter_suggestion_factory_get_strategy() -> None:
    """Test FilterSuggestionFactory.get_strategy (covers line 769)."""
    strategy = FilterSuggestionFactory.get_strategy("author")
    assert isinstance(strategy, AuthorSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("title")
    assert isinstance(strategy, TitleSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("genre")
    assert isinstance(strategy, GenreSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("publisher")
    assert isinstance(strategy, PublisherSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("identifier")
    assert isinstance(strategy, IdentifierSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("series")
    assert isinstance(strategy, SeriesSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("format")
    assert isinstance(strategy, FormatSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("rating")
    assert isinstance(strategy, RatingSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("language")
    assert isinstance(strategy, LanguageSuggestionStrategy)

    strategy = FilterSuggestionFactory.get_strategy("invalid")
    assert strategy is None


# Repository Method Tests


def test_build_book_with_relations() -> None:
    """Test _build_book_with_relations (covers lines 1124-1138)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = "Test Series"

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.all.return_value = ["Author 1", "Author 2"]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo._build_book_with_relations(mock_session_obj, mock_result)

            assert result is not None
            assert result.book.id == 1
            assert result.series == "Test Series"
            assert result.authors == ["Author 1", "Author 2"]


def test_build_book_with_relations_none_book() -> None:
    """Test _build_book_with_relations returns None when book is None (covers lines 1124-1138)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_result = MagicMock()
        mock_result.Book = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo._build_book_with_relations(mock_session_obj, mock_result)

            assert result is None


def test_build_book_with_relations_no_id() -> None:
    """Test _build_book_with_relations returns None when book.id is None (covers lines 1124-1138)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        book = Book(id=None, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo._build_book_with_relations(mock_session_obj, mock_result)

            assert result is None


def test_get_sort_field() -> None:
    """Test _get_sort_field (covers lines 1157-1164)."""
    repo = CalibreBookRepository("/path/to/library")

    assert repo._get_sort_field("timestamp") == Book.timestamp
    assert repo._get_sort_field("pubdate") == Book.pubdate
    assert repo._get_sort_field("title") == Book.title
    assert repo._get_sort_field("author_sort") == Book.author_sort
    assert repo._get_sort_field("series_index") == Book.series_index
    assert repo._get_sort_field("invalid") == Book.timestamp  # Default


def test_list_books_with_filters() -> None:
    """Test list_books_with_filters (covers lines 1221-1261)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books_with_filters(
                limit=10,
                offset=0,
                author_ids=[1, 2],
                title_ids=[3, 4],
                sort_by="timestamp",
                sort_order="desc",
            )

            assert len(result) == 1
            assert result[0].book.id == 1


def test_list_books_with_filters_asc() -> None:
    """Test list_books_with_filters with asc order (covers lines 1221-1261)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books_with_filters(limit=10, offset=0, sort_order="asc")

            assert len(result) == 1


def test_list_books_with_filters_invalid_sort_order() -> None:
    """Test list_books_with_filters with invalid sort_order (covers lines 1221-1261)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.all.side_effect = [[mock_result], []]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.list_books_with_filters(
                limit=10, offset=0, sort_order="invalid"
            )

            assert len(result) == 1


def test_count_books_with_filters() -> None:
    """Test count_books_with_filters (covers lines 1303-1326)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value.one.return_value = 5

            result = repo.count_books_with_filters(
                author_ids=[1, 2], title_ids=[3, 4], genre_ids=[5, 6]
            )

            assert result == 5


def test_count_books_with_filters_zero() -> None:
    """Test count_books_with_filters returns 0 when result is None (covers lines 1303-1326)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value.one.return_value = None

            result = repo.count_books_with_filters()

            assert result == 0


def test_filter_suggestions() -> None:
    """Test filter_suggestions (covers lines 1491-1499)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.all.return_value = [(1, "Author 1")]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.filter_suggestions("author", "author", 10)

            assert len(result) == 1
            assert result[0] == {"id": 1, "name": "Author 1"}


def test_filter_suggestions_empty_query() -> None:
    """Test filter_suggestions with empty query (covers lines 1491-1499)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        result = repo.filter_suggestions("", "author", 10)

        assert result == []


def test_filter_suggestions_invalid_type() -> None:
    """Test filter_suggestions with invalid filter_type (covers lines 1491-1499)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        result = repo.filter_suggestions("query", "invalid", 10)

        assert result == []


def test_search_suggestions() -> None:
    """Test search_suggestions (covers lines 1404-1466)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.all.side_effect = [
                [(1, "Book 1")],  # books
                [(1, "Author 1")],  # authors
                [(1, "Tag 1")],  # tags
                [(1, "Series 1")],  # series
            ]
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.search_suggestions(
                "test", book_limit=3, author_limit=3, tag_limit=3, series_limit=3
            )

            assert "books" in result
            assert "authors" in result
            assert "tags" in result
            assert "series" in result
            assert len(result["books"]) == 1


def test_search_suggestions_empty_query() -> None:
    """Test search_suggestions with empty query (covers lines 1404-1466)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        result = repo.search_suggestions("")

        assert result == {"books": [], "authors": [], "tags": [], "series": []}


def test_search_suggestions_whitespace_query() -> None:
    """Test search_suggestions with whitespace-only query (covers lines 1404-1466)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        result = repo.search_suggestions("   ")

        assert result == {"books": [], "authors": [], "tags": [], "series": []}


def test_get_book_full_success() -> None:
    """Test get_book_full returns BookWithFullRelations when found (covers lines 683-785)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = "Test Series"
        mock_result.series_id = 1

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            # First query for book with series
            mock_exec1 = MagicMock()
            mock_exec1.first.return_value = mock_result
            # Authors query
            mock_exec2 = MagicMock()
            mock_exec2.all.return_value = ["Author 1", "Author 2"]
            # Tags query
            mock_exec3 = MagicMock()
            mock_exec3.all.return_value = ["Tag 1", "Tag 2"]
            # Identifiers query
            mock_exec4 = MagicMock()
            mock_exec4.all.return_value = [
                ("isbn", "1234567890"),
                ("doi", "10.1234/test"),
            ]
            # Comment query
            mock_exec5 = MagicMock()
            mock_exec5.first.return_value = "Test description"
            # Publisher query
            mock_exec6 = MagicMock()
            mock_exec6.first.return_value = ("Test Publisher", 1)
            # Language query
            mock_exec7 = MagicMock()
            mock_exec7.first.return_value = ("en", 1)
            # Rating query
            mock_exec8 = MagicMock()
            mock_exec8.first.return_value = (5, 1)

            mock_session_obj.exec.side_effect = [
                mock_exec1,  # Book query
                mock_exec2,  # Authors
                mock_exec3,  # Tags
                mock_exec4,  # Identifiers
                mock_exec5,  # Comment
                mock_exec6,  # Publisher
                mock_exec7,  # Language
                mock_exec8,  # Rating
            ]
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.get_book_full(1)

            assert result is not None
            assert result.book.id == 1
            assert result.series == "Test Series"
            assert result.series_id == 1
            assert result.authors == ["Author 1", "Author 2"]
            assert result.tags == ["Tag 1", "Tag 2"]
            assert result.identifiers == [
                {"type": "isbn", "val": "1234567890"},
                {"type": "doi", "val": "10.1234/test"},
            ]
            assert result.description == "Test description"
            assert result.publisher == "Test Publisher"
            assert result.publisher_id == 1
            assert result.language == "en"
            assert result.language_id == 1
            assert result.rating == 5
            assert result.rating_id == 1


def test_get_book_full_not_found() -> None:
    """Test get_book_full returns None when book not found (covers lines 694-695)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.first.return_value = None
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.get_book_full(999)

            assert result is None


def test_get_book_full_unwrap_returns_none() -> None:
    """Test get_book_full returns None when unwrap returns None (covers line 703)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        # Mock result that will cause _unwrap_book_from_result to return None
        # The unwrap method tries multiple strategies to extract Book, all will fail
        # Use a plain object that's not a Book and doesn't have Book attribute
        class NonBookResult:
            """Result that doesn't contain a Book."""

        mock_result = NonBookResult()

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.first.return_value = mock_result
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.get_book_full(1)

            assert result is None


def test_get_book_full_no_comment() -> None:
    """Test get_book_full handles missing comment (covers lines 740-742)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        mock_result = MagicMock()
        mock_result.Book = book
        mock_result.series_name = None
        mock_result.series_id = None

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec1 = MagicMock()
            mock_exec1.first.return_value = mock_result
            mock_exec2 = MagicMock()
            mock_exec2.all.return_value = []
            mock_exec3 = MagicMock()
            mock_exec3.all.return_value = []
            mock_exec4 = MagicMock()
            mock_exec4.all.return_value = []
            mock_exec5 = MagicMock()
            mock_exec5.first.return_value = None  # No comment
            mock_exec6 = MagicMock()
            mock_exec6.first.return_value = None  # No publisher
            mock_exec7 = MagicMock()
            mock_exec7.first.return_value = None  # No language
            mock_exec8 = MagicMock()
            mock_exec8.first.return_value = None  # No rating

            mock_session_obj.exec.side_effect = [
                mock_exec1,
                mock_exec2,
                mock_exec3,
                mock_exec4,
                mock_exec5,
                mock_exec6,
                mock_exec7,
                mock_exec8,
            ]
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.get_book_full(1)

            assert result is not None
            assert result.description is None
            assert result.publisher is None
            assert result.language is None
            assert result.rating is None


def test_get_book_full_series_id_from_index() -> None:
    """Test get_book_full extracts series_id from indexable result (covers lines 707-712)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Test Book", uuid="test-uuid")
        # Use tuple result to test index-based extraction
        mock_result = (book, "Test Series", 5)  # (book, series_name, series_id)

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec1 = MagicMock()
            mock_exec1.first.return_value = mock_result
            mock_exec2 = MagicMock()
            mock_exec2.all.return_value = []
            mock_exec3 = MagicMock()
            mock_exec3.all.return_value = []
            mock_exec4 = MagicMock()
            mock_exec4.all.return_value = []
            mock_exec5 = MagicMock()
            mock_exec5.first.return_value = None
            mock_exec6 = MagicMock()
            mock_exec6.first.return_value = None
            mock_exec7 = MagicMock()
            mock_exec7.first.return_value = None
            mock_exec8 = MagicMock()
            mock_exec8.first.return_value = None

            mock_session_obj.exec.side_effect = [
                mock_exec1,
                mock_exec2,
                mock_exec3,
                mock_exec4,
                mock_exec5,
                mock_exec6,
                mock_exec7,
                mock_exec8,
            ]
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.get_book_full(1)

            assert result is not None
            assert result.series == "Test Series"
            assert result.series_id == 5


def test_update_book_fields() -> None:
    """Test _update_book_fields updates book fields (covers lines 821-827)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        book = Book(id=1, title="Original", uuid="test-uuid")

        repo._update_book_fields(
            book,
            title="New Title",
            pubdate=datetime(2024, 1, 1, tzinfo=UTC),
            series_index=2.5,
        )

        assert book.title == "New Title"
        assert book.pubdate == datetime(2024, 1, 1, tzinfo=UTC)
        assert book.series_index == 2.5
        assert book.last_modified is not None


def test_update_book_authors() -> None:
    """Test _update_book_authors updates authors (covers lines 844-870)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing author names query (selects Author.name, returns strings)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = ["Author 1"]

        # Mock existing links query (selects BookAuthorLink, returns objects)
        existing_link = BookAuthorLink(book=1, author=1)
        mock_exec2 = MagicMock()
        mock_exec2.all.return_value = [existing_link]

        # Mock author lookup - first author exists, second doesn't
        author1 = Author(id=1, name="Author 1")
        mock_exec3 = MagicMock()
        mock_exec3.first.side_effect = [author1, None]  # First exists, second doesn't

        # Mock link check
        mock_exec4 = MagicMock()
        mock_exec4.first.side_effect = [None, None]  # Links don't exist

        mock_session.exec.side_effect = [
            mock_exec1,  # Get current author names (strings)
            mock_exec2,  # Get existing links to delete (BookAuthorLink objects)
            mock_exec3,  # Author lookup (first)
            mock_exec4,  # Link check (first)
            mock_exec3,  # Author lookup (second)
            mock_exec4,  # Link check (second)
        ]
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)
        mock_session.flush = MagicMock()

        repo._update_book_authors(mock_session, 1, ["Author 1", "Author 2"])

        # Verify existing link was deleted
        assert existing_link in mock_session.deleted
        # Verify new authors were added
        assert len([a for a in mock_session.added if isinstance(a, Author)]) >= 1
        assert (
            len([a for a in mock_session.added if isinstance(a, BookAuthorLink)]) >= 1
        )


def test_update_book_authors_skips_empty() -> None:
    """Test _update_book_authors skips empty author names (covers line 856)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()

        mock_exec = MagicMock()
        mock_exec.all.return_value = []
        mock_session.exec.return_value = mock_exec

        repo._update_book_authors(mock_session, 1, ["Author 1", "", "   ", "Author 2"])

        # Should only process non-empty names
        # Verify exec was called (for deleting links and finding/creating authors)
        assert mock_session.exec.call_count >= 2


def test_update_book_series_with_name() -> None:
    """Test _update_book_series creates series from name (covers lines 913-927)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing link deletion
        existing_link = BookSeriesLink(book=1, series=1)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]

        # Mock series lookup - doesn't exist, will be created
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = None

        mock_session.exec.side_effect = [mock_exec1, mock_exec2]

        def flush_mock() -> None:
            # Simulate flush setting IDs on added entities
            for entity in mock_session.added:
                if isinstance(entity, Series) and entity.id is None:
                    entity.id = 2

        def add_entity(entity: object) -> None:
            mock_session.added.append(entity)

        mock_session.flush = flush_mock
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = add_entity

        repo._update_book_series(mock_session, 1, series_name="New Series")

        # Verify series was created and link was added
        added_series = [s for s in mock_session.added if isinstance(s, Series)]
        added_links = [s for s in mock_session.added if isinstance(s, BookSeriesLink)]
        assert len(added_series) == 1
        assert added_series[0].name == "New Series"
        assert len(added_links) == 1


def test_update_book_series_remove() -> None:
    """Test _update_book_series removes series when empty (covers lines 906-911)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookSeriesLink(book=1, series=1)
        mock_exec = MagicMock()
        mock_exec.first.return_value = existing_link
        mock_session.exec.return_value = mock_exec
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_series(mock_session, 1, series_name="")

        # Verify link was deleted
        assert existing_link in mock_session.deleted
        # Should not add new series
        added_series = [s for s in mock_session.added if isinstance(s, Series)]
        assert len(added_series) == 0


def test_update_book_tags() -> None:
    """Test _update_book_tags updates tags (covers lines 939-957)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing tag names query (selects Tag.name, returns strings)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = ["Tag 1"]

        # Mock existing links query (selects BookTagLink, returns objects)
        existing_link = BookTagLink(book=1, tag=1)
        mock_exec2 = MagicMock()
        mock_exec2.all.return_value = [existing_link]

        # Mock tag lookup - first exists, second doesn't
        tag1 = Tag(id=1, name="Tag 1")
        mock_exec3 = MagicMock()
        # First call: lookup Tag 1 (exists), Second call: lookup Tag 2 (doesn't exist)
        mock_exec3.first.side_effect = [tag1, None]

        mock_session.exec.side_effect = [mock_exec1, mock_exec2, mock_exec3, mock_exec3]

        tag_id_counter = [2]  # Start from 2 for new tags

        def flush_mock() -> None:
            # Simulate flush setting IDs on added tags
            for entity in mock_session.added:
                if isinstance(entity, Tag) and entity.id is None:
                    entity.id = tag_id_counter[0]
                    tag_id_counter[0] += 1

        def add_entity(entity: object) -> None:
            mock_session.added.append(entity)

        mock_session.flush = flush_mock
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = add_entity

        repo._update_book_tags(mock_session, 1, ["Tag 1", "Tag 2"])

        # Verify tags were processed
        added_tags = [t for t in mock_session.added if isinstance(t, Tag)]
        added_links = [t for t in mock_session.added if isinstance(t, BookTagLink)]
        assert len(added_tags) >= 1  # At least Tag 2 should be created
        assert len(added_links) >= 2  # Links for both tags


def test_update_book_tags_skips_whitespace() -> None:
    """Test _update_book_tags skips whitespace-only tag names (covers line 947)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing tag names query (selects Tag.name, returns strings)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = []

        # Mock existing links deletion (1 call)
        mock_exec2 = MagicMock()
        mock_exec2.all.return_value = []

        # Mock tag lookups - only for non-whitespace tags (2 calls: Tag 1 and Tag 2)
        mock_exec3 = MagicMock()
        mock_exec3.first.return_value = None  # Tags don't exist

        mock_session.exec.side_effect = [mock_exec1, mock_exec2, mock_exec3, mock_exec3]
        mock_session.flush = MagicMock()
        mock_session.delete = MagicMock()
        mock_session.add = MagicMock()

        repo._update_book_tags(mock_session, 1, ["Tag 1", "", "   ", "\t", "Tag 2"])

        # Should only process non-whitespace tags
        # 1 call for getting current tag names + 1 call for deleting existing links + 2 calls for tag lookups (Tag 1 and Tag 2)
        # Empty/whitespace tags should be skipped
        assert mock_session.exec.call_count == 4


def test_update_book_tags_skips_none_id() -> None:
    """Test _update_book_tags skips tags with None id after flush (covers line 955)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing tag names query (selects Tag.name, returns strings)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = []

        # Mock existing links query (selects BookTagLink, returns objects)
        mock_exec2 = MagicMock()
        mock_exec2.all.return_value = []

        # Mock tag lookup - tag doesn't exist, will be created
        mock_exec3 = MagicMock()
        mock_exec3.first.return_value = None

        mock_session.exec.side_effect = [mock_exec1, mock_exec2, mock_exec3]

        def flush_mock() -> None:
            # Simulate flush NOT setting ID (failure case)
            # Don't set IDs, leaving them as None
            pass

        def add_entity(entity: object) -> None:
            mock_session.added.append(entity)
            # Ensure tag.id remains None after flush
            if isinstance(entity, Tag):
                entity.id = None

        mock_session.flush = flush_mock
        mock_session.delete = MagicMock()
        mock_session.add = add_entity

        repo._update_book_tags(mock_session, 1, ["Tag 1"])

        # Verify tag was created but link was NOT created (because tag.id is None)
        added_tags = [t for t in mock_session.added if isinstance(t, Tag)]
        added_links = [t for t in mock_session.added if isinstance(t, BookTagLink)]
        assert len(added_tags) == 1  # Tag was created
        assert len(added_links) == 0  # But link was NOT created because tag.id is None


def test_update_book_identifiers() -> None:
    """Test _update_book_identifiers updates identifiers (covers lines 974-985)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing identifiers
        existing_ident = Identifier(book=1, type="isbn", val="old")
        mock_exec = MagicMock()
        mock_exec.all.return_value = [existing_ident]
        mock_session.exec.return_value = mock_exec
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_identifiers(
            mock_session,
            1,
            [
                {"type": "isbn", "val": "1234567890"},
                {"type": "doi", "val": "10.1234/test"},
            ],
        )

        # Verify old identifier was deleted
        assert existing_ident in mock_session.deleted
        # Verify new identifiers were added
        added_idents = [i for i in mock_session.added if isinstance(i, Identifier)]
        assert len(added_idents) == 2
        assert any(i.type == "isbn" and i.val == "1234567890" for i in added_idents)
        assert any(i.type == "doi" and i.val == "10.1234/test" for i in added_idents)


def test_update_book_identifiers_skips_empty() -> None:
    """Test _update_book_identifiers skips empty values (covers line 988)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []

        mock_exec = MagicMock()
        mock_exec.all.return_value = []
        mock_session.exec.return_value = mock_exec
        mock_session.delete = lambda x: None
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_identifiers(
            mock_session,
            1,
            [{"type": "isbn", "val": "1234567890"}, {"type": "doi", "val": ""}],
        )

        # Should only add identifier with non-empty value
        added_idents = [i for i in mock_session.added if isinstance(i, Identifier)]
        assert len(added_idents) == 1
        assert added_idents[0].val == "1234567890"


def test_update_book_description_new() -> None:
    """Test _update_book_description creates new comment (covers lines 1008-1010)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []

        mock_exec = MagicMock()
        mock_exec.first.return_value = None  # No existing comment
        mock_session.exec.return_value = mock_exec
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_description(mock_session, 1, "New description")

        # Verify comment was created
        added_comments = [c for c in mock_session.added if isinstance(c, Comment)]
        assert len(added_comments) == 1
        assert added_comments[0].text == "New description"
        assert added_comments[0].book == 1


def test_update_book_description_existing() -> None:
    """Test _update_book_description updates existing comment (covers lines 1011-1012)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []

        existing_comment = Comment(book=1, text="Old description")
        mock_exec = MagicMock()
        mock_exec.first.return_value = existing_comment
        mock_session.exec.return_value = mock_exec
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_description(mock_session, 1, "Updated description")

        # Verify comment text was updated
        assert existing_comment.text == "Updated description"
        # Should not add new comment
        added_comments = [c for c in mock_session.added if isinstance(c, Comment)]
        assert len(added_comments) == 0


def test_update_book_publisher_with_name() -> None:
    """Test _update_book_publisher creates publisher from name (covers lines 1042-1056)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing link deletion
        existing_link = BookPublisherLink(book=1, publisher=1)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]

        # Mock publisher lookup - doesn't exist
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = None

        mock_session.exec.side_effect = [mock_exec1, mock_exec2]

        def flush_mock() -> None:
            # Simulate flush setting IDs on added entities
            for entity in mock_session.added:
                if isinstance(entity, Publisher) and entity.id is None:
                    entity.id = 2

        def add_entity(entity: object) -> None:
            mock_session.added.append(entity)

        mock_session.flush = flush_mock
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = add_entity

        repo._update_book_publisher(mock_session, 1, publisher_name="New Publisher")

        # Verify publisher was created and link was added
        added_publishers = [p for p in mock_session.added if isinstance(p, Publisher)]
        added_links = [
            p for p in mock_session.added if isinstance(p, BookPublisherLink)
        ]
        assert len(added_publishers) == 1
        assert added_publishers[0].name == "New Publisher"
        assert len(added_links) == 1


def test_update_book_language_with_code() -> None:
    """Test _update_book_language creates language from code (covers lines 1086-1102)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing link deletion
        existing_link = BookLanguageLink(book=1, lang_code=1)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]

        # Mock language lookup - doesn't exist
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = None

        # Mock defensive check query (after flush, check if link exists)
        mock_exec3 = MagicMock()
        mock_exec3.first.return_value = None  # Link doesn't exist, so it will be added

        mock_session.exec.side_effect = [mock_exec1, mock_exec2, mock_exec3]

        def flush_mock() -> None:
            # Simulate flush setting IDs on added entities
            for entity in mock_session.added:
                if isinstance(entity, Language) and entity.id is None:
                    entity.id = 2

        def add_entity(entity: object) -> None:
            mock_session.added.append(entity)

        mock_session.flush = flush_mock
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = add_entity

        repo._update_book_language(mock_session, 1, language_code="fr")

        # Verify language was created and link was added
        added_languages = [
            lang for lang in mock_session.added if isinstance(lang, Language)
        ]
        added_links = [
            link for link in mock_session.added if isinstance(link, BookLanguageLink)
        ]
        assert len(added_languages) == 1
        assert added_languages[0].lang_code == "fr"
        assert len(added_links) == 1


def test_update_book_rating_with_value() -> None:
    """Test _update_book_rating creates rating from value (covers lines 1132-1146)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing link deletion
        existing_link = BookRatingLink(book=1, rating=1)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]

        # Mock rating lookup - doesn't exist
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = None

        mock_session.exec.side_effect = [mock_exec1, mock_exec2]

        def flush_mock() -> None:
            # Simulate flush setting IDs on added entities
            for entity in mock_session.added:
                if isinstance(entity, Rating) and entity.id is None:
                    entity.id = 2

        def add_entity(entity: object) -> None:
            mock_session.added.append(entity)

        mock_session.flush = flush_mock
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = add_entity

        repo._update_book_rating(mock_session, 1, rating_value=5)

        # Verify rating was created and link was added
        added_ratings = [r for r in mock_session.added if isinstance(r, Rating)]
        added_links = [r for r in mock_session.added if isinstance(r, BookRatingLink)]
        assert len(added_ratings) == 1
        assert added_ratings[0].rating == 5
        assert len(added_links) == 1


def test_update_book_orchestration() -> None:
    """Test update_book orchestrates all update methods (covers lines 1202-1252)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Original", uuid="test-uuid")
        updated_book = BookWithFullRelations(
            book=Book(id=1, title="Updated", uuid="test-uuid"),
            authors=[],
            series=None,
            series_id=None,
            tags=[],
            identifiers=[],
            description=None,
            publisher=None,
            publisher_id=None,
            language=None,
            language_id=None,
            rating=None,
            rating_id=None,
        )

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            # Book lookup
            mock_exec1 = MagicMock()
            mock_exec1.first.return_value = book
            # _update_book_authors calls:
            # - Get current author names (strings)
            mock_exec2 = MagicMock()
            mock_exec2.all.return_value = []
            # - Delete existing links
            mock_exec3 = MagicMock()
            mock_exec3.all.return_value = []
            # - Lookup author
            mock_exec4 = MagicMock()
            mock_exec4.first.return_value = None  # Author doesn't exist
            # - Check link doesn't exist
            mock_exec5 = MagicMock()
            mock_exec5.first.return_value = None
            # _update_book_tags calls:
            # - Get current tag names (strings)
            mock_exec6 = MagicMock()
            mock_exec6.all.return_value = []
            # - Delete existing links
            mock_exec7 = MagicMock()
            mock_exec7.all.return_value = []
            # - Lookup tag
            mock_exec8 = MagicMock()
            mock_exec8.first.return_value = None  # Tag doesn't exist

            mock_session_obj.exec.side_effect = [
                mock_exec1,  # Book lookup
                mock_exec2,  # Authors: get current names
                mock_exec3,  # Authors: delete links
                mock_exec4,  # Authors: lookup author
                mock_exec5,  # Authors: check link
                mock_exec6,  # Tags: get current names
                mock_exec7,  # Tags: delete links
                mock_exec8,  # Tags: lookup tag
            ]
            mock_session_obj.flush = MagicMock()
            mock_session_obj.commit = MagicMock()
            mock_session_obj.refresh = MagicMock()
            mock_session_obj.delete = MagicMock()
            mock_session_obj.add = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_obj

            with patch.object(repo, "get_book_full", return_value=updated_book):
                result = repo.update_book(
                    book_id=1,
                    title="Updated",
                    author_names=["Author 1"],
                    tag_names=["Tag 1"],
                )

                assert result is not None
                assert result.book.title == "Updated"
                mock_session_obj.commit.assert_called_once()
                mock_session_obj.refresh.assert_called_once_with(book)


def test_update_book_not_found() -> None:
    """Test update_book returns None when book not found (covers lines 1209-1214)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.first.return_value = None  # Book not found
            mock_session_obj.exec.return_value = mock_exec
            mock_session.return_value.__enter__.return_value = mock_session_obj

            result = repo.update_book(book_id=999, title="New Title")

            assert result is None


def test_update_book_series_with_id() -> None:
    """Test _update_book_series uses series_id when provided (covers lines 913-927)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookSeriesLink(book=1, series=1)
        mock_exec = MagicMock()
        mock_exec.all.return_value = [existing_link]
        mock_session.exec.return_value = mock_exec
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_series(mock_session, 1, series_id=5)

        # Should use provided series_id, not lookup by name
        added_links = [s for s in mock_session.added if isinstance(s, BookSeriesLink)]
        assert len(added_links) == 1
        assert added_links[0].series == 5


def test_update_book_series_with_existing_series() -> None:
    """Test _update_book_series uses existing series when found (covers lines 916-923)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookSeriesLink(book=1, series=1)
        existing_series = Series(id=2, name="Existing Series")
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = existing_series

        mock_session.exec.side_effect = [mock_exec1, mock_exec2]
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_series(mock_session, 1, series_name="Existing Series")

        # Should use existing series, not create new one
        added_series = [s for s in mock_session.added if isinstance(s, Series)]
        added_links = [s for s in mock_session.added if isinstance(s, BookSeriesLink)]
        assert len(added_series) == 0  # Should not create new series
        assert len(added_links) == 1
        assert added_links[0].series == 2


def test_update_book_publisher_with_id() -> None:
    """Test _update_book_publisher uses publisher_id when provided (covers lines 1042-1056)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookPublisherLink(book=1, publisher=1)
        mock_exec = MagicMock()
        mock_exec.all.return_value = [existing_link]
        mock_session.exec.return_value = mock_exec
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_publisher(mock_session, 1, publisher_id=5)

        # Should use provided publisher_id
        added_links = [
            p for p in mock_session.added if isinstance(p, BookPublisherLink)
        ]
        assert len(added_links) == 1
        assert added_links[0].publisher == 5


def test_update_book_publisher_with_existing() -> None:
    """Test _update_book_publisher uses existing publisher when found (covers lines 1045-1052)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookPublisherLink(book=1, publisher=1)
        existing_publisher = Publisher(id=2, name="Existing Publisher")
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = existing_publisher

        mock_session.exec.side_effect = [mock_exec1, mock_exec2]
        mock_session.flush = MagicMock()
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_publisher(
            mock_session, 1, publisher_name="Existing Publisher"
        )

        # Should use existing publisher
        added_publishers = [p for p in mock_session.added if isinstance(p, Publisher)]
        added_links = [
            p for p in mock_session.added if isinstance(p, BookPublisherLink)
        ]
        assert len(added_publishers) == 0
        assert len(added_links) == 1
        assert added_links[0].publisher == 2


def test_update_book_language_with_id() -> None:
    """Test _update_book_language uses language_id when provided (covers lines 1086-1102)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookLanguageLink(book=1, lang_code=1)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]
        # Mock defensive check query (after flush, check if link exists)
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = None  # Link doesn't exist, so it will be added

        mock_session.exec.side_effect = [mock_exec1, mock_exec2]
        mock_session.flush = MagicMock()
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_language(mock_session, 1, language_id=5)

        # Should use provided language_id
        added_links = [
            link for link in mock_session.added if isinstance(link, BookLanguageLink)
        ]
        assert len(added_links) == 1
        assert added_links[0].lang_code == 5


def test_update_book_language_with_existing() -> None:
    """Test _update_book_language uses existing language when found (covers lines 1089-1098)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookLanguageLink(book=1, lang_code=1)
        existing_language = Language(id=2, lang_code="fr")
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = existing_language
        # Mock defensive check query (after flush, check if link exists)
        mock_exec3 = MagicMock()
        mock_exec3.first.return_value = None  # Link doesn't exist, so it will be added

        mock_session.exec.side_effect = [mock_exec1, mock_exec2, mock_exec3]
        mock_session.flush = MagicMock()
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_language(mock_session, 1, language_code="fr")

        # Should use existing language
        added_languages = [
            lang for lang in mock_session.added if isinstance(lang, Language)
        ]
        added_links = [
            link for link in mock_session.added if isinstance(link, BookLanguageLink)
        ]
        assert len(added_languages) == 0
        assert len(added_links) == 1
        assert added_links[0].lang_code == 2


def test_update_book_rating_with_id() -> None:
    """Test _update_book_rating uses rating_id when provided (covers lines 1132-1146)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookRatingLink(book=1, rating=1)
        mock_exec = MagicMock()
        mock_exec.all.return_value = [existing_link]
        mock_session.exec.return_value = mock_exec
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_rating(mock_session, 1, rating_id=5)

        # Should use provided rating_id
        added_links = [r for r in mock_session.added if isinstance(r, BookRatingLink)]
        assert len(added_links) == 1
        assert added_links[0].rating == 5


def test_update_book_rating_with_existing() -> None:
    """Test _update_book_rating uses existing rating when found (covers lines 1135-1142)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookRatingLink(book=1, rating=1)
        existing_rating = Rating(id=2, rating=5)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = existing_rating

        mock_session.exec.side_effect = [mock_exec1, mock_exec2]
        mock_session.flush = MagicMock()
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_rating(mock_session, 1, rating_value=5)

        # Should use existing rating
        added_ratings = [r for r in mock_session.added if isinstance(r, Rating)]
        added_links = [r for r in mock_session.added if isinstance(r, BookRatingLink)]
        assert len(added_ratings) == 0
        assert len(added_links) == 1
        assert added_links[0].rating == 2


def test_update_book_series_whitespace_only() -> None:
    """Test _update_book_series removes series when whitespace-only name (covers lines 906-911)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookSeriesLink(book=1, series=1)
        mock_exec = MagicMock()
        mock_exec.first.return_value = existing_link
        mock_session.exec.return_value = mock_exec
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)

        repo._update_book_series(mock_session, 1, series_name="   ")

        # Should remove series
        assert existing_link in mock_session.deleted
        added_series = [s for s in mock_session.added if isinstance(s, Series)]
        assert len(added_series) == 0


def test_update_book_author_with_existing_link() -> None:
    """Test _update_book_authors skips creating duplicate links (covers lines 901-909)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing author names query (selects Author.name, returns strings)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = ["Author 1"]

        # Mock existing links query (selects BookAuthorLink, returns objects)
        existing_link = BookAuthorLink(book=1, author=1)
        mock_exec2 = MagicMock()
        mock_exec2.all.return_value = [existing_link]

        author1 = Author(id=1, name="Author 1")
        mock_exec3 = MagicMock()
        mock_exec3.first.return_value = author1

        # Link already exists
        mock_exec4 = MagicMock()
        mock_exec4.first.return_value = existing_link

        mock_session.exec.side_effect = [mock_exec1, mock_exec2, mock_exec3, mock_exec4]
        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = lambda x: mock_session.added.append(x)
        mock_session.flush = MagicMock()

        repo._update_book_authors(mock_session, 1, ["Author 1"])

        # Should not add duplicate link
        added_links = [a for a in mock_session.added if isinstance(a, BookAuthorLink)]
        assert len(added_links) == 0


def test_update_book_author_id_none_after_flush() -> None:
    """Test _update_book_authors handles author.id being None after flush (covers lines 897-900)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        # Mock existing author names query (selects Author.name, returns strings)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = []

        # Mock existing links query (selects BookAuthorLink, returns objects)
        mock_exec2 = MagicMock()
        mock_exec2.all.return_value = []

        # Author created but id is None after flush
        mock_exec3 = MagicMock()
        mock_exec3.first.return_value = None  # Author doesn't exist
        mock_session.exec.side_effect = [mock_exec1, mock_exec2, mock_exec3]
        mock_session.flush = MagicMock()

        # After flush, author.id is still None (simulate failure)
        def add_author(auth: Author) -> None:
            mock_session.added.append(auth)
            # Simulate id not being set after flush
            auth.id = None

        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = add_author

        repo._update_book_authors(mock_session, 1, ["Author 1"])

        # Should skip author with None id
        added_links = [a for a in mock_session.added if isinstance(a, BookAuthorLink)]
        assert len(added_links) == 0


def test_update_book_series_id_none_after_flush() -> None:
    """Test _update_book_series handles series.id being None after flush (covers lines 933-935)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))
        mock_session = MagicMock()
        mock_session.added = []
        mock_session.deleted = []

        existing_link = BookSeriesLink(book=1, series=1)
        mock_exec1 = MagicMock()
        mock_exec1.all.return_value = [existing_link]

        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = None

        mock_session.exec.side_effect = [mock_exec1, mock_exec2]
        mock_session.flush = MagicMock()

        def add_series(series: Series) -> None:
            mock_session.added.append(series)
            # Simulate id not being set after flush
            series.id = None

        mock_session.delete = lambda x: mock_session.deleted.append(x)
        mock_session.add = add_series

        repo._update_book_series(mock_session, 1, series_name="New Series")

        # Should not add link if series.id is None
        added_links = [s for s in mock_session.added if isinstance(s, BookSeriesLink)]
        assert len(added_links) == 0


def test_update_book_all_fields() -> None:
    """Test update_book with all fields provided (covers lines 1216-1251)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()

        repo = CalibreBookRepository(str(tmpdir))

        book = Book(id=1, title="Original", uuid="test-uuid")
        updated_book = BookWithFullRelations(
            book=Book(id=1, title="Updated", uuid="test-uuid"),
            authors=["Author 1"],
            series="Series 1",
            series_id=1,
            tags=["Tag 1"],
            identifiers=[{"type": "isbn", "val": "123"}],
            description="Description",
            publisher="Publisher 1",
            publisher_id=1,
            language="en",
            language_id=1,
            rating=5,
            rating_id=1,
        )

        with patch.object(repo, "_get_session") as mock_session:
            mock_session_obj = MagicMock()
            mock_exec = MagicMock()
            mock_exec.first.return_value = book
            mock_session_obj.exec.return_value = mock_exec
            mock_session_obj.commit = MagicMock()
            mock_session_obj.refresh = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_session_obj

            with (
                patch.object(repo, "get_book_full", return_value=updated_book),
                patch.object(repo, "_update_book_fields") as mock_fields,
                patch.object(repo, "_update_book_authors") as mock_authors,
                patch.object(repo, "_update_book_series") as mock_series,
                patch.object(repo, "_update_book_tags") as mock_tags,
                patch.object(repo, "_update_book_identifiers") as mock_identifiers,
                patch.object(repo, "_update_book_description") as mock_description,
                patch.object(repo, "_update_book_publisher") as mock_publisher,
                patch.object(repo, "_update_book_language") as mock_language,
                patch.object(repo, "_update_book_rating") as mock_rating,
            ):
                result = repo.update_book(
                    book_id=1,
                    title="Updated",
                    pubdate=datetime(2024, 1, 1, tzinfo=UTC),
                    author_names=["Author 1"],
                    series_name="Series 1",
                    series_index=1.0,
                    tag_names=["Tag 1"],
                    identifiers=[
                        {
                            "type": "isbn",
                            "val": "123",
                        }
                    ],
                    description="Description",
                    publisher_name="Publisher 1",
                    language_code="en",
                    rating_value=5,
                )

                assert result is not None
                mock_fields.assert_called_once()
                mock_authors.assert_called_once()
                mock_series.assert_called_once()
                mock_tags.assert_called_once()
                mock_identifiers.assert_called_once()
                mock_description.assert_called_once()
                mock_publisher.assert_called_once()
                mock_language.assert_called_once()
                mock_rating.assert_called_once()
                mock_session_obj.commit.assert_called_once()
                mock_session_obj.refresh.assert_called_once_with(book)
