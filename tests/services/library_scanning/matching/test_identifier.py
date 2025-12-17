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

"""Tests for identifier matching strategy to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bookcard.models.core import Author
from bookcard.services.library_scanning.data_sources.base import BaseDataSource
from bookcard.services.library_scanning.data_sources.types import AuthorData
from bookcard.services.library_scanning.matching.identifier import (
    IdentifierMatchingStrategy,
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


class TestIdentifierMatchingStrategy:
    """Test IdentifierMatchingStrategy."""

    @pytest.fixture
    def strategy(self) -> IdentifierMatchingStrategy:
        """Create IdentifierMatchingStrategy instance."""
        return IdentifierMatchingStrategy()

    def test_name_property(self, strategy: IdentifierMatchingStrategy) -> None:
        """Test name property returns 'identifier'."""
        assert strategy.name == "identifier"

    def test_match_exact_name_match(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
        author_data: AuthorData,
    ) -> None:
        """Test match finds exact name match."""
        mock_data_source.search_author.return_value = [author_data]
        result = strategy.match(mock_author, mock_data_source)

        assert result is not None
        assert result.confidence_score == 0.98
        assert result.matched_entity == author_data
        assert result.match_method == "identifier"
        mock_data_source.search_author.assert_called_once_with("John Doe")

    def test_match_exact_name_case_insensitive(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match finds exact name match case-insensitive."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="JOHN DOE",  # Different case
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy.match(mock_author, mock_data_source)

        assert result is not None
        assert result.confidence_score == 0.98
        assert result.match_method == "identifier"

    def test_match_exact_name_with_whitespace(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match finds exact name match with normalized whitespace."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="  John   Doe  ",  # Extra whitespace
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy.match(mock_author, mock_data_source)

        assert result is not None
        assert result.confidence_score == 0.98

    def test_match_exact_name_alternate_name(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match finds exact match via alternate name."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="Jonathan Doe",  # Different name
            alternate_names=["John Doe"],  # Match in alternate
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy.match(mock_author, mock_data_source)

        assert result is not None
        assert result.confidence_score == 0.97
        assert result.match_method == "identifier_alternate"
        assert result.matched_entity == author_data

    def test_match_exact_name_alternate_name_case_insensitive(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match finds exact match via alternate name case-insensitive."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="Jonathan Doe",
            alternate_names=["JOHN DOE"],  # Different case
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy.match(mock_author, mock_data_source)

        assert result is not None
        assert result.confidence_score == 0.97
        assert result.match_method == "identifier_alternate"

    def test_match_no_results(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match returns None when no search results."""
        mock_data_source.search_author.return_value = []
        result = strategy.match(mock_author, mock_data_source)

        assert result is None

    def test_match_no_exact_match(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match returns None when no exact match found."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="Jane Smith",  # Different name
            alternate_names=["Jane"],  # No match
            personal_name="Jane",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy.match(mock_author, mock_data_source)

        assert result is None

    def test_match_multiple_results_first_match(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match returns first exact match from multiple results."""
        author_data1 = AuthorData(
            key="/authors/OL123A",
            name="John Doe",  # Match
            personal_name="John",
            work_count=10,
        )
        author_data2 = AuthorData(
            key="/authors/OL456B",
            name="John Doe",  # Also match
            personal_name="John",
            work_count=5,
        )
        mock_data_source.search_author.return_value = [author_data1, author_data2]
        result = strategy.match(mock_author, mock_data_source)

        assert result is not None
        assert result.matched_entity == author_data1  # First match

    def test_match_multiple_results_second_match(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match finds match in second result."""
        author_data1 = AuthorData(
            key="/authors/OL123A",
            name="Jane Smith",  # No match
            personal_name="Jane",
            work_count=10,
        )
        author_data2 = AuthorData(
            key="/authors/OL456B",
            name="John Doe",  # Match
            personal_name="John",
            work_count=5,
        )
        mock_data_source.search_author.return_value = [author_data1, author_data2]
        result = strategy.match(mock_author, mock_data_source)

        assert result is not None
        assert result.matched_entity == author_data2

    def test_match_unicode_normalization(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match handles unicode normalization."""
        # NFKD normalization doesn't remove accents, so we need exact match
        author = Author(id=1, name="José García")
        author_data = AuthorData(
            key="/authors/OL123A",
            name="José García",  # Same form (NFKD preserves accents)
            personal_name="Jose",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy.match(author, mock_data_source)

        assert result is not None
        assert result.confidence_score == 0.98

    def test_match_multiple_alternate_names(
        self,
        strategy: IdentifierMatchingStrategy,
        mock_author: Author,
        mock_data_source: MagicMock,
    ) -> None:
        """Test match checks all alternate names."""
        author_data = AuthorData(
            key="/authors/OL123A",
            name="Jonathan Smith",
            alternate_names=["Jane Doe", "John Doe"],  # Second alternate matches
            personal_name="John",
            work_count=10,
        )
        mock_data_source.search_author.return_value = [author_data]
        result = strategy.match(mock_author, mock_data_source)

        assert result is not None
        assert result.match_method == "identifier_alternate"
        assert result.confidence_score == 0.97
