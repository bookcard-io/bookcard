# Copyright (C) 2026 knguyen and others
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

"""Network utilities for Anna's Archive indexer."""

import logging
import time
from collections.abc import Callable
from typing import Protocol, TypeVar, runtime_checkable

import httpx

from bookcard.pvr.exceptions import PVRProviderNetworkError

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Error raised when retries are exhausted."""


@runtime_checkable
class HttpResponse(Protocol):
    """Protocol for HTTP response."""

    @property
    def text(self) -> str:
        """Response body as text."""
        ...

    def raise_for_status(self) -> None:
        """Raise exception for error status codes."""
        ...


@runtime_checkable
class HttpClient(Protocol):
    """Protocol for HTTP client."""

    def get(self, url: str, *, params: dict[str, str] | None = None) -> HttpResponse:
        """Make GET request."""
        ...


class HttpxResponseAdapter(HttpResponse):
    """Adapter for httpx.Response."""

    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    @property
    def text(self) -> str:
        """Response body as text."""
        return self._response.text

    def raise_for_status(self) -> None:
        """Raise exception for error status codes."""
        self._response.raise_for_status()


class HttpxClientAdapter(HttpClient):
    """Adapter for httpx.Client."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    def get(self, url: str, *, params: dict[str, str] | None = None) -> HttpResponse:
        """Make GET request."""
        with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
            try:
                response = client.get(url, params=params)
                response.raise_for_status()
                return HttpxResponseAdapter(response)
            except httpx.HTTPError as e:
                # Wrap httpx errors that occur during the request
                # This ensures consistent error handling even inside the adapter
                msg = f"HTTP Error: {e}"
                raise PVRProviderNetworkError(msg) from e


T = TypeVar("T")


class RetryStrategy:
    """Implements retry logic with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ) -> None:
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    def execute(
        self,
        func: Callable[[], T],
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ) -> T:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func()
            except retryable_exceptions as e:
                last_exception = e

                if attempt == self.max_retries:
                    break

                # Calculate delay with exponential backoff
                delay = min(
                    self.initial_delay * (self.exponential_base**attempt),
                    self.max_delay,
                )

                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.2fs...",
                    attempt + 1,
                    self.max_retries + 1,
                    e,
                    delay,
                )
                time.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception

        msg = "Retry loop finished without result or exception"
        raise RetryError(msg)
