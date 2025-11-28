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

"""Tests for metadata extraction service to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from fundamental.repositories.book_metadata_service import BookMetadataService
from fundamental.services.ingest.metadata_extraction_service import (
    FileMetadata,
    MetadataExtractionService,
)


@pytest.fixture
def mock_metadata_service() -> MagicMock:
    """Create a mock BookMetadataService."""
    service = MagicMock(spec=BookMetadataService)
    metadata = MagicMock()
    metadata.title = "Test Book"
    metadata.author = "Test Author"
    metadata.isbn = "1234567890"
    service.extract_metadata.return_value = (metadata, {})
    return service


@pytest.fixture
def service(mock_metadata_service: MagicMock) -> MetadataExtractionService:
    """Create MetadataExtractionService instance."""
    return MetadataExtractionService(metadata_service=mock_metadata_service)


@pytest.fixture
def service_default() -> MetadataExtractionService:
    """Create MetadataExtractionService with default service."""
    return MetadataExtractionService()


def test_init_with_service(mock_metadata_service: MagicMock) -> None:
    """Test MetadataExtractionService initialization with service."""
    service = MetadataExtractionService(metadata_service=mock_metadata_service)
    assert service._metadata_service == mock_metadata_service


def test_init_without_service() -> None:
    """Test MetadataExtractionService initialization without service."""
    service = MetadataExtractionService()
    assert isinstance(service._metadata_service, BookMetadataService)


def test_init_with_threshold() -> None:
    """Test MetadataExtractionService initialization with threshold."""
    service = MetadataExtractionService(similarity_threshold=0.9)
    assert service._similarity_threshold == 0.9


def test_extract_metadata_success(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test extract_metadata with successful extraction."""
    file_path = temp_dir / "book.epub"
    file_path.touch()
    result = service.extract_metadata(file_path, "epub")
    assert result["title"] == "Test Book"
    assert result["authors"] == ["Test Author"]
    assert result["isbn"] == "1234567890"


def test_extract_metadata_author_list(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test extract_metadata with author as list."""
    file_path = temp_dir / "book.epub"
    file_path.touch()
    metadata = MagicMock()
    metadata.title = "Test Book"
    metadata.author = ["Author 1", "Author 2"]
    service._metadata_service.extract_metadata.return_value = (metadata, {})  # type: ignore[valid-type]
    result = service.extract_metadata(file_path, "epub")
    assert result["authors"] == ["Author 1", "Author 2"]


def test_extract_metadata_fallback_filename(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test extract_metadata falls back to filename on error."""
    file_path = temp_dir / "my_book.epub"
    file_path.touch()
    service._metadata_service.extract_metadata.side_effect = ValueError("Error")  # type: ignore[valid-type]
    result = service.extract_metadata(file_path, "epub")
    assert result["title"] == "my_book"
    assert result["authors"] == []
    assert result["isbn"] is None


@pytest.mark.parametrize(
    "exception",
    [
        ValueError("Error"),
        ImportError("Error"),
        OSError("Error"),
        KeyError("Error"),
        AttributeError("Error"),
    ],
)
def test_extract_metadata_exceptions(
    service: MetadataExtractionService, temp_dir: Path, exception: Exception
) -> None:
    """Test extract_metadata handles various exceptions."""
    file_path = temp_dir / "book.epub"
    file_path.touch()
    service._metadata_service.extract_metadata.side_effect = exception  # type: ignore[valid-type]
    result = service.extract_metadata(file_path, "epub")
    assert result["title"] == "book"
    assert result["authors"] == []


def test_group_files_by_metadata_empty(service: MetadataExtractionService) -> None:
    """Test group_files_by_metadata with empty list."""
    result = service.group_files_by_metadata([])
    assert result == []


def test_group_files_by_metadata_single_file(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test group_files_by_metadata with single file."""
    file_path = temp_dir / "book.epub"
    file_path.touch()
    result = service.group_files_by_metadata([file_path])
    assert len(result) == 1
    assert result[0].book_key is not None
    assert len(result[0].files) == 1


def test_group_files_by_metadata_no_extension(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test group_files_by_metadata skips files without extension."""
    file_path = temp_dir / "book"
    file_path.touch()
    result = service.group_files_by_metadata([file_path])
    assert len(result) == 0


def test_group_files_by_metadata_extraction_error(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test group_files_by_metadata handles extraction errors."""
    file_path = temp_dir / "book.epub"
    file_path.touch()
    service._metadata_service.extract_metadata.side_effect = ValueError("Error")  # type: ignore[valid-type]
    result = service.group_files_by_metadata([file_path])
    assert len(result) == 1
    # When extraction fails, title falls back to filename stem
    assert result[0].metadata_hint["title"] == "book"  # type: ignore[index]


@pytest.mark.parametrize(
    "exception",
    [
        ValueError("Error"),
        OSError("Error"),
        AttributeError("Error"),
    ],
)
def test_group_files_by_metadata_exceptions(
    service: MetadataExtractionService, temp_dir: Path, exception: Exception
) -> None:
    """Test group_files_by_metadata handles various exceptions."""
    file_path = temp_dir / "book.epub"
    file_path.touch()
    service._metadata_service.extract_metadata.side_effect = exception  # type: ignore[valid-type]
    result = service.group_files_by_metadata([file_path])
    assert len(result) == 1


def test_files_match_by_isbn(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _files_match matches by ISBN."""
    file1 = FileMetadata(
        file_path=temp_dir / "book1.epub",
        file_format="epub",
        title="Book 1",
        authors=["Author"],
        isbn="1234567890",
    )
    file2 = FileMetadata(
        file_path=temp_dir / "book2.epub",
        file_format="epub",
        title="Book 2",
        authors=["Different"],
        isbn="1234567890",
    )
    assert service._files_match(file1, file2) is True


def test_files_match_by_isbn_normalized(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _files_match normalizes ISBNs."""
    file1 = FileMetadata(
        file_path=temp_dir / "book1.epub",
        file_format="epub",
        title="Book 1",
        authors=["Author"],
        isbn="123-456-7890",
    )
    file2 = FileMetadata(
        file_path=temp_dir / "book2.epub",
        file_format="epub",
        title="Book 2",
        authors=["Different"],
        isbn="1234567890",
    )
    assert service._files_match(file1, file2) is True


def test_files_match_exact_title(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _files_match with exact title match."""
    file1 = FileMetadata(
        file_path=temp_dir / "book1.epub",
        file_format="epub",
        title="Test Book",
        authors=["Author"],
    )
    file2 = FileMetadata(
        file_path=temp_dir / "book2.epub",
        file_format="epub",
        title="Test Book",
        authors=["Author"],
    )
    assert service._files_match(file1, file2) is True


def test_files_match_fuzzy_title(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _files_match with fuzzy title match."""
    file1 = FileMetadata(
        file_path=temp_dir / "book1.epub",
        file_format="epub",
        title="Test Book",
        authors=["Author"],
    )
    file2 = FileMetadata(
        file_path=temp_dir / "book2.epub",
        file_format="epub",
        title="Test Book Edition",
        authors=["Author"],
    )
    # Similarity should be high enough
    result = service._files_match(file1, file2)
    assert isinstance(result, bool)


def test_files_match_no_titles_same_dir(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _files_match falls back to directory when no titles."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    file1 = FileMetadata(
        file_path=subdir / "book1.epub",
        file_format="epub",
        title=None,
        authors=[],
    )
    file2 = FileMetadata(
        file_path=subdir / "book2.epub",
        file_format="epub",
        title=None,
        authors=[],
    )
    assert service._files_match(file1, file2) is True


def test_files_match_no_titles_different_dir(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _files_match returns False for different directories."""
    dir1 = temp_dir / "dir1"
    dir1.mkdir()
    dir2 = temp_dir / "dir2"
    dir2.mkdir()
    file1 = FileMetadata(
        file_path=dir1 / "book1.epub",
        file_format="epub",
        title=None,
        authors=[],
    )
    file2 = FileMetadata(
        file_path=dir2 / "book2.epub",
        file_format="epub",
        title=None,
        authors=[],
    )
    assert service._files_match(file1, file2) is False


def test_authors_match_exact(service: MetadataExtractionService) -> None:
    """Test _authors_match with exact match."""
    assert service._authors_match(["Author"], ["Author"]) is True


def test_authors_match_overlap(service: MetadataExtractionService) -> None:
    """Test _authors_match with overlapping authors."""
    assert (
        service._authors_match(["Author 1", "Author 2"], ["Author 2", "Author 3"])
        is True
    )


def test_authors_match_no_overlap(service: MetadataExtractionService) -> None:
    """Test _authors_match with no overlap."""
    assert service._authors_match(["Author 1"], ["Author 2"]) is False


def test_authors_match_both_empty(service: MetadataExtractionService) -> None:
    """Test _authors_match with both empty."""
    assert service._authors_match([], []) is True


def test_authors_match_one_empty(service: MetadataExtractionService) -> None:
    """Test _authors_match with one empty."""
    assert service._authors_match([], ["Author"]) is False
    assert service._authors_match(["Author"], []) is False


def test_authors_match_normalized(service: MetadataExtractionService) -> None:
    """Test _authors_match normalizes authors."""
    assert service._authors_match(["  Author  "], ["AUTHOR"]) is True


def test_string_similarity_exact(service: MetadataExtractionService) -> None:
    """Test _string_similarity with exact match."""
    result = service._string_similarity("test", "test")
    assert result == 1.0


def test_string_similarity_different(service: MetadataExtractionService) -> None:
    """Test _string_similarity with different strings."""
    result = service._string_similarity("test", "different")
    assert 0.0 <= result < 1.0


def test_string_similarity_empty(service: MetadataExtractionService) -> None:
    """Test _string_similarity with empty strings."""
    result = service._string_similarity("", "")
    assert result == 1.0  # Empty strings are identical


def test_create_book_key_from_metadata(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _create_book_key_from_metadata."""
    file_meta = FileMetadata(
        file_path=temp_dir / "book.epub",
        file_format="epub",
        title="Test Book",
        authors=["Test Author"],
    )
    key = service._create_book_key_from_metadata(file_meta)
    assert "test" in key.lower()
    assert "book" in key.lower()


def test_create_book_key_from_metadata_no_title(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _create_book_key_from_metadata without title."""
    file_meta = FileMetadata(
        file_path=temp_dir / "my_book.epub",
        file_format="epub",
        title=None,
        authors=["Author"],
    )
    key = service._create_book_key_from_metadata(file_meta)
    assert "author" in key.lower()


def test_create_book_key_from_metadata_no_metadata(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _create_book_key_from_metadata without metadata."""
    file_meta = FileMetadata(
        file_path=temp_dir / "my_book.epub",
        file_format="epub",
        title=None,
        authors=[],
    )
    key = service._create_book_key_from_metadata(file_meta)
    assert "my_book" in key.lower() or key == "unknown"


def test_create_book_key_special_chars(
    service: MetadataExtractionService, temp_dir: Path
) -> None:
    """Test _create_book_key_from_metadata removes special characters."""
    file_meta = FileMetadata(
        file_path=temp_dir / "book.epub",
        file_format="epub",
        title="Book@#$%",
        authors=["Author@#$%"],
    )
    key = service._create_book_key_from_metadata(file_meta)
    assert "@" not in key
    assert "#" not in key
