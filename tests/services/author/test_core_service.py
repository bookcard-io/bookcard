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

"""Tests for AuthorCoreService to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.author_metadata import AuthorMetadata, AuthorUserMetadata
from bookcard.models.config import Library
from bookcard.repositories.author_repository import AuthorRepository
from bookcard.services.author.core_service import AuthorCoreService
from bookcard.services.author_exceptions import NoActiveLibraryError
from bookcard.services.config_service import LibraryService

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def active_library() -> Library:
    """Create an active library with ID."""
    return Library(
        id=1,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def active_library_no_id() -> Library:
    """Create an active library without ID."""
    return Library(
        id=None,
        name="Test Library",
        calibre_db_path="/path/to/library",
        calibre_db_file="metadata.db",
        is_active=True,
    )


@pytest.fixture
def mock_author_repo() -> MagicMock:
    """Create a mock author repository."""
    return MagicMock(spec=AuthorRepository)


@pytest.fixture
def mock_library_service(active_library: Library) -> MagicMock:
    """Create a mock library service."""
    service = MagicMock(spec=LibraryService)
    service.get_active_library.return_value = active_library
    return service


@pytest.fixture
def mock_library_service_no_id(active_library_no_id: Library) -> MagicMock:
    """Create a mock library service with library without ID."""
    service = MagicMock(spec=LibraryService)
    service.get_active_library.return_value = active_library_no_id
    return service


@pytest.fixture
def core_service(
    session: DummySession,
    mock_author_repo: MagicMock,
    mock_library_service: MagicMock,
) -> AuthorCoreService:
    """Create AuthorCoreService instance with mocked dependencies."""
    return AuthorCoreService(
        session,  # type: ignore[arg-type]
        author_repo=mock_author_repo,
        library_service=mock_library_service,
    )


@pytest.fixture
def author_metadata() -> AuthorMetadata:
    """Create sample author metadata."""
    return AuthorMetadata(
        id=1,
        openlibrary_key="OL123A",
        name="Test Author",
    )


# ============================================================================
# list_authors Tests
# ============================================================================


class TestListAuthors:
    """Test list_authors method."""

    def test_list_authors_success(
        self,
        core_service: AuthorCoreService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test list_authors with successful response."""
        mock_author_repo.list_by_library.return_value = ([author_metadata], 1)

        authors, total = core_service.list_authors()

        assert len(authors) == 1
        assert total == 1
        assert authors[0].name == "Test Author"
        mock_author_repo.list_by_library.assert_called_once()

    def test_list_authors_with_pagination(
        self,
        core_service: AuthorCoreService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test list_authors with custom pagination."""
        mock_author_repo.list_by_library.return_value = ([author_metadata], 1)

        authors, total = core_service.list_authors(page=2, page_size=10)

        assert len(authors) == 1
        assert total == 1
        mock_author_repo.list_by_library.assert_called_once()

    def test_list_authors_unmatched_filter(
        self,
        core_service: AuthorCoreService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test list_authors with unmatched filter."""
        mock_author_repo.list_unmatched_by_library.return_value = ([author_metadata], 1)

        authors, total = core_service.list_authors(filter_type="unmatched")

        assert len(authors) == 1
        assert total == 1
        mock_author_repo.list_unmatched_by_library.assert_called_once()

    def test_list_authors_library_id_none(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service_no_id: MagicMock,
    ) -> None:
        """Test list_authors raises NoActiveLibraryError when library ID is None."""
        service = AuthorCoreService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service_no_id,
        )

        # Patch ensure_active_library in the core_service module to return a library with None id
        # to test the specific check in list_authors
        with (
            patch(
                "bookcard.services.author.core_service.ensure_active_library",
                return_value=Library(id=None, name="Test", is_active=True),
            ),
            pytest.raises(NoActiveLibraryError, match="Active library ID is None"),
        ):
            service.list_authors()


# ============================================================================
# get_author Tests
# ============================================================================


class TestGetAuthor:
    """Test get_author method."""

    def test_get_author_success(
        self,
        core_service: AuthorCoreService,
        mock_author_repo: MagicMock,
        author_metadata: AuthorMetadata,
    ) -> None:
        """Test get_author with successful response."""
        with patch(
            "bookcard.services.author.core_service.AuthorLookupStrategyChain"
        ) as mock_chain_class:
            mock_chain = MagicMock()
            mock_chain.lookup.return_value = author_metadata
            mock_chain_class.return_value = mock_chain

            service = AuthorCoreService(
                core_service._session,  # type: ignore[arg-type]
                author_repo=mock_author_repo,
                library_service=core_service._library_service,
            )

            result = service.get_author("1")

            assert result.name == "Test Author"
            mock_chain.lookup.assert_called_once()

    def test_get_author_library_id_none(
        self,
        session: DummySession,
        mock_author_repo: MagicMock,
        mock_library_service_no_id: MagicMock,
    ) -> None:
        """Test get_author raises NoActiveLibraryError when library ID is None."""
        service = AuthorCoreService(
            session,  # type: ignore[arg-type]
            author_repo=mock_author_repo,
            library_service=mock_library_service_no_id,
        )

        # Patch ensure_active_library in the core_service module to return a library with None id
        # to test the specific check in get_author
        with (
            patch(
                "bookcard.services.author.core_service.ensure_active_library",
                return_value=Library(id=None, name="Test", is_active=True),
            ),
            pytest.raises(NoActiveLibraryError, match="Active library ID is None"),
        ):
            service.get_author("1")


# ============================================================================
# _save_user_metadata Tests
# ============================================================================


class TestSaveUserMetadata:
    """Test _save_user_metadata method."""

    @pytest.mark.parametrize(
        "value",
        [
            ["Fiction", "Sci-Fi"],
            {"key": "value"},
            "string_value",
        ],
    )
    def test_save_user_metadata_new(
        self,
        core_service: AuthorCoreService,
        session: DummySession,
        value: list[str] | dict[str, object] | str,
    ) -> None:
        """Test _save_user_metadata creates new user metadata."""
        session.set_exec_result([])  # type: ignore[attr-defined]

        core_service._save_user_metadata(
            author_metadata_id=1,
            field_name="genres",
            value=value,
        )

        assert len(session.added) == 1  # type: ignore[attr-defined]
        added = session.added[0]  # type: ignore[attr-defined]
        assert isinstance(added, AuthorUserMetadata)
        assert added.author_metadata_id == 1
        assert added.field_name == "genres"
        assert added.is_user_defined is True

    def test_save_user_metadata_existing(
        self,
        core_service: AuthorCoreService,
        session: DummySession,
    ) -> None:
        """Test _save_user_metadata updates existing user metadata."""
        existing = AuthorUserMetadata(
            id=1,
            author_metadata_id=1,
            field_name="genres",
            field_value=["Old"],
            is_user_defined=False,
        )
        session.set_exec_result([existing])  # type: ignore[attr-defined]

        core_service._save_user_metadata(
            author_metadata_id=1,
            field_name="genres",
            value=["Fiction", "Sci-Fi"],
        )

        assert existing.field_value == ["Fiction", "Sci-Fi"]
        assert existing.is_user_defined is True
        assert existing in session.added  # type: ignore[attr-defined]


# ============================================================================
# _delete_user_metadata Tests
# ============================================================================


class TestDeleteUserMetadata:
    """Test _delete_user_metadata method."""

    def test_delete_user_metadata_existing(
        self,
        core_service: AuthorCoreService,
        session: DummySession,
    ) -> None:
        """Test _delete_user_metadata deletes existing user metadata."""
        existing = AuthorUserMetadata(
            id=1,
            author_metadata_id=1,
            field_name="genres",
            field_value=["Fiction"],
            is_user_defined=True,
        )
        session.set_exec_result([existing])  # type: ignore[attr-defined]

        core_service._delete_user_metadata(
            author_metadata_id=1,
            field_name="genres",
        )

        assert existing in session.deleted  # type: ignore[attr-defined]

    def test_delete_user_metadata_not_found(
        self,
        core_service: AuthorCoreService,
        session: DummySession,
    ) -> None:
        """Test _delete_user_metadata when metadata not found."""
        session.set_exec_result([])  # type: ignore[attr-defined]

        core_service._delete_user_metadata(
            author_metadata_id=1,
            field_name="genres",
        )

        assert len(session.deleted) == 0  # type: ignore[attr-defined]
