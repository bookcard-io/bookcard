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

"""Additional tests for repository facade to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bookcard.repositories.calibre.repository import CalibreBookRepository

if TYPE_CHECKING:
    from sqlmodel import Session


class TestCalibreBookRepositoryAdditional:
    """Additional tests for CalibreBookRepository to achieve 100% coverage."""

    def test_list_books_with_filters_delegation(
        self, in_memory_db: Session, temp_library_path: Path
    ) -> None:
        """Test list_books_with_filters delegates to reads."""
        # Create the database file
        temp_library_path.mkdir(parents=True, exist_ok=True)
        db_path = temp_library_path / "metadata.db"
        db_path.touch()

        from tests.repositories.calibre.conftest import MockSessionManager

        session_manager = MockSessionManager(in_memory_db)
        repo = CalibreBookRepository(
            calibre_db_path=str(temp_library_path),
            session_manager=session_manager,
        )
        result = repo.list_books_with_filters()
        assert isinstance(result, list)

    def test_count_books_with_filters_delegation(
        self, in_memory_db: Session, temp_library_path: Path
    ) -> None:
        """Test count_books_with_filters delegates to reads."""
        # Create the database file
        temp_library_path.mkdir(parents=True, exist_ok=True)
        db_path = temp_library_path / "metadata.db"
        db_path.touch()

        from tests.repositories.calibre.conftest import MockSessionManager

        session_manager = MockSessionManager(in_memory_db)
        repo = CalibreBookRepository(
            calibre_db_path=str(temp_library_path),
            session_manager=session_manager,
        )
        result = repo.count_books_with_filters()
        assert isinstance(result, int)

    def test_add_book_delegation(
        self, in_memory_db: Session, temp_library_path: Path
    ) -> None:
        """Test add_book delegates to writes."""
        repo = CalibreBookRepository(
            calibre_db_path=str(temp_library_path / "metadata.db")
        )
        # This will fail because file doesn't exist, but tests delegation
        with pytest.raises((ValueError, FileNotFoundError)):
            repo.add_book(
                file_path=Path("/nonexistent/file.epub"),
                file_format="epub",
            )

    def test_add_format_delegation(
        self, in_memory_db: Session, temp_library_path: Path
    ) -> None:
        """Test add_format delegates to formats."""
        # Create the database file
        temp_library_path.mkdir(parents=True, exist_ok=True)
        db_path = temp_library_path / "metadata.db"
        db_path.touch()

        from tests.repositories.calibre.conftest import MockSessionManager

        session_manager = MockSessionManager(in_memory_db)
        repo = CalibreBookRepository(
            calibre_db_path=str(temp_library_path),
            session_manager=session_manager,
        )
        # This will fail because file doesn't exist, but tests delegation
        with pytest.raises(ValueError, match=r"File not found|not found"):
            repo.add_format(
                book_id=999,
                file_path=Path("/nonexistent/file.epub"),
                file_format="epub",
            )

    def test_delete_format_delegation(
        self, in_memory_db: Session, temp_library_path: Path
    ) -> None:
        """Test delete_format delegates to formats."""

        # Create the database file in the library directory
        temp_library_path.mkdir(parents=True, exist_ok=True)
        db_path = temp_library_path / "metadata.db"
        db_path.touch()

        from tests.repositories.calibre.conftest import MockSessionManager

        session_manager = MockSessionManager(in_memory_db)
        repo = CalibreBookRepository(
            calibre_db_path=str(temp_library_path),
            session_manager=session_manager,
        )
        # This will fail because book doesn't exist, but tests delegation
        with pytest.raises(ValueError, match=r"book_not_found|not found"):
            repo.delete_format(book_id=999, file_format="epub")

    def test_delete_book_delegation(
        self, in_memory_db: Session, temp_library_path: Path
    ) -> None:
        """Test delete_book delegates to deletion."""
        # Create the database file in the library directory
        temp_library_path.mkdir(parents=True, exist_ok=True)
        db_path = temp_library_path / "metadata.db"
        db_path.touch()

        from tests.repositories.calibre.conftest import MockSessionManager

        session_manager = MockSessionManager(in_memory_db)
        repo = CalibreBookRepository(
            calibre_db_path=str(temp_library_path),
            session_manager=session_manager,
        )
        # This will fail because book doesn't exist, but tests delegation
        with pytest.raises(ValueError, match=r"book_not_found|not found"):
            repo.delete_book(book_id=999)
