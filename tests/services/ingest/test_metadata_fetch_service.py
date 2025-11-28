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

"""Tests for metadata fetch service to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from unittest.mock import MagicMock

from fundamental.models.metadata import MetadataRecord
from fundamental.services.ingest.metadata_fetch_service import MetadataFetchService
from fundamental.services.ingest.metadata_merger import MergeStrategy, MetadataMerger
from fundamental.services.ingest.metadata_query import MetadataQuery
from fundamental.services.ingest.metadata_scorer import MetadataScorer, ScoringConfig
from fundamental.services.metadata_service import MetadataService


@pytest.fixture
def scorer() -> MetadataScorer:
    """Create MetadataScorer instance."""
    return MetadataScorer()


@pytest.fixture
def merger() -> MetadataMerger:
    """Create MetadataMerger instance."""
    return MetadataMerger()


@pytest.fixture
def service(
    mock_metadata_service: MagicMock, scorer: MetadataScorer, merger: MetadataMerger
) -> MetadataFetchService:
    """Create MetadataFetchService instance."""
    return MetadataFetchService(
        metadata_service=mock_metadata_service,
        scorer=scorer,
        merger=merger,
    )


@pytest.fixture
def service_with_providers(
    mock_metadata_service: MagicMock,
    scorer: MetadataScorer,
    merger: MetadataMerger,
) -> MetadataFetchService:
    """Create MetadataFetchService with enabled providers."""
    return MetadataFetchService(
        metadata_service=mock_metadata_service,
        scorer=scorer,
        merger=merger,
        enabled_providers=["openlibrary", "google"],
    )


def test_init_with_all_deps(
    mock_metadata_service: MagicMock, scorer: MetadataScorer, merger: MetadataMerger
) -> None:
    """Test MetadataFetchService initialization with all dependencies."""
    service = MetadataFetchService(
        metadata_service=mock_metadata_service,
        scorer=scorer,
        merger=merger,
    )
    assert service._metadata_service == mock_metadata_service
    assert service._scorer == scorer
    assert service._merger == merger


def test_init_with_defaults(mock_metadata_service: MagicMock) -> None:
    """Test MetadataFetchService initialization with default dependencies."""
    service = MetadataFetchService(metadata_service=mock_metadata_service)
    assert isinstance(service._scorer, MetadataScorer)
    assert isinstance(service._merger, MetadataMerger)


def test_create_default() -> None:
    """Test create_default factory method."""
    service = MetadataFetchService.create_default()
    assert isinstance(service._metadata_service, MetadataService)
    assert isinstance(service._scorer, MetadataScorer)
    assert isinstance(service._merger, MetadataMerger)


def test_create_default_with_providers() -> None:
    """Test create_default with enabled providers."""
    service = MetadataFetchService.create_default(enabled_providers=["openlibrary"])
    assert service._enabled_providers == ["openlibrary"]


def test_create_default_with_weights() -> None:
    """Test create_default with provider weights."""
    service = MetadataFetchService.create_default(provider_weights={"openlibrary": 1.5})
    assert service._scorer._provider_weights == {"openlibrary": 1.5}


def test_create_default_with_config() -> None:
    """Test create_default with scoring config."""
    config = ScoringConfig()
    service = MetadataFetchService.create_default(scoring_config=config)
    assert service._scorer._config == config


def test_create_default_with_strategy() -> None:
    """Test create_default with merge strategy."""
    service = MetadataFetchService.create_default(
        merge_strategy=MergeStrategy.FIRST_WINS
    )
    assert service._merger._strategy == MergeStrategy.FIRST_WINS


def test_fetch_metadata_invalid_query(service: MetadataFetchService) -> None:
    """Test fetch_metadata with invalid query."""
    query = MetadataQuery()
    result = service.fetch_metadata(query)
    assert result is None


def test_fetch_metadata_empty_search_string(service: MetadataFetchService) -> None:
    """Test fetch_metadata with empty search string."""
    query = MetadataQuery(title="", authors=[], isbn="")
    result = service.fetch_metadata(query)
    assert result is None


def test_fetch_metadata_success(
    service: MetadataFetchService,
    mock_metadata_service: MagicMock,
    metadata_record: MetadataRecord,
) -> None:
    """Test fetch_metadata with successful fetch."""
    query = MetadataQuery(title="Test Book", authors=["Test Author"])
    mock_metadata_service.search.return_value = [metadata_record]
    result = service.fetch_metadata(query)
    assert result is not None
    assert result.title == "Test Book"


def test_fetch_metadata_no_results(
    service: MetadataFetchService, mock_metadata_service: MagicMock
) -> None:
    """Test fetch_metadata with no results."""
    query = MetadataQuery(title="Test Book")
    mock_metadata_service.search.return_value = []
    result = service.fetch_metadata(query)
    assert result is None


@pytest.mark.parametrize(
    "exception",
    [
        ValueError("Error"),
        RuntimeError("Error"),
        ConnectionError("Error"),
        TimeoutError("Error"),
    ],
)
def test_fetch_metadata_exceptions(
    service: MetadataFetchService,
    mock_metadata_service: MagicMock,
    exception: Exception,
) -> None:
    """Test fetch_metadata handles various exceptions."""
    query = MetadataQuery(title="Test Book")
    mock_metadata_service.search.side_effect = exception
    result = service.fetch_metadata(query)
    assert result is None


def test_fetch_metadata_with_enabled_providers(
    service_with_providers: MetadataFetchService,
    mock_metadata_service: MagicMock,
    metadata_record: MetadataRecord,
) -> None:
    """Test fetch_metadata uses enabled providers."""
    query = MetadataQuery(title="Test Book")
    mock_metadata_service.search.return_value = [metadata_record]
    result = service_with_providers.fetch_metadata(query)
    assert result is not None
    mock_metadata_service.search.assert_called_once()
    call_kwargs = mock_metadata_service.search.call_args[1]
    assert call_kwargs["provider_ids"] == ["openlibrary", "google"]


def test_fetch_metadata_with_locale(
    service: MetadataFetchService,
    mock_metadata_service: MagicMock,
    metadata_record: MetadataRecord,
) -> None:
    """Test fetch_metadata passes locale to search."""
    query = MetadataQuery(title="Test Book", locale="fr")
    mock_metadata_service.search.return_value = [metadata_record]
    service.fetch_metadata(query)
    call_kwargs = mock_metadata_service.search.call_args[1]
    assert call_kwargs["locale"] == "fr"


def test_fetch_metadata_with_max_results(
    service: MetadataFetchService,
    mock_metadata_service: MagicMock,
    metadata_record: MetadataRecord,
) -> None:
    """Test fetch_metadata passes max_results_per_provider."""
    query = MetadataQuery(title="Test Book", max_results_per_provider=5)
    mock_metadata_service.search.return_value = [metadata_record]
    service.fetch_metadata(query)
    call_kwargs = mock_metadata_service.search.call_args[1]
    assert call_kwargs["max_results_per_provider"] == 5


def test_score_and_merge(
    service: MetadataFetchService,
    metadata_record: MetadataRecord,
    scorer: MetadataScorer,
    merger: MetadataMerger,
) -> None:
    """Test _score_and_merge method."""
    query = MetadataQuery(title="Test Book", authors=["Test Author"])
    records = [metadata_record]
    result = service._score_and_merge(records, query)
    assert result is not None
    assert isinstance(result, MetadataRecord)
