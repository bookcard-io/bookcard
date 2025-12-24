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

"""Tests for tracked book service to achieve 100% coverage."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import pytest

from bookcard.api.schemas.tracked_books import TrackedBookCreate, TrackedBookUpdate
from bookcard.models.config import Library
from bookcard.models.pvr import TrackedBook, TrackedBookStatus
from bookcard.services.tracked_book_service import (
    TrackedBookRepository,
    TrackedBookService,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from tests.conftest import DummySession


@pytest.fixture
def tracked_book() -> TrackedBook:
    """Create a tracked book for testing.

    Returns
    -------
    TrackedBook
        Tracked book instance.
    """
    return TrackedBook(
        id=1,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
        library_id=1,
        metadata_source_id="google",
        metadata_external_id="123",
        status=TrackedBookStatus.WANTED,
        auto_search_enabled=True,
        auto_download_enabled=False,
        preferred_formats=["epub"],
        matched_book_id=None,
        matched_library_id=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def library_config() -> Library:
    """Create a library configuration for testing.

    Returns
    -------
    Library
        Library configuration.
    """
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/tmp/calibre",
        library_root="/tmp/calibre",
    )


class TestTrackedBookRepository:
    """Test TrackedBookRepository class."""

    def test_repository_init(self, session: DummySession) -> None:
        """Test repository initialization.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        repo = TrackedBookRepository(cast("Session", session))
        assert repo._session == session
        assert repo._model_type == TrackedBook

    def test_list_by_status(
        self, session: DummySession, tracked_book: TrackedBook
    ) -> None:
        """Test list_by_status filters by status.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        repo = TrackedBookRepository(cast("Session", session))
        session.add_exec_result([tracked_book])

        result = repo.list_by_status(TrackedBookStatus.WANTED)

        assert len(result) == 1
        assert result[0].id == tracked_book.id
        assert result[0].status == TrackedBookStatus.WANTED

    def test_get_by_metadata_id(
        self, session: DummySession, tracked_book: TrackedBook
    ) -> None:
        """Test get_by_metadata_id returns book by metadata ID.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        repo = TrackedBookRepository(cast("Session", session))
        session.add_exec_result([tracked_book])

        result = repo.get_by_metadata_id("google", "123")

        assert result is not None
        assert result.id == tracked_book.id


class TestTrackedBookService:
    """Test TrackedBookService class."""

    def test_service_init_without_repository(self, session: DummySession) -> None:
        """Test service initialization without repository.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = TrackedBookService(cast("Session", session))
        assert service._session == session
        assert isinstance(service._repository, TrackedBookRepository)

    def test_service_init_with_repository(self, session: DummySession) -> None:
        """Test service initialization with repository.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        repo = TrackedBookRepository(cast("Session", session))
        service = TrackedBookService(cast("Session", session), repository=repo)
        assert service._session == session
        assert service._repository == repo

    def test_service_init_with_library_service(self, session: DummySession) -> None:
        """Test service initialization with library_service (covers line 134).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        from bookcard.services.config_service import LibraryService

        mock_library_service = MagicMock(spec=LibraryService)
        service = TrackedBookService(
            cast("Session", session), library_service=mock_library_service
        )
        assert service._session == session
        assert service._library_service == mock_library_service

    def test_create_tracked_book_success(
        self,
        session: DummySession,
        library_config: Library,
    ) -> None:
        """Test create_tracked_book creates new tracked book.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        library_config : Library
            Library configuration fixture.
        """
        service = TrackedBookService(cast("Session", session))
        create_data = TrackedBookCreate(
            title="New Book",
            author="New Author",
            metadata_source_id="google",
            metadata_external_id="new123",
        )

        with (
            patch.object(service._repository, "get_by_metadata_id", return_value=None),
            patch.object(service._repository, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
            patch.object(service, "_find_library_match") as mock_match,
        ):
            mock_match.return_value = (None, False)
            result = service.create_tracked_book(create_data)

            assert result.title == create_data.title
            assert result.status == TrackedBookStatus.WANTED
            assert result.matched_book_id is None
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

    def test_create_tracked_book_already_exists(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test create_tracked_book raises ValueError if already tracked.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Existing tracked book fixture.
        """
        service = TrackedBookService(cast("Session", session))
        create_data = TrackedBookCreate(
            title="Test Book",
            author="Test Author",
            metadata_source_id="google",
            metadata_external_id="123",
        )

        with (
            patch.object(
                service._repository, "get_by_metadata_id", return_value=tracked_book
            ),
            pytest.raises(ValueError, match="already being tracked"),
        ):
            service.create_tracked_book(create_data)

    def test_create_tracked_book_with_match(
        self,
        session: DummySession,
    ) -> None:
        """Test create_tracked_book with library match found.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = TrackedBookService(cast("Session", session))
        create_data = TrackedBookCreate(
            title="Matched Book",
            author="Author",
            library_id=1,
        )

        with (
            patch.object(service._repository, "get_by_metadata_id", return_value=None),
            patch.object(service._repository, "add"),
            patch.object(session, "commit"),
            patch.object(session, "refresh"),
            patch.object(service, "_find_library_match") as mock_match,
        ):
            # Match found with files
            mock_match.return_value = (100, True)
            result = service.create_tracked_book(create_data)

            assert result.matched_book_id == 100
            assert result.matched_library_id == 1
            assert result.status == TrackedBookStatus.COMPLETED

    def test_get_tracked_book(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test get_tracked_book returns book.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        service = TrackedBookService(cast("Session", session))
        session.set_get_result(TrackedBook, tracked_book)

        result = service.get_tracked_book(1)

        assert result is not None
        assert result.id == tracked_book.id

    def test_list_tracked_books(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test list_tracked_books returns list.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        service = TrackedBookService(cast("Session", session))

        # Test listing all
        with patch.object(service._repository, "list", return_value=[tracked_book]):
            result = service.list_tracked_books()
            assert len(result) == 1
            assert result[0].id == tracked_book.id

        # Test listing by status
        with patch.object(
            service._repository, "list_by_status", return_value=[tracked_book]
        ):
            result = service.list_tracked_books(status=TrackedBookStatus.WANTED)
            assert len(result) == 1
            assert result[0].status == TrackedBookStatus.WANTED

    def test_update_tracked_book(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test update_tracked_book updates fields.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        service = TrackedBookService(cast("Session", session))
        session.set_get_result(TrackedBook, tracked_book)
        update_data = TrackedBookUpdate(status=TrackedBookStatus.SEARCHING)

        with (
            patch.object(session, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
        ):
            result = service.update_tracked_book(1, update_data)

            assert result is not None
            assert result.status == TrackedBookStatus.SEARCHING
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

    def test_update_tracked_book_not_found(self, session: DummySession) -> None:
        """Test update_tracked_book returns None if not found (covers line 325).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = TrackedBookService(cast("Session", session))
        update_data = TrackedBookUpdate(status=TrackedBookStatus.SEARCHING)

        # Mock repository.get to return None for non-existent book
        with patch.object(service._repository, "get", return_value=None):
            result = service.update_tracked_book(999, update_data)

        assert result is None

    def test_delete_tracked_book(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test delete_tracked_book deletes book.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        service = TrackedBookService(cast("Session", session))
        session.set_get_result(TrackedBook, tracked_book)

        with (
            patch.object(service._repository, "delete") as mock_delete,
            patch.object(session, "commit") as mock_commit,
        ):
            result = service.delete_tracked_book(1)

            assert result is True
            mock_delete.assert_called_once()
            mock_commit.assert_called_once()

    def test_delete_tracked_book_not_found(self, session: DummySession) -> None:
        """Test delete_tracked_book returns False if not found.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = TrackedBookService(cast("Session", session))

        result = service.delete_tracked_book(999)

        assert result is False

    def test_check_status_not_found(self, session: DummySession) -> None:
        """Test check_status returns None when tracked book not found (covers line 325).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = TrackedBookService(cast("Session", session))

        with patch.object(service._repository, "get", return_value=None):
            result = service.check_status(999)

        assert result is None

    def test_check_status_no_change(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test check_status with no change in match.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        service = TrackedBookService(cast("Session", session))
        session.set_get_result(TrackedBook, tracked_book)

        # Same match status (None)
        with patch.object(
            service, "_find_library_match", return_value=(None, False)
        ) as mock_match:
            result = service.check_status(1)

            assert result is not None
            assert result.matched_book_id is None
            mock_match.assert_called_once()

    def test_check_status_new_match(
        self,
        session: DummySession,
        tracked_book: TrackedBook,
    ) -> None:
        """Test check_status with new match found.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        tracked_book : TrackedBook
            Tracked book fixture.
        """
        service = TrackedBookService(cast("Session", session))
        session.set_get_result(TrackedBook, tracked_book)

        with (
            patch.object(
                service, "_find_library_match", return_value=(100, True)
            ) as mock_match,
            patch.object(session, "add") as mock_add,
            patch.object(session, "commit") as mock_commit,
            patch.object(session, "refresh") as mock_refresh,
        ):
            result = service.check_status(1)

            assert result is not None
            assert result.matched_book_id == 100
            assert result.status == TrackedBookStatus.COMPLETED
            mock_match.assert_called_once()
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()

    def test_find_library_match(
        self,
        session: DummySession,
        library_config: Library,
    ) -> None:
        """Test _find_library_match logic.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        library_config : Library
            Library configuration fixture.
        """
        service = TrackedBookService(cast("Session", session))

        # Mock dependencies
        mock_repo = MagicMock()
        mock_book = MagicMock()
        mock_book.book.title = "Target Title"
        mock_book.book.id = 100
        mock_book.authors = ["Target Author"]
        mock_book.formats = ["EPUB"]

        with (
            patch.object(
                service._library_service, "get_library", return_value=library_config
            ),
            patch(
                "bookcard.services.tracked_book_service.CalibreBookRepository"
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = mock_repo
            mock_repo.list_books.return_value = [mock_book]

            # Exact match
            book_id, has_files = service._find_library_match(
                "Target Title", "Target Author", 1
            )
            assert book_id == 100
            assert has_files is True

            # Mismatch title
            book_id, has_files = service._find_library_match(
                "Other Title", "Target Author", 1
            )
            assert book_id is None

            # Mismatch author
            book_id, has_files = service._find_library_match(
                "Target Title", "Other Author", 1
            )
            assert book_id is None

    def test_find_library_match_no_library(self, session: DummySession) -> None:
        """Test _find_library_match with no library found.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        """
        service = TrackedBookService(cast("Session", session))

        with patch.object(service._library_service, "get_library", return_value=None):
            book_id, has_files = service._find_library_match("Title", "Author", 999)
            assert book_id is None
            assert has_files is False

    def test_find_library_match_exception(
        self,
        session: DummySession,
        library_config: Library,
    ) -> None:
        """Test _find_library_match handles exceptions.

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        library_config : Library
            Library configuration fixture.
        """
        service = TrackedBookService(cast("Session", session))

        with (
            patch.object(
                service._library_service, "get_library", return_value=library_config
            ),
            patch(
                "bookcard.services.tracked_book_service.CalibreBookRepository"
            ) as mock_repo_cls,
        ):
            mock_repo = mock_repo_cls.return_value
            mock_repo.list_books.side_effect = Exception("DB Error")

            book_id, has_files = service._find_library_match("Title", "Author", 1)
            assert book_id is None
            assert has_files is False
            mock_repo.dispose.assert_called_once()

    def test_find_library_match_with_active_library(
        self,
        session: DummySession,
        library_config: Library,
    ) -> None:
        """Test _find_library_match uses active library when library_id is None (covers line 368).

        Parameters
        ----------
        session : DummySession
            Database session fixture.
        library_config : Library
            Library configuration fixture.
        """
        service = TrackedBookService(cast("Session", session))

        # Mock dependencies
        mock_repo = MagicMock()
        mock_book = MagicMock()
        mock_book.book.title = "Target Title"
        mock_book.book.id = 100
        mock_book.authors = ["Target Author"]
        mock_book.formats = ["EPUB"]

        with (
            patch.object(
                service._library_service,
                "get_active_library",
                return_value=library_config,
                new_callable=MagicMock,
            ) as mock_get_active,
            patch(
                "bookcard.services.tracked_book_service.CalibreBookRepository"
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = mock_repo
            mock_repo.list_books.return_value = [mock_book]

            # Call with library_id=None to trigger get_active_library path
            book_id, has_files = service._find_library_match(
                "Target Title", "Target Author", None
            )
            assert book_id == 100
            assert has_files is True
            mock_get_active.assert_called_once()
