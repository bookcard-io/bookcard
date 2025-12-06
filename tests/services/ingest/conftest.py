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

"""Shared fixtures for ingest service tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from fundamental.models.ingest import IngestConfig, IngestHistory, IngestStatus
from fundamental.models.metadata import MetadataRecord
from fundamental.services.ingest.file_discovery_service import FileGroup


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for file operations."""
    return tmp_path


@pytest.fixture
def mock_ingest_config() -> MagicMock:
    """Create a mock IngestConfig."""
    config = MagicMock(spec=IngestConfig)
    config.enabled = True
    config.ingest_dir = "/tmp/ingest"
    config.metadata_providers = ["openlibrary", "google"]
    config.supported_formats = ["epub", "pdf", "mobi"]
    config.ignore_patterns = ["*.tmp", "*.bak"]
    config.metadata_merge_strategy = "first_wins"
    return config


@pytest.fixture
def ingest_config() -> IngestConfig:
    """Create an IngestConfig instance."""
    return IngestConfig(
        enabled=True,
        ingest_dir="/tmp/ingest",
        metadata_providers=["openlibrary", "google"],
        supported_formats=["epub", "pdf", "mobi"],
        ignore_patterns=["*.tmp", "*.bak"],
        metadata_merge_strategy="first_wins",
    )


@pytest.fixture
def ingest_history() -> IngestHistory:
    """Create an IngestHistory instance."""
    return IngestHistory(
        id=1,
        file_path="/tmp/book.epub",
        status=IngestStatus.PENDING,
        ingest_metadata={
            "book_key": "test_book",
            "file_count": 1,
            "files": ["/tmp/book.epub"],
        },
    )


@pytest.fixture
def file_group(temp_dir: Path) -> FileGroup:
    """Create a FileGroup instance."""
    file_path = temp_dir / "book.epub"
    file_path.touch()
    return FileGroup(
        book_key="test_book",
        files=[file_path],
        metadata_hint={"title": "Test Book", "authors": ["Test Author"]},
    )


@pytest.fixture
def metadata_record() -> MetadataRecord:
    """Create a MetadataRecord instance."""
    return MetadataRecord(
        source_id="openlibrary",
        external_id="OL123456",
        title="Test Book",
        authors=["Test Author"],
        url="https://example.com/book",
        description="A test book",
        cover_url="https://example.com/cover.jpg",
        series="Test Series",
        series_index=1,
        publisher="Test Publisher",
        published_date="2020-01-01",
        identifiers={"isbn": "1234567890"},
    )


@pytest.fixture
def mock_metadata_service() -> MagicMock:
    """Create a mock MetadataService."""
    service = MagicMock()
    service.search.return_value = []
    return service


@pytest.fixture
def mock_book_metadata_service() -> MagicMock:
    """Create a mock BookMetadataService."""
    service = MagicMock()
    metadata = MagicMock()
    metadata.title = "Test Book"
    metadata.author = "Test Author"
    metadata.isbn = "1234567890"
    service.extract_metadata.return_value = (metadata, {})
    return service
