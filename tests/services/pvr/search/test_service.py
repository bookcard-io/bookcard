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

"""Tests for IndexerSearchService."""

from unittest.mock import MagicMock, patch

import pytest

from bookcard.models.pvr import IndexerDefinition
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.indexer_service import IndexerService
from bookcard.services.pvr.search.aggregation import (
    ResultAggregator,
    URLDeduplicationStrategy,
)
from bookcard.services.pvr.search.filtering import IndexerSearchFilter
from bookcard.services.pvr.search.orchestration import SearchOrchestrator
from bookcard.services.pvr.search.scoring import DefaultScoringStrategy, ReleaseScorer
from bookcard.services.pvr.search.service import IndexerSearchService


@pytest.fixture
def mock_indexer_service() -> MagicMock:
    """Create mock indexer service.

    Returns
    -------
    MagicMock
        Mock indexer service.
    """
    return MagicMock(spec=IndexerService)


@pytest.fixture
def search_service(mock_indexer_service: MagicMock) -> IndexerSearchService:
    """Create search service with mocked dependencies.

    Parameters
    ----------
    mock_indexer_service : MagicMock
        Mock indexer service.

    Returns
    -------
    IndexerSearchService
        Search service instance.
    """
    return IndexerSearchService(indexer_service=mock_indexer_service)


class TestIndexerSearchService:
    """Test IndexerSearchService."""

    def test_init_defaults(self, mock_indexer_service: MagicMock) -> None:
        """Test service initialization with defaults.

        Parameters
        ----------
        mock_indexer_service : MagicMock
            Mock indexer service.
        """
        service = IndexerSearchService(indexer_service=mock_indexer_service)

        assert service._indexer_service == mock_indexer_service
        assert isinstance(service._scorer, ReleaseScorer)
        assert isinstance(service._aggregator, ResultAggregator)
        assert isinstance(service._orchestrator, SearchOrchestrator)

    def test_init_custom_components(self, mock_indexer_service: MagicMock) -> None:
        """Test service initialization with custom components.

        Parameters
        ----------
        mock_indexer_service : MagicMock
            Mock indexer service.
        """
        scorer = ReleaseScorer(DefaultScoringStrategy())
        aggregator = ResultAggregator(URLDeduplicationStrategy())
        orchestrator = SearchOrchestrator(max_workers=10, timeout_seconds=60)

        service = IndexerSearchService(
            indexer_service=mock_indexer_service,
            scorer=scorer,
            aggregator=aggregator,
            orchestrator=orchestrator,
        )

        assert service._scorer == scorer
        assert service._aggregator == aggregator
        assert service._orchestrator == orchestrator

    def test_search_all_indexers_empty_query(
        self, search_service: IndexerSearchService
    ) -> None:
        """Test search with empty query.

        Parameters
        ----------
        search_service : IndexerSearchService
            Search service instance.
        """
        results = search_service.search_all_indexers(query="")
        assert results == []

        results = search_service.search_all_indexers(query="   ")
        assert results == []

    def test_search_all_indexers_no_indexers(
        self, search_service: IndexerSearchService, mock_indexer_service: MagicMock
    ) -> None:
        """Test search with no enabled indexers.

        Parameters
        ----------
        search_service : IndexerSearchService
            Search service instance.
        mock_indexer_service : MagicMock
            Mock indexer service.
        """
        mock_indexer_service.list_decrypted_indexers.return_value = []

        results = search_service.search_all_indexers(query="test")

        assert results == []

    @patch("bookcard.services.pvr.search.service.create_indexer")
    def test_search_all_indexers_success(
        self,
        mock_create_indexer: MagicMock,
        search_service: IndexerSearchService,
        mock_indexer_service: MagicMock,
        sample_indexer: IndexerDefinition,
    ) -> None:
        """Test successful search across indexers.

        Parameters
        ----------
        mock_create_indexer : MagicMock
            Mock create_indexer function.
        search_service : IndexerSearchService
            Search service instance.
        mock_indexer_service : MagicMock
            Mock indexer service.
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        mock_indexer_service.list_decrypted_indexers.return_value = [sample_indexer]

        mock_indexer = MagicMock()
        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/book.torrent",
        )
        mock_indexer.search.return_value = [release]
        mock_create_indexer.return_value = mock_indexer

        results = search_service.search_all_indexers(query="test")

        assert len(results) > 0
        assert results[0].release == release

    def test_search_indexer_not_found(
        self, search_service: IndexerSearchService, mock_indexer_service: MagicMock
    ) -> None:
        """Test search with non-existent indexer.

        Parameters
        ----------
        search_service : IndexerSearchService
            Search service instance.
        mock_indexer_service : MagicMock
            Mock indexer service.
        """
        mock_indexer_service.get_decrypted_indexer.return_value = None

        with pytest.raises(ValueError, match="not found"):
            search_service.search_indexer(indexer_id=999, query="test")

    def test_search_indexer_disabled(
        self,
        search_service: IndexerSearchService,
        mock_indexer_service: MagicMock,
        sample_indexer: IndexerDefinition,
    ) -> None:
        """Test search with disabled indexer.

        Parameters
        ----------
        search_service : IndexerSearchService
            Search service instance.
        mock_indexer_service : MagicMock
            Mock indexer service.
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        sample_indexer.enabled = False
        mock_indexer_service.get_decrypted_indexer.return_value = sample_indexer

        results = search_service.search_indexer(indexer_id=1, query="test")

        assert results == []

    @patch("bookcard.services.pvr.search.service.create_indexer")
    def test_search_indexer_success(
        self,
        mock_create_indexer: MagicMock,
        search_service: IndexerSearchService,
        mock_indexer_service: MagicMock,
        sample_indexer: IndexerDefinition,
    ) -> None:
        """Test successful single indexer search.

        Parameters
        ----------
        mock_create_indexer : MagicMock
            Mock create_indexer function.
        search_service : IndexerSearchService
            Search service instance.
        mock_indexer_service : MagicMock
            Mock indexer service.
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        mock_indexer_service.get_decrypted_indexer.return_value = sample_indexer

        mock_indexer = MagicMock()
        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/book.torrent",
        )
        mock_indexer.search.return_value = [release]
        mock_create_indexer.return_value = mock_indexer

        results = search_service.search_indexer(indexer_id=1, query="test")

        assert len(results) > 0
        assert results[0].release == release

    def test_search_indexer_with_filter(
        self,
        search_service: IndexerSearchService,
        mock_indexer_service: MagicMock,
        sample_indexer: IndexerDefinition,
    ) -> None:
        """Test search with filter criteria.

        Parameters
        ----------
        search_service : IndexerSearchService
            Search service instance.
        mock_indexer_service : MagicMock
            Mock indexer service.
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        mock_indexer_service.get_decrypted_indexer.return_value = sample_indexer

        with patch(
            "bookcard.services.pvr.search.service.create_indexer"
        ) as mock_create:
            mock_indexer = MagicMock()
            release1 = ReleaseInfo(
                title="Test Book EPUB",
                download_url="https://example.com/book1.torrent",
                quality="epub",
            )
            release2 = ReleaseInfo(
                title="Test Book PDF",
                download_url="https://example.com/book2.torrent",
                quality="pdf",
            )
            mock_indexer.search.return_value = [release1, release2]
            mock_create.return_value = mock_indexer

            filter_criteria = IndexerSearchFilter(formats=["epub"])

            results = search_service.search_indexer(
                indexer_id=1, query="test", filter_criteria=filter_criteria
            )

            # Should only return epub result
            assert len(results) == 1
            assert results[0].release.quality == "epub"

    def test_get_indexers_to_search_specific_ids(
        self,
        search_service: IndexerSearchService,
        mock_indexer_service: MagicMock,
        sample_indexer: IndexerDefinition,
    ) -> None:
        """Test getting specific indexers by ID.

        Parameters
        ----------
        search_service : IndexerSearchService
            Search service instance.
        mock_indexer_service : MagicMock
            Mock indexer service.
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        mock_indexer_service.get_decrypted_indexer.return_value = sample_indexer

        indexers = search_service._get_indexers_to_search([1, 2])

        assert len(indexers) > 0

    def test_get_indexers_to_search_all_enabled(
        self,
        search_service: IndexerSearchService,
        mock_indexer_service: MagicMock,
        sample_indexer: IndexerDefinition,
    ) -> None:
        """Test getting all enabled indexers.

        Parameters
        ----------
        search_service : IndexerSearchService
            Search service instance.
        mock_indexer_service : MagicMock
            Mock indexer service.
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        mock_indexer_service.list_decrypted_indexers.return_value = [sample_indexer]

        indexers = search_service._get_indexers_to_search(None)

        assert len(indexers) == 1
        assert indexers[0] == sample_indexer
