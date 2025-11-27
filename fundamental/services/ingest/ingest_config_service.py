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

"""Ingest configuration service.

Manages ingest service configuration. Follows SRP and IOC principles.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fundamental.models.ingest import IngestConfig  # noqa: TC001
from fundamental.repositories.ingest_repository import IngestConfigRepository

if TYPE_CHECKING:
    from sqlmodel import Session


class IngestConfigService:
    """Service for managing ingest configuration.

    Provides business logic for ingest configuration management.
    Follows SRP by focusing solely on configuration operations.

    Parameters
    ----------
    session : Session
        Database session.
    config_repo : IngestConfigRepository | None
        Optional config repository (creates default if None).
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        config_repo: IngestConfigRepository | None = None,
    ) -> None:
        """Initialize ingest config service.

        Parameters
        ----------
        session : Session
            Database session.
        config_repo : IngestConfigRepository | None
            Optional config repository.
        """
        self._session = session
        self._config_repo = config_repo or IngestConfigRepository(session)

    def get_config(self) -> IngestConfig:
        """Get ingest configuration.

        Returns
        -------
        IngestConfig
            Current ingest configuration.
        """
        return self._config_repo.get_config()

    def update_config(self, **kwargs: object) -> IngestConfig:
        """Update ingest configuration.

        Parameters
        ----------
        **kwargs : object
            Configuration fields to update.

        Returns
        -------
        IngestConfig
            Updated configuration.

        Raises
        ------
        ValueError
            If invalid configuration values are provided.
        """
        # Validate ingest_dir if provided
        if "ingest_dir" in kwargs:
            ingest_dir = str(kwargs["ingest_dir"])
            path = Path(ingest_dir)
            if not path.is_absolute():
                msg = f"ingest_dir must be an absolute path: {ingest_dir}"
                raise ValueError(msg)

        # Validate metadata_providers if provided
        if "metadata_providers" in kwargs:
            providers = kwargs["metadata_providers"]
            if not isinstance(providers, list):
                msg = "metadata_providers must be a list"
                raise ValueError(msg)
            valid_providers = ["google", "hardcover", "openlibrary"]
            for provider in providers:
                if provider not in valid_providers:
                    msg = f"Invalid metadata provider: {provider}. Valid: {valid_providers}"
                    raise ValueError(msg)

        return self._config_repo.update_config(**kwargs)

    def is_enabled(self) -> bool:
        """Check if ingest service is enabled.

        Returns
        -------
        bool
            True if ingest is enabled, False otherwise.
        """
        config = self.get_config()
        return config.enabled

    def get_ingest_dir(self) -> Path:
        """Get ingest directory path.

        Returns
        -------
        Path
            Ingest directory path.
        """
        config = self.get_config()
        return Path(config.ingest_dir)

    def get_enabled_providers(self) -> list[str]:
        """Get list of enabled metadata providers.

        Returns
        -------
        list[str]
            List of enabled provider IDs.
        """
        config = self.get_config()
        if config.metadata_providers is None:
            return []
        if isinstance(config.metadata_providers, list):
            return config.metadata_providers
        return []

    def get_supported_formats(self) -> list[str]:
        """Get list of supported file formats.

        Returns
        -------
        list[str]
            List of supported file extensions (without dots).
        """
        config = self.get_config()
        if config.supported_formats is None:
            return []
        if isinstance(config.supported_formats, list):
            return config.supported_formats
        return []

    def get_ignore_patterns(self) -> list[str]:
        """Get list of ignore patterns.

        Returns
        -------
        list[str]
            List of file patterns to ignore.
        """
        config = self.get_config()
        if config.ignore_patterns is None:
            return []
        if isinstance(config.ignore_patterns, list):
            return config.ignore_patterns
        return []
