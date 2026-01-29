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

"""Tests for cover enforcer to achieve 100% coverage."""

from __future__ import annotations

import subprocess  # noqa: S404
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

from bookcard.models.config import Library
from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.repositories.models import BookWithFullRelations
from bookcard.services.metadata_enforcement.cover_enforcer import (
    CoverEnforcementService,
)


@pytest.fixture
def library() -> Library:
    """Create a test library."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/test/library",
        calibre_db_file="metadata.db",
    )


@pytest.fixture
def book() -> Book:
    """Create a test book."""
    from datetime import UTC, datetime

    return Book(
        id=1,
        title="Test Book",
        timestamp=datetime.now(UTC),
        pubdate=datetime(2020, 1, 1, tzinfo=UTC),
        uuid="test-uuid-123",
        has_cover=True,
        path="Author Name/Test Book (1)",
    )


@pytest.fixture
def book_no_cover(book: Book) -> Book:
    """Create a test book without cover."""
    book.has_cover = False
    return book


@pytest.fixture
def book_with_rels(book: Book) -> BookWithFullRelations:
    """Create a test book with relations."""
    return BookWithFullRelations(
        book=book,
        authors=["Author One"],
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


@pytest.fixture
def valid_image(tmp_path: Path) -> Path:
    """Create a valid test image file."""
    img_path = tmp_path / "cover.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    return img_path


def test_init(library: Library) -> None:
    """Test CoverEnforcementService initialization."""
    service = CoverEnforcementService(library)
    assert service._library == library
    assert service._path_resolver is not None


def test_enforce_cover_no_cover(library: Library, book_no_cover: Book) -> None:
    """Test enforce_cover when book has no cover."""
    book_with_rels = BookWithFullRelations(
        book=book_no_cover,
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
    service = CoverEnforcementService(library)
    result = service.enforce_cover(book_with_rels)
    assert result is False


def test_enforce_cover_cover_not_found(
    library: Library, book_with_rels: BookWithFullRelations, tmp_path: Path
) -> None:
    """Test enforce_cover when cover file doesn't exist."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)

    with patch(
        "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        service = CoverEnforcementService(library)
        result = service.enforce_cover(book_with_rels)
        assert result is False


def test_enforce_cover_invalid_image(
    library: Library, book_with_rels: BookWithFullRelations, tmp_path: Path
) -> None:
    """Test enforce_cover when cover file is invalid."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    cover_file = book_dir / "cover.jpg"
    cover_file.write_text("not an image")

    with patch(
        "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        service = CoverEnforcementService(library)
        result = service.enforce_cover(book_with_rels)
        assert result is False


def test_enforce_cover_valid_no_ebooks(
    library: Library,
    book_with_rels: BookWithFullRelations,
    valid_image: Path,
    tmp_path: Path,
) -> None:
    """Test enforce_cover with valid cover but no ebook files."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    cover_file = book_dir / "cover.jpg"
    cover_file.write_bytes(valid_image.read_bytes())

    with (
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
        ) as mock_resolver_class,
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.CalibreBookRepository"
        ) as mock_repo_class,
    ):
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = CoverEnforcementService(library)
        result = service.enforce_cover(book_with_rels)
        # Should return True because cover file verification passed, even if no embedding happened
        assert result is True


def test_enforce_cover_oserror(
    library: Library, book_with_rels: BookWithFullRelations
) -> None:
    """Test enforce_cover with OSError."""
    with patch(
        "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.side_effect = OSError("Permission denied")
        mock_resolver_class.return_value = mock_resolver

        service = CoverEnforcementService(library)
        result = service.enforce_cover(book_with_rels)
        assert result is False


def test_enforce_cover_valueerror(
    library: Library,
    book_with_rels: BookWithFullRelations,
    tmp_path: Path,
) -> None:
    """Test enforce_cover with ValueError."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    cover_file = book_dir / "cover.jpg"
    cover_file.write_bytes(b"invalid")

    with (
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
        ) as mock_resolver_class,
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.Image.open"
        ) as mock_image,
    ):
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        mock_image.side_effect = ValueError("Invalid image")

        service = CoverEnforcementService(library)
        result = service.enforce_cover(book_with_rels)
        assert result is False


def test_get_ebook_polish_path_docker(library: Library) -> None:
    """Test _get_ebook_polish_path with Docker path."""
    with patch("pathlib.Path.exists", return_value=True):
        service = CoverEnforcementService(library)
        result = service._get_ebook_polish_path()
        assert Path(str(result)).as_posix() == "/app/calibre/ebook-polish"


def test_get_ebook_polish_path_system(library: Library) -> None:
    """Test _get_ebook_polish_path with system path."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        patch("shutil.which", return_value="/usr/bin/ebook-polish"),
    ):
        service = CoverEnforcementService(library)
        result = service._get_ebook_polish_path()
        assert result == "/usr/bin/ebook-polish"


def test_get_ebook_polish_path_not_found(library: Library) -> None:
    """Test _get_ebook_polish_path when not found."""
    with (
        patch("pathlib.Path.exists", return_value=False),
        patch("shutil.which", return_value=None),
    ):
        service = CoverEnforcementService(library)
        result = service._get_ebook_polish_path()
        assert result is None


def test_run_ebook_polish_success(library: Library) -> None:
    """Test _run_ebook_polish with successful execution."""
    polish_path = "/usr/bin/ebook-polish"
    cover_path = Path("/test/cover.jpg")
    ebook_path = Path("/test/book.azw3")

    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result):
        service = CoverEnforcementService(library)
        result = service._run_ebook_polish(polish_path, cover_path, ebook_path)
        assert result is True


def test_run_ebook_polish_failure(library: Library) -> None:
    """Test _run_ebook_polish with failed execution."""
    polish_path = "/usr/bin/ebook-polish"
    cover_path = Path("/test/cover.jpg")
    ebook_path = Path("/test/book.azw3")

    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stderr = "Error message"

    with patch("subprocess.run", return_value=mock_result):
        service = CoverEnforcementService(library)
        result = service._run_ebook_polish(polish_path, cover_path, ebook_path)
        assert result is False


def test_run_ebook_polish_timeout(library: Library) -> None:
    """Test _run_ebook_polish with timeout."""
    polish_path = "/usr/bin/ebook-polish"
    cover_path = Path("/test/cover.jpg")
    ebook_path = Path("/test/book.azw3")

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 300)):
        service = CoverEnforcementService(library)
        result = service._run_ebook_polish(polish_path, cover_path, ebook_path)
        assert result is False


def test_run_ebook_polish_exception(library: Library) -> None:
    """Test _run_ebook_polish with exception."""
    polish_path = "/usr/bin/ebook-polish"
    cover_path = Path("/test/cover.jpg")
    ebook_path = Path("/test/book.azw3")

    with patch("subprocess.run", side_effect=Exception("Unexpected error")):
        service = CoverEnforcementService(library)
        result = service._run_ebook_polish(polish_path, cover_path, ebook_path)
        assert result is False


def test_find_ebook_file_primary(library: Library, tmp_path: Path) -> None:
    """Test _find_ebook_file with primary path."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    ebook_file = book_dir / "test.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    service = CoverEnforcementService(library)
    result = service._find_ebook_file(book_dir, 1, data_record)
    assert result == ebook_file


def test_find_ebook_file_alternative(library: Library, tmp_path: Path) -> None:
    """Test _find_ebook_file with alternative path."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    ebook_file = book_dir / "1.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="other")

    service = CoverEnforcementService(library)
    result = service._find_ebook_file(book_dir, 1, data_record)
    assert result == ebook_file


def test_find_ebook_file_by_extension(library: Library, tmp_path: Path) -> None:
    """Test _find_ebook_file by extension."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    ebook_file = book_dir / "random.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name=None)

    service = CoverEnforcementService(library)
    result = service._find_ebook_file(book_dir, 1, data_record)
    assert result == ebook_file


def test_find_ebook_file_not_found(library: Library, tmp_path: Path) -> None:
    """Test _find_ebook_file when file not found."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    service = CoverEnforcementService(library)
    result = service._find_ebook_file(book_dir, 1, data_record)
    assert result is None


def test_embed_cover_into_ebooks_no_polish(
    library: Library, book_with_rels: BookWithFullRelations, tmp_path: Path
) -> None:
    """Test _embed_cover_into_ebooks when ebook-polish not found."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    cover_file = book_dir / "cover.jpg"
    cover_file.write_bytes(b"test")

    with (
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
        ) as mock_resolver_class,
        patch.object(
            CoverEnforcementService, "_get_ebook_polish_path", return_value=None
        ),
    ):
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        service = CoverEnforcementService(library)
        result = service._embed_cover_into_ebooks(book_with_rels, book_dir, cover_file)
        assert result is False


def test_embed_cover_into_ebooks_no_book_id(
    library: Library, book_with_rels: BookWithFullRelations, tmp_path: Path
) -> None:
    """Test _embed_cover_into_ebooks when book ID is None."""
    book_with_rels.book.id = None
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    cover_file = book_dir / "cover.jpg"
    cover_file.write_bytes(b"test")

    with patch(
        "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
    ) as mock_resolver_class:
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        service = CoverEnforcementService(library)
        result = service._embed_cover_into_ebooks(book_with_rels, book_dir, cover_file)
        assert result is False


def test_embed_cover_into_ebooks_success(
    library: Library, book_with_rels: BookWithFullRelations, tmp_path: Path
) -> None:
    """Test _embed_cover_into_ebooks with successful embedding (AZW3)."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    cover_file = book_dir / "cover.jpg"
    cover_file.write_bytes(b"test")
    ebook_file = book_dir / "test.azw3"
    ebook_file.write_text("test")

    # Use AZW3 to test polish logic
    data_record = Data(id=1, book=1, format="AZW3", uncompressed_size=100, name="test")

    with (
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
        ) as mock_resolver_class,
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.CalibreBookRepository"
        ) as mock_repo_class,
        patch.object(
            CoverEnforcementService,
            "_get_ebook_polish_path",
            return_value="/usr/bin/ebook-polish",
        ),
        patch.object(CoverEnforcementService, "_run_ebook_polish", return_value=True),
        patch.object(
            CoverEnforcementService, "_find_ebook_file", return_value=ebook_file
        ),
    ):
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [data_record]
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = CoverEnforcementService(library)
        result = service._embed_cover_into_ebooks(book_with_rels, book_dir, cover_file)
        assert result is True


def test_embed_cover_into_ebooks_skips_epub(
    library: Library, book_with_rels: BookWithFullRelations, tmp_path: Path
) -> None:
    """Test _embed_cover_into_ebooks skips EPUB format."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    cover_file = book_dir / "cover.jpg"
    cover_file.write_bytes(b"test")
    ebook_file = book_dir / "test.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    with (
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
        ) as mock_resolver_class,
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.CalibreBookRepository"
        ) as mock_repo_class,
        patch.object(
            CoverEnforcementService,
            "_get_ebook_polish_path",
            return_value="/usr/bin/ebook-polish",
        ),
    ):
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [data_record]
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = CoverEnforcementService(library)
        result = service._embed_cover_into_ebooks(book_with_rels, book_dir, cover_file)
        assert result is False


def test_embed_cover_into_ebooks_unsupported_format(
    library: Library, book_with_rels: BookWithFullRelations, tmp_path: Path
) -> None:
    """Test _embed_cover_into_ebooks with unsupported format."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    cover_file = book_dir / "cover.jpg"
    cover_file.write_bytes(b"test")

    data_record = Data(id=1, book=1, format="PDF", uncompressed_size=100, name="test")

    with (
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.LibraryPathResolver"
        ) as mock_resolver_class,
        patch(
            "bookcard.services.metadata_enforcement.cover_enforcer.CalibreBookRepository"
        ) as mock_repo_class,
        patch.object(
            CoverEnforcementService,
            "_get_ebook_polish_path",
            return_value="/usr/bin/ebook-polish",
        ),
    ):
        mock_resolver = MagicMock()
        mock_resolver.get_library_root.return_value = library_root
        mock_resolver_class.return_value = mock_resolver

        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [data_record]
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = CoverEnforcementService(library)
        result = service._embed_cover_into_ebooks(book_with_rels, book_dir, cover_file)
        assert result is False
