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

"""OpenLibrary service for managing dump file operations.

Follows SRP by focusing solely on OpenLibrary dump file business operations.
Uses IOC by accepting TaskRunner and AppConfig as dependencies.
Separates concerns: HTTP handling (routes) vs business logic (service).
"""

from typing import TYPE_CHECKING

from bookcard.models.tasks import TaskType

if TYPE_CHECKING:
    from bookcard.config import AppConfig
    from bookcard.services.tasks.base import TaskRunner


class OpenLibraryService:
    """Service for OpenLibrary dump file operations.

    Handles creation of tasks for downloading and ingesting OpenLibrary dump files.
    Uses TaskRunner for task execution and AppConfig for configuration.

    Parameters
    ----------
    task_runner : TaskRunner
        Task runner for enqueueing background tasks.
    config : AppConfig
        Application configuration containing data_directory.
    """

    def __init__(
        self,
        task_runner: "TaskRunner",
        config: "AppConfig",
    ) -> None:
        """Initialize OpenLibrary service.

        Parameters
        ----------
        task_runner : TaskRunner
            Task runner instance.
        config : AppConfig
            Application configuration.
        """
        self._task_runner = task_runner
        self._config = config

    def create_download_task(
        self,
        urls: list[str],
        user_id: int,
    ) -> int:
        """Create a task to download OpenLibrary dump files from URLs.

        Parameters
        ----------
        urls : list[str]
            List of file URLs to download.
        user_id : int
            ID of user creating the task.

        Returns
        -------
        int
            Task ID for tracking the download progress.

        Raises
        ------
        ValueError
            If no URLs provided.
        """
        if not urls:
            msg = "No URLs provided"
            raise ValueError(msg)

        return self._task_runner.enqueue(
            task_type=TaskType.OPENLIBRARY_DUMP_DOWNLOAD,
            payload={"urls": urls},
            user_id=user_id,
            metadata={
                "task_type": TaskType.OPENLIBRARY_DUMP_DOWNLOAD,
                "urls": urls,
                "data_directory": self._config.data_directory,
            },
        )

    def create_ingest_task(
        self,
        user_id: int,
        process_authors: bool = True,
        process_works: bool = True,
        process_editions: bool = True,
    ) -> int:
        """Create a task to ingest OpenLibrary dump files into database.

        Parameters
        ----------
        user_id : int
            ID of user creating the task.
        process_authors : bool
            Whether to process authors dump file. Defaults to True.
        process_works : bool
            Whether to process works dump file. Defaults to True.
        process_editions : bool
            Whether to process editions dump file. Defaults to True.

        Returns
        -------
        int
            Task ID for tracking the ingest progress.
        """
        return self._task_runner.enqueue(
            task_type=TaskType.OPENLIBRARY_DUMP_INGEST,
            payload={},
            user_id=user_id,
            metadata={
                "task_type": TaskType.OPENLIBRARY_DUMP_INGEST,
                "data_directory": self._config.data_directory,
                "process_authors": process_authors,
                "process_works": process_works,
                "process_editions": process_editions,
            },
        )
