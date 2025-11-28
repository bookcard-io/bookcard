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

"""Tests for metadata extraction to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.models.ingest import IngestHistory, IngestStatus
from fundamental.services.ingest.metadata_extraction import (
    ExtractedMetadata,
    extract_metadata,
)


@pytest.fixture
def history_with_metadata() -> IngestHistory:
    """Create IngestHistory with metadata."""
    return IngestHistory(
        id=1,
        file_path="/tmp/book.epub",
        status=IngestStatus.PENDING,
        ingest_metadata={
            "metadata_hint": {"title": "History Title", "authors": ["History Author"]},
            "fetched_metadata": {"title": "Fetched Title", "isbn": "1234567890"},
        },
    )


@pytest.fixture
def history_empty() -> IngestHistory:
    """Create IngestHistory with empty metadata."""
    return IngestHistory(
        id=1,
        file_path="/tmp/book.epub",
        status=IngestStatus.PENDING,
        ingest_metadata=None,
    )


@pytest.mark.parametrize(
    ("authors", "expected_primary"),
    [
        (["Author1", "Author2"], "Author1"),
        (["Single Author"], "Single Author"),
        ([], None),
    ],
)
def test_extracted_metadata_primary_author(
    authors: list[str], expected_primary: str | None
) -> None:
    """Test primary_author property."""
    metadata = ExtractedMetadata(authors=authors)
    assert metadata.primary_author == expected_primary


def test_extracted_metadata_defaults() -> None:
    """Test ExtractedMetadata default values."""
    metadata = ExtractedMetadata()
    assert metadata.title is None
    assert metadata.authors == []
    assert metadata.isbn is None


@pytest.mark.parametrize(
    ("metadata_hint", "expected_title", "expected_authors", "expected_isbn"),
    [
        (
            {"title": "Hint Title", "authors": ["Hint Author"], "isbn": "9876543210"},
            "Hint Title",
            ["Hint Author"],
            "9876543210",  # From hint
        ),
        (
            {"title": "Hint Title"},
            "Hint Title",
            ["History Author"],  # From history metadata_hint (priority 2)
            "1234567890",  # From fetched_metadata (priority 3)
        ),
        (
            None,
            "History Title",
            ["History Author"],
            "1234567890",  # From fetched_metadata (priority 3)
        ),
    ],
)
def test_extract_metadata_with_hint(
    history_with_metadata: IngestHistory,
    metadata_hint: dict | None,
    expected_title: str | None,
    expected_authors: list[str],
    expected_isbn: str | None,
) -> None:
    """Test extract_metadata with explicit hint (priority 1)."""
    result = extract_metadata(history_with_metadata, metadata_hint=metadata_hint)
    assert result.title == expected_title
    assert result.authors == expected_authors
    assert result.isbn == expected_isbn


def test_extract_metadata_from_history_hint(
    history_with_metadata: IngestHistory,
) -> None:
    """Test extract_metadata from history's metadata_hint (priority 2)."""
    result = extract_metadata(history_with_metadata)
    assert result.title == "History Title"
    assert result.authors == ["History Author"]
    # ISBN comes from fetched_metadata (priority 3) since metadata_hint doesn't have it
    assert result.isbn == "1234567890"


def test_extract_metadata_from_fetched(history_empty: IngestHistory) -> None:
    """Test extract_metadata from history's fetched_metadata (priority 3)."""
    history_empty.ingest_metadata = {
        "fetched_metadata": {"title": "Fetched Title", "isbn": "1234567890"},
    }
    result = extract_metadata(history_empty)
    assert result.title == "Fetched Title"
    assert result.isbn == "1234567890"


def test_extract_metadata_fallback_title(history_empty: IngestHistory) -> None:
    """Test extract_metadata with fallback title."""
    result = extract_metadata(history_empty, fallback_title="Fallback Title")
    assert result.title == "Fallback Title"


def test_extract_metadata_authors_as_string(history_empty: IngestHistory) -> None:
    """Test extract_metadata handles authors as string (not list)."""
    history_empty.ingest_metadata = {"metadata_hint": {"authors": "Single Author"}}
    result = extract_metadata(history_empty)
    assert result.authors == ["Single Author"]


def test_extract_metadata_empty_sources(history_empty: IngestHistory) -> None:
    """Test extract_metadata with no sources."""
    result = extract_metadata(history_empty)
    assert result.title is None
    assert result.authors == []
    assert result.isbn is None


def test_extract_metadata_empty_dict_source(history_empty: IngestHistory) -> None:
    """Test extract_metadata with empty dict source."""
    history_empty.ingest_metadata = {"metadata_hint": {}}
    result = extract_metadata(history_empty, metadata_hint={})
    assert result.title is None
    assert result.authors == []
    assert result.isbn is None
