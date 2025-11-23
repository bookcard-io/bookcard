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

"""Author photo service for photo management.

Follows Single Responsibility Principle by focusing solely on photo operations.
"""

import io
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from PIL import Image
from sqlmodel import Session, desc, select

from fundamental.models.author_metadata import AuthorUserPhoto
from fundamental.repositories.author_repository import AuthorRepository
from fundamental.services.author.core_service import AuthorCoreService
from fundamental.services.author.helpers import ensure_active_library
from fundamental.services.author.interfaces import PhotoStorageInterface
from fundamental.services.author.lookup_strategies import AuthorLookupStrategyChain
from fundamental.services.author_exceptions import (
    AuthorNotFoundError,
    InvalidPhotoFormatError,
    NoActiveLibraryError,
    PhotoNotFoundError,
    PhotoStorageError,
)
from fundamental.services.config_service import LibraryService


class AuthorPhotoService:
    """Service for managing author photos.

    Handles photo upload, deletion, and primary photo selection.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        author_repo: AuthorRepository,
        library_service: LibraryService,
        photo_storage: PhotoStorageInterface,
        core_service: AuthorCoreService,
    ) -> None:
        """Initialize author photo service.

        Parameters
        ----------
        session : Session
            Database session.
        author_repo : AuthorRepository
            Author repository.
        library_service : LibraryService
            Library service for active library management.
        photo_storage : PhotoStorageInterface
            Photo storage implementation.
        core_service : AuthorCoreService
            Core author service for author lookups.
        """
        self._session = session
        self._author_repo = author_repo
        self._library_service = library_service
        self._photo_storage = photo_storage
        self._core_service = core_service
        self._lookup_chain = AuthorLookupStrategyChain()

    def upload_photo(
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
        active_library = ensure_active_library(self._library_service)
        if active_library.id is None:
            msg = "Active library ID is None"
            raise NoActiveLibraryError(msg)
        library_id: int = active_library.id

        author = self._lookup_chain.lookup(
            author_id,
            library_id,
            self._author_repo,
        )
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise AuthorNotFoundError(msg)

        # Validate file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            msg = "invalid_file_type"
            raise InvalidPhotoFormatError(msg)

        # Save file using storage
        relative_path = self._photo_storage.save(file_content, filename, author.id)

        # Get MIME type
        mime_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_type_map.get(file_ext, "image/jpeg")

        # If setting as primary, unset other primary photos
        if set_as_primary:
            existing_primary = self._session.exec(
                select(AuthorUserPhoto).where(
                    AuthorUserPhoto.author_metadata_id == author.id,
                    AuthorUserPhoto.is_primary == True,  # noqa: E712
                )
            ).all()
            for photo in existing_primary:
                photo.is_primary = False
                self._session.add(photo)

        # Create photo record
        user_photo = AuthorUserPhoto(
            author_metadata_id=author.id,
            file_path=relative_path,
            file_name=filename,
            file_size=len(file_content),
            mime_type=mime_type,
            is_primary=set_as_primary,
            order=0,
        )
        self._session.add(user_photo)
        self._session.commit()
        self._session.refresh(user_photo)

        return user_photo

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
        content_type = "image/jpeg"  # Default fallback
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if not content_type.startswith("image/"):
                    msg = "url_not_an_image"
                    raise InvalidPhotoFormatError(msg)

                try:
                    image = Image.open(io.BytesIO(response.content))
                    image.verify()
                except Exception as exc:
                    msg = "invalid_image_format"
                    raise InvalidPhotoFormatError(msg) from exc
                else:
                    # Reopen image after verify() closes it
                    image = Image.open(io.BytesIO(response.content))
                    file_content = response.content
        except httpx.HTTPError as exc:
            msg = f"failed_to_download_image: {exc!s}"
            raise PhotoStorageError(msg) from exc

        # Determine filename from URL or content type
        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        parsed_url = urlparse(url)
        url_path = unquote(parsed_url.path)
        base_filename = Path(url_path).name or "photo"

        base_name = Path(base_filename).stem
        ext = ext_map.get(
            content_type.split(";")[0].strip(), ".jpg"
        )  # Handle "image/jpeg; charset=utf-8"
        filename = f"{base_name}{ext}"

        # Upload using file upload method, then update source_url
        user_photo = self.upload_photo(
            author_id=author_id,
            file_content=file_content,
            filename=filename,
            set_as_primary=set_as_primary,
        )
        # Update source_url to track original URL
        user_photo.source_url = url
        self._session.add(user_photo)
        self._session.commit()
        self._session.refresh(user_photo)
        return user_photo

    def get_photos(self, author_id: str) -> list[AuthorUserPhoto]:
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
        active_library = ensure_active_library(self._library_service)
        if active_library.id is None:
            msg = "Active library ID is None"
            raise NoActiveLibraryError(msg)
        library_id: int = active_library.id

        author = self._lookup_chain.lookup(
            author_id,
            library_id,
            self._author_repo,
        )
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise AuthorNotFoundError(msg)

        photos = self._session.exec(
            select(AuthorUserPhoto)
            .where(AuthorUserPhoto.author_metadata_id == author.id)
            .order_by(
                desc(AuthorUserPhoto.is_primary),
                AuthorUserPhoto.order,
                AuthorUserPhoto.created_at,
            )
        ).all()

        return list(photos)

    def get_photo_by_id(self, author_id: str, photo_id: int) -> AuthorUserPhoto | None:
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
        try:
            active_library = ensure_active_library(self._library_service)
        except NoActiveLibraryError:
            return None

        if active_library.id is None:
            msg = "Active library ID is None"
            raise NoActiveLibraryError(msg)
        library_id: int = active_library.id
        author = self._lookup_chain.lookup(author_id, library_id, self._author_repo)
        if not author or author.id is None:
            return None

        # Get photo and verify it belongs to author
        return self._session.exec(
            select(AuthorUserPhoto).where(
                AuthorUserPhoto.id == photo_id,
                AuthorUserPhoto.author_metadata_id == author.id,
            )
        ).first()

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
            If author or photo not found.
        NoActiveLibraryError
            If no active library exists.
        """
        active_library = ensure_active_library(self._library_service)
        if active_library.id is None:
            msg = "Active library ID is None"
            raise NoActiveLibraryError(msg)
        library_id: int = active_library.id

        author = self._lookup_chain.lookup(
            author_id,
            library_id,
            self._author_repo,
        )
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise AuthorNotFoundError(msg)

        # Get photo
        photo = self._session.exec(
            select(AuthorUserPhoto).where(
                AuthorUserPhoto.id == photo_id,
                AuthorUserPhoto.author_metadata_id == author.id,
            )
        ).first()

        if not photo:
            msg = f"Photo not found: {photo_id}"
            raise PhotoNotFoundError(msg)

        # Unset other primary photos
        existing_primary = self._session.exec(
            select(AuthorUserPhoto).where(
                AuthorUserPhoto.author_metadata_id == author.id,
                AuthorUserPhoto.is_primary == True,  # noqa: E712
                AuthorUserPhoto.id != photo_id,
            )
        ).all()
        for existing in existing_primary:
            existing.is_primary = False
            self._session.add(existing)

        # Set this photo as primary
        photo.is_primary = True
        self._session.add(photo)
        self._session.commit()
        self._session.refresh(photo)

        return photo

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
        active_library = ensure_active_library(self._library_service)
        if active_library.id is None:
            msg = "Active library ID is None"
            raise NoActiveLibraryError(msg)
        library_id: int = active_library.id

        author = self._lookup_chain.lookup(
            author_id,
            library_id,
            self._author_repo,
        )
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise AuthorNotFoundError(msg)

        # Get photo
        photo = self._session.exec(
            select(AuthorUserPhoto).where(
                AuthorUserPhoto.id == photo_id,
                AuthorUserPhoto.author_metadata_id == author.id,
            )
        ).first()

        if not photo:
            msg = f"Photo not found: {photo_id}"
            raise PhotoNotFoundError(msg)

        # Store file path before deletion
        self._photo_storage.get_full_path(photo.file_path)

        # Delete record first (atomic DB operation)
        self._session.delete(photo)
        self._session.commit()

        # Delete file after successful DB deletion (best effort)
        self._photo_storage.delete(photo.file_path)
