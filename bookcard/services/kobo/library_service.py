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

"""Kobo library service.

Handles library operations including metadata, deletion, and sync orchestration.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from bookcard.models.kobo import KoboArchivedBook
from bookcard.repositories.kobo_repository import (
    KoboArchivedBookRepository,
    KoboSyncedBookRepository,
)

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.services.book_service import BookService
    from bookcard.services.kobo.book_lookup_service import KoboBookLookupService
    from bookcard.services.kobo.metadata_service import KoboMetadataService
    from bookcard.services.kobo.shelf_service import KoboShelfService
    from bookcard.services.kobo.store_proxy_service import KoboStoreProxyService
    from bookcard.services.kobo.sync_service import KoboSyncService
    from bookcard.services.kobo.sync_token_service import SyncToken

KOBO_STOREAPI_URL = "https://storeapi.kobo.com"


class KoboLibraryService:
    """Service for handling Kobo library operations.

    Handles metadata retrieval, book deletion, and library sync orchestration.

    Parameters
    ----------
    session : Session
        Database session.
    book_service : BookService
        Book service.
    metadata_service : KoboMetadataService
        Metadata service.
    sync_service : KoboSyncService
        Sync service.
    shelf_service : KoboShelfService
        Shelf service.
    proxy_service : KoboStoreProxyService
        Store proxy service.
    book_lookup_service : KoboBookLookupService
        Book lookup service.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        book_service: BookService,
        metadata_service: KoboMetadataService,
        sync_service: KoboSyncService,
        shelf_service: KoboShelfService,
        proxy_service: KoboStoreProxyService,
        book_lookup_service: KoboBookLookupService,
    ) -> None:
        self._session = session
        self._book_service = book_service
        self._metadata_service = metadata_service
        self._sync_service = sync_service
        self._shelf_service = shelf_service
        self._proxy_service = proxy_service
        self._book_lookup_service = book_lookup_service

    def get_book_metadata(self, book_uuid: str) -> dict[str, object]:
        """Get book metadata in Kobo format.

        Parameters
        ----------
        book_uuid : str
            Book UUID.

        Returns
        -------
        dict[str, object]
            Book metadata.

        Raises
        ------
        HTTPException
            If book not found (404).
        """
        book_result = self._book_lookup_service.find_book_by_uuid(book_uuid)
        if book_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="book_not_found",
            )

        book_id, _book = book_result
        book_with_rels = self._book_lookup_service.get_book_with_relations(book_id)
        if book_with_rels is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="book_not_found",
            )

        return self._metadata_service.get_book_metadata(book_with_rels)

    def archive_book(self, user_id: int, book_uuid: str) -> None:
        """Archive a book for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        book_uuid : str
            Book UUID.

        Raises
        ------
        HTTPException
            If book not found (404).
        """
        book_result = self._book_lookup_service.find_book_by_uuid(book_uuid)
        if book_result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="book_not_found",
            )

        book_id, _book = book_result

        # Archive book for this user
        archived_repo = KoboArchivedBookRepository(self._session)
        archived_book = archived_repo.find_by_user_and_book(user_id, book_id)
        if archived_book:
            archived_book.is_archived = True
        else:
            archived_book = KoboArchivedBook(
                user_id=user_id,
                book_id=book_id,
                is_archived=True,
            )
            archived_repo.add(archived_book)

        # Remove from synced books
        synced_repo = KoboSyncedBookRepository(self._session)
        synced_repo.delete_by_user_and_book(user_id, book_id)

    async def sync_library(
        self,
        request: Request,
        user_id: int,
        library_id: int,
        sync_token: SyncToken,
    ) -> JSONResponse:
        """Perform library sync.

        Parameters
        ----------
        request : Request
            FastAPI request.
        user_id : int
            User ID.
        library_id : int
            Library ID.
        sync_token : SyncToken
            Sync token.

        Returns
        -------
        JSONResponse
            Sync response with results.
        """
        # Perform sync
        sync_results, continue_sync = self._sync_service.sync_library(
            user_id=user_id,
            library_id=library_id,
            sync_token=sync_token,
            only_shelves=False,  # Can be enhanced with user preference
        )

        # Get shelf sync results
        shelf_results = self._shelf_service.sync_shelves(
            user_id=user_id,
            library_id=library_id,
            sync_token=sync_token,
            book_service=self._book_service,
        )
        sync_results.extend(shelf_results)

        # Merge with store if proxy enabled
        if self._proxy_service.should_proxy() and not continue_sync:
            sync_results = await self._merge_store_sync(
                request, sync_token, sync_results
            )

        # Build response headers
        response_headers: dict[str, str] = {}
        if continue_sync:
            response_headers["x-kobo-sync"] = "continue"
        sync_token.to_headers(response_headers)

        # Commit session
        self._session.commit()

        return JSONResponse(
            content=sync_results,
            headers=response_headers,
            media_type="application/json; charset=utf-8",
        )

    async def _merge_store_sync(
        self,
        request: Request,
        sync_token: SyncToken,
        sync_results: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        """Merge local sync results with Kobo Store results.

        Parameters
        ----------
        request : Request
            FastAPI request.
        sync_token : SyncToken
            Sync token.
        sync_results : list[dict[str, object]]
            Local sync results.

        Returns
        -------
        list[dict[str, object]]
            Merged sync results.
        """
        auth_token = request.path_params.get("auth_token", "")
        path = request.url.path.replace(f"/kobo/{auth_token}", "")
        with suppress(httpx.HTTPError, httpx.RequestError, KeyError, AttributeError):
            store_response = await self._proxy_service.proxy_request(
                path=path,
                method=request.method,
                headers=dict(request.headers),
                data=None,
                sync_token=sync_token,
            )
            if store_response.status_code == 200:
                store_results = store_response.json()
                sync_results = self._proxy_service.merge_sync_responses(
                    sync_results, store_results
                )
                sync_token.merge_from_store_response(store_response)

        return sync_results
