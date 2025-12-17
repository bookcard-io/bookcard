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

"""Author metadata fetch task implementation.

Handles fetching and updating author metadata from OpenLibrary
with progress tracking.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from bookcard.repositories.author_repository import AuthorRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.author_service import AuthorService
from bookcard.services.config_service import LibraryService
from bookcard.services.tasks.base import BaseTask

if TYPE_CHECKING:
    from sqlmodel import Session

logger = logging.getLogger(__name__)


class AuthorMetadataFetchTask(BaseTask):
    """Task for fetching and updating author metadata.

    Handles fetching latest biography, metadata, subjects, etc. from OpenLibrary
    with progress tracking.

    Attributes
    ----------
    author_id : str
        Author ID or OpenLibrary key to fetch metadata for.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize author metadata fetch task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing author_id.
        """
        super().__init__(task_id, user_id, metadata)
        author_id = metadata.get("author_id", "")
        if not author_id:
            msg = "author_id is required in task metadata"
            raise ValueError(msg)
        self.author_id = author_id

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute author metadata fetch task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        session: Session = worker_context["session"]
        update_progress = worker_context["update_progress"]

        try:
            # Check if cancelled
            if self.check_cancelled():
                logger.info("Task %s cancelled before processing", self.task_id)
                return

            # Update progress: 0.1 - starting
            update_progress(0.1, {"status": "initializing"})

            # Create author service
            author_repo = AuthorRepository(session)
            library_repo = LibraryRepository(session)
            library_service = LibraryService(session, library_repo)
            author_service = AuthorService(
                session=session,
                author_repo=author_repo,
                library_service=library_service,
                library_repo=library_repo,
            )

            # Update progress: 0.3 - service created
            update_progress(0.3, {"status": "fetching_metadata"})

            # Check if cancelled
            if self.check_cancelled():
                return

            # Fetch metadata (this is the long-running operation)
            result = author_service.fetch_author_metadata(self.author_id)

            # Update progress: 0.9 - metadata fetched
            update_progress(0.9, {"status": "completed", **result})

            # Update progress: 1.0 - complete
            update_progress(1.0, self.metadata)

            logger.info(
                "Task %s: Author metadata fetched successfully for %s: %s",
                self.task_id,
                self.author_id,
                result.get("message", "Success"),
            )

        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise
