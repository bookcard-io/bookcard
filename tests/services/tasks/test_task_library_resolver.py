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

"""Tests for the shared task library resolver."""

from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.services.tasks.exceptions import LibraryNotConfiguredError
from bookcard.services.tasks.task_library_resolver import resolve_task_library
from tests.conftest import DummySession


@pytest.fixture
def session() -> Session:
    """Create a DummySession for testing.

    Returns
    -------
    Session
        A mock-friendly session cast to Session.
    """
    return cast("Session", DummySession())


@pytest.fixture
def library() -> Library:
    """Create a test Library model.

    Returns
    -------
    Library
        A Library instance with id=1.
    """
    lib = Library(
        name="Test Library",
        path="/tmp/test-library",
        is_active=True,
    )
    lib.id = 1
    return lib


@pytest.fixture
def library_b() -> Library:
    """Create a second test Library model.

    Returns
    -------
    Library
        A Library instance with id=2.
    """
    lib = Library(
        name="Second Library",
        path="/tmp/second-library",
        is_active=False,
    )
    lib.id = 2
    return lib


class TestResolveFromMetadata:
    """Tests for resolution strategy 1: explicit library_id in metadata."""

    def test_resolves_library_from_metadata_library_id(
        self,
        session: Session,
        library: Library,
    ) -> None:
        """Library is resolved when metadata contains a valid library_id.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Expected library.
        """
        with patch(
            "bookcard.services.tasks.task_library_resolver.LibraryRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = library
            mock_repo_class.return_value = mock_repo

            result = resolve_task_library(session, {"library_id": 1})

            mock_repo.get.assert_called_once_with(1)
            assert result is library

    def test_falls_through_when_metadata_library_id_not_found(
        self,
        session: Session,
        library: Library,
    ) -> None:
        """Falls back to first available library when metadata library_id not in DB.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Expected library (returned by first-available fallback).
        """
        with patch(
            "bookcard.services.tasks.task_library_resolver.LibraryRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get.return_value = None
            mock_repo.list_all.return_value = [library]
            mock_repo_class.return_value = mock_repo

            result = resolve_task_library(session, {"library_id": 999})

            assert result is library
            mock_repo.get.assert_called_once_with(999)

    def test_metadata_without_library_id_skips_strategy(
        self,
        session: Session,
        library: Library,
    ) -> None:
        """Metadata without library_id skips directly to later strategies.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Expected library.
        """
        with patch(
            "bookcard.services.tasks.task_library_resolver.LibraryRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [library]
            mock_repo_class.return_value = mock_repo

            result = resolve_task_library(session, {"book_id": 42})

            # Should NOT have called repo.get since there's no library_id
            mock_repo.get.assert_not_called()
            assert result is library


class TestResolveFromUserLibrary:
    """Tests for resolution strategy 2: per-user active library."""

    def test_resolves_from_user_active_library(
        self,
        session: Session,
        library: Library,
    ) -> None:
        """Library is resolved from the user's active library assignment.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Expected library.
        """
        with patch(
            "bookcard.repositories.user_library_repository.UserLibraryRepository"
        ) as mock_ul_repo_class:
            mock_ul_repo = MagicMock()
            mock_ul_repo.get_active_library_for_user.return_value = library
            mock_ul_repo_class.return_value = mock_ul_repo

            result = resolve_task_library(session, {}, user_id=42)

            mock_ul_repo.get_active_library_for_user.assert_called_once_with(42)
            assert result is library

    def test_skips_user_strategy_when_no_user_id(
        self,
        session: Session,
        library: Library,
    ) -> None:
        """User strategy is skipped when user_id is None.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Expected library (returned by first-available fallback).
        """
        with patch(
            "bookcard.services.tasks.task_library_resolver.LibraryRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [library]
            mock_repo_class.return_value = mock_repo

            result = resolve_task_library(session, {}, user_id=None)

            assert result is library

    def test_falls_through_when_user_has_no_active_library(
        self,
        session: Session,
        library: Library,
    ) -> None:
        """Falls back to first available when user has no active library.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Expected library (returned by first-available fallback).
        """
        with (
            patch(
                "bookcard.repositories.user_library_repository.UserLibraryRepository"
            ) as mock_ul_repo_class,
            patch(
                "bookcard.services.tasks.task_library_resolver.LibraryRepository"
            ) as mock_repo_class,
        ):
            mock_ul_repo = MagicMock()
            mock_ul_repo.get_active_library_for_user.return_value = None
            mock_ul_repo_class.return_value = mock_ul_repo

            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [library]
            mock_repo_class.return_value = mock_repo

            result = resolve_task_library(session, {}, user_id=42)

            mock_ul_repo.get_active_library_for_user.assert_called_once_with(42)
            assert result is library


class TestResolveFromFirstAvailable:
    """Tests for resolution strategy 3: first available library."""

    def test_resolves_from_first_available_library(
        self,
        session: Session,
        library: Library,
    ) -> None:
        """Library is resolved from the first available library.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Expected library.
        """
        with patch(
            "bookcard.services.tasks.task_library_resolver.LibraryRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [library]
            mock_repo_class.return_value = mock_repo

            result = resolve_task_library(session, {})

            assert result is library

    def test_raises_when_no_library_found(self, session: Session) -> None:
        """Raises LibraryNotConfiguredError when all strategies fail.

        Parameters
        ----------
        session : Session
            Mock session.
        """
        with patch(
            "bookcard.services.tasks.task_library_resolver.LibraryRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = []
            mock_repo_class.return_value = mock_repo

            with pytest.raises(LibraryNotConfiguredError):
                resolve_task_library(session, {})


class TestResolutionPriority:
    """Tests for the priority ordering of resolution strategies."""

    def test_metadata_takes_priority_over_user_and_global(
        self,
        session: Session,
        library: Library,
        library_b: Library,
    ) -> None:
        """Metadata library_id is preferred over user or first available.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Library returned by metadata lookup (expected winner).
        library_b : Library
            Library that would be returned by user lookup (should not be used).
        """
        with (
            patch(
                "bookcard.services.tasks.task_library_resolver.LibraryRepository"
            ) as mock_repo_class,
            patch(
                "bookcard.repositories.user_library_repository.UserLibraryRepository"
            ) as mock_ul_repo_class,
        ):
            mock_repo = MagicMock()
            mock_repo.get.return_value = library
            mock_repo_class.return_value = mock_repo

            mock_ul_repo = MagicMock()
            mock_ul_repo.get_active_library_for_user.return_value = library_b
            mock_ul_repo_class.return_value = mock_ul_repo

            result = resolve_task_library(session, {"library_id": 1}, user_id=42)

            assert result is library
            # User strategy should NOT have been called
            mock_ul_repo.get_active_library_for_user.assert_not_called()

    def test_user_takes_priority_over_first_available(
        self,
        session: Session,
        library: Library,
        library_b: Library,
    ) -> None:
        """User active library is preferred over first available.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Library returned by user lookup (expected winner).
        library_b : Library
            Library that would be returned by first available (should not be used).
        """
        with patch(
            "bookcard.repositories.user_library_repository.UserLibraryRepository"
        ) as mock_ul_repo_class:
            mock_ul_repo = MagicMock()
            mock_ul_repo.get_active_library_for_user.return_value = library
            mock_ul_repo_class.return_value = mock_ul_repo

            result = resolve_task_library(session, {}, user_id=42)

            assert result is library

    def test_full_fallback_chain(self, session: Session, library: Library) -> None:
        """All strategies fail in order until first available succeeds.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Library returned by first available (last resort).
        """
        with (
            patch(
                "bookcard.services.tasks.task_library_resolver.LibraryRepository"
            ) as mock_repo_class,
            patch(
                "bookcard.repositories.user_library_repository.UserLibraryRepository"
            ) as mock_ul_repo_class,
        ):
            mock_repo = MagicMock()
            mock_repo.get.return_value = None  # metadata lookup fails
            mock_repo.list_all.return_value = [library]  # first available succeeds
            mock_repo_class.return_value = mock_repo

            mock_ul_repo = MagicMock()
            mock_ul_repo.get_active_library_for_user.return_value = (
                None  # user lookup fails
            )
            mock_ul_repo_class.return_value = mock_ul_repo

            result = resolve_task_library(session, {"library_id": 999}, user_id=42)

            assert result is library
            mock_repo.get.assert_called_once_with(999)
            mock_ul_repo.get_active_library_for_user.assert_called_once_with(42)
            mock_repo.list_all.assert_called_once()

    def test_all_strategies_fail_raises(self, session: Session) -> None:
        """LibraryNotConfiguredError raised when all three strategies fail.

        Parameters
        ----------
        session : Session
            Mock session.
        """
        with (
            patch(
                "bookcard.services.tasks.task_library_resolver.LibraryRepository"
            ) as mock_repo_class,
            patch(
                "bookcard.repositories.user_library_repository.UserLibraryRepository"
            ) as mock_ul_repo_class,
        ):
            mock_repo = MagicMock()
            mock_repo.get.return_value = None
            mock_repo.list_all.return_value = []
            mock_repo_class.return_value = mock_repo

            mock_ul_repo = MagicMock()
            mock_ul_repo.get_active_library_for_user.return_value = None
            mock_ul_repo_class.return_value = mock_ul_repo

            with pytest.raises(LibraryNotConfiguredError):
                resolve_task_library(session, {"library_id": 999}, user_id=42)

    def test_empty_metadata_dict(self, session: Session, library: Library) -> None:
        """Empty metadata dict skips to later strategies.

        Parameters
        ----------
        session : Session
            Mock session.
        library : Library
            Expected library.
        """
        with patch(
            "bookcard.services.tasks.task_library_resolver.LibraryRepository"
        ) as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [library]
            mock_repo_class.return_value = mock_repo

            result = resolve_task_library(session, {})

            mock_repo.get.assert_not_called()
            assert result is library
