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

"""Additional tests for Calibre book repository to achieve 100% coverage.

This file covers methods that were not fully covered in other test files.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Identifier,
    Language,
    Publisher,
    Series,
    Tag,
)
from fundamental.models.media import Data
from fundamental.repositories import CalibreBookRepository
from fundamental.services.book_metadata import BookMetadata, Contributor

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def temp_repo() -> Generator[CalibreBookRepository, None, None]:
    """Create a CalibreBookRepository with a temporary database.

    Yields
    ------
    CalibreBookRepository
        Repository instance with temporary database path.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"
        db_file.touch()
        yield CalibreBookRepository(str(tmpdir))


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock session with common setup.

    Returns
    -------
    MagicMock
        Mock session with added/deleted tracking.
    """
    session = MagicMock()
    session.added = []
    session.deleted = []
    session.add = lambda x: session.added.append(x)
    session.delete = lambda x: session.deleted.append(x)
    session.flush = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    return session


def test_get_library_stats(temp_repo: CalibreBookRepository) -> None:
    """Test get_library_stats returns correct statistics (covers lines 1757-1792)."""
    from sqlmodel import create_engine

    # Create a real database for this test
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "metadata.db"
        engine = create_engine(f"sqlite:///{db_path}")
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(engine)

        repo = CalibreBookRepository(str(tmpdir))

        with repo._get_session() as session:
            # Create test data
            book1 = Book(id=1, title="Book 1", uuid="uuid1")
            book2 = Book(id=2, title="Book 2", uuid="uuid2")
            session.add(book1)
            session.add(book2)
            session.flush()

            # Add some links
            session.add(BookAuthorLink(book=1, author=1))
            session.add(BookAuthorLink(book=2, author=2))
            session.add(BookSeriesLink(book=1, series=1))
            session.add(BookTagLink(book=1, tag=1))
            session.add(BookTagLink(book=2, tag=2))
            session.add(BookRatingLink(book=1, rating=1))
            session.add(
                Data(book=1, format="EPUB", uncompressed_size=1000, name="book1")
            )
            session.add(
                Data(book=2, format="PDF", uncompressed_size=2000, name="book2")
            )
            session.commit()

        stats = repo.get_library_stats()

        assert stats["total_books"] == 2
        assert stats["total_series"] == 1
        assert stats["total_authors"] == 2
        assert stats["total_tags"] == 2
        assert stats["total_ratings"] == 1
        assert stats["total_content_size"] == 3000


def test_get_library_stats_empty_database(temp_repo: CalibreBookRepository) -> None:
    """Test get_library_stats handles empty database (covers lines 1789-1790)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "metadata.db"

        from sqlmodel import create_engine

        engine = create_engine(f"sqlite:///{db_file}")
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(engine)

        repo = CalibreBookRepository(str(tmpdir))
        stats = repo.get_library_stats()

        assert stats["total_books"] == 0
        assert stats["total_series"] == 0
        assert stats["total_authors"] == 0
        assert stats["total_tags"] == 0
        assert stats["total_ratings"] == 0
        assert stats["total_content_size"] == 0


@pytest.mark.parametrize(
    ("name", "max_length", "expected"),
    [
        ("normal_name.txt", 96, "normal_name.txt"),
        ("file<>name.txt", 96, "file__name.txt"),
        ("file:name.txt", 96, "file_name.txt"),
        ("file/name.txt", 96, "file_name.txt"),
        ("file\\name.txt", 96, "file_name.txt"),
        ("file|name.txt", 96, "file_name.txt"),
        ("file?name.txt", 96, "file_name.txt"),
        ("file*name.txt", 96, "file_name.txt"),
        ("a" * 100, 96, "a" * 96),
        ("   ", 96, "Unknown"),
        ("", 96, "Unknown"),
    ],
)
def test_sanitize_filename(
    temp_repo: CalibreBookRepository,
    name: str,
    max_length: int,
    expected: str,
) -> None:
    """Test _sanitize_filename sanitizes filenames correctly (covers lines 1817-1821)."""
    result = temp_repo._sanitize_filename(name, max_length)
    assert result == expected


def test_get_or_create_author_creates_new(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _get_or_create_author creates new author (covers lines 1843-1854)."""
    mock_exec = MagicMock()
    mock_exec.first.return_value = None  # Author doesn't exist
    mock_session.exec.return_value = mock_exec

    # Mock flush to assign ID
    def mock_flush() -> None:
        if mock_session.added:
            author = mock_session.added[0]
            if isinstance(author, Author) and author.id is None:
                author.id = 1

    mock_session.flush = mock_flush

    author = temp_repo._get_or_create_author(mock_session, "New Author")

    assert author.name == "New Author"
    assert author.id == 1
    assert author in mock_session.added


def test_get_or_create_author_returns_existing(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _get_or_create_author returns existing author."""
    existing_author = Author(id=1, name="Existing Author")
    mock_exec = MagicMock()
    mock_exec.first.return_value = existing_author
    mock_session.exec.return_value = mock_exec

    author = temp_repo._get_or_create_author(mock_session, "Existing Author")

    assert author is existing_author
    assert len(mock_session.added) == 0


def test_get_or_create_author_raises_on_failure(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _get_or_create_author raises ValueError when author creation fails."""
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_session.exec.return_value = mock_exec

    # Mock flush to not assign ID
    def mock_flush() -> None:
        pass

    mock_session.flush = mock_flush

    # Create author but don't assign ID
    author = Author(name="Test Author")
    mock_session.added.append(author)

    with pytest.raises(ValueError, match="Failed to create author"):
        # The method will check if author.id is None after flush
        temp_repo._get_or_create_author(mock_session, "Test Author")


def test_create_book_record(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _create_book_record creates book record (covers lines 1892-1914)."""
    from datetime import UTC, datetime

    # Mock flush to assign ID
    def mock_flush() -> None:
        for item in mock_session.added:
            if isinstance(item, Book) and item.id is None:
                item.id = 1

    mock_session.flush = mock_flush

    book = temp_repo._create_book_record(
        mock_session,
        "Test Book",
        "Test Author",
        "Test Author/Test Book",
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
        series_index=1.5,
    )

    assert book.title == "Test Book"
    assert book.author_sort == "Test Author"
    assert book.path == "Test Author/Test Book"
    assert book.series_index == 1.5
    assert book in mock_session.added


def test_create_book_record_defaults(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _create_book_record uses defaults when None provided."""

    def mock_flush() -> None:
        for item in mock_session.added:
            if isinstance(item, Book) and item.id is None:
                item.id = 1

    mock_session.flush = mock_flush

    book = temp_repo._create_book_record(
        mock_session, "Test Book", "Test Author", "Test Author/Test Book"
    )

    assert book.pubdate is not None
    assert book.series_index == 1.0


def test_create_book_record_raises_on_failure(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _create_book_record raises ValueError when book creation fails."""

    def mock_flush() -> None:
        pass

    mock_session.flush = mock_flush

    with pytest.raises(ValueError, match="Failed to create book"):
        temp_repo._create_book_record(
            mock_session, "Test Book", "Test Author", "Test Author/Test Book"
        )


def test_save_book_file(temp_repo: CalibreBookRepository) -> None:
    """Test _save_book_file copies file to library directory (covers lines 1939-1944)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir) / "library"
        library_path.mkdir()
        source_file = Path(tmpdir) / "source.txt"
        source_file.write_text("test content")

        temp_repo._save_book_file(
            source_file, library_path, "Author/Title", "Title", "txt"
        )

        target_file = library_path / "Author" / "Title" / "Title.txt"
        assert target_file.exists()
        assert target_file.read_text() == "test content"


def test_add_book_file_not_found(temp_repo: CalibreBookRepository) -> None:
    """Test add_book raises ValueError when file doesn't exist (covers line 1983-1985)."""
    nonexistent_file = Path("/nonexistent/file.epub")

    with pytest.raises(ValueError, match="File not found"):
        temp_repo.add_book(nonexistent_file, "epub")


def test_add_book_with_metadata(temp_repo: CalibreBookRepository) -> None:
    """Test add_book creates book with metadata (covers lines 1987-2059)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        db_file = library_path / "metadata.db"

        from sqlmodel import create_engine

        engine = create_engine(f"sqlite:///{db_file}")
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(engine)

        repo = CalibreBookRepository(str(library_path))

        # Create a test file
        test_file = library_path / "test.epub"
        test_file.write_text("fake epub content")

        # Mock metadata extractor
        mock_metadata = BookMetadata(
            title="Test Book",
            author="Test Author",
            description="Test description",
            tags=["tag1", "tag2"],
            publisher="Test Publisher",
            identifiers=[{"type": "isbn", "val": "123456"}],
            languages=["en"],
            series="Test Series",
        )

        with patch(
            "fundamental.services.book_metadata_extractor.BookMetadataExtractor"
        ) as mock_extractor_class:
            mock_extractor = MagicMock()
            mock_extractor.extract_metadata.return_value = mock_metadata
            mock_extractor_class.return_value = mock_extractor

            book_id = repo.add_book(test_file, "epub", library_path=library_path)

            assert book_id is not None
            assert (
                library_path / "Test Author" / "Test Book" / "Test Book.epub"
            ).exists()


def test_match_files_by_extension_no_data_records(
    temp_repo: CalibreBookRepository,
) -> None:
    """Test _match_files_by_extension handles no data records (covers lines 2088-2095)."""
    all_files = [Path("book1.epub"), Path("book2.pdf")]
    data_records: list = []
    existing_paths: list[Path] = []
    book_id = 1

    result = temp_repo._match_files_by_extension(
        all_files, data_records, existing_paths, book_id
    )

    assert result == []


def test_match_files_by_extension_matches_by_extension(
    temp_repo: CalibreBookRepository,
) -> None:
    """Test _match_files_by_extension matches files by extension (covers lines 2097-2114)."""
    all_files = [Path("book1.epub"), Path("book2.pdf"), Path("other.txt")]
    data_records = [
        Data(book=1, format="EPUB", uncompressed_size=1000, name="book1"),
        Data(book=1, format="PDF", uncompressed_size=2000, name="book2"),
    ]
    existing_paths: list[Path] = []
    book_id = 1

    result = temp_repo._match_files_by_extension(
        all_files, data_records, existing_paths, book_id
    )

    assert len(result) == 2
    assert Path("book1.epub") in result
    assert Path("book2.pdf") in result
    assert Path("other.txt") not in result


def test_collect_filesystem_paths_no_directory(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _collect_filesystem_paths handles missing directory (covers lines 2144-2149)."""
    result = temp_repo._collect_filesystem_paths(
        mock_session, 1, "Nonexistent/Path", Path("/nonexistent")
    )

    filesystem_paths, book_dir = result
    assert filesystem_paths == []
    assert book_dir is None


def test_collect_filesystem_paths_finds_files(
    temp_repo: CalibreBookRepository,
) -> None:
    """Test _collect_filesystem_paths finds files (covers lines 2151-2197)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        db_file = library_path / "metadata.db"

        from sqlmodel import create_engine

        engine = create_engine(f"sqlite:///{db_file}")
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(engine)

        book_dir = library_path / "Author" / "Title"
        book_dir.mkdir(parents=True)

        # Create test files
        file1 = book_dir / "Title.epub"
        file1.write_text("content1")
        file2 = book_dir / "1.pdf"
        file2.write_text("content2")
        cover = book_dir / "cover.jpg"
        cover.write_text("cover")

        repo = CalibreBookRepository(str(library_path))

        with repo._get_session() as session:
            # Add data records
            data1 = Data(book=1, format="EPUB", uncompressed_size=1000, name="Title")
            data2 = Data(book=1, format="PDF", uncompressed_size=2000, name="1")
            session.add(data1)
            session.add(data2)
            session.commit()

            filesystem_paths, result_book_dir = repo._collect_filesystem_paths(
                session, 1, "Author/Title", library_path
            )

            assert len(filesystem_paths) == 3
            assert file1 in filesystem_paths
            assert file2 in filesystem_paths
            assert cover in filesystem_paths
            assert result_book_dir == book_dir


def test_collect_filesystem_paths_oserror_handling(
    temp_repo: CalibreBookRepository,
) -> None:
    """Test _collect_filesystem_paths handles OSError when listing files (covers lines 2173-2176)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        db_file = library_path / "metadata.db"

        from sqlmodel import create_engine

        engine = create_engine(f"sqlite:///{db_file}")
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(engine)

        book_dir = library_path / "Author" / "Title"
        book_dir.mkdir(parents=True)

        repo = CalibreBookRepository(str(library_path))

        with repo._get_session() as session:
            # Add data record
            data = Data(book=1, format="EPUB", uncompressed_size=1000, name="Title")
            session.add(data)
            session.commit()

            # Create a file that matches the pattern
            file_path = book_dir / "Title.epub"
            file_path.write_text("content")

            # Mock Path.iterdir to raise OSError
            import fundamental.repositories.calibre_book_repository as repo_mod

            original_path = repo_mod.Path

            class MockPath(Path):
                def iterdir(self: Path) -> list[Path]:
                    if str(self) == str(book_dir):
                        raise OSError("Permission denied")
                    return Path.iterdir(self)  # type: ignore[arg-type]

            # Temporarily replace Path in the module
            repo_mod.Path = MockPath  # type: ignore[assignment]

            try:
                filesystem_paths, _result_book_dir = repo._collect_filesystem_paths(
                    session, 1, "Author/Title", library_path
                )

                # Should still return paths found via Data records (even if iterdir fails)
                assert isinstance(filesystem_paths, list)
                # Should have found the file via Data record pattern matching
                assert len(filesystem_paths) >= 1
            finally:
                repo_mod.Path = original_path


def test_execute_database_deletion_commands(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _execute_database_deletion_commands executes all commands (covers lines 2221-2240)."""
    book = Book(id=1, title="Test Book", uuid="test-uuid")

    # Mock exec to return empty results for all queries
    mock_exec = MagicMock()
    mock_exec.all.return_value = []
    mock_exec.first.return_value = None
    mock_session.exec.return_value = mock_exec

    temp_repo._execute_database_deletion_commands(mock_session, 1, book)

    # Should have executed multiple delete commands
    assert mock_session.exec.call_count > 0


def test_execute_filesystem_deletion_commands_empty(
    temp_repo: CalibreBookRepository,
) -> None:
    """Test _execute_filesystem_deletion_commands handles empty list (covers line 2262-2263)."""
    temp_repo._execute_filesystem_deletion_commands([], None)
    # Should return without error


def test_execute_filesystem_deletion_commands_with_files(
    temp_repo: CalibreBookRepository,
) -> None:
    """Test _execute_filesystem_deletion_commands deletes files (covers lines 2265-2273)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        book_dir = Path(tmpdir) / "book_dir"
        book_dir.mkdir()

        temp_repo._execute_filesystem_deletion_commands([file1, file2], book_dir)

        assert not file1.exists()
        assert not file2.exists()
        assert not book_dir.exists()  # Should be deleted if empty


def test_get_book_or_raise_found(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _get_book_or_raise returns book when found (covers lines 2299-2304)."""
    book = Book(id=1, title="Test Book", uuid="test-uuid")
    mock_exec = MagicMock()
    mock_exec.first.return_value = book
    mock_session.exec.return_value = mock_exec

    result = temp_repo._get_book_or_raise(mock_session, 1)
    assert result is book


def test_get_book_or_raise_not_found(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _get_book_or_raise raises ValueError when not found."""
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_session.exec.return_value = mock_exec

    with pytest.raises(ValueError, match="book_not_found"):
        temp_repo._get_book_or_raise(mock_session, 999)


def test_delete_book_not_found(temp_repo: CalibreBookRepository) -> None:
    """Test delete_book raises ValueError when book not found (covers line 2338)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        db_file = library_path / "metadata.db"

        from sqlmodel import create_engine

        engine = create_engine(f"sqlite:///{db_file}")
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(engine)

        repo = CalibreBookRepository(str(library_path))

        with pytest.raises(ValueError, match="book_not_found"):
            repo.delete_book(999)


def test_delete_book_with_files(temp_repo: CalibreBookRepository) -> None:
    """Test delete_book deletes files when requested (covers lines 2344-2359)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        library_path = Path(tmpdir)
        db_file = library_path / "metadata.db"

        from sqlmodel import create_engine

        engine = create_engine(f"sqlite:///{db_file}")
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(engine)

        repo = CalibreBookRepository(str(library_path))

        with repo._get_session() as session:
            book = Book(id=1, title="Test Book", uuid="test-uuid", path="Author/Title")
            session.add(book)
            session.flush()

            data = Data(book=1, format="EPUB", uncompressed_size=1000, name="Title")
            session.add(data)
            session.commit()

        # Create book directory and file
        book_dir = library_path / "Author" / "Title"
        book_dir.mkdir(parents=True)
        book_file = book_dir / "Title.epub"
        book_file.write_text("content")

        repo.delete_book(1, delete_files_from_drive=True, library_path=library_path)

        assert not book_file.exists()
        assert not book_dir.exists()


def test_add_book_metadata(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_metadata adds all metadata (covers lines 2384-2412)."""
    from fundamental.models.core import Comment

    metadata = BookMetadata(
        title="Test",
        author="Author",
        description="Description",
        tags=["tag1"],
        publisher="Publisher",
        identifiers=[{"type": "isbn", "val": "123"}],
        languages=["en"],
        series="Series",
        contributors=[Contributor(name="Editor", role="editor")],
    )

    # Mock all the helper methods
    with (
        patch.object(temp_repo, "_add_book_tags") as mock_tags,
        patch.object(temp_repo, "_add_book_publisher") as mock_pub,
        patch.object(temp_repo, "_add_book_identifiers") as mock_idents,
        patch.object(temp_repo, "_add_book_languages") as mock_langs,
        patch.object(temp_repo, "_add_book_series") as mock_series,
        patch.object(temp_repo, "_add_book_contributors") as mock_contribs,
    ):
        temp_repo._add_book_metadata(mock_session, 1, metadata)

        # Should have added comment
        assert len(mock_session.added) > 0
        assert any(isinstance(item, Comment) for item in mock_session.added)
        mock_tags.assert_called_once()
        mock_pub.assert_called_once()
        mock_idents.assert_called_once()
        mock_langs.assert_called_once()
        mock_series.assert_called_once()
        mock_contribs.assert_called_once()


def test_add_book_tags(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_tags adds tags (covers lines 2428-2444)."""
    # Mock existing tag
    existing_tag = Tag(id=1, name="existing")
    mock_exec = MagicMock()
    mock_exec.first.side_effect = [
        existing_tag,
        None,
        None,
        None,
    ]  # Tag exists, link doesn't, new tag, new link
    mock_session.exec.return_value = mock_exec

    temp_repo._add_book_tags(mock_session, 1, ["existing", "new"])

    # Should have added new tag and links
    assert len(mock_session.added) > 0


def test_add_book_tags_skips_empty(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_tags skips empty tag names."""
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_session.exec.return_value = mock_exec

    temp_repo._add_book_tags(mock_session, 1, ["", "   ", "valid"])

    # Should only process "valid"
    assert len(mock_session.added) > 0


def test_add_book_publisher(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_publisher adds publisher (covers lines 2460-2476)."""
    # Mock no existing publisher
    mock_exec = MagicMock()
    mock_exec.first.side_effect = [None, None]  # Publisher doesn't exist, link doesn't
    mock_session.exec.return_value = mock_exec

    # Mock flush to assign ID
    def mock_flush() -> None:
        for item in mock_session.added:
            if isinstance(item, Publisher) and item.id is None:
                item.id = 1

    mock_session.flush = mock_flush

    temp_repo._add_book_publisher(mock_session, 1, "New Publisher")

    # Should have added publisher and link
    assert len(mock_session.added) == 2


def test_add_book_identifiers(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_identifiers adds identifiers (covers lines 2496-2523)."""
    # Mock no existing identifier
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_session.exec.return_value = mock_exec

    temp_repo._add_book_identifiers(
        mock_session,
        1,
        [{"type": "isbn", "val": "123456"}, {"type": "doi", "val": "10.1234/test"}],
    )

    # Should have added identifiers
    assert len(mock_session.added) == 2


def test_add_book_identifiers_deduplicates(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_identifiers deduplicates by type."""
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_session.exec.return_value = mock_exec

    temp_repo._add_book_identifiers(
        mock_session,
        1,
        [
            {"type": "isbn", "val": "123"},
            {"type": "isbn", "val": "456"},  # Duplicate type, should be skipped
        ],
    )

    # Should only add one identifier (first of each type)
    assert len(mock_session.added) == 1


def test_add_book_identifiers_updates_existing(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_identifiers updates existing identifier."""
    existing = Identifier(book=1, type="isbn", val="old")
    mock_exec = MagicMock()
    mock_exec.first.return_value = existing
    mock_session.exec.return_value = mock_exec

    temp_repo._add_book_identifiers(mock_session, 1, [{"type": "isbn", "val": "new"}])

    assert existing.val == "new"
    assert len(mock_session.added) == 0  # No new identifier added


def test_add_book_identifiers_skips_empty(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_identifiers skips empty values."""
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_session.exec.return_value = mock_exec

    temp_repo._add_book_identifiers(
        mock_session, 1, [{"type": "isbn", "val": ""}, {"type": "isbn", "val": "   "}]
    )

    # Should not add empty identifiers
    assert len(mock_session.added) == 0


def test_add_book_languages(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_languages adds languages (covers lines 2539-2552)."""
    lang = Language(id=1, lang_code="en")
    mock_exec = MagicMock()
    mock_exec.first.return_value = None  # Link doesn't exist
    mock_session.exec.return_value = mock_exec

    # Mock _find_or_create_language
    with patch.object(
        temp_repo, "_find_or_create_language", return_value=lang
    ) as mock_find:
        temp_repo._add_book_languages(mock_session, 1, ["en"])

        assert len(mock_session.added) == 1
        mock_find.assert_called_once_with(mock_session, "en")


def test_add_book_languages_skips_empty(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_languages skips empty language codes."""
    lang = Language(id=1, lang_code="en")
    mock_exec = MagicMock()
    mock_exec.first.return_value = None
    mock_session.exec.return_value = mock_exec

    with patch.object(temp_repo, "_find_or_create_language", return_value=lang):
        temp_repo._add_book_languages(mock_session, 1, ["", "   ", "en"])

        # Should only process "en"
        assert len(mock_session.added) == 1


def test_add_book_languages_handles_none_language(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_languages handles None language from _find_or_create_language."""
    with patch.object(
        temp_repo, "_find_or_create_language", return_value=None
    ) as mock_find:
        temp_repo._add_book_languages(mock_session, 1, ["invalid"])

        assert len(mock_session.added) == 0
        mock_find.assert_called_once()


def test_add_book_series(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_series adds series (covers lines 2568-2581)."""
    # Mock no existing series
    mock_exec = MagicMock()
    mock_exec.first.side_effect = [None, None]  # Series doesn't exist, link doesn't
    mock_session.exec.return_value = mock_exec

    # Mock flush to assign ID
    def mock_flush() -> None:
        for item in mock_session.added:
            if isinstance(item, Series) and item.id is None:
                item.id = 1

    mock_session.flush = mock_flush

    temp_repo._add_book_series(mock_session, 1, "New Series")

    # Should have added series and link
    assert len(mock_session.added) == 2


def test_add_book_contributors(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_contributors adds contributors (covers lines 2600-2612)."""
    contributor = Contributor(name="Contributor", role="editor")
    mock_exec = MagicMock()
    mock_exec.first.return_value = None  # Link doesn't exist
    mock_session.exec.return_value = mock_exec

    # Mock _get_or_create_author
    author = Author(id=2, name="Contributor")
    with patch.object(
        temp_repo, "_get_or_create_author", return_value=author
    ) as mock_get_author:
        temp_repo._add_book_contributors(mock_session, 1, [contributor])

        assert len(mock_session.added) == 1
        mock_get_author.assert_called_once_with(mock_session, "Contributor")


def test_add_book_contributors_skips_author_role(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_contributors skips contributors with 'author' role."""
    contributor = Contributor(name="Author", role="author")
    temp_repo._add_book_contributors(mock_session, 1, [contributor])

    # Should not add anything (author role is skipped)
    assert len(mock_session.added) == 0


def test_add_book_contributors_skips_none_role(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_contributors skips contributors with None role."""
    contributor = Contributor(name="Contributor", role=None)
    temp_repo._add_book_contributors(mock_session, 1, [contributor])

    # Should not add anything (None role is skipped)
    assert len(mock_session.added) == 0


def test_add_book_contributors_skips_empty_name(
    temp_repo: CalibreBookRepository, mock_session: MagicMock
) -> None:
    """Test _add_book_contributors skips contributors with empty name."""
    contributor = Contributor(name="", role="editor")
    temp_repo._add_book_contributors(mock_session, 1, [contributor])

    # Should not add anything (empty name is skipped)
    assert len(mock_session.added) == 0
