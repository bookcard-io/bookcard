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

"""Direct HTTP download client implementation."""

import logging
import uuid
from collections.abc import Callable, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

import httpx

from bookcard.pvr.base import (
    DownloadClientSettings,
    TrackingDownloadClient,
)
from bookcard.pvr.base.interfaces import (
    FileFetcherProtocol,
    HttpClientProtocol,
    UrlRouterProtocol,
)
from bookcard.pvr.download_clients._http_client import create_httpx_client
from bookcard.pvr.download_clients.direct_http.anna import AnnaArchiveConfig
from bookcard.pvr.download_clients.direct_http.downloader import FileDownloader
from bookcard.pvr.download_clients.direct_http.protocols import (
    BeautifulSoupParser,
    HtmlParser,
    StreamingHttpClient,
    SystemTimeProvider,
    TimeProvider,
)
from bookcard.pvr.download_clients.direct_http.resolvers import (
    AnnaArchiveResolver,
    DirectUrlResolver,
    FilenameResolver,
    UrlResolver,
)
from bookcard.pvr.download_clients.direct_http.settings import (
    DirectHttpSettings,
    DownloadConstants,
)
from bookcard.pvr.download_clients.direct_http.state import DownloadStateManager
from bookcard.pvr.exceptions import PVRProviderError
from bookcard.pvr.models import DownloadItem
from bookcard.pvr.utils.status import DownloadStatus

logger = logging.getLogger(__name__)


class DirectHttpClient(TrackingDownloadClient):
    """Direct HTTP download client implementation.

    Handles resolving Anna's Archive pages and downloading files directly.
    """

    def __init__(
        self,
        settings: DirectHttpSettings | DownloadClientSettings,
        file_fetcher: FileFetcherProtocol,
        url_router: UrlRouterProtocol,
        http_client_factory: Callable[[], HttpClientProtocol] | None = None,
        enabled: bool = True,
        # Dependency injection
        state_manager: DownloadStateManager | None = None,
        url_resolvers: list[UrlResolver] | None = None,
        file_downloader: FileDownloader | None = None,
        filename_resolver: FilenameResolver | None = None,
        html_parser: HtmlParser | None = None,
        time_provider: TimeProvider | None = None,
    ) -> None:
        """Initialize Direct HTTP client."""
        if isinstance(settings, DownloadClientSettings) and not isinstance(
            settings, DirectHttpSettings
        ):
            settings = DirectHttpSettings(
                host=settings.host,
                port=settings.port,
                username=settings.username,
                password=settings.password,
                use_ssl=settings.use_ssl,
                timeout_seconds=settings.timeout_seconds,
                category=settings.category,
                download_path=settings.download_path,
            )

        super().__init__(
            settings, file_fetcher, url_router, http_client_factory, enabled
        )
        self.settings: DirectHttpSettings = settings

        if self._http_client_factory is None:
            self._http_client_factory = lambda: create_httpx_client(
                timeout=self.settings.timeout_seconds
            )

        # Initialize dependencies
        self._time = time_provider or SystemTimeProvider()
        self._parser = html_parser or BeautifulSoupParser()

        if state_manager:
            self._state_manager = state_manager
        else:
            base_path = (
                self.settings.download_path or DownloadConstants.DEFAULT_TEMP_DIR
            )
            # Ensure base path exists
            try:
                Path(base_path).mkdir(parents=True, exist_ok=True)
            except OSError:
                logger.warning(
                    "Could not create download path %s, using temp dir", base_path
                )
                base_path = DownloadConstants.DEFAULT_TEMP_DIR
                Path(base_path).mkdir(parents=True, exist_ok=True)

            state_file = Path(base_path) / ".direct_http_state.json"
            self._state_manager = DownloadStateManager(state_file=state_file)

        self._filename_resolver = filename_resolver or FilenameResolver()
        self._file_downloader = file_downloader or FileDownloader(self._time)

        # Initialize resolvers
        aa_config = AnnaArchiveConfig(donator_key=self.settings.aa_donator_key)
        self._url_resolvers = url_resolvers or [
            AnnaArchiveResolver(
                self._http_client_factory,
                self._parser,
                self._time,
                config=aa_config,
                flaresolverr_url=self.settings.flaresolverr_url,
                flaresolverr_path=self.settings.flaresolverr_path,
                flaresolverr_timeout=self.settings.flaresolverr_timeout,
                use_seleniumbase=self.settings.use_seleniumbase,
            ),
            DirectUrlResolver(),
        ]

        # Thread pool
        self._executor = ThreadPoolExecutor(
            max_workers=5, thread_name_prefix="download-worker"
        )
        self._active_futures: dict[str, Future] = {}

    @property
    def client_name(self) -> str:
        """Return client name."""
        return "DirectHTTP"

    def _raise_provider_error(self, msg: str) -> None:
        """Raise PVRProviderError with message."""
        raise PVRProviderError(msg)

    def add_url(
        self,
        url: str,
        title: str | None,
        _category: str | None,
        download_path: str | None,
        **kwargs: Any,  # noqa: ANN401
    ) -> str:
        """Add a new download from URL.

        Parameters
        ----------
        url : str
            The download URL or Anna's Archive detail page URL.
        title : str | None
            Human-readable title for the download.
        _category : str | None
            Category (unused).
        download_path : str | None
            Target directory.
        **kwargs : Any
            Additional metadata (author, quality, guid).

        Returns
        -------
        str
            Unique download ID.
        """
        # Cleanup old downloads
        self._state_manager.cleanup_old(DownloadConstants.RETENTION_SECONDS)

        download_id = str(uuid.uuid4())
        target_path_str = (
            download_path
            or self.settings.download_path
            or DownloadConstants.DEFAULT_TEMP_DIR
        )

        self._state_manager.create(
            download_id,
            url,
            title or "Unknown",
            target_path_str,
            extra=kwargs,
        )

        future = self._executor.submit(
            self._download_worker,
            download_id,
            url,
            Path(target_path_str),
            title,
            kwargs,
        )
        self._active_futures[download_id] = future

        return download_id

    def _resolve_url(self, url: str) -> str:
        """Resolve URL using registered resolvers."""
        for resolver in self._url_resolvers:
            if resolver.can_resolve(url):
                resolved = resolver.resolve(url)
                if resolved:
                    return resolved
        return url

    def _download_worker(
        self,
        download_id: str,
        url: str,
        target_dir: Path,
        title: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Background worker to handle the download."""
        try:
            self._state_manager.update_status(download_id, DownloadStatus.DOWNLOADING)

            # 1. Resolve URL
            actual_url = self._resolve_url(url)
            if not actual_url:
                self._raise_provider_error("Could not find valid download link")

            # 2. Setup client and filename
            factory = self._http_client_factory
            if factory is None:
                self._raise_provider_error("HTTP client factory not initialized")

            with cast("Callable[[], StreamingHttpClient]", factory)() as client:
                # We need a quick HEAD or GET to determine filename before full stream
                headers = {"Referer": url} if url != actual_url else None
                try:
                    with client.stream(
                        "GET", actual_url, follow_redirects=True, headers=headers
                    ) as response:
                        response.raise_for_status()

                        # Extract metadata for filename resolution
                        meta = metadata or {}
                        filename = self._filename_resolver.resolve(
                            response,
                            actual_url,
                            title,
                            author=meta.get("author"),
                            quality=meta.get("quality"),
                            guid=meta.get("guid"),
                        )
                except httpx.HTTPError as e:
                    # If stream fails immediately (e.g. 404), we catch it here
                    msg = f"HTTP Error resolving filename: {e}"
                    raise PVRProviderError(msg) from e

                file_path = target_dir / filename
                target_dir.mkdir(parents=True, exist_ok=True)

                # 3. Download
                headers = {"Referer": url} if url != actual_url else None
                self._file_downloader.download(
                    client,
                    actual_url,
                    file_path,
                    download_id,
                    self._state_manager,
                    headers=headers,
                )

            self._state_manager.update_status(download_id, DownloadStatus.COMPLETED)

        except httpx.HTTPError:
            logger.exception("HTTP error downloading %s", url)
            self._state_manager.update_status(
                download_id, DownloadStatus.FAILED, "HTTP Error"
            )
        except PVRProviderError as e:
            logger.exception("Provider error")
            self._state_manager.update_status(
                download_id, DownloadStatus.FAILED, str(e)
            )
        except Exception as e:
            logger.exception("Unexpected error downloading %s", url)
            self._state_manager.update_status(
                download_id, DownloadStatus.FAILED, f"Unexpected Error: {e}"
            )

    def get_items(self) -> Sequence[DownloadItem]:
        """Get list of active downloads."""
        items = []
        for state in self._state_manager.get_all():
            item: DownloadItem = {
                "client_item_id": state.id,
                "title": state.title,
                "status": state.status,
                "progress": state.progress,
                "size_bytes": state.size_bytes,
                "downloaded_bytes": state.downloaded_bytes,
                "download_speed_bytes_per_sec": state.speed,
                "eta_seconds": state.eta,
                "file_path": state.path,
                "comment": state.error,
                "guid": None,
            }
            items.append(item)
        return items

    def remove_item(self, client_item_id: str, delete_files: bool = False) -> bool:
        """Remove item."""
        del delete_files
        # Cancel future if active
        future = self._active_futures.pop(client_item_id, None)
        if future and not future.done():
            future.cancel()

        return self._state_manager.remove(client_item_id)

    def test_connection(self) -> bool:
        """Test connection by making a simple HTTP request."""
        try:
            factory = self._http_client_factory
            if factory is None:
                return False

            with cast("Callable[[], StreamingHttpClient]", factory)() as client:
                client.get("https://httpbin.org/status/200", timeout=5.0)
                return True
        except Exception:
            logger.exception("Connection test failed")
            return False

    def shutdown(self) -> None:
        """Gracefully shutdown executor."""
        self._executor.shutdown(wait=True, cancel_futures=True)
