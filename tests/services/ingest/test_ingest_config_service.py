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

"""Tests for ingest config service to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from fundamental.models.ingest import IngestConfig
from fundamental.repositories.ingest_repository import IngestConfigRepository
from fundamental.services.ingest.ingest_config_service import IngestConfigService

if TYPE_CHECKING:
    from tests.conftest import DummySession


@pytest.fixture
def mock_config_repo() -> MagicMock:
    """Create a mock IngestConfigRepository."""
    repo = MagicMock(spec=IngestConfigRepository)
    config = MagicMock(spec=IngestConfig)
    config.enabled = True
    config.ingest_dir = "/tmp/ingest"
    config.metadata_providers = ["openlibrary", "google"]
    config.supported_formats = ["epub", "pdf"]
    config.ignore_patterns = ["*.tmp"]
    config.metadata_merge_strategy = "merge_best"
    repo.get_config.return_value = config
    repo.update_config.return_value = config
    return repo


@pytest.fixture
def service(session: DummySession, mock_config_repo: MagicMock) -> IngestConfigService:
    """Create IngestConfigService with mock repository."""
    return IngestConfigService(session=session, config_repo=mock_config_repo)  # type: ignore[valid-type]


@pytest.fixture
def service_default_repo(session: DummySession) -> IngestConfigService:  # type: ignore[valid-type]
    """Create IngestConfigService with default repository."""
    return IngestConfigService(session=session)  # type: ignore[valid-type]


def test_init_with_repo(session: DummySession, mock_config_repo: MagicMock) -> None:  # type: ignore[valid-type]
    """Test IngestConfigService initialization with repository."""
    service = IngestConfigService(session=session, config_repo=mock_config_repo)  # type: ignore[valid-type]
    assert service._config_repo == mock_config_repo


def test_init_without_repo(session: DummySession) -> None:  # type: ignore[valid-type]
    """Test IngestConfigService initialization without repository."""
    service = IngestConfigService(session=session)  # type: ignore[valid-type]
    assert isinstance(service._config_repo, IngestConfigRepository)


def test_get_config(service: IngestConfigService, mock_config_repo: MagicMock) -> None:
    """Test get_config method."""
    result = service.get_config()
    mock_config_repo.get_config.assert_called_once()
    assert result is not None


def test_update_config_valid(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test update_config with valid parameters."""
    result = service.update_config(enabled=False)
    mock_config_repo.update_config.assert_called_once_with(enabled=False)
    assert result is not None


def test_update_config_absolute_path(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test update_config with absolute path."""
    result = service.update_config(ingest_dir="/absolute/path")
    mock_config_repo.update_config.assert_called_once_with(ingest_dir="/absolute/path")
    assert result is not None


def test_update_config_relative_path(service: IngestConfigService) -> None:
    """Test update_config raises ValueError for relative path."""
    with pytest.raises(ValueError, match="ingest_dir must be an absolute path"):
        service.update_config(ingest_dir="relative/path")


def test_update_config_metadata_providers_list(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test update_config with valid metadata_providers list."""
    result = service.update_config(metadata_providers=["provider1", "provider2"])
    mock_config_repo.update_config.assert_called_once_with(
        metadata_providers=["provider1", "provider2"]
    )
    assert result is not None


def test_update_config_metadata_providers_invalid(service: IngestConfigService) -> None:
    """Test update_config raises ValueError for invalid metadata_providers."""
    with pytest.raises(ValueError, match="metadata_providers must be a list"):
        service.update_config(metadata_providers="not_a_list")


def test_is_enabled(service: IngestConfigService, mock_config_repo: MagicMock) -> None:
    """Test is_enabled method."""
    result = service.is_enabled()
    assert result is True
    mock_config_repo.get_config.assert_called_once()


def test_get_ingest_dir(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test get_ingest_dir method."""
    result = service.get_ingest_dir()
    assert isinstance(result, Path)
    assert str(result) == "/tmp/ingest"
    mock_config_repo.get_config.assert_called_once()


@pytest.mark.parametrize(
    ("providers", "expected"),
    [
        (["openlibrary", "google"], ["openlibrary", "google"]),
        (None, []),
        ([], []),
    ],
)
def test_get_enabled_providers(
    service: IngestConfigService,
    mock_config_repo: MagicMock,
    providers: list[str] | None,
    expected: list[str],
) -> None:
    """Test get_enabled_providers method with various inputs."""
    config = mock_config_repo.get_config.return_value
    config.metadata_providers = providers
    result = service.get_enabled_providers()
    assert result == expected


def test_get_enabled_providers_not_list(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test get_enabled_providers returns empty list when not a list."""
    config = mock_config_repo.get_config.return_value
    config.metadata_providers = "not_a_list"
    result = service.get_enabled_providers()
    assert result == []


@pytest.mark.parametrize(
    ("formats", "expected"),
    [
        (["epub", "pdf"], ["epub", "pdf"]),
        (None, []),
        ([], []),
    ],
)
def test_get_supported_formats(
    service: IngestConfigService,
    mock_config_repo: MagicMock,
    formats: list[str] | None,
    expected: list[str],
) -> None:
    """Test get_supported_formats method with various inputs."""
    config = mock_config_repo.get_config.return_value
    config.supported_formats = formats
    result = service.get_supported_formats()
    assert result == expected


def test_get_supported_formats_not_list(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test get_supported_formats returns empty list when not a list."""
    config = mock_config_repo.get_config.return_value
    config.supported_formats = "not_a_list"
    result = service.get_supported_formats()
    assert result == []


@pytest.mark.parametrize(
    ("patterns", "expected"),
    [
        (["*.tmp", "*.bak"], ["*.tmp", "*.bak"]),
        (None, []),
        ([], []),
    ],
)
def test_get_ignore_patterns(
    service: IngestConfigService,
    mock_config_repo: MagicMock,
    patterns: list[str] | None,
    expected: list[str],
) -> None:
    """Test get_ignore_patterns method with various inputs."""
    config = mock_config_repo.get_config.return_value
    config.ignore_patterns = patterns
    result = service.get_ignore_patterns()
    assert result == expected


def test_get_ignore_patterns_not_list(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test get_ignore_patterns returns empty list when not a list."""
    config = mock_config_repo.get_config.return_value
    config.ignore_patterns = "not_a_list"
    result = service.get_ignore_patterns()
    assert result == []


def test_get_merge_strategy(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test get_merge_strategy method."""
    result = service.get_merge_strategy()
    assert result == "merge_best"
    mock_config_repo.get_config.assert_called_once()


def test_get_merge_strategy_none(
    service: IngestConfigService, mock_config_repo: MagicMock
) -> None:
    """Test get_merge_strategy returns default when None."""
    config = mock_config_repo.get_config.return_value
    config.metadata_merge_strategy = None
    result = service.get_merge_strategy()
    assert result == "merge_best"
