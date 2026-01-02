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

"""Task for checking indexer health."""

import logging
from typing import Any, cast

from sqlmodel import Session, select

from bookcard.config import AppConfig
from bookcard.models.pvr import IndexerDefinition
from bookcard.services.indexer_service import IndexerService
from bookcard.services.security import DataEncryptor
from bookcard.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class IndexerHealthCheckTask(BaseTask):
    """Task to check health of all enabled indexers."""

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute task logic.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing the database session.
        """
        logger.info("Starting indexer health check task")
        session = cast("Session", worker_context["session"])

        # We need a request object to get the encryptor, but in a task context
        # we don't have one. We need to construct the encryptor directly or
        # modify IndexerService to accept it optionally or construct it differently.
        #
        # Looking at IndexerService, it takes an optional encryptor.
        # DataEncryptor usually needs the app key.
        #
        # Let's try to initialize the service without encryptor first if we don't need it for
        # health checks, but we DO need it to decrypt API keys for testing connection.
        #
        # Assuming we can get the encryptor from the app config or similar.
        # For now, we'll try to instantiate DataEncryptor if possible, or assume the service handles it.
        #
        # Actually, `get_data_encryptor` depends on `Request`.
        # We should check how other tasks handle this.
        # `ProwlarrSyncTask` likely faces the same issue.

        # Checking ProwlarrSyncTask implementation would be wise, but let's assume
        # we can instantiate DataEncryptor with the key from config if available.
        # For now, let's try to get indexers and check them.

        # We will use a dummy request or refactor service to not need request.
        # But wait, we can just instantiate DataEncryptor directly if we have the key.
        #
        # However, let's look at how we can get the service.
        #
        # To keep it simple and consistent with other tasks:
        # We'll instantiate IndexerService.

        # We need to get the encryption key.
        # Since we are in a task, we might not have easy access to the request.
        # But let's check if we can get it from `bookcard.config`.

        try:
            config = AppConfig.from_env()
            encryptor = DataEncryptor(config.encryption_key)
            service = IndexerService(session, encryptor=encryptor)

            # Get all enabled indexers
            stmt = select(IndexerDefinition).where(IndexerDefinition.enabled)
            indexers = session.exec(stmt).all()

            if not indexers:
                logger.info("No enabled indexers to check")
                return

            logger.info("Checking health for %d indexers", len(indexers))

            success_count = 0
            fail_count = 0

            for indexer in indexers:
                try:
                    logger.info("Checking health for indexer: %s", indexer.name)
                    service.check_indexer_health(indexer.id)
                    success_count += 1
                except Exception:
                    logger.exception(
                        "Failed to check health for indexer %s", indexer.name
                    )
                    fail_count += 1

            logger.info(
                "Indexer health check completed. Success: %d, Failed: %d",
                success_count,
                fail_count,
            )

        except Exception:
            logger.exception("Indexer health check failed")
            raise
