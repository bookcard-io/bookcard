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

"""Service for book cover operations.

Handles cover download, validation, and storage.
Follows SRP by handling only cover-related operations.
"""

import hashlib
import io
import logging
import tempfile
from pathlib import Path

import httpx
from PIL import Image
from sqlmodel import select

from fundamental.models.core import Book
from fundamental.services.book_service import BookService

logger = logging.getLogger(__name__)


class BookCoverService:
    """Service for book cover operations.

    Handles downloading, validating, and saving cover images.
    Uses IOC by accepting BookService as dependency.
    """

    def __init__(self, book_service: BookService) -> None:
        """Initialize cover service.

        Parameters
        ----------
        book_service : BookService
            Book service for accessing book data and repository.
        """
        self._book_service = book_service

    def validate_url(self, url: str) -> None:
        """Validate cover URL format.

        Parameters
        ----------
        url : str
            Image URL to validate.

        Raises
        ------
        ValueError
            If URL is empty or invalid format.
        """
        if not url:
            error_msg = "url_required"
            raise ValueError(error_msg)

        if not url.startswith(("http://", "https://")):
            error_msg = "invalid_url_format"
            raise ValueError(error_msg)

    def download_and_validate_image(self, url: str) -> tuple[bytes, Image.Image]:
        """Download image from URL and validate it.

        Parameters
        ----------
        url : str
            Image URL to download.

        Returns
        -------
        tuple[bytes, Image.Image]
            Image content bytes and PIL Image object.

        Raises
        ------
        ValueError
            If download fails or image is invalid.
        """
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if not content_type.startswith("image/"):
                    error_msg = "url_not_an_image"
                    raise ValueError(error_msg)

                try:
                    image = Image.open(io.BytesIO(response.content))
                    image.verify()
                except Exception as exc:
                    error_msg = "invalid_image_format"
                    raise ValueError(error_msg) from exc
                else:
                    # Reopen image after verify() closes it
                    image = Image.open(io.BytesIO(response.content))
                    return response.content, image
        except httpx.HTTPError as exc:
            error_msg = f"failed_to_download_image: {exc!s}"
            raise ValueError(error_msg) from exc

    def save_cover_from_url(
        self,
        book_id: int,
        url: str,
    ) -> str:
        """Download cover from URL and save to book directory.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        url : str
            Image URL to download.

        Returns
        -------
        str
            Cover URL path for API access.

        Raises
        ------
        ValueError
            If book not found, URL invalid, or save fails.
        """
        from datetime import UTC, datetime

        self.validate_url(url)
        content, _image = self.download_and_validate_image(url)

        # Get book with relations to access book path
        book_with_rels = self._book_service.get_book_full(book_id)
        if book_with_rels is None:
            error_msg = "book_not_found"
            raise ValueError(error_msg)

        book_obj = book_with_rels.book

        # Get library path
        lib_root = getattr(self._book_service._library, "library_root", None)  # type: ignore[attr-defined]  # noqa: SLF001
        if lib_root:
            library_path = Path(lib_root)
        else:
            library_db_path = self._book_service._library.calibre_db_path  # type: ignore[attr-defined]  # noqa: SLF001
            library_db_path_obj = Path(library_db_path)
            if library_db_path_obj.is_dir():
                library_path = library_db_path_obj
            else:
                library_path = library_db_path_obj.parent

        book_path = library_path / book_obj.path
        book_path.mkdir(parents=True, exist_ok=True)

        # Save cover as cover.jpg (Calibre standard)
        cover_path = book_path / "cover.jpg"
        cover_path.write_bytes(content)

        # Update database to mark book as having a cover
        with self._book_service._book_repo.get_session() as calibre_session:  # type: ignore[attr-defined]  # noqa: SLF001
            book_stmt = select(Book).where(Book.id == book_id)
            calibre_book = calibre_session.exec(book_stmt).first()
            if calibre_book:
                calibre_book.has_cover = True
                calibre_book.last_modified = datetime.now(UTC)
                calibre_session.add(calibre_book)
                calibre_session.commit()

        return f"/api/books/{book_id}/cover"

    def save_temp_cover(self, content: bytes, image: Image.Image) -> str:
        """Save image to temporary location and return URL.

        Parameters
        ----------
        content : bytes
            Image content bytes.
        image : Image.Image
            PIL Image object.

        Returns
        -------
        str
            Temporary URL to access the image.
        """
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        file_extension = image.format.lower() if image.format else "jpg"
        if file_extension not in ("jpg", "jpeg", "png", "webp"):
            file_extension = "jpg"

        temp_dir = Path(tempfile.gettempdir()) / "calibre_covers"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_filename = f"{content_hash}.{file_extension}"
        temp_path = temp_dir / temp_filename

        temp_path.write_bytes(content)

        # Store in module-level dict (could be moved to service state)
        from fundamental.api.routes.books import _temp_cover_storage

        _temp_cover_storage[content_hash] = temp_path

        return f"/api/books/temp-covers/{content_hash}.{file_extension}"
