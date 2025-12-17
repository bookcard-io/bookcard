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

"""URL download plugin source."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from bookcard.services.calibre_plugin_service.exceptions import PluginSourceError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from bookcard.services.calibre_plugin_service.sources.base import (
        TempDirectoryFactory,
    )


def _validate_url(url: str) -> None:
    """Validate a URL.

    Parameters
    ----------
    url : str
        URL to validate.

    Raises
    ------
    PluginSourceError
        If the URL is invalid.
    """
    if not url or not url.strip():
        msg = "URL cannot be empty"
        raise PluginSourceError(msg)
    parsed = urlparse(url)
    if not parsed.scheme:
        msg = "URL must include a scheme (e.g., http:// or https://)"
        raise PluginSourceError(msg)
    if parsed.scheme not in {"http", "https"}:
        msg = f"Unsupported URL scheme: {parsed.scheme}. Only http:// and https:// are supported"
        raise PluginSourceError(msg)


@dataclass(frozen=True, slots=True)
class UrlZipSource:
    """Download a plugin ZIP from a URL.

    Parameters
    ----------
    url : str
        URL to download the ZIP file from.
    tempdirs : TempDirectoryFactory
        Temporary directory factory.
    timeout_s : float, optional
        Timeout for HTTP request.
    """

    url: str
    tempdirs: TempDirectoryFactory
    timeout_s: float = 120.0

    def open(self) -> contextlib.AbstractContextManager[Path]:
        """Download ZIP from URL and yield the local path.

        Returns
        -------
        contextlib.AbstractContextManager[Path]
            Context manager yielding the downloaded ZIP path.

        Raises
        ------
        PluginSourceError
            If the URL is invalid or download fails.
        FileNotFoundError
            If the downloaded file does not exist.
        ValueError
            If the downloaded file is not a ZIP.
        """
        _validate_url(self.url)

        @contextlib.contextmanager
        def _cm() -> Iterator[Path]:
            with self.tempdirs.create(prefix="calibre_plugin_url_") as tmp:
                zip_path = tmp / "plugin.zip"

                try:
                    with httpx.Client(
                        timeout=self.timeout_s,
                        follow_redirects=True,
                    ) as client:
                        response = client.get(self.url)
                        response.raise_for_status()
                        zip_path.write_bytes(response.content)
                except httpx.HTTPStatusError as e:
                    msg = f"Failed to download plugin: HTTP {e.response.status_code}"
                    raise PluginSourceError(msg) from e
                except httpx.RequestError as e:
                    msg = f"Failed to download plugin: {e}"
                    raise PluginSourceError(msg) from e
                except OSError as e:
                    msg = f"Failed to save downloaded plugin: {e}"
                    raise PluginSourceError(msg) from e

                if not zip_path.exists():
                    msg = "Downloaded file not found"
                    raise FileNotFoundError(msg)
                if zip_path.suffix.lower() != ".zip":
                    msg = "Only .zip plugins are supported"
                    raise ValueError(msg)

                yield zip_path

        return _cm()
