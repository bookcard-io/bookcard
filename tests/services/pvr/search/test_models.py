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

"""Tests for search result models."""

import pytest

from bookcard.models.pvr import IndexerDefinition
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.models import IndexerSearchResult


class TestIndexerSearchResult:
    """Test IndexerSearchResult dataclass."""

    def test_minimal_result(self, sample_release_minimal: ReleaseInfo) -> None:
        """Test IndexerSearchResult with minimal fields.

        Parameters
        ----------
        sample_release_minimal : ReleaseInfo
            Minimal release fixture.
        """
        result = IndexerSearchResult(
            release=sample_release_minimal,
            score=0.5,
        )

        assert result.release == sample_release_minimal
        assert result.score == 0.5
        assert result.indexer_name is None
        assert result.indexer_priority == 0

    def test_complete_result(
        self, sample_release: ReleaseInfo, sample_indexer: IndexerDefinition
    ) -> None:
        """Test IndexerSearchResult with all fields.

        Parameters
        ----------
        sample_release : ReleaseInfo
            Sample release fixture.
        sample_indexer
            Sample indexer fixture.
        """
        result = IndexerSearchResult(
            release=sample_release,
            score=0.85,
            indexer_name=sample_indexer.name,
            indexer_priority=sample_indexer.priority,
        )

        assert result.release == sample_release
        assert result.score == 0.85
        assert result.indexer_name == sample_indexer.name
        assert result.indexer_priority == sample_indexer.priority

    @pytest.mark.parametrize(
        ("score", "expected_valid"),
        [
            (0.0, True),
            (0.5, True),
            (1.0, True),
            (-0.1, True),  # Dataclass doesn't validate range
            (1.1, True),  # Dataclass doesn't validate range
        ],
    )
    def test_score_values(
        self, sample_release_minimal: ReleaseInfo, score: float, expected_valid: bool
    ) -> None:
        """Test IndexerSearchResult with various score values.

        Parameters
        ----------
        sample_release_minimal : ReleaseInfo
            Minimal release fixture.
        score : float
            Score value to test.
        expected_valid : bool
            Whether the score is expected to be valid.
        """
        result = IndexerSearchResult(
            release=sample_release_minimal,
            score=score,
        )
        assert result.score == score
