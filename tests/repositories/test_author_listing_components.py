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

"""Tests for author listing components."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from fundamental.models.author_metadata import AuthorMetadata
from fundamental.models.core import Author
from fundamental.repositories.author_listing_components import (
    AuthorHydrator,
    AuthorResultCombiner,
    MappedIdsFetcher,
    MatchedAuthorQueryBuilder,
    UnmatchedAuthorFetcher,
    UnmatchedAuthorRow,
)
from fundamental.repositories.calibre_book_repository import CalibreBookRepository


class MockResult:
    """Mock result for session.exec()."""

    def __init__(self, items: list[object]) -> None:
        """Initialize mock result.

        Parameters
        ----------
        items : list[object]
            Items to return.
        """
        self._items = items

    def all(self) -> list[object]:
        """Return all items.

        Returns
        -------
        list[object]
            All items.
        """
        return self._items

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
        self._exec_results: list[list[object]] = []
        self._exec_call_count = 0

    def set_exec_result(self, items: list[object]) -> None:
        """Set result for next exec call.

        Parameters
        ----------
        items : list[object]
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
            result = MockResult(self._exec_results[self._exec_call_count])
            self._exec_call_count += 1
            return result
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
def library_id() -> int:
    """Create library ID.

    Returns
    -------
    int
        Library ID.
    """
    return 1


class TestUnmatchedAuthorRow:
    """Test UnmatchedAuthorRow."""

    def test_init(self) -> None:
        """Test initialization.

        Covers lines 63-65.
        """
        row = UnmatchedAuthorRow("Test Author", 123)
        assert row.name == "Test Author"
        assert row.type == "unmatched"
        assert row.id == 123


class TestMatchedAuthorQueryBuilder:
    """Test MatchedAuthorQueryBuilder."""

    def test_build_query(self, library_id: int) -> None:
        """Test build_query.

        Parameters
        ----------
        library_id : int
            Library ID.

        Covers lines 88-96.
        """
        query = MatchedAuthorQueryBuilder.build_query(library_id)
        assert query is not None

    def test_build_count_query(self, library_id: int) -> None:
        """Test build_count_query.

        Parameters
        ----------
        library_id : int
            Library ID.

        Covers lines 112-113.
        """
        query = MatchedAuthorQueryBuilder.build_count_query(library_id)
        assert query is not None


class TestMappedIdsFetcher:
    """Test MappedIdsFetcher."""

    def test_init(self, mock_session: MockSession) -> None:
        """Test initialization.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.

        Covers lines 130.
        """
        fetcher = MappedIdsFetcher(mock_session)  # type: ignore[arg-type]
        assert fetcher._session is mock_session

    def test_get_mapped_ids(self, mock_session: MockSession, library_id: int) -> None:
        """Test get_mapped_ids.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.
        library_id : int
            Library ID.

        Covers lines 145-148.
        """
        mock_session.set_exec_result([1, 2, 3, None, 4])
        fetcher = MappedIdsFetcher(mock_session)  # type: ignore[arg-type]
        result = fetcher.get_mapped_ids(library_id)
        assert result == {1, 2, 3, 4}

    def test_get_mapped_ids_empty(
        self, mock_session: MockSession, library_id: int
    ) -> None:
        """Test get_mapped_ids with empty result.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.
        library_id : int
            Library ID.

        Covers lines 145-148.
        """
        mock_session.set_exec_result([])
        fetcher = MappedIdsFetcher(mock_session)  # type: ignore[arg-type]
        result = fetcher.get_mapped_ids(library_id)
        assert result == set()


class TestUnmatchedAuthorFetcher:
    """Test UnmatchedAuthorFetcher."""

    def test_init(self, mock_session: MockSession) -> None:
        """Test initialization.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.

        Covers lines 172-173.
        """
        fetcher = UnmatchedAuthorFetcher(mock_session)  # type: ignore[arg-type]
        assert fetcher._session is mock_session
        assert fetcher._calibre_repo_factory is CalibreBookRepository

    def test_fetch_unmatched_no_calibre_db_path(
        self, mock_session: MockSession
    ) -> None:
        """Test fetch_unmatched with no calibre_db_path.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.

        Covers lines 197-198.
        """
        fetcher = UnmatchedAuthorFetcher(mock_session)  # type: ignore[arg-type]
        result = fetcher.fetch_unmatched(set(), None, "metadata.db")
        assert result == []

    @patch("fundamental.repositories.author_listing_components.CalibreBookRepository")
    def test_fetch_unmatched_success(
        self,
        mock_repo_class: MagicMock,
        mock_session: MockSession,
    ) -> None:
        """Test fetch_unmatched success.

        Parameters
        ----------
        mock_repo_class : MagicMock
            Mock repository class.
        mock_session : MockSession
            Mock session.

        Covers lines 200-209.
        """
        # Create mock authors
        author1 = Author(id=1, name="Author 1")
        author2 = Author(id=2, name="Author 2")
        author3 = Author(id=3, name="Author 3")

        # Create mock calibre session
        mock_calibre_session = MagicMock()
        mock_calibre_result = MagicMock()
        mock_calibre_result.all.return_value = [author1, author2, author3]
        mock_calibre_session.exec.return_value = mock_calibre_result

        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.get_session.return_value.__enter__.return_value = mock_calibre_session
        mock_repo_class.return_value = mock_repo

        fetcher = UnmatchedAuthorFetcher(  # type: ignore[arg-type]
            mock_session,  # type: ignore[arg-type]
            calibre_repo_factory=mock_repo_class,  # type: ignore[arg-type]
        )
        mapped_ids = {1}  # Author 1 is mapped
        result = fetcher.fetch_unmatched(mapped_ids, "/path/to/db", "metadata.db")

        assert len(result) == 2
        assert author2 in result
        assert author3 in result
        assert author1 not in result

    @patch("fundamental.repositories.author_listing_components.CalibreBookRepository")
    def test_fetch_unmatched_with_none_id(
        self,
        mock_repo_class: MagicMock,
        mock_session: MockSession,
    ) -> None:
        """Test fetch_unmatched with author having None id.

        Parameters
        ----------
        mock_repo_class : MagicMock
            Mock repository class.
        mock_session : MockSession
            Mock session.

        Covers lines 200-209.
        """
        # Create mock author with None id
        author1 = Author(id=None, name="Author 1")

        # Create mock calibre session
        mock_calibre_session = MagicMock()
        mock_calibre_result = MagicMock()
        mock_calibre_result.all.return_value = [author1]
        mock_calibre_session.exec.return_value = mock_calibre_result

        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.get_session.return_value.__enter__.return_value = mock_calibre_session
        mock_repo_class.return_value = mock_repo

        fetcher = UnmatchedAuthorFetcher(  # type: ignore[arg-type]
            mock_session,  # type: ignore[arg-type]
            calibre_repo_factory=mock_repo_class,  # type: ignore[arg-type]
        )
        result = fetcher.fetch_unmatched(set(), "/path/to/db", "metadata.db")

        assert len(result) == 0

    @patch("fundamental.repositories.author_listing_components.logger")
    @patch("fundamental.repositories.author_listing_components.CalibreBookRepository")
    def test_fetch_unmatched_exception(
        self,
        mock_repo_class: MagicMock,
        mock_logger: MagicMock,
        mock_session: MockSession,
    ) -> None:
        """Test fetch_unmatched with exception.

        Parameters
        ----------
        mock_repo_class : MagicMock
            Mock repository class.
        mock_logger : MagicMock
            Mock logger.
        mock_session : MockSession
            Mock session.

        Covers lines 210-215.
        """
        mock_repo_class.side_effect = Exception("Database error")

        fetcher = UnmatchedAuthorFetcher(  # type: ignore[arg-type]
            mock_session,  # type: ignore[arg-type]
            calibre_repo_factory=mock_repo_class,  # type: ignore[arg-type]
        )
        result = fetcher.fetch_unmatched(set(), "/path/to/db", "metadata.db")

        assert result == []
        mock_logger.exception.assert_called_once()


class TestAuthorResultCombiner:
    """Test AuthorResultCombiner."""

    @pytest.mark.parametrize(
        ("matched_count", "unmatched_count", "page", "page_size", "expected_count"),
        [
            (5, 5, 1, 10, 10),
            (5, 5, 1, 5, 5),
            (5, 5, 2, 5, 5),
            (5, 5, 3, 5, 0),
            (0, 0, 1, 10, 0),
            (10, 0, 1, 5, 5),
            (0, 10, 1, 5, 5),
        ],
    )
    def test_combine_and_paginate(
        self,
        matched_count: int,
        unmatched_count: int,
        page: int,
        page_size: int,
        expected_count: int,
    ) -> None:
        """Test combine_and_paginate.

        Parameters
        ----------
        matched_count : int
            Number of matched results.
        unmatched_count : int
            Number of unmatched authors.
        page : int
            Page number.
        page_size : int
            Page size.
        expected_count : int
            Expected result count.

        Covers lines 249-261.
        """
        # Create matched results
        matched_results = [
            type("Row", (), {"name": f"Matched {i}", "type": "matched", "id": i})()
            for i in range(1, matched_count + 1)
        ]

        # Create unmatched authors
        unmatched_authors = [
            Author(id=i, name=f"Unmatched {i}") for i in range(1, unmatched_count + 1)
        ]

        result = AuthorResultCombiner.combine_and_paginate(
            matched_results, unmatched_authors, page, page_size
        )

        assert len(result) == expected_count
        # Verify results are sorted by name
        names = [r.name for r in result]
        assert names == sorted(names)

    def test_combine_and_paginate_with_none_id(self) -> None:
        """Test combine_and_paginate with author having None id.

        Covers lines 249-261.
        """
        matched_results = []
        unmatched_authors = [Author(id=None, name="Author None")]

        result = AuthorResultCombiner.combine_and_paginate(
            matched_results, unmatched_authors, 1, 10
        )

        assert len(result) == 0


class TestAuthorHydrator:
    """Test AuthorHydrator."""

    def test_init(self, mock_session: MockSession) -> None:
        """Test initialization.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.

        Covers lines 278.
        """
        hydrator = AuthorHydrator(mock_session)  # type: ignore[arg-type]
        assert hydrator._session is mock_session

    def test_hydrate_matched_empty(self, mock_session: MockSession) -> None:
        """Test hydrate_matched with empty list.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.

        Covers lines 293-294.
        """
        hydrator = AuthorHydrator(mock_session)  # type: ignore[arg-type]
        result = hydrator.hydrate_matched([])
        assert result == {}

    def test_hydrate_matched_success(self, mock_session: MockSession) -> None:
        """Test hydrate_matched success.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.

        Covers lines 296-310.
        """
        author1 = AuthorMetadata(id=1, name="Author 1", openlibrary_key="OL1A")
        author2 = AuthorMetadata(id=2, name="Author 2", openlibrary_key="OL2A")
        mock_session.set_exec_result([author1, author2])

        hydrator = AuthorHydrator(mock_session)  # type: ignore[arg-type]
        result = hydrator.hydrate_matched([1, 2])

        assert len(result) == 2
        assert result[1].id == 1
        assert result[2].id == 2

    @patch("fundamental.repositories.author_listing_components.logger")
    def test_hydrate_matched_exception(
        self, mock_logger: MagicMock, mock_session: MockSession
    ) -> None:
        """Test hydrate_matched with exception.

        Parameters
        ----------
        mock_logger : MagicMock
            Mock logger.
        mock_session : MockSession
            Mock session.

        Covers lines 311-313.
        """
        mock_session.set_exec_result([])
        mock_session.exec = MagicMock(side_effect=Exception("Database error"))  # type: ignore[assignment]

        hydrator = AuthorHydrator(mock_session)  # type: ignore[arg-type]
        with pytest.raises(Exception, match="Database error"):
            hydrator.hydrate_matched([1, 2])
        mock_logger.exception.assert_called_once()

    def test_create_unmatched_metadata_empty(self, mock_session: MockSession) -> None:
        """Test create_unmatched_metadata with empty list.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.

        Covers lines 334-335.
        """
        hydrator = AuthorHydrator(mock_session)  # type: ignore[arg-type]
        result = hydrator.create_unmatched_metadata([], "/path/to/db", "metadata.db")
        assert result == {}

    @patch("fundamental.repositories.author_listing_components.CalibreBookRepository")
    def test_create_unmatched_metadata_success(
        self,
        mock_repo_class: MagicMock,
        mock_session: MockSession,
    ) -> None:
        """Test create_unmatched_metadata success.

        Parameters
        ----------
        mock_repo_class : MagicMock
            Mock repository class.
        mock_session : MockSession
            Mock session.

        Covers lines 337-357.
        """
        author1 = Author(id=1, name="Author 1")
        author2 = Author(id=2, name="Author 2")

        # Create mock calibre session
        mock_calibre_session = MagicMock()
        mock_calibre_result = MagicMock()
        mock_calibre_result.all.return_value = [author1, author2]
        mock_calibre_session.exec.return_value = mock_calibre_result

        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.get_session.return_value.__enter__.return_value = mock_calibre_session
        mock_repo_class.return_value = mock_repo

        hydrator = AuthorHydrator(mock_session)  # type: ignore[arg-type]
        result = hydrator.create_unmatched_metadata(
            [1, 2], "/path/to/db", "metadata.db"
        )

        assert len(result) == 2
        assert 1 in result
        assert 2 in result
        assert result[1].name == "Author 1"
        # Check that is_unmatched was set (may be stored as private attribute)
        assert hasattr(result[1], "_calibre_id")
        assert result[1].openlibrary_key == "calibre-1"
        assert result[1].id is None

    @patch("fundamental.repositories.author_listing_components.CalibreBookRepository")
    def test_create_unmatched_metadata_with_none_id(
        self,
        mock_repo_class: MagicMock,
        mock_session: MockSession,
    ) -> None:
        """Test create_unmatched_metadata with author having None id.

        Parameters
        ----------
        mock_repo_class : MagicMock
            Mock repository class.
        mock_session : MockSession
            Mock session.

        Covers lines 337-357.
        """
        author1 = Author(id=None, name="Author 1")

        # Create mock calibre session
        mock_calibre_session = MagicMock()
        mock_calibre_result = MagicMock()
        mock_calibre_result.all.return_value = [author1]
        mock_calibre_session.exec.return_value = mock_calibre_result

        # Create mock repository
        mock_repo = MagicMock()
        mock_repo.get_session.return_value.__enter__.return_value = mock_calibre_session
        mock_repo_class.return_value = mock_repo

        hydrator = AuthorHydrator(mock_session)  # type: ignore[arg-type]
        result = hydrator.create_unmatched_metadata([1], "/path/to/db", "metadata.db")

        assert len(result) == 0

    @patch("fundamental.repositories.author_listing_components.logger")
    @patch("fundamental.repositories.author_listing_components.CalibreBookRepository")
    def test_create_unmatched_metadata_exception(
        self,
        mock_repo_class: MagicMock,
        mock_logger: MagicMock,
        mock_session: MockSession,
    ) -> None:
        """Test create_unmatched_metadata with exception.

        Parameters
        ----------
        mock_repo_class : MagicMock
            Mock repository class.
        mock_logger : MagicMock
            Mock logger.
        mock_session : MockSession
            Mock session.

        Covers lines 358-360.
        """
        mock_repo_class.side_effect = Exception("Database error")

        hydrator = AuthorHydrator(mock_session)  # type: ignore[arg-type]
        with pytest.raises(Exception, match="Database error"):
            hydrator.create_unmatched_metadata([1, 2], "/path/to/db", "metadata.db")
        mock_logger.exception.assert_called_once()


class TestMappedAuthorWithoutKeyFetcher:
    """Test MappedAuthorWithoutKeyFetcher."""

    def test_init(self, mock_session: MockSession) -> None:
        """Test initialization.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.

        Covers line 235.
        """
        from fundamental.repositories.author_listing_components import (
            MappedAuthorWithoutKeyFetcher,
        )

        fetcher = MappedAuthorWithoutKeyFetcher(mock_session)  # type: ignore[arg-type]
        assert fetcher._session is mock_session

    def test_fetch_mapped_without_key_success(
        self, mock_session: MockSession, library_id: int
    ) -> None:
        """Test fetch_mapped_without_key success.

        Parameters
        ----------
        mock_session : MockSession
            Mock session.
        library_id : int
            Library ID.

        Covers lines 250-270.
        """
        from fundamental.repositories.author_listing_components import (
            MappedAuthorWithoutKeyFetcher,
        )

        author1 = AuthorMetadata(
            id=1, name="Author 1", openlibrary_key=None, is_unmatched=False
        )
        author2 = AuthorMetadata(
            id=2, name="Author 2", openlibrary_key=None, is_unmatched=False
        )
        mock_session.set_exec_result([author1, author2])

        fetcher = MappedAuthorWithoutKeyFetcher(mock_session)  # type: ignore[arg-type]
        result = fetcher.fetch_mapped_without_key(library_id)

        assert len(result) == 2
        assert author1 in result
        assert author2 in result

    @patch("fundamental.repositories.author_listing_components.logger")
    def test_fetch_mapped_without_key_exception(
        self,
        mock_logger: MagicMock,
        mock_session: MockSession,
        library_id: int,
    ) -> None:
        """Test fetch_mapped_without_key with exception.

        Parameters
        ----------
        mock_logger : MagicMock
            Mock logger.
        mock_session : MockSession
            Mock session.
        library_id : int
            Library ID.

        Covers lines 271-273.
        """
        from fundamental.repositories.author_listing_components import (
            MappedAuthorWithoutKeyFetcher,
        )

        mock_session.exec = MagicMock(side_effect=Exception("Database error"))  # type: ignore[assignment]

        fetcher = MappedAuthorWithoutKeyFetcher(mock_session)  # type: ignore[arg-type]
        with pytest.raises(Exception, match="Database error"):
            fetcher.fetch_mapped_without_key(library_id)
        mock_logger.exception.assert_called_once()
