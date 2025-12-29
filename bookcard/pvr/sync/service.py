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

"""Service for syncing Prowlarr indexers."""

import logging
from collections.abc import Callable

from sqlmodel import Session, select

from bookcard.models.pvr import IndexerDefinition, IndexerStatus, ProwlarrConfig
from bookcard.pvr.sync.client import ProwlarrClient, ProwlarrClientInterface
from bookcard.pvr.sync.exceptions import (
    ProwlarrConfigurationError,
    ProwlarrSyncError,
)
from bookcard.pvr.sync.mappers import IndexerUrlBuilder, ProtocolMapper
from bookcard.pvr.sync.models import ProwlarrIndexerResponse, SyncStatistics
from bookcard.services.security import DataEncryptor

logger = logging.getLogger(__name__)

TARGET_CATEGORIES = {"Audio", "Books"}


class ProwlarrSyncService:
    """Service for syncing Prowlarr indexers."""

    def __init__(
        self,
        session: Session,
        client_factory: Callable[[str, str], ProwlarrClientInterface] = ProwlarrClient,
        encryptor: DataEncryptor | None = None,
    ) -> None:
        """Initialize sync service.

        Parameters
        ----------
        session : Session
            Database session.
        client_factory : Callable[[str, str], ProwlarrClientInterface]
            Factory function to create Prowlarr client.
        encryptor : DataEncryptor | None
            Data encryptor for securing API keys.
        """
        self.session = session
        self._client_factory = client_factory
        self._encryptor = encryptor

    def sync_indexers(self) -> dict[str, int]:
        """Sync indexers from Prowlarr.

        Returns
        -------
        dict[str, int]
            Statistics about the sync (added, updated, removed).

        Raises
        ------
        ProwlarrSyncError
            If sync fails.
        """
        try:
            config = self._get_validated_config()
        except ProwlarrConfigurationError as e:
            logger.warning("Prowlarr sync skipped: %s", e)
            return SyncStatistics().to_dict()

        client = self._client_factory(config.url, config.api_key)  # type: ignore[arg-type]

        try:
            prowlarr_indexers = client.get_indexers()
        except ProwlarrSyncError:
            raise
        except Exception as e:
            msg = f"Unexpected error: {e}"
            logger.exception("Unexpected error during Prowlarr sync")
            raise ProwlarrSyncError(msg) from e

        return self._process_indexers(prowlarr_indexers, config)

    def _get_validated_config(self) -> ProwlarrConfig:
        """Get and validate Prowlarr configuration.

        Returns
        -------
        ProwlarrConfig
            Validated configuration.

        Raises
        ------
        ProwlarrConfigurationError
            If configuration is invalid or disabled.
        """
        config = self.session.exec(select(ProwlarrConfig)).first()
        if not config:
            msg = "Prowlarr configuration not found"
            raise ProwlarrConfigurationError(msg)

        if not config.enabled:
            msg = "Prowlarr integration is disabled"
            raise ProwlarrConfigurationError(msg)

        if not config.url or not config.api_key:
            msg = "Prowlarr URL or API key missing"
            raise ProwlarrConfigurationError(msg)

        return config

    def _process_indexers(
        self, indexers: list[ProwlarrIndexerResponse], config: ProwlarrConfig
    ) -> dict[str, int]:
        """Process indexers and update database.

        Parameters
        ----------
        indexers : list[ProwlarrIndexerResponse]
            List of indexers from Prowlarr.
        config : ProwlarrConfig
            Current configuration.

        Returns
        -------
        dict[str, int]
            Sync statistics.
        """
        stats = SyncStatistics()

        for p_indexer in indexers:
            try:
                self._sync_single_indexer(p_indexer, config, stats)
                # Commit per indexer to avoid partial failures rolling back everything
                # In a production environment with strict consistency requirements,
                # we might want to do this differently, but for sync, partial success is better.
                self.session.commit()
            except Exception:
                self.session.rollback()
                logger.exception("Failed to sync indexer %s", p_indexer.name)
                stats.errors += 1

        logger.info("Prowlarr sync completed: %s", stats.to_dict())
        return stats.to_dict()

    def _sync_single_indexer(
        self,
        p_indexer: ProwlarrIndexerResponse,
        config: ProwlarrConfig,
        stats: SyncStatistics,
    ) -> None:
        """Sync a single indexer.

        Parameters
        ----------
        p_indexer : ProwlarrIndexerResponse
            Prowlarr indexer data.
        config : ProwlarrConfig
            Configuration.
        stats : SyncStatistics
            Statistics object to update.
        """
        if not p_indexer.enable:
            return

        # Filter by category
        # Target only Audio or Books categories
        should_sync = False

        if p_indexer.capabilities and "categories" in p_indexer.capabilities:
            categories = p_indexer.capabilities["categories"]
            # Check if any category matches "Audio" or "Books"
            for category in categories:
                if (
                    isinstance(category, dict)
                    and category.get("name") in TARGET_CATEGORIES
                ):
                    should_sync = True
                    break

        # If no matching categories found, skip
        if not should_sync:
            return

        mapping = ProtocolMapper.map_protocol(p_indexer.protocol)
        if not mapping:
            logger.warning(
                "Unknown protocol for indexer %s: %s",
                p_indexer.name,
                p_indexer.protocol,
            )
            return

        protocol, indexer_type = mapping
        base_url = config.url.rstrip("/")
        indexer_url = IndexerUrlBuilder.build_url(base_url, p_indexer.id)

        # Find existing
        stmt = select(IndexerDefinition).where(IndexerDefinition.name == p_indexer.name)
        existing = self.session.exec(stmt).first()

        if existing:
            self._update_indexer(
                existing, indexer_url, config, protocol, indexer_type, p_indexer
            )
            stats.updated += 1
        else:
            self._create_indexer(p_indexer, indexer_url, config, protocol, indexer_type)
            stats.added += 1

    def _update_indexer(
        self,
        existing: IndexerDefinition,
        indexer_url: str,
        config: ProwlarrConfig,
        protocol: str,
        indexer_type: str,
        p_indexer: ProwlarrIndexerResponse,
    ) -> None:
        """Update an existing indexer.

        Parameters
        ----------
        existing : IndexerDefinition
            Existing indexer to update.
        indexer_url : str
            Constructed URL for the indexer.
        config : ProwlarrConfig
            Prowlarr configuration.
        protocol : str
            Mapped protocol.
        indexer_type : str
            Mapped indexer type.
        p_indexer : ProwlarrIndexerResponse
            Prowlarr indexer data.
        """
        api_key = config.api_key
        if api_key and self._encryptor:
            api_key = self._encryptor.encrypt(api_key)

        existing.base_url = indexer_url
        existing.api_key = api_key
        existing.protocol = protocol  # type: ignore[assignment]
        existing.indexer_type = indexer_type  # type: ignore[assignment]

        settings = existing.additional_settings or {}
        settings["prowlarr_id"] = p_indexer.id
        existing.additional_settings = settings

        self.session.add(existing)

    def _create_indexer(
        self,
        p_indexer: ProwlarrIndexerResponse,
        indexer_url: str,
        config: ProwlarrConfig,
        protocol: str,
        indexer_type: str,
    ) -> None:
        """Create a new indexer.

        Parameters
        ----------
        p_indexer : ProwlarrIndexerResponse
            Prowlarr indexer data.
        indexer_url : str
            Constructed URL for the indexer.
        config : ProwlarrConfig
            Prowlarr configuration.
        protocol : str
            Mapped protocol.
        indexer_type : str
            Mapped indexer type.
        """
        api_key = config.api_key
        if api_key and self._encryptor:
            api_key = self._encryptor.encrypt(api_key)

        new_indexer = IndexerDefinition(
            name=p_indexer.name,
            indexer_type=indexer_type,  # type: ignore[arg-type]
            protocol=protocol,  # type: ignore[arg-type]
            base_url=indexer_url,
            api_key=api_key,
            enabled=True,
            priority=p_indexer.priority,
            additional_settings={"prowlarr_id": p_indexer.id},
            status=IndexerStatus.UNHEALTHY,
        )
        self.session.add(new_indexer)
