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

"""Tests for merge_strategies to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from bookcard.models.author_metadata import AuthorMapping, AuthorMetadata
from bookcard.services.author_merge.author_relationship_repository import (
    AuthorRelationshipRepository,
)
from bookcard.services.author_merge.calibre_author_service import (
    CalibreAuthorService,
)
from bookcard.services.author_merge.merge_strategies import (
    BothHaveBooksMergeStrategy,
    MergeStrategyFactory,
    ZeroBooksMergeStrategy,
)
from bookcard.services.author_merge.value_objects import MergeContext

if TYPE_CHECKING:
    from tests.conftest import DummySession

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_calibre_author_service() -> MagicMock:
    """Create a mock Calibre author service."""
    return MagicMock(spec=CalibreAuthorService)


@pytest.fixture
def mock_relationship_repo() -> MagicMock:
    """Create a mock relationship repository."""
    return MagicMock(spec=AuthorRelationshipRepository)


@pytest.fixture
def keep_author() -> AuthorMetadata:
    """Create keep author."""
    return AuthorMetadata(id=1, openlibrary_key="OL1A", name="Keep Author")


@pytest.fixture
def merge_author() -> AuthorMetadata:
    """Create merge author."""
    return AuthorMetadata(id=2, openlibrary_key="OL2A", name="Merge Author")


@pytest.fixture
def keep_mapping() -> AuthorMapping:
    """Create keep author mapping."""
    return AuthorMapping(
        id=1,
        calibre_author_id=10,
        author_metadata_id=1,
        library_id=1,
        is_verified=True,
    )


@pytest.fixture
def merge_mapping() -> AuthorMapping:
    """Create merge author mapping."""
    return AuthorMapping(
        id=2,
        calibre_author_id=20,
        author_metadata_id=2,
        library_id=1,
        is_verified=False,
    )


@pytest.fixture
def merge_context(
    keep_author: AuthorMetadata,
    merge_author: AuthorMetadata,
    keep_mapping: AuthorMapping,
    merge_mapping: AuthorMapping,
) -> MergeContext:
    """Create merge context."""
    return MergeContext(
        keep_author=keep_author,
        merge_author=merge_author,
        library_id=1,
        keep_mapping=keep_mapping,
        merge_mapping=merge_mapping,
    )


@pytest.fixture
def zero_books_strategy(
    session: DummySession,
    mock_calibre_author_service: MagicMock,
    mock_relationship_repo: MagicMock,
) -> ZeroBooksMergeStrategy:
    """Create ZeroBooksMergeStrategy instance."""
    return ZeroBooksMergeStrategy(
        session=session,  # type: ignore[arg-type]
        calibre_author_service=mock_calibre_author_service,
        relationship_repo=mock_relationship_repo,
        data_directory=None,
    )


@pytest.fixture
def both_have_books_strategy(
    session: DummySession,
    mock_calibre_author_service: MagicMock,
    mock_relationship_repo: MagicMock,
) -> BothHaveBooksMergeStrategy:
    """Create BothHaveBooksMergeStrategy instance."""
    return BothHaveBooksMergeStrategy(
        session=session,  # type: ignore[arg-type]
        calibre_author_service=mock_calibre_author_service,
        relationship_repo=mock_relationship_repo,
        data_directory=None,
    )


# ============================================================================
# ZeroBooksMergeStrategy Tests
# ============================================================================


class TestZeroBooksMergeStrategyInit:
    """Test ZeroBooksMergeStrategy initialization."""

    def test_init(
        self,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test __init__ stores dependencies."""
        strategy = ZeroBooksMergeStrategy(
            session=session,  # type: ignore[arg-type]
            calibre_author_service=mock_calibre_author_service,
            relationship_repo=mock_relationship_repo,
            data_directory="/data",
        )

        assert strategy._session == session
        assert strategy._calibre_author_service == mock_calibre_author_service
        assert strategy._relationship_repo == mock_relationship_repo
        assert strategy._data_directory == "/data"


class TestZeroBooksMergeStrategyCanHandle:
    """Test ZeroBooksMergeStrategy.can_handle method."""

    def test_can_handle_zero_books(
        self,
        zero_books_strategy: ZeroBooksMergeStrategy,
        merge_context: MergeContext,
        mock_calibre_author_service: MagicMock,
    ) -> None:
        """Test can_handle returns True when merge author has zero books."""
        mock_calibre_author_service.get_book_count.return_value = 0

        result = zero_books_strategy.can_handle(merge_context)

        assert result is True
        mock_calibre_author_service.get_book_count.assert_called_once_with(20)

    def test_can_handle_non_zero_books(
        self,
        zero_books_strategy: ZeroBooksMergeStrategy,
        merge_context: MergeContext,
        mock_calibre_author_service: MagicMock,
    ) -> None:
        """Test can_handle returns False when merge author has books."""
        mock_calibre_author_service.get_book_count.return_value = 5

        result = zero_books_strategy.can_handle(merge_context)

        assert result is False


class TestZeroBooksMergeStrategyExecute:
    """Test ZeroBooksMergeStrategy.execute method."""

    def test_execute_with_author_id(
        self,
        zero_books_strategy: ZeroBooksMergeStrategy,
        merge_context: MergeContext,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test execute with author having ID."""
        zero_books_strategy.execute(merge_context)

        mock_calibre_author_service.delete_author.assert_called_once_with(20)
        assert merge_context.merge_mapping in session.deleted
        assert session.flush_count >= 1
        mock_relationship_repo.delete_author_works.assert_called_once_with(2)
        mock_relationship_repo.delete_author_user_photos.assert_called_once_with(
            2, None
        )
        mock_relationship_repo.delete_author_user_metadata.assert_called_once_with(2)
        mock_relationship_repo.cleanup_remaining_similarities.assert_called_once_with(2)
        assert merge_context.merge_author in session.deleted

    def test_execute_without_author_id(
        self,
        zero_books_strategy: ZeroBooksMergeStrategy,
        merge_context: MergeContext,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test execute with author without ID."""
        merge_context.merge_author.id = None

        zero_books_strategy.execute(merge_context)

        mock_calibre_author_service.delete_author.assert_called_once_with(20)
        assert merge_context.merge_mapping in session.deleted
        mock_relationship_repo.delete_author_works.assert_not_called()
        mock_relationship_repo.delete_author_user_photos.assert_not_called()
        mock_relationship_repo.delete_author_user_metadata.assert_not_called()
        mock_relationship_repo.cleanup_remaining_similarities.assert_not_called()
        assert merge_context.merge_author in session.deleted

    def test_execute_with_data_directory(
        self,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
        merge_context: MergeContext,
    ) -> None:
        """Test execute with data directory."""
        strategy = ZeroBooksMergeStrategy(
            session=session,  # type: ignore[arg-type]
            calibre_author_service=mock_calibre_author_service,
            relationship_repo=mock_relationship_repo,
            data_directory="/data",
        )

        strategy.execute(merge_context)

        mock_relationship_repo.delete_author_user_photos.assert_called_once_with(
            2, "/data"
        )


# ============================================================================
# BothHaveBooksMergeStrategy Tests
# ============================================================================


class TestBothHaveBooksMergeStrategyInit:
    """Test BothHaveBooksMergeStrategy initialization."""

    def test_init(
        self,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test __init__ stores dependencies."""
        strategy = BothHaveBooksMergeStrategy(
            session=session,  # type: ignore[arg-type]
            calibre_author_service=mock_calibre_author_service,
            relationship_repo=mock_relationship_repo,
            data_directory="/data",
        )

        assert strategy._session == session
        assert strategy._calibre_author_service == mock_calibre_author_service
        assert strategy._relationship_repo == mock_relationship_repo
        assert strategy._data_directory == "/data"


class TestBothHaveBooksMergeStrategyCanHandle:
    """Test BothHaveBooksMergeStrategy.can_handle method."""

    def test_can_handle_has_books(
        self,
        both_have_books_strategy: BothHaveBooksMergeStrategy,
        merge_context: MergeContext,
        mock_calibre_author_service: MagicMock,
    ) -> None:
        """Test can_handle returns True when merge author has books."""
        mock_calibre_author_service.get_book_count.return_value = 5

        result = both_have_books_strategy.can_handle(merge_context)

        assert result is True
        mock_calibre_author_service.get_book_count.assert_called_once_with(20)

    def test_can_handle_zero_books(
        self,
        both_have_books_strategy: BothHaveBooksMergeStrategy,
        merge_context: MergeContext,
        mock_calibre_author_service: MagicMock,
    ) -> None:
        """Test can_handle returns False when merge author has zero books."""
        mock_calibre_author_service.get_book_count.return_value = 0

        result = both_have_books_strategy.can_handle(merge_context)

        assert result is False


class TestBothHaveBooksMergeStrategyExecute:
    """Test BothHaveBooksMergeStrategy.execute method."""

    def test_execute_with_author_id(
        self,
        both_have_books_strategy: BothHaveBooksMergeStrategy,
        merge_context: MergeContext,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test execute with author having ID."""
        both_have_books_strategy.execute(merge_context)

        mock_calibre_author_service.reassign_books.assert_called_once_with(20, 10)
        mock_calibre_author_service.delete_author.assert_called_once_with(20)
        assert merge_context.merge_mapping in session.deleted
        assert session.flush_count >= 1
        mock_relationship_repo.delete_author_works.assert_called_once_with(2)
        mock_relationship_repo.delete_author_user_photos.assert_called_once_with(
            2, None
        )
        mock_relationship_repo.delete_author_user_metadata.assert_called_once_with(2)
        mock_relationship_repo.cleanup_remaining_similarities.assert_called_once_with(2)
        assert merge_context.merge_author in session.deleted

    def test_execute_without_author_id(
        self,
        both_have_books_strategy: BothHaveBooksMergeStrategy,
        merge_context: MergeContext,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test execute with author without ID."""
        merge_context.merge_author.id = None

        both_have_books_strategy.execute(merge_context)

        mock_calibre_author_service.reassign_books.assert_called_once_with(20, 10)
        mock_calibre_author_service.delete_author.assert_called_once_with(20)
        assert merge_context.merge_mapping in session.deleted
        mock_relationship_repo.delete_author_works.assert_not_called()
        mock_relationship_repo.delete_author_user_photos.assert_not_called()
        mock_relationship_repo.delete_author_user_metadata.assert_not_called()
        mock_relationship_repo.cleanup_remaining_similarities.assert_not_called()
        assert merge_context.merge_author in session.deleted

    def test_execute_with_data_directory(
        self,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
        merge_context: MergeContext,
    ) -> None:
        """Test execute with data directory."""
        strategy = BothHaveBooksMergeStrategy(
            session=session,  # type: ignore[arg-type]
            calibre_author_service=mock_calibre_author_service,
            relationship_repo=mock_relationship_repo,
            data_directory="/data",
        )

        strategy.execute(merge_context)

        mock_relationship_repo.delete_author_user_photos.assert_called_once_with(
            2, "/data"
        )


# ============================================================================
# MergeStrategyFactory Tests
# ============================================================================


class TestMergeStrategyFactoryInit:
    """Test MergeStrategyFactory initialization."""

    def test_init(
        self,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
    ) -> None:
        """Test __init__ creates strategies."""
        factory = MergeStrategyFactory(
            session=session,  # type: ignore[arg-type]
            calibre_author_service=mock_calibre_author_service,
            relationship_repo=mock_relationship_repo,
            data_directory="/data",
        )

        assert len(factory._strategies) == 2
        assert isinstance(factory._strategies[0], ZeroBooksMergeStrategy)
        assert isinstance(factory._strategies[1], BothHaveBooksMergeStrategy)


class TestMergeStrategyFactoryGetStrategy:
    """Test MergeStrategyFactory.get_strategy method."""

    def test_get_strategy_zero_books(
        self,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
        merge_context: MergeContext,
    ) -> None:
        """Test get_strategy returns ZeroBooksMergeStrategy for zero books."""
        mock_calibre_author_service.get_book_count.return_value = 0

        factory = MergeStrategyFactory(
            session=session,  # type: ignore[arg-type]
            calibre_author_service=mock_calibre_author_service,
            relationship_repo=mock_relationship_repo,
        )

        strategy = factory.get_strategy(merge_context)

        assert isinstance(strategy, ZeroBooksMergeStrategy)

    def test_get_strategy_both_have_books(
        self,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
        merge_context: MergeContext,
    ) -> None:
        """Test get_strategy returns BothHaveBooksMergeStrategy when both have books."""
        mock_calibre_author_service.get_book_count.return_value = 5

        factory = MergeStrategyFactory(
            session=session,  # type: ignore[arg-type]
            calibre_author_service=mock_calibre_author_service,
            relationship_repo=mock_relationship_repo,
        )

        strategy = factory.get_strategy(merge_context)

        assert isinstance(strategy, BothHaveBooksMergeStrategy)

    def test_get_strategy_no_match(
        self,
        session: DummySession,
        mock_calibre_author_service: MagicMock,
        mock_relationship_repo: MagicMock,
        merge_context: MergeContext,
    ) -> None:
        """Test get_strategy raises ValueError when no strategy matches."""
        # Mock both strategies to return False
        mock_calibre_author_service.get_book_count.return_value = -1  # Invalid value

        factory = MergeStrategyFactory(
            session=session,  # type: ignore[arg-type]
            calibre_author_service=mock_calibre_author_service,
            relationship_repo=mock_relationship_repo,
        )

        with pytest.raises(
            ValueError, match="No strategy found to handle merge context"
        ):
            factory.get_strategy(merge_context)
