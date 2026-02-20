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

"""Author service for business logic.

Refactored to use specialized services following SOLID principles.
Delegates to AuthorCoreService, AuthorPhotoService, AuthorMetadataService,
and AuthorSerializationService for focused responsibilities.
"""

from __future__ import annotations

import contextlib
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlmodel import Session

    from bookcard.models.author_metadata import AuthorUserPhoto
    from bookcard.models.config import Library
from bookcard.repositories.author_repository import AuthorRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.author.core_service import AuthorCoreService
from bookcard.services.author.metadata_service import AuthorMetadataService
from bookcard.services.author.photo_service import AuthorPhotoService
from bookcard.services.author.photo_storage import FileSystemPhotoStorage
from bookcard.services.author.serialization_service import AuthorSerializationService
from bookcard.services.author_exceptions import (
    AuthorNotFoundError,
    PhotoNotFoundError,
)
from bookcard.services.config_service import LibraryService


class AuthorService:
    """Service for author business operations.

    Facade that orchestrates specialized services following SOLID principles.
    Delegates to AuthorCoreService, AuthorPhotoService, AuthorMetadataService,
    and AuthorSerializationService for focused responsibilities.
    """

    def __init__(
        self,
        session: Session,
        author_repo: AuthorRepository | None = None,
        library_service: LibraryService | None = None,
        library_repo: LibraryRepository | None = None,
        data_directory: str = "/data",
    ) -> None:
        """Initialize author service.

        Parameters
        ----------
        session : Session
            Database session.
        author_repo : AuthorRepository | None
            Author repository. If None, creates a new instance.
        library_service : LibraryService | None
            Library service. If None, creates a new instance.
        library_repo : LibraryRepository | None
            Library repository. If None, creates a new instance.
        data_directory : str
            Data directory path for storing files (default: "/data").
        """
        self._session = session
        self._author_repo = author_repo or AuthorRepository(session)

        if library_service is None:
            lib_repo = library_repo or LibraryRepository(session)
            self._library_service = LibraryService(session, lib_repo)
        else:
            self._library_service = library_service

        # Initialize specialized services
        self._core_service = AuthorCoreService(
            session, self._author_repo, self._library_service
        )
        self._serialization_service = AuthorSerializationService(session)
        self._metadata_service = AuthorMetadataService(session, self._library_service)

        # Initialize photo storage and service
        photo_storage = FileSystemPhotoStorage(Path(data_directory))
        self._photo_service = AuthorPhotoService(
            session,
            self._author_repo,
            self._library_service,
            photo_storage,
            self._core_service,
        )

    def list_authors_for_active_library(
        self,
        page: int = 1,
        page_size: int = 20,
        filter_type: str | None = None,
    ) -> tuple[list[dict[str, object]], int]:
        """List authors for the active library with pagination.

        Parameters
        ----------
        page : int
            Page number (1-indexed, default: 1).
        page_size : int
            Number of items per page (default: 20).
        filter_type : str | None
            Filter type: "unmatched" to show only unmatched authors, None for all authors.

        Returns
        -------
        tuple[list[dict[str, object]], int]
            List of author dictionaries and total count.

        Raises
        ------
        NoActiveLibraryError
            If no active library is found.
        """
        authors, total = self._core_service.list_authors(page, page_size, filter_type)
        return [
            self._serialization_service.to_dict(author) for author in authors
        ], total

    def get_author_by_id_or_key(
        self,
        author_id: str,
        include_similar: bool = True,
        library_id: int | None = None,
    ) -> dict[str, object]:
        """Get a single author by ID or OpenLibrary key.

        If the author doesn't have a row in author_metadata (unmatched),
        fetches details from Calibre's database instead.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
        include_similar : bool
            Whether to include similar authors (default: True).
        library_id : int | None
            Explicit library ID for Calibre fallback and similar-author
            queries.  When ``None`` the caller's active library is resolved
            via ``LibraryService``.

        Returns
        -------
        dict[str, object]
            Author data dictionary.

        Raises
        ------
        AuthorNotFoundError
            If author is not found.
        NoActiveLibraryError
            If no active library exists.
        """
        resolved_library = self._resolve_library(library_id)

        try:
            author = self._core_service.get_author(author_id)
        except AuthorNotFoundError:
            # If not found and it's a calibre-{id} format, try fetching from Calibre
            if author_id.startswith("calibre-") and resolved_library:
                with contextlib.suppress(ValueError):
                    calibre_id = int(author_id.replace("calibre-", ""))
                    return self._core_service.get_calibre_author_dict(
                        resolved_library, calibre_id
                    )
            raise

        author_data = self._serialization_service.to_dict(author)

        # Add similar authors if requested
        if (
            include_similar
            and author.id
            and resolved_library
            and resolved_library.id is not None
        ):
            similar_authors = self._core_service.get_similar_authors(
                author.id,
                resolved_library.id,
            )
            if similar_authors:
                author_data["similar_authors"] = [
                    self._serialization_service.to_dict(a) for a in similar_authors
                ]

        return author_data

    def _resolve_library(self, library_id: int | None = None) -> Library | None:
        """Resolve a library by explicit ID.

        Parameters
        ----------
        library_id : int | None
            Explicit library ID.  When ``None``, returns ``None``
            (callers should pass the library ID from the request context).

        Returns
        -------
        Library | None
            Resolved library, or ``None`` when *library_id* is not provided.
        """
        if library_id is None:
            return None
        lib_repo = LibraryRepository(self._session)
        return lib_repo.get(library_id)

    def fetch_author_metadata(
        self,
        author_id: str,
    ) -> dict[str, object]:
        """Fetch and update metadata for a single author.

        Triggers the ingest stage of the pipeline for this author only.
        Fetches latest biography, metadata, subjects, etc. from OpenLibrary.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").

        Returns
        -------
        dict[str, object]
            Result dictionary with success status, message, and stats.

        Raises
        ------
        AuthorNotFoundError
            If author is not found.
        AuthorMetadataFetchError
            If fetch fails.
        NoActiveLibraryError
            If no active library exists.
        """
        # Get the author to retrieve OpenLibrary key
        author_data = self.get_author_by_id_or_key(author_id)
        # The author dict uses "key" for the OpenLibrary key (matching OpenLibrary API format)
        openlibrary_key_raw = author_data.get("key")
        if not openlibrary_key_raw or not isinstance(openlibrary_key_raw, str):
            msg = "Author does not have an OpenLibrary key"
            raise AuthorNotFoundError(msg)
        openlibrary_key: str = openlibrary_key_raw

        return self._metadata_service.fetch_author_metadata(openlibrary_key)

    def update_author(
        self,
        author_id: str,
        update: dict[str, object],
    ) -> dict[str, object]:
        """Update author metadata and user-defined fields.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
        update : dict[str, object]
            Update payload with fields to update.

        Returns
        -------
        dict[str, object]
            Updated author data dictionary.

        Raises
        ------
        AuthorNotFoundError
            If author is not found.
        NoActiveLibraryError
            If no active library exists.
        """
        author = self._core_service.get_author(author_id)

        # Update AuthorMetadata fields
        self._core_service.update_author_metadata(author, update)

        # Save user-defined metadata fields
        if author.id is not None:
            self._core_service.update_user_metadata(author.id, update)

        # Handle photo_url update
        if update.get("photo_url"):
            photo_url = str(update["photo_url"])
            match = re.search(r"/photos/(\d+)$", photo_url)
            if match:
                photo_id = int(match.group(1))
                photo = self._photo_service.get_photo_by_id(author_id, photo_id)
                if photo:
                    with contextlib.suppress(PhotoNotFoundError):
                        self._photo_service.set_primary_photo(author_id, photo_id)
                        self._session.expire(author, ["user_photos"])

        self._session.add(author)
        self._session.commit()
        self._session.refresh(author)

        # Return updated author dict
        return self._serialization_service.to_dict(author)

    def upload_author_photo(
        self,
        author_id: str,
        file_content: bytes,
        filename: str,
        set_as_primary: bool = False,
    ) -> AuthorUserPhoto:
        """Upload and save an author photo from file.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        file_content : bytes
            File content to save.
        filename : str
            Original filename.
        set_as_primary : bool
            Whether to set this photo as primary (default: False).

        Returns
        -------
        AuthorUserPhoto
            Created photo record.

        Raises
        ------
        AuthorNotFoundError
            If author not found.
        InvalidPhotoFormatError
            If invalid file type.
        PhotoStorageError
            If save operation fails.
        NoActiveLibraryError
            If no active library exists.
        """
        return self._photo_service.upload_photo(
            author_id, file_content, filename, set_as_primary
        )

    def upload_photo_from_url(
        self,
        author_id: str,
        url: str,
        set_as_primary: bool = False,
    ) -> AuthorUserPhoto:
        """Upload and save an author photo from URL.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        url : str
            URL of the image to download.
        set_as_primary : bool
            Whether to set this photo as primary (default: False).

        Returns
        -------
        AuthorUserPhoto
            Created photo record.

        Raises
        ------
        AuthorNotFoundError
            If author not found.
        InvalidPhotoFormatError
            If download fails or invalid image.
        PhotoStorageError
            If save operation fails.
        NoActiveLibraryError
            If no active library exists.
        """
        return self._photo_service.upload_photo_from_url(author_id, url, set_as_primary)

    def get_author_photos(self, author_id: str) -> list[AuthorUserPhoto]:
        """Get all user-uploaded photos for an author.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.

        Returns
        -------
        list[AuthorUserPhoto]
            List of photo records.

        Raises
        ------
        AuthorNotFoundError
            If author not found.
        NoActiveLibraryError
            If no active library exists.
        """
        return self._photo_service.get_photos(author_id)

    def get_author_photo_by_id(
        self, author_id: str, photo_id: int
    ) -> AuthorUserPhoto | None:
        """Get a specific photo by ID for an author.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        photo_id : int
            Photo ID to retrieve.

        Returns
        -------
        AuthorUserPhoto | None
            Photo record if found and belongs to author, None otherwise.
        """
        return self._photo_service.get_photo_by_id(author_id, photo_id)

    def set_primary_photo(self, author_id: str, photo_id: int) -> AuthorUserPhoto:
        """Set a photo as the primary photo for an author.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        photo_id : int
            Photo ID to set as primary.

        Returns
        -------
        AuthorUserPhoto
            Updated photo record.

        Raises
        ------
        AuthorNotFoundError
            If author not found.
        PhotoNotFoundError
            If photo not found.
        NoActiveLibraryError
            If no active library exists.
        """
        return self._photo_service.set_primary_photo(author_id, photo_id)

    def delete_photo(self, author_id: str, photo_id: int) -> None:
        """Delete an author photo and its file.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        photo_id : int
            Photo ID to delete.

        Raises
        ------
        AuthorNotFoundError
            If author not found.
        PhotoNotFoundError
            If photo not found.
        NoActiveLibraryError
            If no active library exists.
        """
        self._photo_service.delete_photo(author_id, photo_id)
