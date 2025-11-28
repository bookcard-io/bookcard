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

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from fundamental.models.author_metadata import AuthorMapping, AuthorMetadata
from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceNetworkError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.data_sources.types import AuthorData
from fundamental.services.library_scanning.matching.base import BaseMatchingStrategy
from fundamental.services.library_scanning.matching.orchestrator import (
    MatchingOrchestrator,
)
from fundamental.services.library_scanning.matching.types import MatchResult
from tests.conftest import DummySession


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


@pytest.fixture
def orchestrator() -> MatchingOrchestrator:
    """Create MatchingOrchestrator instance."""
    return MatchingOrchestrator()


class TestMatchingOrchestratorShouldSkipMatch:
    """Test _should_skip_match method."""

    def test_should_skip_match_valid_mapping(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match returns True for valid existing mapping."""
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            matched_by="exact",
        )
        metadata = AuthorMetadata(
            id=1,
            name="Test Author",
            openlibrary_key="OL123A",
        )
        session.set_exec_result([(mapping, metadata)])

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=None,
        )

        assert result is True

    def test_should_skip_match_unmatched_mapping(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match returns False for unmatched mapping."""
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            matched_by="unmatched",
        )
        metadata = AuthorMetadata(
            id=1,
            name="Test Author",
            openlibrary_key=None,
        )
        session.set_exec_result([(mapping, metadata)])

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=None,
        )

        assert result is False

    def test_should_skip_match_no_metadata_key(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match returns False when metadata has no key."""
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            matched_by="exact",
        )
        metadata = AuthorMetadata(
            id=1,
            name="Test Author",
            openlibrary_key=None,
        )
        session.set_exec_result([(mapping, metadata)])

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=None,
        )

        assert result is False

    def test_should_skip_match_no_mapping(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match returns False when no mapping exists."""
        session.set_exec_result([None])

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=None,
        )

        assert result is False

    def test_should_skip_match_stale_data_fresh(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match returns True for fresh data."""
        session.set_exec_result([None])  # No valid mapping from first query
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            updated_at=datetime.now(UTC) - timedelta(days=5),
        )
        session.add_exec_result([mapping])

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=30,
        )

        assert result is True

    def test_should_skip_match_stale_data_old(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match returns False for stale data."""
        session.set_exec_result([None])  # No valid mapping from first query
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            updated_at=datetime.now(UTC) - timedelta(days=35),
        )
        session.add_exec_result([mapping])

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=30,
        )

        assert result is False

    def test_should_skip_match_stale_data_no_updated_at(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match uses created_at when updated_at is None."""
        session.set_exec_result([None])  # No valid mapping from first query
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            updated_at=None,
            created_at=datetime.now(UTC) - timedelta(days=5),
        )
        session.add_exec_result([mapping])

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=30,
        )

        assert result is True

    def test_should_skip_match_stale_data_no_tzinfo(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match handles datetime without tzinfo."""
        session.set_exec_result([None])  # No valid mapping from first query
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            updated_at=datetime.now(UTC) - timedelta(days=5),
        )
        session.add_exec_result([mapping])

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=30,
        )

        assert result is True

    def test_should_skip_match_stale_data_no_mapping(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _should_skip_match returns False when no mapping for staleness check."""
        session.set_exec_result([None])  # No valid mapping from first query
        session.add_exec_result([None])  # No mapping for staleness check

        result = orchestrator._should_skip_match(
            session=session,  # type: ignore[arg-type]
            calibre_author_id=1,
            library_id=1,
            stale_data_max_age_days=30,
        )

        assert result is False


class TestMatchingOrchestratorHandleUnmatched:
    """Test _handle_unmatched method."""

    def test_handle_unmatched_author_id_none(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _handle_unmatched raises ValueError when author.id is None."""
        author = Author(id=None, name="Test Author")

        with pytest.raises(ValueError, match="Author ID cannot be None"):
            orchestrator._handle_unmatched(
                session=session,  # type: ignore[arg-type]
                author=author,
                library_id=1,
            )

    def test_handle_unmatched_creates_new(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _handle_unmatched creates new unmatched metadata and mapping."""
        author = Author(id=1, name="Test Author")
        session.set_exec_result([None])  # No existing mapping

        result = orchestrator._handle_unmatched(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
        )

        assert result is not None
        # Check that unmatched metadata was created
        unmatched_metadata = [m for m in session.added if isinstance(m, AuthorMetadata)]
        assert len(unmatched_metadata) == 1
        assert unmatched_metadata[0].name == "Test Author"
        assert unmatched_metadata[0].openlibrary_key is None
        assert session.commit_count > 0

    def test_handle_unmatched_reuses_existing_unmatched(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _handle_unmatched reuses existing unmatched metadata."""
        author = Author(id=1, name="Test Author Updated")
        existing_mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
        )
        existing_metadata = AuthorMetadata(
            id=1,
            name="Test Author",
            openlibrary_key=None,
        )
        session.set_exec_result([existing_mapping])
        session.set_get_result(AuthorMetadata, existing_metadata)  # type: ignore[valid-type]

        result = orchestrator._handle_unmatched(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
        )

        assert result == 1
        # Check that metadata name was updated
        assert existing_metadata.name == "Test Author Updated"
        assert existing_metadata in session.added
        assert session.commit_count > 0

    def test_handle_unmatched_does_not_reuse_matched(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _handle_unmatched does not reuse metadata with openlibrary_key."""
        author = Author(id=1, name="Test Author")
        existing_mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
        )
        existing_metadata = AuthorMetadata(
            id=1,
            name="Test Author",
            openlibrary_key="OL123A",  # Has key, so not unmatched
        )
        session.set_exec_result([existing_mapping])
        session.set_get_result(AuthorMetadata, existing_metadata)  # type: ignore[valid-type]

        result = orchestrator._handle_unmatched(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
        )

        assert result is not None
        # Should create new unmatched metadata
        unmatched_metadata = [
            m
            for m in session.added
            if isinstance(m, AuthorMetadata) and m.openlibrary_key is None
        ]
        assert len(unmatched_metadata) == 1

    def test_handle_unmatched_updates_existing_mapping(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _handle_unmatched updates existing mapping."""
        author = Author(id=1, name="Test Author")
        existing_mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
        )
        existing_metadata = AuthorMetadata(
            id=1,
            name="Test Author",
            openlibrary_key=None,
        )
        session.set_exec_result([existing_mapping])
        session.set_get_result(AuthorMetadata, existing_metadata)  # type: ignore[valid-type]

        result = orchestrator._handle_unmatched(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
        )

        assert result == 1
        assert session.commit_count > 0

    def test_handle_unmatched_metadata_id_none_after_flush(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
    ) -> None:
        """Test _handle_unmatched raises ValueError when metadata.id is None after flush."""
        author = Author(id=1, name="Test Author")
        session.set_exec_result([None])  # No existing mapping

        # Mock flush to not assign ID
        original_flush = session.flush

        def mock_flush() -> None:
            original_flush()
            # Remove ID from any added metadata
            for item in session.added:
                if isinstance(item, AuthorMetadata):
                    item.id = None

        session.flush = mock_flush  # type: ignore[method-assign]

        with pytest.raises(ValueError, match="Failed to generate ID"):
            orchestrator._handle_unmatched(
                session=session,  # type: ignore[arg-type]
                author=author,
                library_id=1,
            )


class TestMatchingOrchestratorProcessMatchRequest:
    """Test process_match_request method."""

    def test_process_match_request_author_no_id(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test process_match_request returns None when author has no ID."""
        author = Author(id=None, name="Test Author")

        result = orchestrator.process_match_request(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
            data_source=mock_data_source,
        )

        assert result is None

    def test_process_match_request_skips_when_matched(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test process_match_request skips when author already matched."""
        author = Author(id=1, name="Test Author")
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            matched_by="exact",
        )
        metadata = AuthorMetadata(
            id=1,
            name="Test Author",
            openlibrary_key="OL123A",
        )
        session.set_exec_result([(mapping, metadata)])

        result = orchestrator.process_match_request(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
            data_source=mock_data_source,
        )

        assert result is None

    def test_process_match_request_force_rematch(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test process_match_request performs match when force_rematch is True."""
        author = Author(id=1, name="Test Author")
        mapping = AuthorMapping(
            id=1,
            calibre_author_id=1,
            library_id=1,
            author_metadata_id=1,
            matched_by="exact",
        )
        metadata = AuthorMetadata(
            id=1,
            name="Test Author",
            openlibrary_key="OL123A",
        )
        session.set_exec_result([(mapping, metadata)])  # Existing mapping

        match_result = MatchResult(
            confidence_score=0.9,
            matched_entity=MagicMock(),
            match_method="exact",
        )
        mock_strategy = MagicMock(spec=BaseMatchingStrategy)
        mock_strategy.name = "test"
        mock_strategy.match.return_value = match_result

        orchestrator.strategies = [mock_strategy]

        result = orchestrator.process_match_request(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
            data_source=mock_data_source,
            force_rematch=True,
        )

        assert result == match_result
        assert result.calibre_author_id == 1  # type: ignore[valid-type]

    def test_process_match_request_force_rematch_with_key(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test process_match_request uses openlibrary_key when provided."""
        author = Author(id=1, name="Test Author")
        author_data = AuthorData(
            key="/authors/OL123A",
            name="Test Author",
            personal_name="Test",
            work_count=10,
        )
        mock_data_source.get_author.return_value = author_data

        result = orchestrator.process_match_request(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
            data_source=mock_data_source,
            force_rematch=True,
            openlibrary_key="OL123A",
        )

        assert result is not None
        assert result.confidence_score == 1.0
        assert result.match_method == "direct_key"
        assert result.matched_entity == author_data
        assert result.calibre_author_id == 1
        mock_data_source.get_author.assert_called_once_with("OL123A")

    def test_process_match_request_force_rematch_key_not_found(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test process_match_request handles key not found in data source."""
        author = Author(id=1, name="Test Author")
        mock_data_source.get_author.return_value = None

        result = orchestrator.process_match_request(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
            data_source=mock_data_source,
            force_rematch=True,
            openlibrary_key="OL123A",
        )

        # Should fall through to unmatched handling
        assert result is None
        assert session.commit_count > 0

    def test_process_match_request_no_match_handles_unmatched(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test process_match_request handles unmatched when no match found."""
        author = Author(id=1, name="Test Author")
        session.set_exec_result([None])  # No existing mapping
        session.add_exec_result([None])  # No mapping for staleness check

        mock_strategy = MagicMock(spec=BaseMatchingStrategy)
        mock_strategy.name = "test"
        mock_strategy.match.return_value = None

        orchestrator.strategies = [mock_strategy]

        result = orchestrator.process_match_request(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
            data_source=mock_data_source,
        )

        assert result is None
        # Should have created unmatched metadata
        assert session.commit_count > 0

    def test_process_match_request_match_found(
        self,
        orchestrator: MatchingOrchestrator,
        session: DummySession,
        mock_data_source: MagicMock,
    ) -> None:
        """Test process_match_request returns match result when found."""
        author = Author(id=1, name="Test Author")
        session.set_exec_result([None])  # No existing mapping
        session.add_exec_result([None])  # No mapping for staleness check

        match_result = MatchResult(
            confidence_score=0.9,
            matched_entity=MagicMock(),
            match_method="exact",
        )
        mock_strategy = MagicMock(spec=BaseMatchingStrategy)
        mock_strategy.name = "test"
        mock_strategy.match.return_value = match_result

        orchestrator.strategies = [mock_strategy]

        result = orchestrator.process_match_request(
            session=session,  # type: ignore[arg-type]
            author=author,
            library_id=1,
            data_source=mock_data_source,
        )

        assert result == match_result
        assert result.calibre_author_id == 1  # type: ignore[valid-type]
