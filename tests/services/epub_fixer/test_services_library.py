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

"""Tests for library locator service."""

from pathlib import Path

from fundamental.models.config import Library
from fundamental.services.epub_fixer.services.library import LibraryLocator


def test_library_locator_library_root() -> None:
    """Test LibraryLocator uses library_root when provided."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/metadata.db",
        library_root="/custom/library/root",
    )

    locator = LibraryLocator(library)
    location = locator.get_location()

    assert location == Path(library.library_root)


def test_library_locator_split_library() -> None:
    """Test LibraryLocator uses split_library_dir when enabled."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/metadata.db",
        use_split_library=True,
        split_library_dir="/split/library/dir",
    )

    locator = LibraryLocator(library)
    location = locator.get_location()

    assert location == Path(library.split_library_dir)


def test_library_locator_split_library_priority() -> None:
    """Test LibraryLocator prioritizes library_root over split_library_dir."""
    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/metadata.db",
        library_root="/custom/library/root",
        use_split_library=True,
        split_library_dir="/split/library/dir",
    )

    locator = LibraryLocator(library)
    location = locator.get_location()

    # library_root should take priority
    assert location == Path(library.library_root)


def test_library_locator_calibre_db_path_dir(temp_dir: Path) -> None:
    """Test LibraryLocator uses calibre_db_path when it's a directory."""
    # Create actual directory for is_dir() check
    library_dir = temp_dir / "library"
    library_dir.mkdir()

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path=str(library_dir),  # Directory path
    )

    locator = LibraryLocator(library)
    location = locator.get_location()

    assert location == library_dir


def test_library_locator_calibre_db_path_file(temp_dir: Path) -> None:
    """Test LibraryLocator uses parent of calibre_db_path when it's a file."""
    # Create actual file for is_dir() check
    db_file = temp_dir / "metadata.db"
    db_file.write_text("test")

    library = Library(
        id=1,
        name="Test Library",
        calibre_db_path=str(db_file),  # File path
    )

    locator = LibraryLocator(library)
    location = locator.get_location()

    # Should return parent directory
    assert location == db_file.parent
