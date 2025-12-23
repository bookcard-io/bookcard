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

"""Pneumatic download client implementation.

Pneumatic is a file-based usenet client that saves NZB files
and creates .strm files for XBMC/Kodi integration.
"""

import logging
import tempfile
from collections.abc import Sequence
from pathlib import Path

import httpx

from bookcard.pvr.base import (
    BaseDownloadClient,
    DownloadClientSettings,
    PVRProviderError,
)

logger = logging.getLogger(__name__)


class PneumaticSettings(DownloadClientSettings):
    """Settings for Pneumatic download client.

    Attributes
    ----------
    nzb_folder : str
        Folder to save NZB files.
    strm_folder : str
        Folder to save .strm files.
    """

    nzb_folder: str = f"{tempfile.gettempdir()}/nzbs"
    strm_folder: str = f"{tempfile.gettempdir()}/strm"


class PneumaticClient(BaseDownloadClient):
    """Pneumatic download client implementation.

    Pneumatic is a file-based usenet client that saves NZB files
    and creates .strm files for XBMC/Kodi integration.
    """

    def __init__(
        self,
        settings: PneumaticSettings | DownloadClientSettings,
        enabled: bool = True,
    ) -> None:
        """Initialize Pneumatic client."""
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, PneumaticSettings
        ):
            pneumatic_settings = PneumaticSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
                nzb_folder=settings.download_path or f"{tempfile.gettempdir()}/nzbs",
                strm_folder=settings.download_path or f"{tempfile.gettempdir()}/strm",
            )
            settings = pneumatic_settings

        super().__init__(settings, enabled)
        self.settings: PneumaticSettings = settings  # type: ignore[assignment]

        # Ensure directories exist
        Path(self.settings.nzb_folder).mkdir(parents=True, exist_ok=True)
        Path(self.settings.strm_folder).mkdir(parents=True, exist_ok=True)

    def add_download(
        self,
        download_url: str,
        title: str | None = None,
        category: str | None = None,  # noqa: ARG002
        download_path: str | None = None,  # noqa: ARG002
    ) -> str:
        """Add a download to Pneumatic.

        Parameters
        ----------
        download_url : str
            URL to NZB file.
        title : str | None
            Optional title.
        category : str | None
            Optional category (not used).
        download_path : str | None
            Optional download path (not used).

        Returns
        -------
        str
            Download ID (based on filename).

        Raises
        ------
        PVRProviderError
            If adding the download fails.
        """
        if not self.is_enabled():
            msg = "Pneumatic client is disabled"
            raise PVRProviderError(msg)

        def _raise_invalid_url_error() -> None:
            """Raise error for invalid download URL."""
            msg = f"Invalid download URL: {download_url}"
            raise PVRProviderError(msg)

        try:
            # Download NZB file
            if download_url.startswith("http"):
                with httpx.Client() as client:
                    response = client.get(download_url, timeout=30)
                    response.raise_for_status()
                    nzb_data = response.content
            else:
                _raise_invalid_url_error()

            # Clean filename
            if title:
                from bookcard.pvr.download_clients.blackhole import _clean_filename

                filename_base = _clean_filename(title)
            else:
                filename_base = "download"

            # Ensure directories exist
            Path(self.settings.nzb_folder).mkdir(parents=True, exist_ok=True)
            Path(self.settings.strm_folder).mkdir(parents=True, exist_ok=True)

            # Save NZB file
            nzb_path = Path(self.settings.nzb_folder) / f"{filename_base}.nzb"
            nzb_path.write_bytes(nzb_data)

            # Create .strm file
            strm_content = (
                f"plugin://plugin.program.pneumatic/?mode=strm&type=add_file&"
                f"nzb={nzb_path}&nzbname={filename_base}"
            )
            strm_path = Path(self.settings.strm_folder) / f"{filename_base}.strm"
            strm_path.write_text(strm_content, encoding="utf-8")

            # Return ID based on filename and modification time
            return f"pneumatic_{strm_path.name}_{int(strm_path.stat().st_mtime)}"

        except Exception as e:
            msg = f"Failed to add download to Pneumatic: {e}"
            raise PVRProviderError(msg) from e

    def get_items(self) -> Sequence[dict[str, str | int | float | None]]:
        """Get list of active downloads.

        Returns
        -------
        Sequence[dict[str, str | int | float | None]]
            Sequence of download items.
        """
        if not self.is_enabled():
            return []

        try:
            items = []
            strm_folder = Path(self.settings.strm_folder)

            if not strm_folder.exists():
                return []

            for strm_file in strm_folder.glob("*.strm"):
                try:
                    # Check if file is locked (being processed)
                    is_locked = False
                    try:
                        # Try to open exclusively
                        with strm_file.open("r+"):
                            pass
                    except OSError:
                        is_locked = True

                    status = "downloading" if is_locked else "completed"

                    # Get file size
                    size_bytes = strm_file.stat().st_size

                    download_id = (
                        f"pneumatic_{strm_file.name}_{int(strm_file.stat().st_mtime)}"
                    )

                    item = {
                        "client_item_id": download_id,
                        "title": strm_file.stem,
                        "status": status,
                        "progress": 1.0 if status == "completed" else 0.5,
                        "size_bytes": size_bytes,
                        "downloaded_bytes": size_bytes
                        if status == "completed"
                        else None,
                        "download_speed_bytes_per_sec": None,
                        "eta_seconds": None,
                        "file_path": str(strm_file),
                    }
                    items.append(item)

                except (OSError, ValueError, AttributeError) as e:
                    logger.warning("Failed to process .strm file %s: %s", strm_file, e)
                    continue

        except (OSError, ValueError) as e:
            logger.warning("Failed to get downloads from Pneumatic: %s", e)
            return []
        else:
            return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:  # noqa: ARG002
        """Remove a download from Pneumatic.

        Parameters
        ----------
        client_item_id : str
            Download ID.
        delete_files : bool
            Whether to delete files.

        Returns
        -------
        bool
            True if removal succeeded.

        Raises
        ------
        PVRProviderError
            If removal fails.
        """
        if not self.is_enabled():
            msg = "Pneumatic client is disabled"
            raise PVRProviderError(msg)

        # Pneumatic doesn't support removal via API
        return False

    def test_connection(self) -> bool:
        """Test connectivity to Pneumatic.

        Returns
        -------
        bool
            True if folders are accessible.

        Raises
        ------
        PVRProviderError
            If the connection test fails.
        """
        try:
            # Test folder accessibility
            nzb_folder = Path(self.settings.nzb_folder)
            strm_folder = Path(self.settings.strm_folder)

            # Try to create test files
            test_nzb = nzb_folder / ".test_write"
            test_strm = strm_folder / ".test_write"

            try:
                test_nzb.write_text("test")
                test_nzb.unlink()
                test_strm.write_text("test")
                test_strm.unlink()
            except (OSError, PermissionError) as e:
                msg = f"Pneumatic folders are not writable: {e}"
                raise PVRProviderError(msg) from e

        except (OSError, PermissionError) as e:
            msg = f"Failed to test Pneumatic connection: {e}"
            raise PVRProviderError(msg) from e
        else:
            return True
