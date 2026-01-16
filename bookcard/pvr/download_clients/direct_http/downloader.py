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

"""File downloader for Direct HTTP download client."""

import logging
from pathlib import Path

from bookcard.pvr.download_clients.direct_http.protocols import (
    StreamingHttpClient,
    TimeProvider,
)
from bookcard.pvr.download_clients.direct_http.settings import DownloadConstants
from bookcard.pvr.download_clients.direct_http.state import DownloadStateManager
from bookcard.pvr.exceptions import PVRProviderError

logger = logging.getLogger(__name__)


class FileDownloader:
    """Handles file downloading with progress tracking."""

    def __init__(self, time_provider: TimeProvider) -> None:
        self._time = time_provider

    def download(
        self,
        client: StreamingHttpClient,
        url: str,
        target_path: Path,
        download_id: str,
        state_manager: DownloadStateManager,
    ) -> None:
        """Download file with progress updates."""
        try:
            with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", 0))
                state_manager.update_info(download_id, total_size, str(target_path))

                downloaded = 0
                start_time = self._time.time()
                last_update = 0.0

                with target_path.open("wb") as f:
                    for chunk in response.iter_bytes(
                        chunk_size=DownloadConstants.DOWNLOAD_CHUNK_SIZE
                    ):
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        now = self._time.time()
                        if now - last_update >= DownloadConstants.UPDATE_INTERVAL:
                            elapsed = now - start_time
                            speed = downloaded / elapsed if elapsed > 0 else 0.0
                            progress = (
                                downloaded / total_size if total_size > 0 else 0.0
                            )
                            state_manager.update_progress(
                                download_id, downloaded, progress, speed
                            )
                            last_update = now

                # Final update
                elapsed = self._time.time() - start_time
                speed = downloaded / elapsed if elapsed > 0 else 0.0
                state_manager.update_progress(download_id, downloaded, 1.0, speed)

        except OSError as e:
            msg = f"File Error: {e}"
            logger.exception(msg)
            raise PVRProviderError(msg) from e
