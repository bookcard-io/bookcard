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

"""Prowlarr sync task implementation."""

import logging
from typing import Any

from bookcard.pvr.sync.service import ProwlarrSyncService
from bookcard.services.tasks.base import BaseTask

logger = logging.getLogger(__name__)


class ProwlarrSyncTask(BaseTask):
    """Task for synchronizing indexers from Prowlarr."""

    def run(self, worker_context: Any) -> None:  # noqa: ANN401
        """Execute the Prowlarr sync task.

        Parameters
        ----------
        worker_context : Any
            Worker context containing the database session.
        """
        logger.info("Starting Prowlarr sync task %s", self.task_id)

        # worker_context is expected to have a session attribute
        # based on usage in other tasks
        session = worker_context.session
        service = ProwlarrSyncService(session)

        try:
            stats = service.sync_indexers()
            self.set_metadata("stats", stats)
            logger.info("Prowlarr sync task %s completed successfully", self.task_id)
        except Exception:
            logger.exception("Prowlarr sync task %s failed", self.task_id)
            raise
