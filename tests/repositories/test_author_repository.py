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

"""Tests for author repository."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.author_metadata import (
    AuthorMapping,
    AuthorMetadata,
)
from fundamental.repositories.author_repository import AuthorRepository


class MockResult:
    """Mock result for session.exec()."""

    def __init__(self, items: list[object] | None = None) -> None:
        """Initialize mock result.

        Parameters
        ----------
        items : list[object] | None
            Items to return.
        """
        self._items = items or []

    def all(self) -> list[object]:
        """Return all items.

        Returns
        -------
        list[object]
            All items.
        """
        return self._items

    def first(self) -> object | None:
        """Return first item.

        Returns
        -------
        object | None
            First item or None.
        """
        return self._items[0] if self._items else None

    def one(self) -> int:
        """Return one item.

        Returns
        -------
        int
            First item.
        """
        return self._items[0] if self._items else 0


class MockSession:
    """Mock session for testing."""

    def __init__(self) -> None:
        """Initialize mock session."""
        self._exec_results: list[list[object] | None] = []
        self._exec_call_count = 0

    def set_exec_result(self, items: list[object] | None) -> None:
        """Set result for next exec call.

        Parameters
        ----------
        items : list[object] | None
            Items to return.
        """
        self._exec_results.append(items)

    def exec(self, stmt: object) -> MockResult:
        """Execute statement.

        Parameters
        ----------
        stmt : object
            Statement to execute.

        Returns
        -------
        MockResult
            Mock result.
        """
        if self._exec_call_count < len(self._exec_results):
            result_items = self._exec_results[self._exec_call_count]
            self._exec_call_count += 1
            return MockResult(result_items)
        return MockResult([])


@pytest.fixture
def mock_session() -> MockSession:
    """Create mock session.

    Returns
    -------
    MockSession
        Mock session instance.
    """
    return MockSession()


@pytest.fixture
def author_repo(mock_session: MockSession) -> AuthorRepository:
    """Create author repository.

    Parameters
    ----------
    mock_session : MockSession
        Mock session.

    Returns
    -------
    AuthorRepository
        Author repository instance.
    """
    return AuthorRepository(mock_session)  # type: ignore[arg-type]


@pytest.fixture
def library_id() -> int:
    """Create library ID.

    Returns
    -------
    int
        Library ID.
    """
    return 1


class TestAuthorRepositoryInit:
    """Test AuthorRepository initialization."""

    def test_init(self, mock_session: MockSession) -> None:
        """Test initialization.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.
        """
        repo = AuthorRepository(mock_session)  # type: ignore[arg-type]
        assert repo._session is mock_session


class TestAuthorRepositoryListByLibrary:
    """Test AuthorRepository.list_by_library."""

    @patch(
        "fundamental.repositories.author_listing_components.MatchedAuthorQueryBuilder"
    )
    @patch("fundamental.repositories.author_listing_components.AuthorHydrator")
    def test_list_by_library_success(
        self,
        mock_hydrator_class: MagicMock,
        mock_query_builder_class: MagicMock,
        author_repo: AuthorRepository,
        library_id: int,
    ) -> None:
        """Test list_by_library success.

        Parameters
        ----------
        mock_hydrator_class : MagicMock
            Mock hydrator class.
        mock_query_builder_class : MagicMock
            Mock query builder class.
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 96-128.
        """
        # Setup mocks
        mock_query_builder = MagicMock()
        mock_count_query = MagicMock()
        mock_query_builder.build_count_query.return_value = mock_count_query
        mock_query_builder_class.return_value = mock_query_builder

        mock_hydrator = MagicMock()
        mock_hydrator.hydrate_matched.return_value = {
            1: AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")
        }
        mock_hydrator_class.return_value = mock_hydrator

        # Create a call counter to track which exec call we're on
        exec_call_count = [0]

        def mock_exec(stmt: object) -> MockResult:
            """Mock exec that returns different results based on call count.

            Parameters
            ----------
            stmt : object
                Statement to execute.

            Returns
            -------
            MockResult
                Mock result.
            """
            exec_call_count[0] += 1
            if exec_call_count[0] == 1:
                # First call is count query
                return MockResult([2])
            # Second call is matched results query
            mock_matched_row = type(
                "Row", (), {"name": "Author 1", "type": "matched", "id": 1}
            )()
            return MockResult([mock_matched_row])

        author_repo._session.exec = mock_exec  # type: ignore[assignment]

        result, total = author_repo.list_by_library(
            library_id, calibre_db_path="/path/to/db", page=1, page_size=20
        )

        assert len(result) == 1
        assert total == 2

    @patch("fundamental.repositories.author_repository.logger")
    def test_count_matched_exception(
        self, mock_logger: MagicMock, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test _count_matched with exception.

        Parameters
        ----------
        mock_logger : MagicMock
            Mock logger.
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 147-152.
        """
        from fundamental.repositories.author_listing_components import (
            MatchedAuthorQueryBuilder,
        )

        author_repo._session.exec = MagicMock(side_effect=Exception("Database error"))  # type: ignore[assignment]

        with pytest.raises(Exception, match="Database error"):
            author_repo._count_matched(MatchedAuthorQueryBuilder(), library_id)
        mock_logger.exception.assert_called_once()

    @patch("fundamental.repositories.author_repository.logger")
    def test_fetch_matched_results_exception(
        self, mock_logger: MagicMock, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test _fetch_matched_results with exception.

        Parameters
        ----------
        mock_logger : MagicMock
            Mock logger.
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 171-176.
        """
        from fundamental.repositories.author_listing_components import (
            MatchedAuthorQueryBuilder,
        )

        author_repo._session.exec = MagicMock(side_effect=Exception("Database error"))  # type: ignore[assignment]

        with pytest.raises(Exception, match="Database error"):
            author_repo._fetch_matched_results(MatchedAuthorQueryBuilder(), library_id)
        mock_logger.exception.assert_called_once()

    def test_hydrate_results(
        self,
        author_repo: AuthorRepository,
    ) -> None:
        """Test _hydrate_results.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.

        Covers lines 203-222.
        """

        matched_author = AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")

        mock_hydrator = MagicMock()
        mock_hydrator.hydrate_matched.return_value = {1: matched_author}

        paginated_results = [
            type("Row", (), {"type": "matched", "id": 1})(),
        ]

        result = author_repo._hydrate_results(
            paginated_results,
            mock_hydrator,
        )

        assert len(result) == 1


class TestAuthorRepositoryGetByIdAndLibrary:
    """Test AuthorRepository.get_by_id_and_library."""

    def test_get_by_id_and_library_found(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_by_id_and_library when author is found.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 243-258.
        """
        author = AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")
        author_repo._session.set_exec_result([author])  # type: ignore[attr-defined]

        result = author_repo.get_by_id_and_library(1, library_id)

        assert result is not None
        assert result.id == 1

    def test_get_by_id_and_library_not_found(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_by_id_and_library when author is not found.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 243-258.
        """
        author_repo._session.set_exec_result([None])  # type: ignore[attr-defined]

        result = author_repo.get_by_id_and_library(999, library_id)

        assert result is None


class TestAuthorRepositoryGetByOpenLibraryKeyAndLibrary:
    """Test AuthorRepository.get_by_openlibrary_key_and_library."""

    def test_get_by_openlibrary_key_and_library_found(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_by_openlibrary_key_and_library when author is found.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 279-294.
        """
        author = AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")
        author_repo._session.set_exec_result([author])  # type: ignore[attr-defined]

        result = author_repo.get_by_openlibrary_key_and_library("OL1A", library_id)

        assert result is not None
        assert result.openlibrary_key == "OL1A"

    def test_get_by_openlibrary_key_and_library_not_found(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_by_openlibrary_key_and_library when author is not found.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 279-294.
        """
        author_repo._session.set_exec_result([None])  # type: ignore[attr-defined]

        result = author_repo.get_by_openlibrary_key_and_library("OL999A", library_id)

        assert result is None

    def test_get_by_openlibrary_key_and_library_with_prefix(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_by_openlibrary_key_and_library with /authors/ prefix (covers line 341).

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        author = AuthorMetadata(id=1, name="Author 1", openlibrary_key="/authors/OL1A")
        author_repo._session.set_exec_result([author])  # type: ignore[attr-defined]

        result = author_repo.get_by_openlibrary_key_and_library(
            "/authors/OL1A", library_id
        )

        assert result is not None
        assert result.openlibrary_key == "/authors/OL1A"

    def test_get_by_openlibrary_key_and_library_without_prefix(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_by_openlibrary_key_and_library without /authors/ prefix (covers line 339).

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        author = AuthorMetadata(id=1, name="Author 1", openlibrary_key="/authors/OL1A")
        author_repo._session.set_exec_result([author])  # type: ignore[attr-defined]

        result = author_repo.get_by_openlibrary_key_and_library("OL1A", library_id)

        assert result is not None
        assert result.openlibrary_key == "/authors/OL1A"


class TestAuthorRepositoryGetSimilarAuthorIds:
    """Test AuthorRepository.get_similar_author_ids."""

    def test_get_similar_author_ids_success(
        self, author_repo: AuthorRepository
    ) -> None:
        """Test get_similar_author_ids success.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.

        Covers lines 316-352.
        """

        # The query returns tuples of (similar_author_id, similarity_score)
        # Mock the exec to return tuples
        def mock_exec(stmt: object) -> MockResult:
            """Mock exec that returns tuples."""
            return MockResult([(2, 0.9), (3, 0.8), (4, 0.7)])

        author_repo._session.exec = mock_exec  # type: ignore[assignment]

        result = author_repo.get_similar_author_ids(1, limit=6)

        assert len(result) == 3
        assert 2 in result
        assert 3 in result
        assert 4 in result
        # Should be sorted by score descending
        assert result[0] == 2  # score 0.9
        assert result[1] == 3  # score 0.8
        assert result[2] == 4  # score 0.7

    def test_get_similar_author_ids_with_none_id(
        self, author_repo: AuthorRepository
    ) -> None:
        """Test get_similar_author_ids with None author IDs.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.

        Covers lines 316-352.
        """

        # Mock the exec to return tuples with None IDs
        def mock_exec(stmt: object) -> MockResult:
            """Mock exec that returns tuples with None IDs."""
            return MockResult([(None, 0.9), (None, 0.8)])

        author_repo._session.exec = mock_exec  # type: ignore[assignment]

        result = author_repo.get_similar_author_ids(1, limit=6)

        assert len(result) == 0

    def test_get_similar_author_ids_with_limit(
        self, author_repo: AuthorRepository
    ) -> None:
        """Test get_similar_author_ids with limit.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.

        Covers lines 316-352.
        """

        # Mock the exec to return tuples
        def mock_exec(stmt: object) -> MockResult:
            """Mock exec that returns tuples."""
            return MockResult([(i, 1.0 - i * 0.1) for i in range(2, 10)])

        author_repo._session.exec = mock_exec  # type: ignore[assignment]

        result = author_repo.get_similar_author_ids(1, limit=3)

        assert len(result) == 3

    def test_get_similar_author_ids_with_duplicates(
        self, author_repo: AuthorRepository
    ) -> None:
        """Test get_similar_author_ids with duplicate author IDs.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.

        Covers lines 316-352.
        """

        # Mock the exec to return tuples with duplicates
        def mock_exec(stmt: object) -> MockResult:
            """Mock exec that returns tuples with duplicates."""
            return MockResult([
                (2, 0.9),
                (3, 0.8),
                (4, 0.7),
                (2, 0.6),
            ])  # 2 appears twice

        author_repo._session.exec = mock_exec  # type: ignore[assignment]

        result = author_repo.get_similar_author_ids(1, limit=6)

        # Should deduplicate
        assert len(result) == 3
        assert result.count(2) == 1
        assert result.count(3) == 1
        assert result.count(4) == 1


class TestAuthorRepositoryIsAuthorInLibrary:
    """Test AuthorRepository.is_author_in_library."""

    def test_is_author_in_library_true(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test is_author_in_library returns True.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 373-377.
        """
        mapping = AuthorMapping(
            author_metadata_id=1, calibre_author_id=1, library_id=library_id
        )
        author_repo._session.set_exec_result([mapping])  # type: ignore[attr-defined]

        result = author_repo.is_author_in_library(1, library_id)

        assert result is True

    def test_is_author_in_library_false(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test is_author_in_library returns False.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.

        Covers lines 373-377.
        """
        author_repo._session.set_exec_result([None])  # type: ignore[attr-defined]

        result = author_repo.is_author_in_library(999, library_id)

        assert result is False


class TestAuthorRepositoryGetById:
    """Test AuthorRepository.get_by_id."""

    def test_get_by_id_found(self, author_repo: AuthorRepository) -> None:
        """Test get_by_id when author is found.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.

        Covers lines 395-396.
        """
        author = AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")
        author_repo._session.set_exec_result([author])  # type: ignore[attr-defined]

        result = author_repo.get_by_id(1)

        assert result is not None
        assert result.id == 1

    def test_get_by_id_not_found(self, author_repo: AuthorRepository) -> None:
        """Test get_by_id when author is not found.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.

        Covers lines 395-396.
        """
        author_repo._session.set_exec_result([None])  # type: ignore[attr-defined]

        result = author_repo.get_by_id(999)

        assert result is None


class TestAuthorRepositoryListUnmatchedByLibrary:
    """Test AuthorRepository.list_unmatched_by_library."""

    @patch("fundamental.repositories.author_repository.MappedAuthorWithoutKeyFetcher")
    @patch("fundamental.repositories.author_repository.MappedIdsFetcher")
    @patch("fundamental.repositories.author_repository.UnmatchedAuthorFetcher")
    @patch("fundamental.repositories.author_repository.AuthorHydrator")
    def test_list_unmatched_by_library_with_calibre_db(
        self,
        mock_hydrator_class: MagicMock,
        mock_unmatched_fetcher_class: MagicMock,
        mock_mapped_ids_fetcher_class: MagicMock,
        mock_mapped_without_key_fetcher_class: MagicMock,
        author_repo: AuthorRepository,
        library_id: int,
    ) -> None:
        """Test list_unmatched_by_library with calibre_db_path (covers lines 138-185).

        Parameters
        ----------
        mock_hydrator_class : MagicMock
            Mock hydrator class.
        mock_unmatched_fetcher_class : MagicMock
            Mock unmatched fetcher class.
        mock_mapped_ids_fetcher_class : MagicMock
            Mock mapped IDs fetcher class.
        mock_mapped_without_key_fetcher_class : MagicMock
            Mock mapped without key fetcher class.
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        from fundamental.models.core import Author

        # Setup mocks
        mock_mapped_without_key_fetcher = MagicMock()
        mock_mapped_without_key_fetcher.fetch_mapped_without_key.return_value = []
        mock_mapped_without_key_fetcher_class.return_value = (
            mock_mapped_without_key_fetcher
        )

        mock_mapped_ids_fetcher = MagicMock()
        mock_mapped_ids_fetcher.get_mapped_ids.return_value = {1, 2}
        mock_mapped_ids_fetcher_class.return_value = mock_mapped_ids_fetcher

        mock_unmatched_fetcher = MagicMock()
        author3 = Author(id=3, name="Author 3")
        author4 = Author(id=4, name="Author 4")
        mock_unmatched_fetcher.fetch_unmatched.return_value = [author3, author4]
        mock_unmatched_fetcher_class.return_value = mock_unmatched_fetcher

        mock_hydrator = MagicMock()
        author3_metadata = AuthorMetadata(
            id=None, name="Author 3", openlibrary_key="calibre-3", is_unmatched=True
        )
        author4_metadata = AuthorMetadata(
            id=None, name="Author 4", openlibrary_key="calibre-4", is_unmatched=True
        )
        mock_hydrator.create_unmatched_metadata.return_value = {
            3: author3_metadata,
            4: author4_metadata,
        }
        mock_hydrator_class.return_value = mock_hydrator

        result, total = author_repo.list_unmatched_by_library(
            library_id,
            page=1,
            page_size=20,
            calibre_db_path="/path/to/db",
            calibre_db_file="metadata.db",
        )

        assert len(result) == 2
        assert total == 2
        mock_mapped_without_key_fetcher.fetch_mapped_without_key.assert_called_once_with(
            library_id
        )
        mock_mapped_ids_fetcher.get_mapped_ids.assert_called_once_with(library_id)
        mock_unmatched_fetcher.fetch_unmatched.assert_called_once()

    @patch("fundamental.repositories.author_repository.MappedAuthorWithoutKeyFetcher")
    def test_list_unmatched_by_library_no_calibre_db(
        self,
        mock_mapped_without_key_fetcher_class: MagicMock,
        author_repo: AuthorRepository,
        library_id: int,
    ) -> None:
        """Test list_unmatched_by_library without calibre_db_path (covers lines 138-185).

        Parameters
        ----------
        mock_mapped_without_key_fetcher_class : MagicMock
            Mock mapped without key fetcher class.
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        author1 = AuthorMetadata(
            id=1, name="Author 1", openlibrary_key=None, is_unmatched=False
        )
        mock_mapped_without_key_fetcher = MagicMock()
        mock_mapped_without_key_fetcher.fetch_mapped_without_key.return_value = [
            author1
        ]
        mock_mapped_without_key_fetcher_class.return_value = (
            mock_mapped_without_key_fetcher
        )

        result, total = author_repo.list_unmatched_by_library(
            library_id,
            page=1,
            page_size=20,
            calibre_db_path=None,
            calibre_db_file="metadata.db",
        )

        assert len(result) == 1
        assert total == 1


class TestAuthorRepositoryGetByCalibreIdAndLibrary:
    """Test AuthorRepository.get_by_calibre_id_and_library."""

    def test_get_by_calibre_id_and_library_found(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_by_calibre_id_and_library when author is found (covers lines 379-396).

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        author = AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")
        author_repo._session.set_exec_result([author])  # type: ignore[attr-defined]

        result = author_repo.get_by_calibre_id_and_library(1, library_id)

        assert result is not None
        assert result.id == 1

    def test_get_by_calibre_id_and_library_not_found(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_by_calibre_id_and_library when author is not found (covers lines 379-396).

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        author_repo._session.set_exec_result([None])  # type: ignore[attr-defined]

        result = author_repo.get_by_calibre_id_and_library(999, library_id)

        assert result is None


class TestAuthorRepositoryGetSimilarAuthorsInLibrary:
    """Test AuthorRepository.get_similar_authors_in_library."""

    def test_get_similar_authors_in_library_success(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_similar_authors_in_library success (covers lines 503-535).

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        # Mock get_similar_author_ids to return IDs
        author_repo.get_similar_author_ids = MagicMock(  # type: ignore[assignment]
            return_value=[2, 3, 4]
        )

        # Mock session.exec to return authors
        author2 = AuthorMetadata(id=2, name="Author 2", openlibrary_key="OL2A")
        author3 = AuthorMetadata(id=3, name="Author 3", openlibrary_key="OL3A")
        author4 = AuthorMetadata(id=4, name="Author 4", openlibrary_key="OL4A")

        def mock_exec(stmt: object) -> MockResult:
            """Mock exec that returns authors."""
            return MockResult([author2, author3, author4])

        author_repo._session.exec = mock_exec  # type: ignore[assignment]

        result = author_repo.get_similar_authors_in_library(1, library_id, limit=6)

        assert len(result) == 3
        assert result[0].id == 2
        assert result[1].id == 3
        assert result[2].id == 4

    def test_get_similar_authors_in_library_empty(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_similar_authors_in_library with no similar authors (covers line 506).

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        author_repo.get_similar_author_ids = MagicMock(return_value=[])  # type: ignore[assignment]

        result = author_repo.get_similar_authors_in_library(1, library_id, limit=6)

        assert result == []

    def test_get_similar_authors_in_library_with_limit(
        self, author_repo: AuthorRepository, library_id: int
    ) -> None:
        """Test get_similar_authors_in_library with limit (covers lines 503-535).

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        library_id : int
            Library ID.
        """
        # Mock get_similar_author_ids to return more IDs than limit
        author_repo.get_similar_author_ids = MagicMock(  # type: ignore[assignment]
            return_value=[2, 3, 4, 5, 6, 7, 8]
        )

        # Mock session.exec to return authors
        authors_list = [
            AuthorMetadata(id=i, name=f"Author {i}", openlibrary_key=f"OL{i}A")
            for i in range(2, 9)
        ]

        def mock_exec(stmt: object) -> MockResult:
            """Mock exec that returns authors."""
            return MockResult(authors_list)

        author_repo._session.exec = mock_exec  # type: ignore[assignment]

        result = author_repo.get_similar_authors_in_library(1, library_id, limit=3)

        assert len(result) == 3
