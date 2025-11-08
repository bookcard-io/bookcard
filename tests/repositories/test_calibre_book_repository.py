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
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import select

from fundamental.models.core import (
    Book,
)
from fundamental.repositories.calibre_book_repository import (
    AuthorFilterStrategy,
    AuthorSuggestionStrategy,
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
