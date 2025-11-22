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

"""Book service for managing Calibre books.

Business logic for querying and serving book data from Calibre libraries.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from fundamental.models.core import Book
from fundamental.repositories import (
    BookWithFullRelations,
    BookWithRelations,
    CalibreBookRepository,
)

if TYPE_CHECKING:
    from datetime import datetime

    from sqlmodel import Session

    from fundamental.models.auth import EReaderDevice
    from fundamental.models.config import Library
    from fundamental.services.email_service import EmailService

logger = logging.getLogger(__name__)


class BookService:
    """Operations for querying books from Calibre libraries.

    Parameters
    ----------
    library : Library
        Active Calibre library configuration.
    session : Session | None
        Optional database session for device lookups.
        Required for send_book method that needs to resolve devices by email.
    """

    def __init__(self, library: Library, session: Session | None = None) -> None:  # type: ignore[type-arg]
        self._library = library
        self._session = session
        self._book_repo = CalibreBookRepository(
            calibre_db_path=library.calibre_db_path,
            calibre_db_file=library.calibre_db_file,
        )

    def list_books(
        self,
        page: int = 1,
        page_size: int = 20,
        search_query: str | None = None,
        author_id: int | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
    ) -> tuple[list[BookWithRelations | BookWithFullRelations], int]:
        """List books with pagination.

        Parameters
        ----------
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.
        search_query : str | None
            Optional search query to filter by title or author.
        author_id : int | None
            Optional author ID to filter by.
        sort_by : str
            Field to sort by (default: 'timestamp').
        sort_order : str
            Sort order: 'asc' or 'desc' (default: 'desc').
        full : bool
            If True, return full book details with all metadata (default: False).

        Returns
        -------
        tuple[list[BookWithRelations | BookWithFullRelations], int]
            Tuple of (books with relations list, total count).
        """
        offset = (page - 1) * page_size
        books = self._book_repo.list_books(
            limit=page_size,
            offset=offset,
            search_query=search_query,
            author_id=author_id,
            sort_by=sort_by,
            sort_order=sort_order,
            full=full,
        )
        total = self._book_repo.count_books(
            search_query=search_query, author_id=author_id
        )
        return books, total

    def get_book(self, book_id: int) -> BookWithRelations | None:
        """Get a book by ID.

        Parameters
        ----------
        book_id : int
            Calibre book ID.

        Returns
        -------
        BookWithRelations | None
            Book with relations if found, None otherwise.
        """
        return self._book_repo.get_book(book_id)

    def get_book_full(self, book_id: int) -> BookWithFullRelations | None:
        """Get a book by ID with all related metadata for editing.

        Parameters
        ----------
        book_id : int
            Calibre book ID.

        Returns
        -------
        BookWithFullRelations | None
            Book with all related metadata if found, None otherwise.
        """
        return self._book_repo.get_book_full(book_id)

    def update_book(
        self,
        book_id: int,
        title: str | None = None,
        pubdate: datetime | None = None,
        author_names: list[str] | None = None,
        series_name: str | None = None,
        series_id: int | None = None,
        series_index: float | None = None,
        tag_names: list[str] | None = None,
        identifiers: list[dict[str, str]] | None = None,
        description: str | None = None,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> BookWithFullRelations | None:
        """Update book metadata.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        title : str | None
            Book title to update.
        pubdate : datetime | None
            Publication date to update.
        author_names : list[str] | None
            List of author names to set (replaces existing).
        series_name : str | None
            Series name to set (creates if doesn't exist).
        series_id : int | None
            Series ID to set (if provided, series_name is ignored).
        series_index : float | None
            Series index to update.
        tag_names : list[str] | None
            List of tag names to set (replaces existing).
        identifiers : list[dict[str, str]] | None
            List of identifiers with 'type' and 'val' keys (replaces existing).
        description : str | None
            Book description/comment to set.
        publisher_name : str | None
            Publisher name to set (creates if doesn't exist).
        publisher_id : int | None
            Publisher ID to set (if provided, publisher_name is ignored).
        language_codes : list[str] | None
            List of language codes to set (creates if doesn't exist).
        language_ids : list[int] | None
            List of language IDs to set (if provided, language_codes is ignored).
        rating_value : int | None
            Rating value to set (creates if doesn't exist).
        rating_id : int | None
            Rating ID to set (if provided, rating_value is ignored).

        Returns
        -------
        BookWithFullRelations | None
            Updated book with all relations if found, None otherwise.
        """
        return self._book_repo.update_book(
            book_id=book_id,
            title=title,
            pubdate=pubdate,
            author_names=author_names,
            series_name=series_name,
            series_id=series_id,
            series_index=series_index,
            tag_names=tag_names,
            identifiers=identifiers,
            description=description,
            publisher_name=publisher_name,
            publisher_id=publisher_id,
            language_codes=language_codes,
            language_ids=language_ids,
            rating_value=rating_value,
            rating_id=rating_id,
        )

    def get_thumbnail_url(
        self, book: Book | BookWithRelations | BookWithFullRelations
    ) -> str | None:
        """Generate thumbnail URL for a book.

        Parameters
        ----------
        book : Book | BookWithRelations | BookWithFullRelations
            Book instance, BookWithRelations, or BookWithFullRelations.

        Returns
        -------
        str | None
            Thumbnail URL if book has a cover, None otherwise.
        """
        book_id = book.id if isinstance(book, Book) else book.book.id
        has_cover = book.has_cover if isinstance(book, Book) else book.book.has_cover

        if not has_cover:
            return None

        # Calibre stores covers as cover.jpg in the book's path directory
        # Format: /api/books/{book_id}/cover
        # Add cache-busting parameter based on cover file modification time
        cover_path = self.get_thumbnail_path(book)
        if cover_path and cover_path.exists():
            # Use cover file's modification time as cache-busting parameter
            # This ensures the URL only changes when the cover file itself changes
            cover_mtime = int(cover_path.stat().st_mtime)
            return f"/api/books/{book_id}/cover?v={cover_mtime}"

        return f"/api/books/{book_id}/cover"

    def get_thumbnail_path(
        self, book: Book | BookWithRelations | BookWithFullRelations
    ) -> Path | None:
        """Get filesystem path to book cover thumbnail.

        Parameters
        ----------
        book : Book | BookWithRelations | BookWithFullRelations
            Book instance, BookWithRelations, or BookWithFullRelations.

        Returns
        -------
        Path | None
            Path to cover image if exists, None otherwise.
        """
        book_obj = book if isinstance(book, Book) else book.book

        if not book_obj.has_cover:
            return None

        # Calibre stores covers as cover.jpg in the book's path directory
        # Prefer explicit library_root from config when provided
        lib_root = getattr(self._library, "library_root", None)
        if lib_root:
            library_path = Path(lib_root)
        else:
            library_path = Path(self._library.calibre_db_path)
        book_path = library_path / book_obj.path
        cover_path = book_path / "cover.jpg"

        if cover_path.exists():
            return cover_path
        return None

    def search_suggestions(
        self,
        query: str,
        book_limit: int = 3,
        author_limit: int = 3,
        tag_limit: int = 3,
        series_limit: int = 3,
    ) -> dict[str, list[dict[str, str | int]]]:
        """Search for suggestions across books, authors, tags, and series.

        Parameters
        ----------
        query : str
            Search query string.
        book_limit : int
            Maximum number of book matches to return (default: 3).
        author_limit : int
            Maximum number of author matches to return (default: 3).
        tag_limit : int
            Maximum number of tag matches to return (default: 3).
        series_limit : int
            Maximum number of series matches to return (default: 3).

        Returns
        -------
        dict[str, list[dict[str, str | int]]]
            Dictionary with keys 'books', 'authors', 'tags', 'series', each
            containing a list of matches with 'name' and 'id' fields.
        """
        return self._book_repo.search_suggestions(
            query=query,
            book_limit=book_limit,
            author_limit=author_limit,
            tag_limit=tag_limit,
            series_limit=series_limit,
        )

    def filter_suggestions(
        self,
        query: str,
        filter_type: str,
        limit: int = 10,
    ) -> list[dict[str, str | int]]:
        """Get filter suggestions for a specific filter type.

        Parameters
        ----------
        query : str
            Search query string.
        filter_type : str
            Type of filter: 'author', 'title', 'genre', 'publisher',
            'identifier', 'series', 'format', 'rating', 'language'.
        limit : int
            Maximum number of suggestions to return (default: 10).

        Returns
        -------
        list[dict[str, str | int]]
            List of suggestions with 'id' and 'name' fields.
        """
        return self._book_repo.filter_suggestions(
            query=query,
            filter_type=filter_type,
            limit=limit,
        )

    def list_books_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        author_ids: list[int] | None = None,
        title_ids: list[int] | None = None,
        genre_ids: list[int] | None = None,
        publisher_ids: list[int] | None = None,
        identifier_ids: list[int] | None = None,
        series_ids: list[int] | None = None,
        formats: list[str] | None = None,
        rating_ids: list[int] | None = None,
        language_ids: list[int] | None = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        full: bool = False,
    ) -> tuple[list[BookWithRelations | BookWithFullRelations], int]:
        """List books with multiple filter criteria using OR conditions.

        Parameters
        ----------
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.
        author_ids : list[int] | None
            List of author IDs to filter by (OR condition).
        title_ids : list[int] | None
            List of book IDs to filter by (OR condition).
        genre_ids : list[int] | None
            List of tag IDs to filter by (OR condition).
        publisher_ids : list[int] | None
            List of publisher IDs to filter by (OR condition).
        identifier_ids : list[int] | None
            List of identifier IDs to filter by (OR condition).
        series_ids : list[int] | None
            List of series IDs to filter by (OR condition).
        formats : list[str] | None
            List of format strings to filter by (OR condition).
        rating_ids : list[int] | None
            List of rating IDs to filter by (OR condition).
        language_ids : list[int] | None
            List of language IDs to filter by (OR condition).
        sort_by : str
            Field to sort by (default: 'timestamp').
        sort_order : str
            Sort order: 'asc' or 'desc' (default: 'desc').
        full : bool
            If True, return full book details with all metadata (default: False).

        Returns
        -------
        tuple[list[BookWithRelations | BookWithFullRelations], int]
            Tuple of (books with relations list, total count).
        """
        offset = (page - 1) * page_size
        books = self._book_repo.list_books_with_filters(
            limit=page_size,
            offset=offset,
            author_ids=author_ids,
            title_ids=title_ids,
            genre_ids=genre_ids,
            publisher_ids=publisher_ids,
            identifier_ids=identifier_ids,
            series_ids=series_ids,
            formats=formats,
            rating_ids=rating_ids,
            language_ids=language_ids,
            sort_by=sort_by,
            sort_order=sort_order,
            full=full,
        )
        total = self._book_repo.count_books_with_filters(
            author_ids=author_ids,
            title_ids=title_ids,
            genre_ids=genre_ids,
            publisher_ids=publisher_ids,
            identifier_ids=identifier_ids,
            series_ids=series_ids,
            formats=formats,
            rating_ids=rating_ids,
            language_ids=language_ids,
        )
        return books, total

    def add_book(
        self,
        file_path: Path,
        file_format: str,
        title: str | None = None,
        author_name: str | None = None,
    ) -> int:
        """Add a book directly to the Calibre library.

        Creates a book record in the database and saves the file to the library.
        Follows the same approach as calibre-web by directly manipulating the database.

        Parameters
        ----------
        file_path : Path
            Path to the uploaded book file (temporary location).
        file_format : str
            File format extension (e.g., 'epub', 'pdf', 'mobi').
        title : str | None
            Book title. If None, uses filename without extension.
        author_name : str | None
            Author name. If None, uses 'Unknown'.

        Returns
        -------
        int
            ID of the newly created book.

        Raises
        ------
        ValueError
            If file_path doesn't exist or file_format is invalid.
        """
        # Determine library path (prefer library_root if set)
        library_path = None
        lib_root = getattr(self._library, "library_root", None)
        if lib_root:
            library_path = Path(lib_root)
        else:
            library_path = Path(self._library.calibre_db_path)

        return self._book_repo.add_book(
            file_path=file_path,
            file_format=file_format,
            title=title,
            author_name=author_name,
            library_path=library_path,
        )

    def delete_book(
        self,
        book_id: int,
        delete_files_from_drive: bool = False,
    ) -> None:
        """Delete a book and all its related data.

        Performs atomic deletion with rollback on error.
        Follows SRP by delegating to repository.

        Parameters
        ----------
        book_id : int
            Calibre book ID to delete.
        delete_files_from_drive : bool
            If True, also delete files from filesystem (default: False).

        Raises
        ------
        ValueError
            If book not found.
        OSError
            If filesystem operations fail (only if delete_files_from_drive is True).
        """
        # Determine library path (prefer library_root if set)
        library_path = None
        lib_root = getattr(self._library, "library_root", None)
        if lib_root:
            library_path = Path(lib_root)
        else:
            library_path = Path(self._library.calibre_db_path)

        self._book_repo.delete_book(
            book_id=book_id,
            delete_files_from_drive=delete_files_from_drive,
            library_path=library_path,
        )

    def send_book_to_device(
        self,
        *,
        book_id: int,
        device: EReaderDevice,
        email_service: EmailService,
        file_format: str | None = None,
    ) -> None:
        """Send a book to an e-reader device via email.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        device : EReaderDevice
            E-reader device to send to.
        email_service : EmailService
            Email service instance.
        file_format : str | None
            Optional file format to send (e.g., 'EPUB', 'MOBI').
            If not provided, uses device's preferred format or first available format.

        Raises
        ------
        ValueError
            If book not found, no formats available, format not found,
            or file not found.
        """
        logger.info("Sending book %d to device %s", book_id, device.email)
        logger.debug(
            "Device: %s, requested format: %s", device.device_name, file_format
        )

        # Get book data
        book_with_rels = self.get_book_full(book_id)
        if book_with_rels is None:
            msg = "book_not_found"
            raise ValueError(msg)

        book = book_with_rels.book
        if book.id is None:
            msg = "book_missing_id"
            raise ValueError(msg)

        logger.debug("Book found: %s (ID: %d)", book.title, book_id)

        author_name = self._get_primary_author_name(book_with_rels)

        # Determine format to send
        format_to_send = self._determine_format_to_send(
            book_with_rels, device, file_format
        )
        logger.debug("Format determined: %s", format_to_send)

        # Find format data
        format_data = self._find_format_in_book(book_with_rels.formats, format_to_send)
        if format_data is None:
            available = [str(f.get("format", "")) for f in book_with_rels.formats]
            msg = f"format_not_found: requested '{format_to_send}', available: {available}"
            raise ValueError(msg)

        # Get file path
        file_path = self._get_book_file_path(book, book_id, format_data, format_to_send)
        logger.info("Sending file: %s", file_path)

        # Send email
        email_service.send_ebook(
            to_email=device.email,
            book_title=book.title,
            book_file_path=file_path,
            preferred_format=format_to_send,
            author=author_name,
        )
        logger.info("Book sent successfully to %s", device.email)

    def send_book(
        self,
        *,
        book_id: int,
        user_id: int,
        email_service: EmailService,
        to_email: str | None = None,
        file_format: str | None = None,
    ) -> None:
        """Send a book via email with intelligent device resolution.

        Handles three use cases:
        1. Generic email (to_email provided, not a known device) - sends without preferred format
        2. Known device email (to_email provided, matches a device) - uses device's preferred_format
        3. No email specified - uses default device or first device

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        user_id : int
            User ID for device lookups.
        email_service : EmailService
            Email service instance.
        to_email : str | None
            Optional email address to send to.
            If None, uses default device or first device.
        file_format : str | None
            Optional file format to send (e.g., 'EPUB', 'MOBI').
            If not provided, uses device's preferred format or first available format.

        Raises
        ------
        ValueError
            If book not found, no devices available when to_email is None,
            no formats available, format not found, or file not found.
        """
        if to_email:
            # Case 1 & 2: Email provided - check if it belongs to a device
            device = self._find_device_by_email(user_id, to_email)
            if device:
                # Case 2: Known device - use device's preferred_format
                logger.info(
                    "Sending book %d to known device %s (%s)",
                    book_id,
                    device.email,
                    device.device_name or "unnamed",
                )
                self.send_book_to_device(
                    book_id=book_id,
                    device=device,
                    email_service=email_service,
                    file_format=file_format,
                )
            else:
                # Case 1: Generic email - send without preferred format
                logger.info("Sending book %d to generic email %s", book_id, to_email)
                self.send_book_to_email(
                    book_id=book_id,
                    to_email=to_email,
                    email_service=email_service,
                    file_format=file_format,
                )
        else:
            # Case 3: No email specified - use default device or first device
            device = self._get_user_device(user_id)
            if device is None:
                msg = "no_device_available"
                raise ValueError(msg)
            logger.info(
                "Sending book %d to device %s (%s)",
                book_id,
                device.email,
                device.device_name or "unnamed",
            )
            self.send_book_to_device(
                book_id=book_id,
                device=device,
                email_service=email_service,
                file_format=file_format,
            )

    def _find_device_by_email(self, user_id: int, email: str) -> EReaderDevice | None:
        """Find a device by email address for a user.

        Parameters
        ----------
        user_id : int
            User ID.
        email : str
            Email address to search for.

        Returns
        -------
        EReaderDevice | None
            Device if found, None otherwise.
        """
        if self._session is None:
            logger.debug("No session available for device lookup")
            return None

        from fundamental.repositories.ereader_repository import EReaderRepository

        device_repo = EReaderRepository(self._session)
        device = device_repo.find_by_email(user_id, email)
        if device:
            logger.debug(
                "Found device for email %s: %s", email, device.device_name or "unnamed"
            )
        else:
            logger.debug("No device found for email %s", email)
        return device

    def _get_user_device(self, user_id: int) -> EReaderDevice | None:
        """Get user's device: default device, or first device if no default.

        Parameters
        ----------
        user_id : int
            User ID.

        Returns
        -------
        EReaderDevice | None
            Default device if found, otherwise first device, or None if no devices.
        """
        if self._session is None:
            logger.debug("No session available for device lookup")
            return None

        from fundamental.repositories.ereader_repository import EReaderRepository

        device_repo = EReaderRepository(self._session)
        # Try default device first
        device = device_repo.find_default(user_id)
        if device:
            logger.debug("Using default device: %s", device.email)
            return device

        # Fallback to first device
        devices = list(device_repo.find_by_user(user_id))
        if devices:
            logger.debug("Using first device: %s", devices[0].email)
            return devices[0]

        logger.debug("No devices found for user %d", user_id)
        return None

    def send_book_to_email(
        self,
        *,
        book_id: int,
        to_email: str,
        email_service: EmailService,
        file_format: str | None = None,
        preferred_format: str | None = None,
    ) -> None:
        """Send a book to an email address.

        Parameters
        ----------
        book_id : int
            Calibre book ID.
        to_email : str
            Email address to send to.
        email_service : EmailService
            Email service instance.
        file_format : str | None
            Optional file format to send (e.g., 'EPUB', 'MOBI').
            If not provided, uses preferred_format or first available format.
        preferred_format : str | None
            Optional preferred format name (e.g., 'EPUB', 'MOBI').
            Used if file_format is not provided.

        Raises
        ------
        ValueError
            If book not found, no formats available, format not found,
            or file not found.
        """
        logger.info("Sending book %d to email %s", book_id, to_email)
        logger.debug(
            "Requested format: %s, preferred format: %s", file_format, preferred_format
        )

        # Get book data
        book_with_rels = self.get_book_full(book_id)
        if book_with_rels is None:
            msg = "book_not_found"
            raise ValueError(msg)

        book = book_with_rels.book
        if book.id is None:
            msg = "book_missing_id"
            raise ValueError(msg)

        logger.debug("Book found: %s (ID: %d)", book.title, book_id)

        # Determine format to send
        format_to_send = file_format
        if format_to_send is None:
            format_to_send = preferred_format
        if format_to_send is None:
            # Use first available format
            if book_with_rels.formats:
                format_str = str(book_with_rels.formats[0].get("format", ""))
                if format_str:
                    format_to_send = format_str.upper()
                else:
                    msg = "no_formats_available"
                    raise ValueError(msg)
            else:
                msg = "no_formats_available"
                raise ValueError(msg)
        else:
            format_to_send = format_to_send.upper()

        logger.debug("Format determined: %s", format_to_send)

        # Find format data
        format_data = self._find_format_in_book(book_with_rels.formats, format_to_send)
        if format_data is None:
            available = [str(f.get("format", "")) for f in book_with_rels.formats]
            msg = f"format_not_found: requested '{format_to_send}', available: {available}"
            raise ValueError(msg)

        # Get file path
        file_path = self._get_book_file_path(book, book_id, format_data, format_to_send)
        logger.info("Sending file: %s", file_path)

        # Send email
        email_service.send_ebook(
            to_email=to_email,
            book_title=book.title,
            book_file_path=file_path,
            preferred_format=format_to_send,
            author=self._get_primary_author_name(book_with_rels),
        )
        logger.info("Book sent successfully to %s", to_email)

    def _determine_format_to_send(
        self,
        book_with_rels: BookWithFullRelations,
        device: EReaderDevice,
        requested_format: str | None,
    ) -> str:
        """Determine which format to send.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with all relations.
        device : EReaderDevice
            E-reader device.
        requested_format : str | None
            Requested format, if any.

        Returns
        -------
        str
            Format to send (uppercase).

        Raises
        ------
        ValueError
            If no formats are available.
        """
        if requested_format:
            return requested_format.upper()

        # Use device's preferred format if available
        if device.preferred_format:
            return device.preferred_format.value.upper()

        # Use first available format
        if book_with_rels.formats:
            format_str = str(book_with_rels.formats[0].get("format", ""))
            if format_str:
                return format_str.upper()

        msg = "no_formats_available"
        raise ValueError(msg)

    def _find_format_in_book(
        self,
        formats: list[dict[str, str | int]],
        requested_format: str,
    ) -> dict[str, str | int] | None:
        """Find format data matching the requested format.

        Parameters
        ----------
        formats : list[dict[str, str | int]]
            List of format dictionaries from book data.
        requested_format : str
            Requested file format (e.g., 'EPUB', 'PDF').

        Returns
        -------
        dict[str, str | int] | None
            Format data if found, None otherwise.
        """
        format_upper = requested_format.upper()
        for fmt in formats:
            fmt_format = fmt.get("format", "")
            if isinstance(fmt_format, str) and fmt_format.upper() == format_upper:
                return fmt
        return None

    def _get_book_file_path(
        self,
        book: Book,
        book_id: int,
        format_data: dict[str, str | int],
        file_format: str,
    ) -> Path:
        """Get the file path for a book format.

        Parameters
        ----------
        book : Book
            Book model.
        book_id : int
            Book ID.
        format_data : dict[str, str | int]
            Format data dictionary.
        file_format : str
            File format (e.g., 'EPUB', 'MOBI').

        Returns
        -------
        Path
            Path to the book file.

        Raises
        ------
        ValueError
            If file is not found.
        """
        # Determine library path
        lib_root = getattr(self._library, "library_root", None)
        if lib_root:
            library_path = Path(lib_root)
        else:
            library_db_path = Path(self._library.calibre_db_path)
            if library_db_path.is_dir():
                library_path = library_db_path
            else:
                library_path = library_db_path.parent

        book_path = library_path / book.path
        logger.debug("Book path: %s", book_path)
        file_name = self._get_file_name(format_data, book_id, file_format)
        file_path = book_path / file_name
        logger.debug("Trying file path: %s", file_path)

        if file_path.exists():
            logger.debug("File found at primary path: %s", file_path)
            return file_path

        # Try alternative: just the format extension
        format_lower = file_format.lower()
        alt_file_name = f"{book_id}.{format_lower}"
        alt_file_path = book_path / alt_file_name
        logger.debug("Trying alternative path: %s", alt_file_path)
        if alt_file_path.exists():
            logger.debug("File found at alternative path: %s", alt_file_path)
            return alt_file_path

        # Try to find file by extension in the directory
        if book_path.exists() and book_path.is_dir():
            logger.debug("Searching directory for %s files", format_lower)
            for file_in_dir in book_path.iterdir():
                if (
                    file_in_dir.is_file()
                    and file_in_dir.suffix.lower() == f".{format_lower}"
                ):
                    logger.debug("File found by directory search: %s", file_in_dir)
                    return file_in_dir

        msg = f"file_not_found: tried {file_path} and {alt_file_path}"
        logger.error(msg)
        raise ValueError(msg)

    def _get_file_name(
        self,
        format_data: dict[str, str | int],
        book_id: int,
        file_format: str,
    ) -> str:
        """Get filename for the book file.

        Parameters
        ----------
        format_data : dict[str, str | int]
            Format data dictionary, may contain 'name' field.
        book_id : int
            Calibre book ID.
        file_format : str
            File format (e.g., 'EPUB', 'PDF').

        Returns
        -------
        str
            Filename for the book file.
        """
        format_lower = file_format.lower()
        if format_data.get("name"):
            name = str(format_data["name"]).strip()
            if not name:
                logger.debug(
                    "Format name is empty, using book_id: %d.%s", book_id, format_lower
                )
                return f"{book_id}.{format_lower}"
            # Check if name already has the extension
            if name.lower().endswith(f".{format_lower}"):
                logger.debug("Using format name with extension: %s", name)
                return name
            # Append extension if not present
            filename = f"{name}.{format_lower}"
            logger.debug("Appended extension to format name: %s -> %s", name, filename)
            return filename
        logger.debug("No format name, using book_id: %d.%s", book_id, format_lower)
        return f"{book_id}.{format_lower}"

    @staticmethod
    def _get_primary_author_name(
        book_with_rels: BookWithFullRelations,
    ) -> str | None:
        """Get display name for book authors.

        Parameters
        ----------
        book_with_rels : BookWithFullRelations
            Book with related author data.

        Returns
        -------
        str | None
            Comma-separated author name(s) or None if no authors.
        """
        if not book_with_rels.authors:
            return None
        return ", ".join(book_with_rels.authors)
