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

"""Ingest discovery task implementation.

Scans the ingest directory and queues book processing tasks.
"""

import logging
from typing import Any

from fundamental.services.ingest.file_discovery_service import FileDiscoveryService
from fundamental.services.ingest.ingest_config_service import IngestConfigService
from fundamental.services.ingest.ingest_processor_service import IngestProcessorService
from fundamental.services.ingest.metadata_extraction_service import (
    MetadataExtractionService,
)
from fundamental.services.tasks.base import BaseTask
from fundamental.services.tasks.context import WorkerContext

logger = logging.getLogger(__name__)


class IngestDiscoveryTask(BaseTask):
    """Task for discovering and queuing book files for ingest.

    Scans the ingest directory, discovers book files, groups them,
    and creates ingest history records. Then queues IngestBookTask
    for each file group.
    """

    def run(self, worker_context: dict[str, Any] | WorkerContext) -> None:
        """Execute ingest discovery task.

        Parameters
        ----------
        worker_context : dict[str, Any] | WorkerContext
            Worker context containing session, task_service, update_progress.
        """
        # Convert dict to WorkerContext for type safety
        if isinstance(worker_context, dict):
            context = WorkerContext(
                session=worker_context["session"],
                update_progress=worker_context["update_progress"],
                task_service=worker_context["task_service"],
            )
        else:
            context = worker_context

        try:
            # Update progress: 0.1 - starting discovery
            context.update_progress(0.1, None)

            # Get config service
            config_service = IngestConfigService(context.session)
            config = config_service.get_config()

            if not config.enabled:
                logger.info("Ingest service is disabled, skipping discovery")
                context.update_progress(1.0, {"message": "Ingest disabled"})
                return

            # Get ingest directory
            ingest_dir = config_service.get_ingest_dir()
            if not ingest_dir.exists():
                logger.warning("Ingest directory does not exist: %s", ingest_dir)
                context.update_progress(1.0, {"error": "Ingest directory not found"})
                return

            # Update progress: 0.2 - discovering files
            context.update_progress(0.2, None)

            # Discover files
            discovery_service = FileDiscoveryService(
                supported_formats=config_service.get_supported_formats(),
                ignore_patterns=config_service.get_ignore_patterns(),
            )
            files = discovery_service.discover_files(ingest_dir)

            if not files:
                logger.info("No book files found in ingest directory")
                context.update_progress(1.0, {"message": "No files found"})
                return

            # Update progress: 0.4 - extracting metadata and grouping
            context.update_progress(0.4, {"file_count": len(files)})

            # Extract metadata and group files
            metadata_service = MetadataExtractionService()
            file_groups = metadata_service.group_files_by_metadata(files)

            logger.info(
                "Discovered %d files, grouped into %d book groups",
                len(files),
                len(file_groups),
            )

            # Update progress: 0.6 - creating history records
            context.update_progress(0.6, {"group_count": len(file_groups)})

            # Process each file group
            processor_service = IngestProcessorService(context.session)
            history_ids: list[int] = []

            for i, file_group in enumerate(file_groups):
                try:
                    history_id = processor_service.process_file_group(
                        file_group, user_id=self.user_id
                    )
                    history_ids.append(history_id)

                    # Queue IngestBookTask for this group
                    # Note: We'll need access to task_runner, which should be in app state
                    # For now, we'll store the history_id and let the watcher or
                    # a scheduled task pick it up
                    logger.info(
                        "Created ingest history %d for group: %s",
                        history_id,
                        file_group.book_key,
                    )
                except Exception:
                    logger.exception(
                        "Failed to process file group %s",
                        file_group.book_key,
                    )

                # Update progress
                progress = 0.6 + (0.3 * (i + 1) / len(file_groups))
                context.update_progress(progress, {"processed": i + 1})

            # Update progress: 1.0 - complete
            context.update_progress(1.0, {"history_ids": history_ids})

            logger.info(
                "Ingest discovery completed: %d file groups processed",
                len(history_ids),
            )

        except Exception:
            logger.exception("Ingest discovery task failed")
            raise
