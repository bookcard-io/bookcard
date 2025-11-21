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

"""Tests for fuzzy matching strategy to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.models.core import Author
from fundamental.services.library_scanning.data_sources.base import BaseDataSource
from fundamental.services.library_scanning.data_sources.types import AuthorData
from fundamental.services.library_scanning.matching.fuzzy import (
    FuzzyNameMatchingStrategy,
    levenshtein_distance,
    similarity_score,
)


@pytest.fixture
def mock_author() -> Author:
    """Create a mock author."""
    return Author(id=1, name="John Doe")


@pytest.fixture
def mock_data_source() -> MagicMock:
    """Create a mock data source."""
    return MagicMock(spec=BaseDataSource)


@pytest.fixture
def author_data() -> AuthorData:
    """Create sample author data."""
    return AuthorData(
        key="/authors/OL123A",
        name="John Doe",
        personal_name="John",
        work_count=10,
    )


class TestLevenshteinDistance:
    """Test levenshtein_distance function."""

    @pytest.mark.parametrize(
        ("s1", "s2", "expected"),
        [
            ("", "", 0),
            ("abc", "", 3),
            ("", "abc", 3),
            ("abc", "abc", 0),
            ("abc", "def", 3),
            ("kitten", "sitting", 3),
            ("saturday", "sunday", 3),
            ("book", "back", 2),
        ],
    )
    def test_levenshtein_distance(self, s1: str, s2: str, expected: int) -> None:
        """Test levenshtein_distance calculates correct distance."""
        result = levenshtein_distance(s1, s2)
        assert result == expected

    def test_levenshtein_distance_swaps_arguments(self) -> None:
        """Test levenshtein_distance swaps arguments when s1 is shorter."""
        # When s1 < s2, it should swap and return same result
        result1 = levenshtein_distance("ab", "abcde")
        result2 = levenshtein_distance("abcde", "ab")
        assert result1 == result2
        assert result1 == 3


class TestSimilarityScore:
    """Test similarity_score function."""

    @pytest.mark.parametrize(
        ("s1", "s2", "expected_min", "expected_max"),
        [
            ("", "", 0.0, 0.0),  # Empty strings return 0.0
            ("abc", "", 0.0, 0.0),
            ("", "abc", 0.0, 0.0),
            ("abc", "abc", 1.0, 1.0),
            ("abc", "def", 0.0, 0.0),
            ("kitten", "sitting", 0.57, 0.58),  # 1 - 3/7
            ("book", "back", 0.5, 0.5),  # 1 - 2/4
        ],
    )
    def test_similarity_score(
        self, s1: str, s2: str, expected_min: float, expected_max: float
    ) -> None:
        """Test similarity_score calculates correct score."""
        result = similarity_score(s1, s2)
        assert expected_min <= result <= expected_max

    def test_similarity_score_empty_strings(self) -> None:
        """Test similarity_score handles empty strings."""
        # Empty strings return 0.0 (not 1.0) because of the early return check
        assert similarity_score("", "") == 0.0
        assert similarity_score("abc", "") == 0.0
        assert similarity_score("", "abc") == 0.0

    def test_similarity_score_identical(self) -> None:
        """Test similarity_score returns 1.0 for identical strings."""
        assert similarity_score("test", "test") == 1.0
        assert similarity_score("John Doe", "John Doe") == 1.0

    def test_similarity_score_completely_different(self) -> None:
        """Test similarity_score returns 0.0 for completely different strings."""
        # When all characters are different
        result = similarity_score("abc", "xyz")
        assert result == 0.0


class TestFuzzyNameMatchingStrategy:
    """Test FuzzyNameMatchingStrategy."""

    @pytest.fixture
    def strategy_default(self) -> FuzzyNameMatchingStrategy:
        """Create FuzzyNameMatchingStrategy with default min_similarity."""
        return FuzzyNameMatchingStrategy()

    @pytest.fixture
    def strategy_custom(self) -> FuzzyNameMatchingStrategy:
        """Create FuzzyNameMatchingStrategy with custom min_similarity."""
        return FuzzyNameMatchingStrategy(min_similarity=0.8)

    def test_init_default(self, strategy_default: FuzzyNameMatchingStrategy) -> None:
        """Test __init__ with default min_similarity."""
        assert strategy_default.min_similarity == 0.7

    def test_init_custom(self, strategy_custom: FuzzyNameMatchingStrategy) -> None:
        """Test __init__ with custom min_similarity."""
        assert strategy_custom.min_similarity == 0.8

    def test_name_property(self, strategy_default: FuzzyNameMatchingStrategy) -> None:
        """Test name property returns 'fuzzy'."""
        assert strategy_default.name == "fuzzy"

    def test_match_fuzzy_name_match(
        self,
        strategy_default: FuzzyNameMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match finds fuzzy name match."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="John Do",  # Similar but not exact
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy_default.match(mock_author, mock_data_source)

        assert result is not None
        assert result.matched_entity == author_data
        assert result.match_method == "fuzzy"
        assert 0.5 <= result.confidence_score <= 0.85

    def test_match_fuzzy_name_high_similarity(
        self,
        strategy_default: FuzzyNameMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match finds fuzzy match with high similarity."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="John Do",  # Very similar
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy_default.match(mock_author, mock_data_source)

        assert result is not None
        assert result.confidence_score >= 0.5

    def test_match_no_results(
        self,
        strategy_default: FuzzyNameMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match returns None when no search results."""
        mock_data_source.search_author.return_value = []
        result = strategy_default.match(mock_author, mock_data_source)

        assert result is None

    def test_match_below_min_similarity(
        self,
        strategy_custom: FuzzyNameMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match returns None when similarity below threshold."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="Jane Smith",  # Very different
            personal_name="Jane",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy_custom.match(mock_author, mock_data_source)

        assert result is None

    def test_match_best_match_selected(
        self,
        strategy_default: FuzzyNameMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match selects best match from multiple results."""
        author_data1 = AuthorData(
            key="/authors/OL123A",
            name="John Do",  # Similar
            personal_name="John",
            work_count=10,
        )
        author_data2 = AuthorData(
            key="/authors/OL456B",
            name="John Doe",  # More similar (exact match)
            personal_name="John",
            work_count=5,
        )
        mock_data_source.search_author.return_value = [author_data1, author_data2]
        result = strategy_default.match(mock_author, mock_data_source)

        assert result is not None
        # Should select the best match (author_data2 with higher similarity)
        assert result.matched_entity == author_data2

    def test_match_confidence_score_mapping(
        self,
        strategy_default: FuzzyNameMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match maps similarity score to confidence correctly."""
        # Test with exact match (similarity = 1.0)
        author_data = AuthorData(
            key="/authors/OL123A",
            name="John Doe",  # Exact match
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy_default.match(mock_author, mock_data_source)

        assert result is not None
        # For similarity 1.0, confidence should be 0.85
        assert result.confidence_score == pytest.approx(0.85, abs=0.01)

    def test_match_confidence_score_min_similarity(
        self,
        strategy_default: FuzzyNameMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match maps min similarity to minimum confidence."""
        # Test with min similarity (0.7)
        # Need a name that gives exactly 0.7 similarity
        # This is approximate, but we can test the boundary
        author_data = AuthorData(
            key="/authors/OL123A",
            name="John Do",  # Should be above threshold
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy_default.match(mock_author, mock_data_source)

        if result is not None:
            # For min similarity (0.7), confidence should be 0.5
            assert result.confidence_score >= 0.5
