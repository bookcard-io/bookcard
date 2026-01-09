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

"""URL builder for OPDS feeds.

Builds absolute URLs for OPDS feed links following OPDS specifications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlencode

if TYPE_CHECKING:
    from fastapi import Request


class OpdsUrlBuilder:
    """Builder for OPDS feed URLs.

    Generates absolute URLs for links in OPDS feeds, including pagination,
    download, and cover image links.
    """

    def __init__(self, request: Request) -> None:
        """Initialize URL builder.

        Parameters
        ----------
        request : Request
            FastAPI request object for building absolute URLs.
        """
        self._request = request

    def build_opds_url(
        self, path: str, query_params: dict[str, str | int] | None = None
    ) -> str:
        """Build absolute OPDS feed URL.

        Parameters
        ----------
        path : str
            OPDS path (e.g., '/opds/', '/opds/books').
        query_params : dict[str, str | int] | None
            Optional query parameters.

        Returns
        -------
        str
            Absolute URL.
        """
        base_url = str(self._request.base_url).rstrip("/")
        url = f"{base_url}{path}"

        if query_params:
            # Filter out None values and convert to strings
            filtered_params = {
                k: str(v) for k, v in query_params.items() if v is not None
            }
            if filtered_params:
                url += f"?{urlencode(filtered_params)}"

        return url

    def build_download_url(self, book_id: int, file_format: str) -> str:
        """Build book download URL.

        Parameters
        ----------
        book_id : int
            Book ID.
        file_format : str
            File format (e.g., 'EPUB', 'PDF').

        Returns
        -------
        str
            Absolute download URL.
        """
        base_url = str(self._request.base_url).rstrip("/")
        return f"{base_url}/opds/download/{book_id}/{file_format}"

    def build_cover_url(self, book_id: int) -> str:
        """Build book cover image URL.

        Parameters
        ----------
        book_id : int
            Book ID.

        Returns
        -------
        str
            Absolute cover URL.
        """
        base_url = str(self._request.base_url).rstrip("/")
        return f"{base_url}/opds/cover/{book_id}"

    def build_pagination_url(
        self,
        path: str,
        offset: int,
        page_size: int | None = None,
    ) -> str:
        """Build pagination URL with offset.

        Parameters
        ----------
        path : str
            OPDS path.
        offset : int
            Pagination offset.
        page_size : int | None
            Optional page size.

        Returns
        -------
        str
            Absolute URL with pagination parameters.
        """
        params: dict[str, str | int] = {"offset": offset}
        if page_size is not None:
            params["page_size"] = page_size
        return self.build_opds_url(path, params)
