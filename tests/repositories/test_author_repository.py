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
    AuthorSimilarity,
)
from fundamental.models.core import Author
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

    @patch("fundamental.repositories.author_repository.MatchedAuthorQueryBuilder")
    @patch("fundamental.repositories.author_repository.MappedIdsFetcher")
    @patch("fundamental.repositories.author_repository.UnmatchedAuthorFetcher")
    @patch("fundamental.repositories.author_repository.AuthorResultCombiner")
    @patch("fundamental.repositories.author_repository.AuthorHydrator")
    def test_list_by_library_success(
        self,
        mock_hydrator_class: MagicMock,
        mock_combiner_class: MagicMock,
        mock_unmatched_fetcher_class: MagicMock,
        mock_ids_fetcher_class: MagicMock,
        mock_query_builder_class: MagicMock,
        author_repo: AuthorRepository,
        library_id: int,
    ) -> None:
        """Test list_by_library success.

        Parameters
        ----------
        mock_hydrator_class : MagicMock
            Mock hydrator class.
        mock_combiner_class : MagicMock
            Mock combiner class.
        mock_unmatched_fetcher_class : MagicMock
            Mock unmatched fetcher class.
        mock_ids_fetcher_class : MagicMock
            Mock IDs fetcher class.
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

        mock_ids_fetcher = MagicMock()
        mock_ids_fetcher.get_mapped_ids.return_value = {1, 2}
        mock_ids_fetcher_class.return_value = mock_ids_fetcher

        mock_unmatched_fetcher = MagicMock()
        mock_unmatched_fetcher.fetch_unmatched.return_value = [
            Author(id=3, name="Unmatched 3")
        ]
        mock_unmatched_fetcher_class.return_value = mock_unmatched_fetcher

        mock_combiner = MagicMock()
        mock_combiner.combine_and_paginate.return_value = [
            type("Row", (), {"type": "matched", "id": 1})(),
            type("Row", (), {"type": "unmatched", "id": 3})(),
        ]
        mock_combiner_class.return_value = mock_combiner

        mock_hydrator = MagicMock()
        mock_hydrator.hydrate_matched.return_value = {
            1: AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")
        }
        mock_hydrator.create_unmatched_metadata.return_value = {
            3: AuthorMetadata(id=None, name="Unmatched 3", openlibrary_key="calibre-3")
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

        assert len(result) == 2
        assert total == 3

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

    @pytest.mark.parametrize(
        ("has_unmatched", "has_calibre_path"),
        [(True, True), (True, False), (False, True), (False, False)],
    )
    def test_hydrate_results(
        self,
        author_repo: AuthorRepository,
        has_unmatched: bool,
        has_calibre_path: bool,
    ) -> None:
        """Test _hydrate_results.

        Parameters
        ----------
        author_repo : AuthorRepository
            Author repository.
        has_unmatched : bool
            Whether there are unmatched results.
        has_calibre_path : bool
            Whether calibre_db_path is provided.

        Covers lines 203-222.
        """

        matched_author = AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")
        unmatched_author = AuthorMetadata(
            id=None, name="Unmatched", openlibrary_key="calibre-3", is_unmatched=True
        )

        mock_hydrator = MagicMock()
        mock_hydrator.hydrate_matched.return_value = {1: matched_author}
        if has_unmatched and has_calibre_path:
            mock_hydrator.create_unmatched_metadata.return_value = {3: unmatched_author}
        else:
            mock_hydrator.create_unmatched_metadata.return_value = {}

        paginated_results = [
            type("Row", (), {"type": "matched", "id": 1})(),
        ]
        if has_unmatched:
            paginated_results.append(type("Row", (), {"type": "unmatched", "id": 3})())

        result = author_repo._hydrate_results(
            paginated_results,
            mock_hydrator,
            "/path/to/db" if has_calibre_path else None,
            "metadata.db",
        )

        if has_unmatched and has_calibre_path:
            assert len(result) == 2
        else:
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
        # Create similarity records where author is author1
        similarity1 = AuthorSimilarity(author1_id=1, author2_id=2, similarity_score=0.9)
        similarity2 = AuthorSimilarity(author1_id=1, author2_id=3, similarity_score=0.8)

        # Create similarity records where author is author2
        similarity3 = AuthorSimilarity(author1_id=4, author2_id=1, similarity_score=0.7)

        # First call returns similarities where author is author1
        author_repo._session.set_exec_result([similarity1, similarity2])  # type: ignore[attr-defined]
        # Second call returns similarities where author is author2
        author_repo._session.set_exec_result([similarity3])  # type: ignore[attr-defined]

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
        # Create similarity with None author2_id
        similarity1 = AuthorSimilarity(
            author1_id=1, author2_id=None, similarity_score=0.9
        )
        # Create similarity with None author1_id
        similarity2 = AuthorSimilarity(
            author1_id=None, author2_id=1, similarity_score=0.8
        )

        author_repo._session.set_exec_result([similarity1])  # type: ignore[attr-defined]
        author_repo._session.set_exec_result([similarity2])  # type: ignore[attr-defined]

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
        similarities = [
            AuthorSimilarity(author1_id=1, author2_id=i, similarity_score=1.0 - i * 0.1)
            for i in range(2, 10)
        ]

        author_repo._session.set_exec_result(similarities)  # type: ignore[attr-defined]
        author_repo._session.set_exec_result([])  # type: ignore[attr-defined]

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
        # Same author appears in both queries
        similarity1 = AuthorSimilarity(author1_id=1, author2_id=2, similarity_score=0.9)
        similarity2 = AuthorSimilarity(author1_id=3, author2_id=1, similarity_score=0.8)
        similarity3 = AuthorSimilarity(author1_id=4, author2_id=1, similarity_score=0.7)

        author_repo._session.set_exec_result([similarity1])  # type: ignore[attr-defined]
        author_repo._session.set_exec_result([similarity2, similarity3])  # type: ignore[attr-defined]

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
