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

"""Tests for metadata enforcement service to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.config import Library
from fundamental.models.core import Book
from fundamental.models.media import Data
from fundamental.models.metadata_enforcement import EnforcementStatus
from fundamental.repositories.models import BookWithFullRelations
from fundamental.services.metadata_enforcement.ebook_enforcer import (
    EbookMetadataEnforcer,
)
from fundamental.services.metadata_enforcement_service import (
    MetadataEnforcementService,
)
from tests.conftest import DummySession


@pytest.fixture
def session() -> DummySession:
    """Create a test session."""
    return DummySession()


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
        has_cover=False,
        path="Author Name/Test Book (1)",
    )


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
def mock_opf_enforcer() -> MagicMock:
    """Create a mock OPF enforcer."""
    enforcer = MagicMock()
    enforcer.enforce_opf.return_value = True
    return enforcer


@pytest.fixture
def mock_cover_enforcer() -> MagicMock:
    """Create a mock cover enforcer."""
    enforcer = MagicMock()
    enforcer.enforce_cover.return_value = True
    return enforcer


@pytest.fixture
def mock_ebook_enforcer() -> MagicMock:
    """Create a mock ebook enforcer."""
    enforcer = MagicMock(spec=EbookMetadataEnforcer)
    enforcer.can_handle.return_value = True
    enforcer.enforce_metadata.return_value = True
    return enforcer


def test_init_default_services(session: DummySession, library: Library) -> None:
    """Test initialization with default services."""
    service = MetadataEnforcementService(session, library)  # type: ignore[arg-type]
    assert service._session == session
    assert service._library == library
    assert service._opf_enforcer is not None
    assert service._cover_enforcer is not None
    assert service._ebook_enforcers is not None
    assert service._repository is not None
    assert service._path_resolver is not None


def test_init_custom_services(
    session: DummySession,
    library: Library,
    mock_opf_enforcer: MagicMock,
    mock_cover_enforcer: MagicMock,
    mock_ebook_enforcer: MagicMock,
) -> None:
    """Test initialization with custom services."""
    service = MetadataEnforcementService(
        session,  # type: ignore[arg-type]
        library,
        opf_enforcer=mock_opf_enforcer,
        cover_enforcer=mock_cover_enforcer,
        ebook_enforcers=[mock_ebook_enforcer],
    )
    assert service._opf_enforcer == mock_opf_enforcer
    assert service._cover_enforcer == mock_cover_enforcer
    assert service._ebook_enforcers == [mock_ebook_enforcer]


def test_enforce_metadata_success(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    mock_opf_enforcer: MagicMock,
    mock_cover_enforcer: MagicMock,
    mock_ebook_enforcer: MagicMock,
    tmp_path: Path,
) -> None:
    """Test successful metadata enforcement."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)

    with patch(
        "fundamental.repositories.calibre_book_repository.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = MetadataEnforcementService(
            session,  # type: ignore[arg-type]
            library,
            opf_enforcer=mock_opf_enforcer,
            cover_enforcer=mock_cover_enforcer,
            ebook_enforcers=[mock_ebook_enforcer],
        )

        with patch.object(
            service._path_resolver, "get_library_root", return_value=library_root
        ):
            result = service.enforce_metadata(1, book_with_rels, user_id=1)

            assert result.success is True
            assert result.opf_updated is True
            assert result.cover_updated is True
            assert result.ebook_files_updated is False
            assert len(session.added) == 1
            operation = session.added[0]
            assert operation.status == EnforcementStatus.COMPLETED
            assert operation.opf_updated is True
            assert operation.cover_updated is True


def test_enforce_metadata_failure(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    mock_opf_enforcer: MagicMock,
    mock_cover_enforcer: MagicMock,
    mock_ebook_enforcer: MagicMock,
) -> None:
    """Test metadata enforcement with exception."""
    mock_opf_enforcer.enforce_opf.side_effect = Exception("Test error")

    service = MetadataEnforcementService(
        session,  # type: ignore[arg-type]
        library,
        opf_enforcer=mock_opf_enforcer,
        cover_enforcer=mock_cover_enforcer,
        ebook_enforcers=[mock_ebook_enforcer],
    )

    result = service.enforce_metadata(1, book_with_rels, user_id=1)

    assert result.success is False
    assert result.error_message == "Test error"
    assert len(session.added) == 1
    operation = session.added[0]
    assert operation.status == EnforcementStatus.FAILED
    assert operation.error_message == "Test error"


def test_enforce_ebook_files_no_directory(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
) -> None:
    """Test _enforce_ebook_files when book directory doesn't exist."""
    service = MetadataEnforcementService(session, library)  # type: ignore[arg-type]

    with patch.object(
        service._path_resolver, "get_library_root", return_value=Path("/nonexistent")
    ):
        any_updated, formats = service._enforce_ebook_files(book_with_rels)
        assert any_updated is False
        assert formats == []


def test_enforce_ebook_files_no_enforcer(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    tmp_path: Path,
) -> None:
    """Test _enforce_ebook_files when no enforcer available."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)

    data_record = Data(id=1, book=1, format="PDF", uncompressed_size=100, name="test")

    with patch(
        "fundamental.repositories.calibre_book_repository.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [data_record]
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = MetadataEnforcementService(session, library)  # type: ignore[arg-type]

        with patch.object(
            service._path_resolver, "get_library_root", return_value=library_root
        ):
            any_updated, formats = service._enforce_ebook_files(book_with_rels)
            assert any_updated is False
            assert formats == []


def test_enforce_ebook_files_no_book_id(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    tmp_path: Path,
) -> None:
    """Test _enforce_ebook_files when book ID is None."""
    book_with_rels.book.id = None
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    with patch(
        "fundamental.repositories.calibre_book_repository.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [data_record]
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = MetadataEnforcementService(session, library)  # type: ignore[arg-type]

        with patch.object(
            service._path_resolver, "get_library_root", return_value=library_root
        ):
            any_updated, formats = service._enforce_ebook_files(book_with_rels)
            assert any_updated is False
            assert formats == []


def test_enforce_ebook_files_file_not_found(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    mock_ebook_enforcer: MagicMock,
    tmp_path: Path,
) -> None:
    """Test _enforce_ebook_files when ebook file not found."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    with patch(
        "fundamental.repositories.calibre_book_repository.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [data_record]
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = MetadataEnforcementService(
            session,  # type: ignore[arg-type]
            library,
            ebook_enforcers=[mock_ebook_enforcer],
        )

        with patch.object(
            service._path_resolver, "get_library_root", return_value=library_root
        ):
            any_updated, formats = service._enforce_ebook_files(book_with_rels)
            assert any_updated is False
            assert formats == []


def test_enforce_ebook_files_success(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    mock_ebook_enforcer: MagicMock,
    tmp_path: Path,
) -> None:
    """Test _enforce_ebook_files with successful enforcement."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    ebook_file = book_dir / "test.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    with patch(
        "fundamental.repositories.calibre_book_repository.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [data_record]
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = MetadataEnforcementService(
            session,  # type: ignore[arg-type]
            library,
            ebook_enforcers=[mock_ebook_enforcer],
        )

        with patch.object(
            service._path_resolver, "get_library_root", return_value=library_root
        ):
            any_updated, formats = service._enforce_ebook_files(book_with_rels)
            assert any_updated is True
            assert "epub" in formats
            mock_ebook_enforcer.enforce_metadata.assert_called_once()


def test_enforce_ebook_files_exception(
    session: DummySession,
    library: Library,
    book_with_rels: BookWithFullRelations,
    mock_ebook_enforcer: MagicMock,
    tmp_path: Path,
) -> None:
    """Test _enforce_ebook_files with exception."""
    library_root = tmp_path / "library"
    library_root.mkdir()
    book_dir = library_root / book_with_rels.book.path
    book_dir.mkdir(parents=True)
    ebook_file = book_dir / "test.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    mock_ebook_enforcer.enforce_metadata.side_effect = Exception("Enforce error")

    with patch(
        "fundamental.repositories.calibre_book_repository.CalibreBookRepository"
    ) as mock_repo_class:
        mock_repo = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [data_record]
        mock_repo.get_session.return_value.__enter__.return_value = mock_session
        mock_repo.get_session.return_value.__exit__.return_value = None
        mock_repo_class.return_value = mock_repo

        service = MetadataEnforcementService(
            session,  # type: ignore[arg-type]
            library,
            ebook_enforcers=[mock_ebook_enforcer],
        )

        with patch.object(
            service._path_resolver, "get_library_root", return_value=library_root
        ):
            any_updated, formats = service._enforce_ebook_files(book_with_rels)
            assert any_updated is False
            assert formats == []


def test_find_ebook_file_primary(
    session: DummySession, library: Library, tmp_path: Path
) -> None:
    """Test _find_ebook_file with primary path."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    ebook_file = book_dir / "test.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    service = MetadataEnforcementService(session, library)  # type: ignore[arg-type]
    result = service._find_ebook_file(book_dir, 1, data_record)
    assert result == ebook_file


def test_find_ebook_file_alternative(
    session: DummySession, library: Library, tmp_path: Path
) -> None:
    """Test _find_ebook_file with alternative path."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    ebook_file = book_dir / "1.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="other")

    service = MetadataEnforcementService(session, library)  # type: ignore[arg-type]
    result = service._find_ebook_file(book_dir, 1, data_record)
    assert result == ebook_file


def test_find_ebook_file_by_extension(
    session: DummySession, library: Library, tmp_path: Path
) -> None:
    """Test _find_ebook_file by extension."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    ebook_file = book_dir / "random.epub"
    ebook_file.write_text("test")

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name=None)

    service = MetadataEnforcementService(session, library)  # type: ignore[arg-type]
    result = service._find_ebook_file(book_dir, 1, data_record)
    assert result == ebook_file


def test_find_ebook_file_not_found(
    session: DummySession, library: Library, tmp_path: Path
) -> None:
    """Test _find_ebook_file when file not found."""
    book_dir = tmp_path / "book"
    book_dir.mkdir()

    data_record = Data(id=1, book=1, format="EPUB", uncompressed_size=100, name="test")

    service = MetadataEnforcementService(session, library)  # type: ignore[arg-type]
    result = service._find_ebook_file(book_dir, 1, data_record)
    assert result is None
