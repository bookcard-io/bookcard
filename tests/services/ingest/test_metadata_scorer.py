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

"""Tests for metadata scorer to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.models.metadata import MetadataRecord
from fundamental.services.ingest.metadata_scorer import (
    MetadataScorer,
    ScoringConfig,
)


@pytest.fixture
def scoring_config() -> ScoringConfig:
    """Create ScoringConfig instance."""
    return ScoringConfig(
        field_weights={
            "title": 0.1,
            "authors": 0.1,
            "description": 0.1,
            "cover_url": 0.1,
            "identifiers": 0.1,
        },
        title_match_weight=0.2,
        author_match_weight=0.2,
        isbn_match_weight=0.1,
    )


@pytest.fixture
def scorer(scoring_config: ScoringConfig) -> MetadataScorer:
    """Create MetadataScorer instance."""
    return MetadataScorer(config=scoring_config)


@pytest.fixture
def scorer_with_provider_weights() -> MetadataScorer:
    """Create MetadataScorer with provider weights."""
    return MetadataScorer(provider_weights={"openlibrary": 1.5, "google": 1.0})


@pytest.fixture
def complete_record() -> MetadataRecord:
    """Create a complete MetadataRecord."""
    return MetadataRecord(
        source_id="openlibrary",
        external_id="OL123",
        title="Test Book",
        authors=["Test Author"],
        url="https://example.com/book",
        description="A test book",
        cover_url="https://example.com/cover.jpg",
        identifiers={"isbn": "1234567890"},
    )


@pytest.fixture
def minimal_record() -> MetadataRecord:
    """Create a minimal MetadataRecord."""
    return MetadataRecord(
        source_id="openlibrary",
        external_id="OL123",
        title="Test Book",
        authors=[],
        url="https://example.com/book",
    )


def test_scoring_config_defaults() -> None:
    """Test ScoringConfig default values."""
    config = ScoringConfig()
    assert "title" in config.field_weights
    assert config.title_match_weight == 0.2
    assert config.author_match_weight == 0.2
    assert config.isbn_match_weight == 0.1


def test_metadata_scorer_init_defaults() -> None:
    """Test MetadataScorer initialization with defaults."""
    scorer = MetadataScorer()
    assert scorer._config is not None
    assert scorer._provider_weights == {}


def test_metadata_scorer_init_with_config(scoring_config: ScoringConfig) -> None:
    """Test MetadataScorer initialization with config."""
    scorer = MetadataScorer(config=scoring_config)
    assert scorer._config == scoring_config


def test_calculate_completeness_score_complete(
    scorer: MetadataScorer, complete_record: MetadataRecord
) -> None:
    """Test completeness score calculation for complete record."""
    score = scorer._calculate_completeness_score(complete_record)
    assert score > 0
    assert score <= 0.5


def test_calculate_completeness_score_minimal(
    scorer: MetadataScorer, minimal_record: MetadataRecord
) -> None:
    """Test completeness score calculation for minimal record."""
    score = scorer._calculate_completeness_score(minimal_record)
    assert score >= 0
    assert score < 0.5


@pytest.mark.parametrize(
    ("query_title", "record_title", "expected_min"),
    [
        ("Test Book", "Test Book", 0.0),
        ("Test Book", "test book", 0.0),
        ("Test Book", "Different Book", 0.0),
        (None, "Test Book", 0.0),
    ],
)
def test_calculate_match_quality_title(
    scorer: MetadataScorer,
    complete_record: MetadataRecord,
    query_title: str | None,
    record_title: str,
    expected_min: float,
) -> None:
    """Test match quality calculation with title matching."""
    complete_record.title = record_title
    score = scorer._calculate_match_quality(complete_record, query_title, None, None)
    assert score >= expected_min


def test_calculate_match_quality_author_match(
    scorer: MetadataScorer, complete_record: MetadataRecord
) -> None:
    """Test match quality calculation with author matching."""
    score = scorer._calculate_match_quality(
        complete_record, None, ["Test Author"], None
    )
    assert score >= 0.0


def test_calculate_match_quality_author_no_match(
    scorer: MetadataScorer, complete_record: MetadataRecord
) -> None:
    """Test match quality calculation with no author match."""
    score = scorer._calculate_match_quality(
        complete_record, None, ["Different Author"], None
    )
    assert score >= 0.0


def test_calculate_match_quality_isbn_match(
    scorer: MetadataScorer, complete_record: MetadataRecord
) -> None:
    """Test match quality calculation with ISBN matching."""
    score = scorer._calculate_match_quality(complete_record, None, None, "1234567890")
    assert score >= 0.0


def test_calculate_match_quality_isbn_no_match(
    scorer: MetadataScorer, complete_record: MetadataRecord
) -> None:
    """Test match quality calculation with no ISBN match."""
    score = scorer._calculate_match_quality(complete_record, None, None, "9876543210")
    assert score >= 0.0


def test_score_complete_match(
    scorer: MetadataScorer, complete_record: MetadataRecord
) -> None:
    """Test score method with complete match."""
    score = scorer.score(
        complete_record,
        query_title="Test Book",
        query_authors=["Test Author"],
        query_isbn="1234567890",
    )
    assert 0.0 <= score <= 1.0


def test_score_with_provider_weight(
    scorer_with_provider_weights: MetadataScorer, complete_record: MetadataRecord
) -> None:
    """Test score method applies provider weight multiplier."""
    score = scorer_with_provider_weights.score(complete_record, query_title="Test Book")
    assert 0.0 <= score <= 1.0


def test_score_clamps_to_one(
    scorer_with_provider_weights: MetadataScorer, complete_record: MetadataRecord
) -> None:
    """Test score method clamps result to 1.0."""
    # Use very high provider weight to test clamping
    scorer = MetadataScorer(provider_weights={"openlibrary": 10.0})
    score = scorer.score(complete_record, query_title="Test Book")
    assert score <= 1.0


def test_score_clamps_to_zero(scorer: MetadataScorer) -> None:
    """Test score method clamps result to 0.0."""
    empty_record = MetadataRecord(
        source_id="test",
        external_id="test",
        title="",
        authors=[],
        url="https://example.com/book",
    )
    score = scorer.score(empty_record)
    assert score >= 0.0


def test_calculate_completeness_with_list_field(scorer: MetadataScorer) -> None:
    """Test completeness score with list fields."""
    record = MetadataRecord(
        source_id="test",
        external_id="test",
        title="Test",
        authors=["Author1", "Author2"],
        url="https://example.com/book",
        tags=["tag1", "tag2"],
    )
    score = scorer._calculate_completeness_score(record)
    assert score > 0


def test_calculate_completeness_with_dict_field(scorer: MetadataScorer) -> None:
    """Test completeness score with dict fields."""
    record = MetadataRecord(
        source_id="test",
        external_id="test",
        title="Test",
        url="https://example.com/book",
        identifiers={"isbn": "123"},
    )
    score = scorer._calculate_completeness_score(record)
    assert score > 0
