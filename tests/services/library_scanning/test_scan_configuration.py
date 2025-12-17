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

"""Tests for scan configuration to achieve 100% coverage."""

from unittest.mock import MagicMock

import pytest

from bookcard.models.config import LibraryScanProviderConfig
from bookcard.services.library_scanning.scan_configuration import (
    DatabaseScanConfigurationProvider,
    ScanConfiguration,
)


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    session = MagicMock()
    session.exec.return_value.first.return_value = None
    return session


@pytest.fixture
def provider_config() -> LibraryScanProviderConfig:
    """Create a provider configuration."""
    return LibraryScanProviderConfig(
        id=1,
        provider_name="openlibrary",
        enabled=True,
        rate_limit_delay_seconds=1.0,
        stale_data_max_age_days=30,
        stale_data_refresh_interval_days=7,
        max_works_per_author=100,
    )


class TestScanConfiguration:
    """Test ScanConfiguration dataclass."""

    def test_scan_configuration_defaults(self) -> None:
        """Test ScanConfiguration with default values."""
        config = ScanConfiguration(
            library_id=1,
            data_source_name="openlibrary",
        )
        assert config.library_id == 1
        assert config.data_source_name == "openlibrary"
        assert config.rate_limit_delay is None
        assert config.stale_data_max_age_days is None
        assert config.stale_data_refresh_interval_days is None
        assert config.max_works_per_author is None
        assert config.enabled is True

    def test_scan_configuration_with_all_values(self) -> None:
        """Test ScanConfiguration with all values set."""
        config = ScanConfiguration(
            library_id=1,
            data_source_name="openlibrary",
            rate_limit_delay=1.0,
            stale_data_max_age_days=30,
            stale_data_refresh_interval_days=7,
            max_works_per_author=100,
            enabled=False,
        )
        assert config.library_id == 1
        assert config.data_source_name == "openlibrary"
        assert config.rate_limit_delay == 1.0
        assert config.stale_data_max_age_days == 30
        assert config.stale_data_refresh_interval_days == 7
        assert config.max_works_per_author == 100
        assert config.enabled is False


class TestDatabaseScanConfigurationProvider:
    """Test DatabaseScanConfigurationProvider."""

    def test_init_stores_session(self, mock_session: MagicMock) -> None:
        """Test __init__ stores session."""
        provider = DatabaseScanConfigurationProvider(mock_session)
        assert provider.session == mock_session

    def test_get_configuration_with_provider_config(
        self, mock_session: MagicMock, provider_config: LibraryScanProviderConfig
    ) -> None:
        """Test get_configuration with provider config from database."""
        mock_session.exec.return_value.first.return_value = provider_config
        provider = DatabaseScanConfigurationProvider(mock_session)

        config = provider.get_configuration(1, {})

        assert config.library_id == 1
        assert config.data_source_name == "openlibrary"
        assert config.rate_limit_delay == 1.0
        assert config.stale_data_max_age_days == 30
        assert config.stale_data_refresh_interval_days == 7
        assert config.max_works_per_author == 100
        assert config.enabled is True

    def test_get_configuration_with_metadata_data_source(
        self, mock_session: MagicMock, provider_config: LibraryScanProviderConfig
    ) -> None:
        """Test get_configuration uses data source from metadata."""
        mock_session.exec.return_value.first.return_value = provider_config
        provider = DatabaseScanConfigurationProvider(mock_session)

        metadata = {
            "data_source_config": {
                "name": "custom_source",
                "kwargs": {},
            },
        }
        config = provider.get_configuration(1, metadata)

        assert config.data_source_name == "custom_source"
        # Verify query was made with custom_source
        mock_session.exec.assert_called_once()

    def test_get_configuration_with_default_data_source(
        self, mock_session: MagicMock
    ) -> None:
        """Test get_configuration uses default data source when not in metadata."""
        mock_session.exec.return_value.first.return_value = None
        provider = DatabaseScanConfigurationProvider(mock_session)

        config = provider.get_configuration(1, {})

        assert config.data_source_name == "openlibrary"
        assert config.enabled is True
        assert config.rate_limit_delay is None

    def test_get_configuration_provider_disabled_raises_error(
        self, mock_session: MagicMock
    ) -> None:
        """Test get_configuration raises ValueError when provider is disabled."""
        disabled_config = LibraryScanProviderConfig(
            id=1,
            provider_name="openlibrary",
            enabled=False,
        )
        mock_session.exec.return_value.first.return_value = disabled_config
        provider = DatabaseScanConfigurationProvider(mock_session)

        with pytest.raises(ValueError, match=r"Provider 'openlibrary' is disabled"):
            provider.get_configuration(1, {})

    def test_get_configuration_no_provider_config_returns_defaults(
        self, mock_session: MagicMock
    ) -> None:
        """Test get_configuration returns defaults when no provider config found."""
        mock_session.exec.return_value.first.return_value = None
        provider = DatabaseScanConfigurationProvider(mock_session)

        config = provider.get_configuration(1, {})

        assert config.library_id == 1
        assert config.data_source_name == "openlibrary"
        assert config.enabled is True
        assert config.rate_limit_delay is None
        assert config.stale_data_max_age_days is None
        assert config.stale_data_refresh_interval_days is None
        assert config.max_works_per_author is None

    def test_get_configuration_with_partial_metadata(
        self, mock_session: MagicMock, provider_config: LibraryScanProviderConfig
    ) -> None:
        """Test get_configuration with partial metadata."""
        mock_session.exec.return_value.first.return_value = provider_config
        provider = DatabaseScanConfigurationProvider(mock_session)

        metadata = {"data_source_config": {"name": "openlibrary"}}
        config = provider.get_configuration(1, metadata)

        assert config.data_source_name == "openlibrary"
        assert config.rate_limit_delay == 1.0
