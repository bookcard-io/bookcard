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

from fundamental.models.core import Book
from fundamental.repositories.calibre_book_repository import (
    CalibreBookRepository,
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
