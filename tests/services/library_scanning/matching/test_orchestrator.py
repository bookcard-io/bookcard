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

"""Tests for matching orchestrator to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceNetworkError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.matching.base import BaseMatchingStrategy
from fundamental.services.library_scanning.matching.orchestrator import (
    MatchingOrchestrator,
)
from fundamental.services.library_scanning.matching.types import MatchResult


@pytest.fixture
def mock_author() -> Author:
    """Create a mock author."""
    return Author(id=1, name="Test Author")


@pytest.fixture
def mock_data_source() -> MagicMock:
    """Create a mock data source."""
    return MagicMock(spec=BaseDataSource)


@pytest.fixture
def mock_strategy() -> MagicMock:
    """Create a mock matching strategy."""
    strategy = MagicMock(spec=BaseMatchingStrategy)
    strategy.name = "test_strategy"
    return strategy


def test_matching_orchestrator_init_default() -> None:
    """Test MatchingOrchestrator initialization with defaults."""
    orchestrator = MatchingOrchestrator()
    assert len(orchestrator.strategies) == 3
    assert orchestrator.min_confidence == 0.5


def test_matching_orchestrator_init_custom() -> None:
    """Test MatchingOrchestrator initialization with custom strategies."""
    strategies = [MagicMock(spec=BaseMatchingStrategy) for _ in range(2)]
    orchestrator = MatchingOrchestrator(strategies=strategies, min_confidence=0.7)
    assert orchestrator.strategies == strategies
    assert orchestrator.min_confidence == 0.7


def test_match_success_first_strategy(
    mock_author: Author,
    mock_data_source: MagicMock,
    mock_strategy: MagicMock,
) -> None:
    """Test match succeeds with first strategy."""
    match_result = MatchResult(
        confidence_score=0.8,
        matched_entity=MagicMock(),
        match_method="test",
    )
    mock_strategy.match.return_value = match_result

    orchestrator = MatchingOrchestrator(strategies=[mock_strategy], min_confidence=0.5)
    result = orchestrator.match(mock_author, mock_data_source)

    assert result == match_result
    mock_strategy.match.assert_called_once_with(mock_author, mock_data_source)


def test_match_below_threshold(
    mock_author: Author,
    mock_data_source: MagicMock,
    mock_strategy: MagicMock,
) -> None:
    """Test match returns None when confidence below threshold."""
    match_result = MatchResult(
        confidence_score=0.3,
        matched_entity=MagicMock(),
        match_method="test",
    )
    mock_strategy.match.return_value = match_result

    orchestrator = MatchingOrchestrator(strategies=[mock_strategy], min_confidence=0.5)
    result = orchestrator.match(mock_author, mock_data_source)

    assert result is None


def test_match_tries_next_strategy_on_low_confidence(
    mock_author: Author,
    mock_data_source: MagicMock,
) -> None:
    """Test match tries next strategy when first returns low confidence."""
    strategy1 = MagicMock(spec=BaseMatchingStrategy)
    strategy1.name = "strategy1"
    strategy1.match.return_value = MatchResult(
        confidence_score=0.3,
        matched_entity=MagicMock(),
        match_method="test",
    )

    strategy2 = MagicMock(spec=BaseMatchingStrategy)
    strategy2.name = "strategy2"
    match_result = MatchResult(
        confidence_score=0.8,
        matched_entity=MagicMock(),
        match_method="test",
    )
    strategy2.match.return_value = match_result

    orchestrator = MatchingOrchestrator(
        strategies=[strategy1, strategy2], min_confidence=0.5
    )
    result = orchestrator.match(mock_author, mock_data_source)

    assert result == match_result
    strategy1.match.assert_called_once()
    strategy2.match.assert_called_once()


def test_match_handles_network_error(
    mock_author: Author,
    mock_data_source: MagicMock,
) -> None:
    """Test match handles DataSourceNetworkError and tries next strategy."""
    strategy1 = MagicMock(spec=BaseMatchingStrategy)
    strategy1.name = "strategy1"
    strategy1.match.side_effect = DataSourceNetworkError("Network error")

    strategy2 = MagicMock(spec=BaseMatchingStrategy)
    strategy2.name = "strategy2"
    match_result = MatchResult(
        confidence_score=0.8,
        matched_entity=MagicMock(),
        match_method="test",
    )
    strategy2.match.return_value = match_result

    orchestrator = MatchingOrchestrator(
        strategies=[strategy1, strategy2], min_confidence=0.5
    )
    result = orchestrator.match(mock_author, mock_data_source)

    assert result == match_result
    strategy1.match.assert_called_once()
    strategy2.match.assert_called_once()


def test_match_handles_rate_limit_error(
    mock_author: Author,
    mock_data_source: MagicMock,
) -> None:
    """Test match handles DataSourceRateLimitError and tries next strategy."""
    strategy1 = MagicMock(spec=BaseMatchingStrategy)
    strategy1.name = "strategy1"
    strategy1.match.side_effect = DataSourceRateLimitError("Rate limit")

    strategy2 = MagicMock(spec=BaseMatchingStrategy)
    strategy2.name = "strategy2"
    match_result = MatchResult(
        confidence_score=0.8,
        matched_entity=MagicMock(),
        match_method="test",
    )
    strategy2.match.return_value = match_result

    orchestrator = MatchingOrchestrator(
        strategies=[strategy1, strategy2], min_confidence=0.5
    )
    result = orchestrator.match(mock_author, mock_data_source)

    assert result == match_result
    strategy1.match.assert_called_once()
    strategy2.match.assert_called_once()


def test_match_returns_none_when_all_fail(
    mock_author: Author,
    mock_data_source: MagicMock,
    mock_strategy: MagicMock,
) -> None:
    """Test match returns None when all strategies fail."""
    mock_strategy.match.return_value = None

    orchestrator = MatchingOrchestrator(strategies=[mock_strategy], min_confidence=0.5)
    result = orchestrator.match(mock_author, mock_data_source)

    assert result is None


def test_match_returns_none_when_all_raise_errors(
    mock_author: Author,
    mock_data_source: MagicMock,
) -> None:
    """Test match returns None when all strategies raise errors."""
    strategy1 = MagicMock(spec=BaseMatchingStrategy)
    strategy1.name = "strategy1"
    strategy1.match.side_effect = DataSourceNetworkError("Network error")

    strategy2 = MagicMock(spec=BaseMatchingStrategy)
    strategy2.name = "strategy2"
    strategy2.match.side_effect = DataSourceRateLimitError("Rate limit")

    orchestrator = MatchingOrchestrator(
        strategies=[strategy1, strategy2], min_confidence=0.5
    )
    result = orchestrator.match(mock_author, mock_data_source)

    assert result is None
