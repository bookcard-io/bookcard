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

"""Tests for CalibreAuthorService to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.models.core import Author, BookAuthorLink
from fundamental.repositories.calibre_book_repository import CalibreBookRepository
from fundamental.services.author_merge.calibre_author_service import (
    CalibreAuthorService,
)
from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_calibre_repo() -> MagicMock:
    """Create a mock Calibre repository."""
    return MagicMock(spec=CalibreBookRepository)


@pytest.fixture
def calibre_session() -> DummySession:
    """Create a dummy Calibre session."""
    return DummySession()


@pytest.fixture
def calibre_author_service(mock_calibre_repo: MagicMock) -> CalibreAuthorService:
    """Create CalibreAuthorService instance."""
    return CalibreAuthorService(calibre_repo=mock_calibre_repo)


@pytest.fixture
def book_author_link() -> BookAuthorLink:
    """Create sample book author link."""
    return BookAuthorLink(book=1, author=1)


@pytest.fixture
def calibre_author() -> Author:
    """Create sample Calibre author."""
    return Author(id=1, name="Test Author", sort="Author, Test")


# ============================================================================
# Initialization Tests
# ============================================================================


class TestCalibreAuthorServiceInit:
    """Test CalibreAuthorService initialization."""

    def test_init(self, mock_calibre_repo: MagicMock) -> None:
        """Test __init__ stores repository."""
        service = CalibreAuthorService(calibre_repo=mock_calibre_repo)

        assert service._calibre_repo == mock_calibre_repo


# ============================================================================
# get_book_count Tests
# ============================================================================


class TestGetBookCount:
    """Test get_book_count method."""

    def test_get_book_count_zero(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
    ) -> None:
        """Test get_book_count with zero books."""
        calibre_author_id = 1

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([])

        result = calibre_author_service.get_book_count(calibre_author_id)

        assert result == 0

    def test_get_book_count_multiple(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
        book_author_link: BookAuthorLink,
    ) -> None:
        """Test get_book_count with multiple books."""
        calibre_author_id = 1

        link1 = BookAuthorLink(book=1, author=calibre_author_id)
        link2 = BookAuthorLink(book=2, author=calibre_author_id)
        link3 = BookAuthorLink(book=3, author=calibre_author_id)

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([link1, link2, link3])

        result = calibre_author_service.get_book_count(calibre_author_id)

        assert result == 3

    def test_get_book_count_one(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
        book_author_link: BookAuthorLink,
    ) -> None:
        """Test get_book_count with one book."""
        calibre_author_id = 1

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([book_author_link])

        result = calibre_author_service.get_book_count(calibre_author_id)

        assert result == 1


# ============================================================================
# reassign_books Tests
# ============================================================================


class TestReassignBooks:
    """Test reassign_books method."""

    def test_reassign_books_no_existing_link(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
    ) -> None:
        """Test reassign_books when keep author has no existing link."""
        from_author_id = 1
        to_author_id = 2

        link = BookAuthorLink(book=1, author=from_author_id)

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([link])  # merge links
        calibre_session.add_exec_result([])  # existing link check

        calibre_author_service.reassign_books(from_author_id, to_author_id)

        assert link.author == to_author_id
        assert link in calibre_session.added
        assert calibre_session.commit_count == 1

    def test_reassign_books_existing_link(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
    ) -> None:
        """Test reassign_books when keep author already has link."""
        from_author_id = 1
        to_author_id = 2

        merge_link = BookAuthorLink(book=1, author=from_author_id)
        existing_link = BookAuthorLink(book=1, author=to_author_id)

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([merge_link])  # merge links
        calibre_session.add_exec_result([existing_link])  # existing link check

        calibre_author_service.reassign_books(from_author_id, to_author_id)

        assert merge_link in calibre_session.deleted
        assert merge_link.author == from_author_id  # Not changed
        assert calibre_session.commit_count == 1

    def test_reassign_books_multiple_links(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
    ) -> None:
        """Test reassign_books with multiple book links."""
        from_author_id = 1
        to_author_id = 2

        link1 = BookAuthorLink(book=1, author=from_author_id)
        link2 = BookAuthorLink(book=2, author=from_author_id)
        link3 = BookAuthorLink(book=3, author=from_author_id)

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([link1, link2, link3])  # merge links
        calibre_session.add_exec_result([])  # existing link check for link1
        calibre_session.add_exec_result([])  # existing link check for link2
        calibre_session.add_exec_result([])  # existing link check for link3

        calibre_author_service.reassign_books(from_author_id, to_author_id)

        assert link1.author == to_author_id
        assert link2.author == to_author_id
        assert link3.author == to_author_id
        assert calibre_session.commit_count == 1

    def test_reassign_books_mixed_existing(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
    ) -> None:
        """Test reassign_books with some existing links."""
        from_author_id = 1
        to_author_id = 2

        link1 = BookAuthorLink(book=1, author=from_author_id)
        link2 = BookAuthorLink(book=2, author=from_author_id)
        existing_link = BookAuthorLink(book=2, author=to_author_id)

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([link1, link2])  # merge links
        calibre_session.add_exec_result([])  # existing link check for link1
        calibre_session.add_exec_result([
            existing_link
        ])  # existing link check for link2

        calibre_author_service.reassign_books(from_author_id, to_author_id)

        assert link1.author == to_author_id
        assert link2 in calibre_session.deleted
        assert calibre_session.commit_count == 1

    def test_reassign_books_no_links(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
    ) -> None:
        """Test reassign_books with no links to reassign."""
        from_author_id = 1
        to_author_id = 2

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([])  # merge links

        calibre_author_service.reassign_books(from_author_id, to_author_id)

        assert len(calibre_session.added) == 0
        assert len(calibre_session.deleted) == 0
        assert calibre_session.commit_count == 1


# ============================================================================
# delete_author Tests
# ============================================================================


class TestDeleteAuthor:
    """Test delete_author method."""

    def test_delete_author_exists(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
        calibre_author: Author,
    ) -> None:
        """Test delete_author when author exists."""
        calibre_author_id = 1

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([calibre_author])

        calibre_author_service.delete_author(calibre_author_id)

        assert calibre_author in calibre_session.deleted
        assert calibre_session.commit_count == 1

    def test_delete_author_not_exists(
        self,
        calibre_author_service: CalibreAuthorService,
        mock_calibre_repo: MagicMock,
        calibre_session: DummySession,
    ) -> None:
        """Test delete_author when author does not exist."""
        calibre_author_id = 999

        mock_calibre_repo.get_session.return_value.__enter__.return_value = (
            calibre_session
        )
        mock_calibre_repo.get_session.return_value.__exit__.return_value = None
        calibre_session.set_exec_result([])

        calibre_author_service.delete_author(calibre_author_id)

        assert len(calibre_session.deleted) == 0
        # When author doesn't exist, commit is not called
        assert calibre_session.commit_count == 0
