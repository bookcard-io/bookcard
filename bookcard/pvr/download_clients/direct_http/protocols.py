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

"""Protocols for Direct HTTP download client."""

import time
from collections.abc import Iterator
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Any, Protocol

import httpx
from bs4 import BeautifulSoup


class StreamingResponse(Protocol):
    """Protocol for streaming HTTP response."""

    @property
    def headers(self) -> httpx.Headers:
        """Return response headers."""
        ...

    @property
    def status_code(self) -> int:
        """Return status code."""
        ...

    @property
    def text(self) -> str:
        """Return response text."""
        ...

    def raise_for_status(self) -> None:
        """Raise exception if status code is error."""
        ...

    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        """Iterate over response bytes."""
        ...


class StreamingHttpClient(Protocol):
    """Protocol for streaming HTTP operations."""

    def get(self, url: str, **kwargs: Any) -> StreamingResponse:  # noqa: ANN401
        """Perform HTTP GET request."""
        ...

    def stream(
        self, method: str, url: str, *, follow_redirects: bool = False
    ) -> AbstractContextManager[StreamingResponse]:
        """Stream HTTP response."""
        ...

    def __enter__(self) -> "StreamingHttpClient":
        """Enter context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit context manager."""
        ...


class HtmlParser(Protocol):
    """Protocol for HTML parsing."""

    def parse(self, html: str) -> BeautifulSoup:
        """Parse HTML string."""
        ...


class BeautifulSoupParser(HtmlParser):
    """BeautifulSoup implementation of HtmlParser."""

    def parse(self, html: str) -> BeautifulSoup:
        """Parse HTML string using BeautifulSoup."""
        return BeautifulSoup(html, "html.parser")


class TimeProvider(Protocol):
    """Protocol for time operations."""

    def sleep(self, seconds: float) -> None:
        """Sleep for seconds."""
        ...

    def time(self) -> float:
        """Get current time."""
        ...


class SystemTimeProvider(TimeProvider):
    """System time implementation."""

    def sleep(self, seconds: float) -> None:
        """Sleep for seconds."""
        time.sleep(seconds)

    def time(self) -> float:
        """Get current time."""
        return time.time()
