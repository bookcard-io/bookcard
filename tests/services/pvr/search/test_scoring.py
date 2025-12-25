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

"""Tests for scoring strategies."""

from datetime import UTC, datetime, timedelta

import pytest

from bookcard.models.pvr import IndexerDefinition, IndexerProtocol, IndexerType
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.scoring import (
    DefaultScoringStrategy,
    ReleaseScorer,
    ScoringWeights,
)


class TestScoringWeights:
    """Test ScoringWeights dataclass."""

    def test_default_weights(self) -> None:
        """Test default weight values."""
        weights = ScoringWeights()

        assert weights.TITLE_MATCH_FULL == 0.4
        assert weights.TITLE_MATCH_PARTIAL == 0.2
        assert weights.AUTHOR_MATCH_FULL == 0.3
        assert weights.AUTHOR_MATCH_PARTIAL == 0.15
        assert weights.ISBN_MATCH == 0.2
        assert weights.FORMAT_QUALITY == 0.1
        assert weights.SEEDER_MAX == 0.1
        assert weights.RECENCY_WEEK == 0.05
        assert weights.RECENCY_MONTH == 0.03
        assert weights.RECENCY_QUARTER == 0.01
        assert weights.INDEXER_PRIORITY_MAX == 0.05

    def test_custom_weights(self) -> None:
        """Test custom weight values."""
        weights = ScoringWeights(
            TITLE_MATCH_FULL=0.5,
            AUTHOR_MATCH_FULL=0.4,
        )

        assert weights.TITLE_MATCH_FULL == 0.5
        assert weights.AUTHOR_MATCH_FULL == 0.4
        assert weights.TITLE_MATCH_PARTIAL == 0.2  # Default value


class TestDefaultScoringStrategy:
    """Test DefaultScoringStrategy."""

    @pytest.fixture
    def strategy(self) -> DefaultScoringStrategy:
        """Create default scoring strategy.

        Returns
        -------
        DefaultScoringStrategy
            Scoring strategy instance.
        """
        return DefaultScoringStrategy()

    @pytest.fixture
    def indexer(self) -> IndexerDefinition:
        """Create sample indexer.

        Returns
        -------
        IndexerDefinition
            Sample indexer.
        """
        return IndexerDefinition(
            id=1,
            name="Test Indexer",
            indexer_type=IndexerType.TORZNAB,
            protocol=IndexerProtocol.TORRENT,
            base_url="https://test.com",
            enabled=True,
            priority=0,
        )

    def test_score_title_match_full(
        self, strategy: DefaultScoringStrategy, indexer: IndexerDefinition
    ) -> None:
        """Test full title match scoring.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        indexer : IndexerDefinition
            Sample indexer.
        """
        release = ReleaseInfo(
            title="The Great Gatsby",
            download_url="https://example.com/book.torrent",
        )

        score = strategy.score(
            release=release,
            query="gatsby",
            title="The Great Gatsby",
            author=None,
            isbn=None,
            indexer=indexer,
        )

        assert score >= strategy.weights.TITLE_MATCH_FULL

    def test_score_title_match_partial(
        self, strategy: DefaultScoringStrategy, indexer: IndexerDefinition
    ) -> None:
        """Test partial title match scoring.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        indexer : IndexerDefinition
            Sample indexer.
        """
        release = ReleaseInfo(
            title="The Great Gatsby Complete Edition",
            download_url="https://example.com/book.torrent",
        )

        score = strategy.score(
            release=release,
            query="gatsby",
            title="Gatsby",  # Single word query
            author=None,
            isbn=None,
            indexer=indexer,
        )

        # Should get partial match (word match) but not full match
        # Score should be at least partial, but may include other factors
        assert score >= strategy.weights.TITLE_MATCH_PARTIAL

    def test_score_author_match_full(
        self, strategy: DefaultScoringStrategy, indexer: IndexerDefinition
    ) -> None:
        """Test full author match scoring.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        indexer : IndexerDefinition
            Sample indexer.
        """
        release = ReleaseInfo(
            title="Some Book",
            download_url="https://example.com/book.torrent",
            author="F. Scott Fitzgerald",
        )

        score = strategy.score(
            release=release,
            query="fitzgerald",
            title=None,
            author="F. Scott Fitzgerald",
            isbn=None,
            indexer=indexer,
        )

        assert score >= strategy.weights.AUTHOR_MATCH_FULL

    def test_score_isbn_match(
        self, strategy: DefaultScoringStrategy, indexer: IndexerDefinition
    ) -> None:
        """Test ISBN match scoring.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        indexer : IndexerDefinition
            Sample indexer.
        """
        release = ReleaseInfo(
            title="Some Book",
            download_url="https://example.com/book.torrent",
            isbn="978-1234567890",
        )

        score = strategy.score(
            release=release,
            query="book",
            title=None,
            author=None,
            isbn="9781234567890",  # Different format
            indexer=indexer,
        )

        assert score >= strategy.weights.ISBN_MATCH

    @pytest.mark.parametrize(
        ("quality", "expected_score"),
        [
            ("epub", 0.1),
            ("EPUB", 0.1),
            ("pdf", 0.1),
            ("mobi", 0.1),
            ("azw", 0.1),
            ("txt", 0.0),
            ("docx", 0.0),
            (None, 0.0),
        ],
    )
    def test_score_format_quality(
        self,
        strategy: DefaultScoringStrategy,
        indexer: IndexerDefinition,
        quality: str | None,
        expected_score: float,
    ) -> None:
        """Test format quality scoring.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        indexer : IndexerDefinition
            Sample indexer.
        quality : str | None
            Quality/format string.
        expected_score : float
            Expected score contribution.
        """
        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/book.torrent",
            quality=quality,
        )

        score = strategy._score_format_quality(release)
        assert score == expected_score

    @pytest.mark.parametrize(
        ("seeders", "expected_max"),
        [
            (0, 0.0),
            (100, 0.1),
            (500, 0.1),  # Capped at SEEDER_MAX
            (1000, 0.1),  # Capped at SEEDER_MAX
            (None, 0.0),
        ],
    )
    def test_score_seeders(
        self,
        strategy: DefaultScoringStrategy,
        seeders: int | None,
        expected_max: float,
    ) -> None:
        """Test seeder count scoring.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        seeders : int | None
            Number of seeders.
        expected_max : float
            Expected maximum score contribution.
        """
        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/book.torrent",
            seeders=seeders,
        )

        score = strategy._score_seeders(release)
        assert score <= expected_max
        if seeders is not None:
            assert score <= strategy.weights.SEEDER_MAX

    @pytest.mark.parametrize(
        ("age_days", "expected_score"),
        [
            (0, 0.05),  # RECENCY_WEEK
            (7, 0.05),  # RECENCY_WEEK
            (8, 0.03),  # RECENCY_MONTH
            (30, 0.03),  # RECENCY_MONTH
            (31, 0.01),  # RECENCY_QUARTER
            (90, 0.01),  # RECENCY_QUARTER
            (91, 0.0),  # Too old
            (365, 0.0),  # Too old
        ],
    )
    def test_score_recency(
        self,
        strategy: DefaultScoringStrategy,
        age_days: int,
        expected_score: float,
    ) -> None:
        """Test recency scoring.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        age_days : int
            Age of release in days.
        expected_score : float
            Expected score contribution.
        """
        publish_date = datetime.now(UTC) - timedelta(days=age_days)
        release = ReleaseInfo(
            title="Test Book",
            download_url="https://example.com/book.torrent",
            publish_date=publish_date,
        )

        score = strategy._score_recency(release)
        assert score == expected_score

    def test_score_indexer_priority(self, strategy: DefaultScoringStrategy) -> None:
        """Test indexer priority scoring.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        """
        high_priority = IndexerDefinition(
            id=1,
            name="High Priority",
            indexer_type=IndexerType.TORZNAB,
            protocol=IndexerProtocol.TORRENT,
            base_url="https://test.com",
            enabled=True,
            priority=0,  # Lower = higher priority
        )

        low_priority = IndexerDefinition(
            id=2,
            name="Low Priority",
            indexer_type=IndexerType.TORZNAB,
            protocol=IndexerProtocol.TORRENT,
            base_url="https://test.com",
            enabled=True,
            priority=1000,  # Higher = lower priority
        )

        high_score = strategy._score_indexer_priority(high_priority)
        low_score = strategy._score_indexer_priority(low_priority)

        assert high_score > low_score
        assert high_score <= strategy.weights.INDEXER_PRIORITY_MAX

    def test_score_clamped_to_one(
        self, strategy: DefaultScoringStrategy, indexer: IndexerDefinition
    ) -> None:
        """Test that total score is clamped to 1.0.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        indexer : IndexerDefinition
            Sample indexer.
        """
        # Create a release that would score very high
        release = ReleaseInfo(
            title="The Great Gatsby",
            download_url="https://example.com/book.torrent",
            author="F. Scott Fitzgerald",
            isbn="9781234567890",
            quality="epub",
            seeders=10000,
            publish_date=datetime.now(UTC),
        )

        score = strategy.score(
            release=release,
            query="gatsby",
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            isbn="9781234567890",
            indexer=indexer,
        )

        assert 0.0 <= score <= 1.0

    def test_score_zero_with_no_matches(
        self, strategy: DefaultScoringStrategy, indexer: IndexerDefinition
    ) -> None:
        """Test score is low when nothing matches.

        Parameters
        ----------
        strategy : DefaultScoringStrategy
            Scoring strategy.
        indexer : IndexerDefinition
            Sample indexer.
        """
        release = ReleaseInfo(
            title="Unrelated Book",
            download_url="https://example.com/book.torrent",
            quality="txt",  # Not preferred format
            publish_date=datetime(2020, 1, 1, tzinfo=UTC),  # Old
        )

        score = strategy.score(
            release=release,
            query="gatsby",
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            isbn=None,
            indexer=indexer,
        )

        assert score < 0.1  # Should be very low


class TestReleaseScorer:
    """Test ReleaseScorer component."""

    def test_delegates_to_strategy(
        self, sample_release: ReleaseInfo, sample_indexer: IndexerDefinition
    ) -> None:
        """Test ReleaseScorer delegates to strategy.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release.
        sample_indexer : IndexerDefinition
            Sample indexer.
        """
        strategy = DefaultScoringStrategy()
        scorer = ReleaseScorer(strategy)

        score = scorer.score_release(
            release=sample_release,
            query="test",
            title="Test Book Title",
            author="Test Author",
            isbn=None,
            indexer=sample_indexer,
        )

        # Should get a score from the strategy
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
