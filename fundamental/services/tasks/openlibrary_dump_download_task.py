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

"""OpenLibrary dump download task implementation.

Handles downloading OpenLibrary data dump files with progress tracking.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx

from fundamental.services.tasks.base import BaseTask

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class OpenLibraryDumpDownloadTask(BaseTask):
    """Task for downloading OpenLibrary dump files.

    Downloads files from URLs and saves them to the configured dump directory
    with progress tracking.

    Attributes
    ----------
    urls : list[str]
        List of URLs to download.
    dump_dir : Path
        Directory where files will be saved.
    """

    def __init__(
        self,
        task_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> None:
        """Initialize OpenLibrary dump download task.

        Parameters
        ----------
        task_id : int
            Database task ID.
        user_id : int
            User ID creating the task.
        metadata : dict[str, Any]
            Task metadata containing urls and data_directory.
        """
        super().__init__(task_id, user_id, metadata)
        urls = metadata.get("urls", [])
        if not urls or not isinstance(urls, list):
            msg = "urls is required in task metadata and must be a list"
            raise ValueError(msg)
        self.urls = urls
        data_directory = metadata.get("data_directory", "/data")
        self.dump_dir = Path(data_directory) / "openlibrary" / "dump"

    def _download_file(
        self,
        url: str,
        update_progress: Callable[..., None],  # type: ignore[type-arg]
        file_index: int,
        total_files: int,
    ) -> str:
        """Download a single file from URL.

        Parameters
        ----------
        url : str
            URL to download.
        update_progress : Any
            Progress update callback.
        file_index : int
            Index of current file (0-based).
        total_files : int
            Total number of files to download.

        Returns
        -------
        str
            Path to downloaded file.

        Raises
        ------
        Exception
            If download fails.
        """
        # Extract filename from URL
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename:
            filename = "download"
        file_path = self.dump_dir / filename

        # Ensure directory exists
        self.dump_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Downloading %s to %s", url, file_path)

        # Download file with progress tracking
        with (
            httpx.Client(timeout=300.0, follow_redirects=True) as client,
            client.stream("GET", url) as response,
        ):
            response.raise_for_status()

            # Get content length for progress calculation
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            # Write file
            with file_path.open("wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    if self.check_cancelled():
                        file_path.unlink(missing_ok=True)
                        error_msg = "Task cancelled"
                        raise InterruptedError(error_msg)

                    f.write(chunk)
                    downloaded += len(chunk)

                    # Update progress: base progress for this file + download progress
                    file_base_progress = file_index / total_files
                    file_progress = downloaded / total_size if total_size > 0 else 0.5
                    overall_progress = file_base_progress + (
                        file_progress / total_files
                    )
                    update_progress(
                        min(overall_progress, 0.99),
                        {
                            "current_file": filename,
                            "downloaded_bytes": downloaded,
                            "total_bytes": total_size if total_size > 0 else None,
                        },
                    )

        logger.info("Successfully downloaded %s", filename)
        return str(file_path)

    def _raise_all_failed_error(self, failed_files: list[str]) -> None:
        """Raise error when all files failed to download.

        Parameters
        ----------
        failed_files : list[str]
            List of URLs that failed to download.

        Raises
        ------
        RuntimeError
            Always raised with error message.
        """
        msg = f"Failed to download all files: {failed_files}"
        raise RuntimeError(msg)

    def run(self, worker_context: dict[str, Any]) -> None:
        """Execute OpenLibrary dump download task.

        Parameters
        ----------
        worker_context : dict[str, Any]
            Worker context containing session, task_service, update_progress.
        """
        update_progress = worker_context["update_progress"]

        try:
            # Check if cancelled
            if self.check_cancelled():
                logger.info("Task %s cancelled before processing", self.task_id)
                return

            total_files = len(self.urls)
            downloaded_files: list[str] = []
            failed_files: list[str] = []

            # Update progress: 0.0 - starting
            update_progress(0.0, {"total_files": total_files})

            # Download each file
            for index, url in enumerate(self.urls):
                if self.check_cancelled():
                    logger.info("Task %s cancelled during download", self.task_id)
                    return

                try:
                    file_path = self._download_file(
                        url,
                        update_progress,
                        index,
                        total_files,
                    )
                    downloaded_files.append(file_path)
                    self.set_metadata("downloaded_files", downloaded_files)
                except Exception:
                    logger.exception("Failed to download %s", url)
                    failed_files.append(url)
                    self.set_metadata("failed_files", failed_files)

            # Update progress: 1.0 - complete
            update_progress(
                1.0,
                {
                    "downloaded_files": downloaded_files,
                    "failed_files": failed_files,
                    "total_files": total_files,
                },
            )

            if failed_files and not downloaded_files:
                self._raise_all_failed_error(failed_files)

            logger.info(
                "Task %s: Downloaded %d file(s), %d failed",
                self.task_id,
                len(downloaded_files),
                len(failed_files),
            )

        except Exception:
            logger.exception("Task %s failed", self.task_id)
            raise
