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

"""Kobo cover service.

Handles cover image retrieval and proxy logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse

if TYPE_CHECKING:
    from bookcard.services.book_service import BookService
    from bookcard.services.kobo.book_lookup_service import KoboBookLookupService
    from bookcard.services.kobo.store_proxy_service import KoboStoreProxyService

KOBO_IMAGEHOST_URL = "https://cdn.kobo.com/book-images"


class KoboCoverService:
    """Service for handling Kobo cover image requests.

    Retrieves cover images from local library or proxies to Kobo Store.

    Parameters
    ----------
    book_service : BookService
        Book service.
    book_lookup_service : KoboBookLookupService
        Book lookup service.
    proxy_service : KoboStoreProxyService
        Store proxy service.
    """

    def __init__(
        self,
        book_service: BookService,  # type: ignore[type-arg]
        book_lookup_service: KoboBookLookupService,
        proxy_service: KoboStoreProxyService,
    ) -> None:
        self._book_service = book_service
        self._book_lookup_service = book_lookup_service
        self._proxy_service = proxy_service

    def get_cover_image(
        self, book_uuid: str, width: str, height: str
    ) -> FileResponse | RedirectResponse:
        """Get cover image for a book.

        Parameters
        ----------
        book_uuid : str
            Book UUID.
        width : str
            Image width.
        height : str
            Image height.

        Returns
        -------
        FileResponse | RedirectResponse
            Cover image file or redirect to Kobo Store.

        Raises
        ------
        HTTPException
            If book not found (404).
            If cover not found (404).
        """
        book_result = self._book_lookup_service.find_book_by_uuid(book_uuid)
        if book_result is None:
            return self._redirect_to_store(book_uuid, width, height)

        book_id, _book = book_result
        book_with_rels = self._book_service.get_book(book_id)
        if book_with_rels is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="book_not_found",
            )

        # Get cover path
        cover_path = self._book_service.get_thumbnail_path(book_with_rels)
        if cover_path is None or not cover_path.exists():
            return self._redirect_to_store(book_uuid, width, height)

        return FileResponse(
            path=str(cover_path),
            media_type="image/jpeg",
        )

    def _redirect_to_store(
        self, book_uuid: str, width: str, height: str
    ) -> RedirectResponse:
        """Redirect to Kobo Store for cover image.

        Parameters
        ----------
        book_uuid : str
            Book UUID.
        width : str
            Image width.
        height : str
            Image height.

        Returns
        -------
        RedirectResponse
            Redirect response to Kobo Store.
        """
        if self._proxy_service.should_proxy():
            return RedirectResponse(
                url=f"{KOBO_IMAGEHOST_URL}/{book_uuid}/{width}/{height}/false/image.jpg",
                status_code=307,
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="cover_not_found",
        )
