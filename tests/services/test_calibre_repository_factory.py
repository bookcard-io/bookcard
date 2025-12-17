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

"""Tests for CalibreRepositoryFactory to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.config import Library
from bookcard.repositories.calibre_book_repository import CalibreBookRepository
from bookcard.services.author_merge.calibre_repository_factory import (
    CalibreRepositoryFactory,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def library_with_path() -> Library:
    """Create library with Calibre database path."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def library_without_path() -> Library:
    """Create library without Calibre database path."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path=None,
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def library_empty_path() -> Library:
    """Create library with empty Calibre database path."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="",
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def library_none() -> None:
    """Create None library."""
    return


# ============================================================================
# create Tests
# ============================================================================


class TestCalibreRepositoryFactoryCreate:
    """Test CalibreRepositoryFactory.create method."""

    def test_create_with_valid_library(
        self,
        library_with_path: Library,
    ) -> None:
        """Test create with valid library."""
        with patch(
            "bookcard.services.author_merge.calibre_repository_factory.CalibreBookRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock(spec=CalibreBookRepository)
            mock_repo_class.return_value = mock_repo

            result = CalibreRepositoryFactory.create(library_with_path)

            assert result == mock_repo
            mock_repo_class.assert_called_once_with(
                calibre_db_path="/path/to/library",
                calibre_db_file="metadata.db",
            )

    def test_create_without_db_path(
        self,
        library_without_path: Library,
    ) -> None:
        """Test create with library without database path."""
        result = CalibreRepositoryFactory.create(library_without_path)

        assert result is None

    def test_create_with_empty_db_path(
        self,
        library_empty_path: Library,
    ) -> None:
        """Test create with library with empty database path."""
        result = CalibreRepositoryFactory.create(library_empty_path)

        assert result is None

    def test_create_with_none_library(
        self,
        library_none: None,
    ) -> None:
        """Test create with None library."""
        result = CalibreRepositoryFactory.create(library_none)

        assert result is None

    def test_create_with_custom_db_file(
        self,
    ) -> None:
        """Test create with custom database file."""
        library = Library(
            id=1,
            name="Test Library",
            calibre_db_path="/path/to/library",
            calibre_db_file="custom.db",
            is_active=True,
        )

        with patch(
            "bookcard.services.author_merge.calibre_repository_factory.CalibreBookRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock(spec=CalibreBookRepository)
            mock_repo_class.return_value = mock_repo

            result = CalibreRepositoryFactory.create(library)

            assert result == mock_repo
            mock_repo_class.assert_called_once_with(
                calibre_db_path="/path/to/library",
                calibre_db_file="custom.db",
            )
