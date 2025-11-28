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

"""Tests for file discovery service to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from fundamental.services.ingest.file_discovery_service import (
    FileDiscoveryService,
    FileGroup,
)


@pytest.fixture
def service() -> FileDiscoveryService:
    """Create FileDiscoveryService instance."""
    return FileDiscoveryService(
        supported_formats=["epub", "pdf", "mobi"],
        ignore_patterns=["*.tmp", "*.bak"],
    )


@pytest.fixture
def service_no_ignore() -> FileDiscoveryService:
    """Create FileDiscoveryService without ignore patterns."""
    return FileDiscoveryService(supported_formats=["epub", "pdf"])


@pytest.mark.parametrize(
    ("formats", "ignore_patterns"),
    [
        (["epub", "pdf"], None),
        (["epub", "pdf"], []),
        (["epub", "pdf"], ["*.tmp"]),
        ([".epub", ".pdf"], None),  # Test with dots
        (["EPUB", "PDF"], None),  # Test case insensitivity
    ],
)
def test_init(formats: list[str], ignore_patterns: list[str] | None) -> None:
    """Test FileDiscoveryService initialization."""
    service = FileDiscoveryService(
        supported_formats=formats, ignore_patterns=ignore_patterns
    )
    assert service._supported_formats == {fmt.lower().lstrip(".") for fmt in formats}
    assert service._ignore_patterns == (ignore_patterns or [])


def test_discover_files_not_exists(
    temp_dir: Path, service: FileDiscoveryService
) -> None:
    """Test discover_files raises FileNotFoundError when directory doesn't exist."""
    non_existent = temp_dir / "nonexistent"
    with pytest.raises(FileNotFoundError, match="Ingest directory does not exist"):
        service.discover_files(non_existent)


def test_discover_files_not_directory(
    temp_dir: Path, service: FileDiscoveryService
) -> None:
    """Test discover_files raises ValueError when path is not a directory."""
    file_path = temp_dir / "file.txt"
    file_path.touch()
    with pytest.raises(ValueError, match="Ingest path is not a directory"):
        service.discover_files(file_path)


def test_discover_files_empty(temp_dir: Path, service: FileDiscoveryService) -> None:
    """Test discover_files with empty directory."""
    result = service.discover_files(temp_dir)
    assert result == []


def test_discover_files_supported_formats(
    temp_dir: Path, service: FileDiscoveryService
) -> None:
    """Test discover_files finds supported formats."""
    (temp_dir / "book1.epub").touch()
    (temp_dir / "book2.pdf").touch()
    (temp_dir / "book3.mobi").touch()
    (temp_dir / "book4.txt").touch()  # Not supported

    result = service.discover_files(temp_dir)
    assert len(result) == 3
    assert all(f.suffix.lower() in [".epub", ".pdf", ".mobi"] for f in result)


def test_discover_files_ignores_patterns(
    temp_dir: Path, service: FileDiscoveryService
) -> None:
    """Test discover_files ignores files matching patterns."""
    (temp_dir / "book.epub").touch()
    (temp_dir / "book.tmp").touch()
    (temp_dir / "backup.bak").touch()

    result = service.discover_files(temp_dir)
    assert len(result) == 1
    assert result[0].name == "book.epub"


def test_discover_files_recursive(
    temp_dir: Path, service: FileDiscoveryService
) -> None:
    """Test discover_files recursively scans subdirectories."""
    (temp_dir / "book1.epub").touch()
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "book2.epub").touch()

    result = service.discover_files(temp_dir)
    assert len(result) == 2


def test_is_book_file(service: FileDiscoveryService, temp_dir: Path) -> None:
    """Test _is_book_file method."""
    epub_file = temp_dir / "book.epub"
    epub_file.touch()
    txt_file = temp_dir / "book.txt"
    txt_file.touch()
    no_ext = temp_dir / "book"
    no_ext.touch()

    assert service._is_book_file(epub_file) is True
    assert service._is_book_file(txt_file) is False
    assert service._is_book_file(no_ext) is False


@pytest.mark.parametrize(
    ("filename", "pattern", "expected"),
    [
        ("test.tmp", "*.tmp", True),
        ("test.bak", "*.bak", True),
        ("test.epub", "*.tmp", False),
        ("backup.bak", "*.bak", True),
        ("test.txt", "*.tmp", False),
    ],
)
def test_should_ignore(
    service: FileDiscoveryService,
    temp_dir: Path,
    filename: str,
    pattern: str,
    expected: bool,
) -> None:
    """Test _should_ignore method."""
    file_path = temp_dir / filename
    file_path.touch()
    service._ignore_patterns = [pattern]
    assert service._should_ignore(file_path) == expected


def test_should_ignore_no_patterns(
    service_no_ignore: FileDiscoveryService, temp_dir: Path
) -> None:
    """Test _should_ignore returns False when no patterns."""
    file_path = temp_dir / "test.tmp"
    file_path.touch()
    assert service_no_ignore._should_ignore(file_path) is False


def test_group_files_by_directory(
    service: FileDiscoveryService, temp_dir: Path
) -> None:
    """Test group_files_by_directory method."""
    dir1 = temp_dir / "dir1"
    dir1.mkdir()
    dir2 = temp_dir / "dir2"
    dir2.mkdir()

    file1 = dir1 / "book1.epub"
    file1.touch()
    file2 = dir1 / "book2.pdf"
    file2.touch()
    file3 = dir2 / "book3.epub"
    file3.touch()

    files = [file1, file2, file3]
    groups = service.group_files_by_directory(files)

    assert len(groups) == 2
    assert any(len(g.files) == 2 for g in groups)
    assert any(len(g.files) == 1 for g in groups)


def test_create_book_key_from_path_file(
    service: FileDiscoveryService, temp_dir: Path
) -> None:
    """Test _create_book_key_from_path with file path."""
    # Create a subdirectory with a name we can test
    book_dir = temp_dir / "My Book"
    book_dir.mkdir()
    file_path = book_dir / "book.epub"
    file_path.touch()
    key = service._create_book_key_from_path(file_path)
    assert key == "my_book"  # Uses parent directory name


def test_create_book_key_from_path_directory(
    service: FileDiscoveryService, temp_dir: Path
) -> None:
    """Test _create_book_key_from_path with directory path."""
    dir_path = temp_dir / "My Book Dir"
    dir_path.mkdir()
    key = service._create_book_key_from_path(dir_path)
    assert key == "my_book_dir"


def test_create_book_key_from_path_special_chars(
    service: FileDiscoveryService, temp_dir: Path
) -> None:
    """Test _create_book_key_from_path removes special characters."""
    # Create a subdirectory with special characters
    book_dir = temp_dir / "Book@#$%^&*()"
    book_dir.mkdir()
    file_path = book_dir / "book.epub"
    file_path.touch()
    key = service._create_book_key_from_path(file_path)
    assert key == "book"  # Special chars removed from parent dir name


def test_create_book_key_from_path_empty(
    service: FileDiscoveryService, temp_dir: Path
) -> None:
    """Test _create_book_key_from_path returns 'unknown' for empty key."""
    # Create a subdirectory with only special characters (no alphanumeric)
    book_dir = temp_dir / "@#$%"
    book_dir.mkdir()
    file_path = book_dir / "book.epub"
    file_path.touch()
    key = service._create_book_key_from_path(file_path)
    assert key == "unknown"  # All special chars removed, empty key


def test_file_group_defaults() -> None:
    """Test FileGroup default values."""
    group = FileGroup(book_key="test", files=[])
    assert group.book_key == "test"
    assert group.files == []
    assert group.metadata_hint is None
