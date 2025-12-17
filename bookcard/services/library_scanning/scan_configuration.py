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

"""Scan configuration models and providers.

Handles loading and providing scan configuration from various sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from sqlmodel import select

if TYPE_CHECKING:
    from sqlmodel import Session

from bookcard.models.config import LibraryScanProviderConfig


@dataclass
class ScanConfiguration:
    """Complete configuration for a library scan.

    Attributes
    ----------
    library_id : int
        Library ID to scan.
    data_source_name : str
        Name of the data source provider (e.g., 'openlibrary').
    rate_limit_delay : float | None
        Delay between API requests in seconds.
    stale_data_max_age_days : int | None
        Maximum age of cached data in days before considering it stale.
    stale_data_refresh_interval_days : int | None
        Minimum interval between refreshes in days.
    max_works_per_author : int | None
        Maximum number of works to fetch per author.
    enabled : bool
        Whether the provider is enabled.
    """

    library_id: int
    data_source_name: str
    rate_limit_delay: float | None = None
    stale_data_max_age_days: int | None = None
    stale_data_refresh_interval_days: int | None = None
    max_works_per_author: int | None = None
    enabled: bool = True


class ScanConfigurationProvider(ABC):
    """Abstract provider for scan configuration.

    Follows Strategy pattern to allow different configuration sources.
    """

    @abstractmethod
    def get_configuration(
        self, library_id: int, metadata: dict[str, Any]
    ) -> ScanConfiguration:
        """Get complete scan configuration.

        Parameters
        ----------
        library_id : int
            Library ID to scan.
        metadata : dict[str, Any]
            Task metadata containing optional data_source_config.

        Returns
        -------
        ScanConfiguration
            Complete scan configuration.

        Raises
        ------
        ValueError
            If provider is disabled or configuration is invalid.
        """


class DatabaseScanConfigurationProvider(ScanConfigurationProvider):
    """Fetch scan configuration from database.

    Merges task metadata with provider configuration from database.
    """

    def __init__(self, session: "Session") -> None:
        """Initialize database configuration provider.

        Parameters
        ----------
        session : Session
            Database session for querying configuration.
        """
        self.session = session

    def get_configuration(
        self, library_id: int, metadata: dict[str, Any]
    ) -> ScanConfiguration:
        """Get configuration from database.

        Parameters
        ----------
        library_id : int
            Library ID to scan.
        metadata : dict[str, Any]
            Task metadata containing optional data_source_config.

        Returns
        -------
        ScanConfiguration
            Complete scan configuration.

        Raises
        ------
        ValueError
            If provider is disabled.
        """
        # Get data source from metadata
        data_source_config = metadata.get("data_source_config", {})
        data_source_name = data_source_config.get("name", "openlibrary")

        # Load provider config from database
        stmt = select(LibraryScanProviderConfig).where(
            LibraryScanProviderConfig.provider_name == data_source_name
        )
        provider_config = self.session.exec(stmt).first()

        # Check if enabled
        if provider_config and not provider_config.enabled:
            error_msg = f"Provider '{data_source_name}' is disabled"
            raise ValueError(error_msg)

        # Build configuration from provider config or defaults
        if provider_config:
            return ScanConfiguration(
                library_id=library_id,
                data_source_name=data_source_name,
                rate_limit_delay=provider_config.rate_limit_delay_seconds,
                stale_data_max_age_days=provider_config.stale_data_max_age_days,
                stale_data_refresh_interval_days=(
                    provider_config.stale_data_refresh_interval_days
                ),
                max_works_per_author=provider_config.max_works_per_author,
                enabled=provider_config.enabled,
            )

        # Return default configuration if no provider config found
        return ScanConfiguration(
            library_id=library_id,
            data_source_name=data_source_name,
            enabled=True,
        )
